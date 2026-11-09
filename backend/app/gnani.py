"""Gnani Vachana speech APIs: Prisma STT and Timbre TTS.

Latency measures: one persistent HTTPS connection pool, an in-memory + on-disk TTS cache (verses, helpline
text and repeated phrases are instant after the first time), requests serialised for accounts limited to one
active request (FIFO, so sentence order is preserved) and retried with backoff on 429/5xx.
"""
from __future__ import annotations

import asyncio
import hashlib
from collections import OrderedDict
from pathlib import Path

import httpx

from .config import Settings
from .lang import tts_voice

BASE = "https://api.vachana.ai"


class GnaniError(RuntimeError):
    def __init__(self, message: str, status: int = 502) -> None:
        super().__init__(message)
        self.status = status


TIMBRE_V3_VOICES = {
    "Chetana", "Shivani", "Lakshmi", "Kalpana", "Vasudha",
    "Riyaa", "Tarika", "Avinash", "Shubham", "Prakash",
    "Devansh", "Yashraj", "Harshad"
}

VOICE_MAP = {
    "Yashvi": "Shivani",
    "Poorvi": "Chetana",
    "Trupti": "Lakshmi",
    "Zahira": "Vasudha",
    "Trisha": "Riyaa",
    "Lehara": "Tarika",
    "Saanvi": "Kalpana",
    "Zayan": "Devansh",
}


class GnaniClient:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self._lock = asyncio.Semaphore(1)
        self._client: httpx.AsyncClient | None = None
        self._mem: OrderedDict[str, bytes] = OrderedDict()
        self._disk = Path(settings.tts_cache_dir)
        self.last_ms = {"stt": 0, "tts": 0}

    @property
    def enabled(self) -> bool:
        return bool(self.s.gnani_api_key)

    def _headers(self) -> dict:
        return {"X-API-Key-ID": self.s.gnani_api_key}

    def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(40.0, connect=8.0),
                                             limits=httpx.Limits(max_keepalive_connections=4))
        return self._client

    async def _post(self, path: str, **kw) -> httpx.Response:
        if not self.enabled:
            raise GnaniError("GNANI_API_KEY is not set", 503)
        last = ""
        async with self._lock:
            for attempt in range(3):
                try:
                    r = await self._http().post(f"{BASE}{path}", **kw)
                except httpx.HTTPError as e:
                    last = str(e)
                else:
                    if r.status_code in (429, 500, 502, 503):
                        last = f"HTTP {r.status_code}"
                    elif r.status_code >= 400:
                        raise GnaniError(f"Gnani HTTP {r.status_code}: {r.text[:300]}", 502)
                    else:
                        return r
                await asyncio.sleep(0.5 * (attempt + 1))
        raise GnaniError(f"Gnani unavailable ({last})", 503)

    async def transcribe(self, audio: bytes, filename: str = "speech.wav", language: str = "indic-auto",
                         keyterms: str = "") -> dict:
        import time
        t0 = time.perf_counter()
        data = {"model": self.s.gnani_stt_model, "language_code": language or "indic-auto", "format": "codemix"}
        if keyterms:
            data["keyterms"] = keyterms
        r = await self._post("/stt/v3", headers=self._headers(), data=data,
                             files={"audio_file": (filename, audio, "audio/wav")})
        try:
            j = r.json()
        except ValueError:
            raise GnaniError(f"Gnani STT returned non-JSON response: {r.text[:120]!r}", 502)
        self.last_ms["stt"] = int((time.perf_counter() - t0) * 1000)
        return {"transcript": (j.get("transcript") or "").strip(),
                "language": j.get("detected_language_code") or "", "ms": self.last_ms["stt"]}

    def _key(self, text: str, api_lang: str, voice: str, speed: float | None = None) -> str:
        spd = speed if speed is not None else self.s.tts_speed
        raw = f"{self.s.gnani_tts_model}|{voice}|{api_lang}|{spd}|{self.s.tts_sample_rate}|{text}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    async def synthesize(self, text: str, lang: str, voice: str | None = None, speed: float | None = None) -> tuple[bytes, str, bool]:
        """Returns (wav bytes, content type, from_cache)."""
        import time
        text = text.strip()
        if not text:
            raise GnaniError("cannot synthesize empty text", 400)
        api_lang, default_voice = tts_voice(lang, self.s.gnani_tts_model)
        chosen_voice = voice or default_voice
        if self.s.gnani_tts_model.startswith("timbre-v3"):
            if chosen_voice not in TIMBRE_V3_VOICES:
                chosen_voice = VOICE_MAP.get(chosen_voice, "Chetana")
            if chosen_voice not in TIMBRE_V3_VOICES:
                chosen_voice = "Chetana"
        chosen_speed = speed if speed is not None else self.s.tts_speed
        key = self._key(text, api_lang, chosen_voice, chosen_speed)
        if key in self._mem:
            self._mem.move_to_end(key)
            return self._mem[key], "audio/wav", True
        f = self._disk / f"{key}.wav"
        if f.exists():
            data = f.read_bytes()
            self._remember(key, data)
            return data, "audio/wav", True
        t0 = time.perf_counter()
        payload = {"text": text, "voice": chosen_voice, "model": self.s.gnani_tts_model, "language": api_lang,
                   "speed": chosen_speed,
                   "audio_config": {"encoding": "linear_pcm", "container": "wav", "num_channels": 1,
                                    "sample_rate": self.s.tts_sample_rate, "sample_width": 2}}
        r = await self._post("/api/v1/tts/inference", headers={**self._headers(), "Content-Type": "application/json"},
                             json=payload)
        self.last_ms["tts"] = int((time.perf_counter() - t0) * 1000)
        data = self._audio_bytes(r)
        self._remember(key, data)
        try:
            self._disk.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        except OSError:
            pass
        return data, "audio/wav", False

    @staticmethod
    def _audio_bytes(r: httpx.Response) -> bytes:
        """The docs show raw audio; tolerate a JSON envelope with base64 audio too."""
        import base64
        data = r.content
        if data[:4] == b"RIFF":
            return data
        try:
            j = r.json()
            for k in ("audio", "audio_content", "audioContent", "data"):
                v = j.get(k) if isinstance(j, dict) else None
                if isinstance(v, str) and v:
                    return base64.b64decode(v)
        except ValueError:
            pass
        raise GnaniError(f"Gnani TTS returned unexpected content: {data[:120]!r}", 502)

    def _remember(self, key: str, data: bytes) -> None:
        self._mem[key] = data
        while len(self._mem) > 64:
            self._mem.popitem(last=False)

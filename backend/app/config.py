"""Settings read from environment variables (and an optional .env file).

Nothing here is cached at import time except the .env load, so tests can
monkeypatch os.environ and call get_settings() again.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT = BACKEND_DIR.parent
FRONTEND_DIR = ROOT / "frontend"
CORPUS_DIR = BACKEND_DIR / "data" / "corpus"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")
_load_dotenv(BACKEND_DIR / ".env")

# provider -> (default base url, default model, env var holding its key)
PROVIDER_PRESETS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "GROQ_API_KEY"),
    "ollama": ("http://localhost:11434", "qwen2.5:7b", ""),
    "openai_compat": ("", "", "LLM_API_KEY"),  # vLLM, Together, OpenRouter, HF endpoints...
    "gemini": ("https://generativelanguage.googleapis.com/v1beta", "gemini-3.1-flash-lite", "GEMINI_API_KEY"),
}


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_fallback_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    groq_api_key: str
    gemini_api_key: str
    llm_api_key: str
    gnani_api_key: str
    gnani_stt_model: str
    gnani_tts_model: str
    tts_speed: float
    embed_model: str
    allowed_origins: tuple[str, ...]
    rate_limit_per_min: int
    show_book_excerpts: bool
    ollama_host: str
    llm_max_tokens: int
    tts_sample_rate: int
    gita_dir: str
    index_dir: str
    tts_cache_dir: str
    chroma_dir: str


def _f(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def get_settings() -> Settings:
    groq_k = _f("GROQ_API_KEY") or _f("GROQ_KEY") or _f("LLM_API_KEY")
    gemini_k = _f("GEMINI_API_KEY") or _f("API_KEY")

    # Auto-detect if user pasted a Groq key (starts with gsk_) into GEMINI_API_KEY
    if gemini_k.startswith("gsk_"):
        if not groq_k:
            groq_k = gemini_k
        gemini_k = ""

    # Auto-detect provider if not explicitly specified
    provider = (_f("LLM_PROVIDER") or "").lower()
    if not provider:
        if groq_k:
            provider = "groq"
        elif gemini_k:
            provider = "gemini"
        else:
            provider = "mock"
    elif provider == "gemini" and not gemini_k and groq_k:
        provider = "groq"
    elif provider == "groq" and not groq_k and gemini_k:
        provider = "gemini"

    # Auto-correct model when provider and model mismatch
    model = _f("LLM_MODEL")
    if provider == "groq" and (not model or "gemini" in model.lower() or "qwen" in model.lower()):
        model = "llama-3.3-70b-versatile"
    elif provider == "gemini" and (not model or "llama" in model.lower() or "qwen" in model.lower() or "mixtral" in model.lower()):
        model = "gemini-3.1-flash-lite"

    origins = tuple(o.strip() for o in _f("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,*").split(",") if o.strip())
    return Settings(
        llm_provider=provider,
        llm_fallback_provider=_f("LLM_FALLBACK_PROVIDER", "mock").lower(),
        llm_model=model,
        llm_base_url=_f("LLM_BASE_URL"),
        llm_temperature=float(_f("LLM_TEMPERATURE", "0.7")),
        groq_api_key=groq_k,
        gemini_api_key=gemini_k,
        llm_api_key=_f("LLM_API_KEY") or groq_k,
        gnani_api_key=_f("GNANI_API_KEY"),
        gnani_stt_model=_f("GNANI_STT_MODEL", "prisma-v3.0"),
        gnani_tts_model=_f("GNANI_TTS_MODEL", "timbre-v2.5"),
        tts_speed=float(_f("GNANI_TTS_SPEED", "0.95")),
        embed_model=_f("EMBED_MODEL", "bge-m3"),
        allowed_origins=origins,
        rate_limit_per_min=int(_f("RATE_LIMIT_PER_MIN", "30")),
        show_book_excerpts=_f("SHOW_BOOK_EXCERPTS", "0") == "1",
        ollama_host=_f("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
        llm_max_tokens=int(_f("LLM_MAX_TOKENS", "260")),
        tts_sample_rate=int(_f("GNANI_TTS_SAMPLE_RATE", "48000")),
        gita_dir=_f("GITA_DIR", str(BACKEND_DIR / "data" / "gita")),
        index_dir=_f("INDEX_DIR", str(BACKEND_DIR / "data" / "index")),
        tts_cache_dir=_f("TTS_CACHE_DIR", str(BACKEND_DIR / "data" / "tts_cache")),
        chroma_dir=_f("CHROMA_DIR", str(BACKEND_DIR / "data" / "chroma_db")),
    )

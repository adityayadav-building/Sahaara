"""Sahaara API & Voice Gateway. Run: uvicorn app.main:app --reload --port 8000 (from backend/)."""
from __future__ import annotations

import asyncio
import base64
import datetime as dt
import json
import re
import time
import uuid
import logging
from contextlib import asynccontextmanager
from collections import defaultdict, deque

logger = logging.getLogger("sahaara")

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, breathing, grounding, prompts, safety
from .config import FRONTEND_DIR, get_settings
from .gnani import GnaniClient, GnaniError
from .lang import LANGUAGES, is_hindi_family, resolve_language
from .llm import LLMError, build_providers
from .rag.embed import OllamaEmbedder
from .rag.retriever import Hit, Retriever, to_card
from .rag.topics import detect_topics, is_smalltalk, wants_breathing
from .textutil import StreamCleaner, tts_prepare
from .voice import get_voice_catalog, match_intent, plan_delivery, VoiceSession, SessionState

SUGGESTIONS = {
    "en": ["I feel anxious about my exam", "I can't stop overthinking", "I feel very lonely", "I'm angry and can't calm down",
           "I can't sleep at night", "Guide me through breathing"],
    "hi": ["मुझे परीक्षा की चिंता हो रही है", "मैं बहुत ज़्यादा सोचता हूँ", "मुझे अकेलापन लग रहा है", "मुझे बहुत गुस्सा आता है",
           "मुझे नींद नहीं आती", "मुझे साँस की एक्सरसाइज़ कराइए"],
}


class Msg(BaseModel):
    role: str
    content: str = Field(max_length=2000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1500)
    history: list[Msg] = Field(default_factory=list, max_length=20)
    language: str = "auto"
    stt_language: str | None = None


class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=900)
    language: str = "en-IN"
    voice: str | None = None
    speed: float | None = None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app() -> FastAPI:
    s = get_settings()
    embedder = OllamaEmbedder(s.ollama_host, s.embed_model) if s.embed_model else None
    retriever = Retriever(settings=s, embedder=embedder)
    providers = build_providers(s)
    gnani = GnaniClient(s)

    @asynccontextmanager
    async def lifespan(_app):
        async def warm():  # load warm models before first user message
            for p in providers:
                if hasattr(p, "warm"):
                    await p.warm()
            if retriever.dense_ready:
                await retriever.embed_query("warm up")
        task = asyncio.create_task(warm())
        yield
        task.cancel()

    app = FastAPI(title="Sahaara", version=__version__, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(s.allowed_origins), allow_methods=["*"], allow_headers=["*"])
    hits_by_ip: dict[str, deque] = defaultdict(deque)

    def limited(request: Request) -> None:
        ip = request.client.host if request.client else "?"
        q, now = hits_by_ip[ip], time.time()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= s.rate_limit_per_min:
            raise HTTPException(429, "Too many requests, please slow down.")
        q.append(now)

    @app.get("/api/health")
    def health():
        return {"ok": True, "version": __version__, "llm": [f"{p.name}:{p.model}" for p in providers],
                "gnani": gnani.enabled, "gita_corpus": retriever.has_gita, "dense_retrieval": retriever.dense_ready,
                "embed_model": s.embed_model, "stt_model": s.gnani_stt_model, "tts_model": s.gnani_tts_model,
                "corpus_chunks": len(retriever), "languages": LANGUAGES}

    @app.get("/api/voices")
    def voices():
        return {"voices": get_voice_catalog()}

    @app.get("/api/helplines")
    def helplines():
        return {"helplines": safety.HELPLINES}

    @app.get("/api/suggestions")
    def suggestions(language: str = "en-IN"):
        return {"suggestions": SUGGESTIONS["hi" if is_hindi_family(language) and language != "hi-en" else "en"]}

    @app.get("/api/verse/daily")
    def verse_daily(language: str = "en-IN"):
        verses = [c for c in retriever.by_type("shloka") if c.topics] or retriever.by_type("shloka")
        c = verses[dt.date.today().toordinal() % len(verses)]
        return to_card(c, language, 1)

    @app.get("/api/breathe/{pattern}")
    def breathe(pattern: str, language: str = "en-IN"):
        p = breathing.get_pattern(pattern, language)
        if not p:
            raise HTTPException(404, "unknown pattern")
        return p

    @app.post("/api/chat")
    async def chat(body: ChatIn, request: Request):
        limited(request)
        history = [m for m in body.history if m.role in ("user", "assistant")][-10:]
        prior_user = [m.content for m in history if m.role == "user"]
        prior_assistant = [m.content for m in history if m.role == "assistant"]
        lang = resolve_language(body.language, body.stt_language, body.message)
        
        # 1. Quick intent check (repeat, slower, faster, stop)
        last_bot = prior_assistant[-1] if prior_assistant else ""
        intent_match = match_intent(body.message, current_speed=s.tts_speed, last_response=last_bot)
        if intent_match and intent_match.action in ("stop", "replay", "set_speed", "set_lang"):
            async def intent_gen():
                yield _sse("meta", {"lang": intent_match.new_lang or lang, "safety": "none", "provider": "intent"})
                yield _sse("token", {"t": intent_match.response_text})
                yield _sse("done", {"text": intent_match.response_text, "cited": [], "provider": "intent"})
            return StreamingResponse(intent_gen(), media_type="text/event-stream")

        sres = safety.assess(body.message, prior_user)

        async def gen():
            base = {"lang": lang, "safety": sres.level}
            if sres.level == "crisis":
                yield _sse("meta", {**base, "helplines": safety.HELPLINES, "provider": "safety"})
                yield _sse("token", {"t": safety.crisis_message(lang)})
                yield _sse("done", {"text": safety.crisis_message(lang), "cited": [], "crisis": True})
                return
            small = is_smalltalk(body.message)
            
            # Prioritize current message topics so new turns don't get trapped in past topics
            topics = detect_topics(body.message)
            if not topics and prior_user:
                topics = detect_topics(" ".join(prior_user[-2:]))
                
            t_start = time.perf_counter()
            hits = [] if small else await retriever.aretrieve(body.message, topics)
            retrieve_ms = int((time.perf_counter() - t_start) * 1000)
            if wants_breathing(body.message) and not any(h.chunk.type == "practice" for h in hits):
                lb = retriever.get("practice-long-exhale")
                if lb:
                    hits.append(Hit(lb, 1.0))
            cards = [to_card(h.chunk, lang, i, s.show_book_excerpts) for i, h in enumerate(hits, 1)]
            note = safety.CONCERN_PROMPT_NOTE if sres.level == "concern" else ""
            meta = {**base, "topics": [t for t, _ in topics]}
            if sres.show_helpline:
                meta["helplines"] = safety.HELPLINES
            system = prompts.build_system(lang, hits, note, small)
            msgs = [{"role": m.role, "content": m.content} for m in history] + [{"role": "user", "content": body.message}]
            text, cited, used, ttft = "", [], None, None
            for p in providers:
                if p.name == "mock":
                    continue
                cleaner = StreamCleaner()
                try:
                    started = False
                    async for chunk in p.stream(system, msgs, s.llm_temperature, s.llm_max_tokens):
                        out = cleaner.feed(chunk)
                        if out:
                            if ttft is None:
                                ttft = int((time.perf_counter() - t_start) * 1000)
                            if not started:
                                yield _sse("meta", {**meta, "provider": p.name})
                                yield _sse("sources", {"sources": cards})
                                started = True
                            yield _sse("token", {"t": out})
                    tail = cleaner.flush()
                    if tail:
                        if not started:
                            yield _sse("meta", {**meta, "provider": p.name})
                            yield _sse("sources", {"sources": cards})
                            started = True
                        yield _sse("token", {"t": tail})
                    if started and cleaner.clean:
                        text, cited, used = cleaner.clean, cleaner.cited, p.name
                        break
                except LLMError as e:
                    print(f"[Chat LLM Error from {p.name}]: {e}", flush=True)
                    if started:  # partial text already shown: keep it rather than restarting
                        text, cited, used = cleaner.clean, cleaner.cited, p.name
                        break
                    continue
            if used is None:  # no provider answered: grounded extractive reply
                text, cited = prompts.extractive_reply(hits, lang, small)
                yield _sse("meta", {**meta, "provider": "extractive"})
                yield _sse("sources", {"sources": cards})
                yield _sse("token", {"t": text})
            clean, issues = grounding.sanitize(text)
            cited = grounding.valid_citations(cited, len(cards))
            yield _sse("done", {"text": clean, "cited": cited, "issues": issues, "provider": used or "extractive",
                                "timing": {"retrieve_ms": retrieve_ms, "ttft_ms": ttft,
                                           "total_ms": int((time.perf_counter() - t_start) * 1000)}})

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.websocket("/api/voice")
    async def voice_ws(ws: WebSocket):
        """Voice Gateway: full-duplex WebSocket with state machine, barge-in, delivery planning, and audio queue."""
        await ws.accept()
        session_id = str(uuid.uuid4())
        session = VoiceSession(session_id=session_id, speed=s.tts_speed, voice="Chetana", lang="auto")
        
        async def send_event(event: str, data: dict):
            try:
                await ws.send_json({"event": event, **data})
            except Exception:
                pass

        async def send_audio_chunk(audio_data: bytes, chunk_idx: int, is_final: bool = False):
            try:
                await send_event("audio_meta", {"chunk_index": chunk_idx, "is_final": is_final})
                await ws.send_bytes(audio_data)
            except Exception:
                pass

        async def process_voice_turn(user_text: str, user_lang: str = "auto"):
            session.cancel_active_turn()
            current_task = asyncio.current_task()
            session.active_task = current_task

            # State -> HEARING
            session.set_state(SessionState.HEARING)
            await send_event("state", {"state": SessionState.HEARING.value, "transcript": user_text})
            session.last_user_text = user_text

            lang = resolve_language(session.lang if session.lang != "auto" else user_lang, user_lang, user_text)

            # 1. Voice Intent Check (0ms LLM latency)
            intent = match_intent(user_text, current_speed=session.speed, last_response=session.last_bot_text, last_verse=session.last_verse_text)
            if intent:
                if intent.action == "set_speed" and intent.new_speed:
                    session.speed = intent.new_speed
                if intent.action == "set_lang" and intent.new_lang:
                    session.lang = intent.new_lang
                    lang = intent.new_lang

                session.set_state(SessionState.SPEAKING)
                await send_event("state", {"state": SessionState.SPEAKING.value})
                await send_event("token", {"t": intent.response_text})

                # Synthesize immediate audio
                try:
                    audio_bytes, ctype, _ = await gnani.synthesize(intent.response_text, lang, voice=session.voice, speed=session.speed)
                    await send_audio_chunk(audio_bytes, 0, True)
                except Exception:
                    pass

                session.add_history("user", user_text)
                session.add_history("assistant", intent.response_text)
                session.last_bot_text = intent.response_text
                session.set_state(SessionState.LISTENING)
                await send_event("state", {"state": SessionState.LISTENING.value})
                await send_event("done", {"text": intent.response_text, "cited": []})
                return

            # 2. Safety Check
            prior_user = [m["content"] for m in session.history if m["role"] == "user"]
            sres = safety.assess(user_text, prior_user)
            if sres.level == "crisis":
                crisis_msg = safety.crisis_message(lang)
                session.set_state(SessionState.SPEAKING)
                await send_event("state", {"state": SessionState.SPEAKING.value})
                await send_event("token", {"t": crisis_msg})
                try:
                    crisis_audio_text = plan_delivery(crisis_msg, ["crisis"], is_crisis=True)
                    audio_bytes, _, _ = await gnani.synthesize(crisis_audio_text, lang, voice=session.voice, speed=session.speed)
                    await send_audio_chunk(audio_bytes, 0, True)
                except Exception:
                    pass
                await send_event("done", {"text": crisis_msg, "crisis": True, "helplines": safety.HELPLINES})
                session.set_state(SessionState.LISTENING)
                await send_event("state", {"state": SessionState.LISTENING.value})
                return

            # 3. State -> THINKING (RAG + Prompt Generation)
            session.set_state(SessionState.THINKING)
            await send_event("state", {"state": SessionState.THINKING.value})

            topics = detect_topics(user_text)
            if not topics and prior_user:
                topics = detect_topics(" ".join(prior_user[-2:]))
            topic_names = [t for t, _ in topics]

            small = is_smalltalk(user_text)
            hits = [] if small else await retriever.aretrieve(user_text, topics)
            if wants_breathing(user_text) and not any(h.chunk.type == "practice" for h in hits):
                lb = retriever.get("practice-long-exhale")
                if lb:
                    hits.append(Hit(lb, 1.0))
            cards = [to_card(h.chunk, lang, i, s.show_book_excerpts) for i, h in enumerate(hits, 1)]
            await send_event("sources", {"sources": cards})

            # Record primary shloka for 'read verse again' intent
            for c in cards:
                if c.get("type") == "shloka":
                    session.last_verse_text = f"{c.get('title', '')}. {c.get('devanagari', '')} {c.get('meaning', '')}"
                    break

            system = prompts.build_system(lang, hits, smalltalk=small)
            msgs = [{"role": m["role"], "content": m["content"]} for m in session.history[-8:]] + [{"role": "user", "content": user_text}]

            # 4. Stream Tokens & Synthesize Audio Chunks
            session.set_state(SessionState.SPEAKING)
            await send_event("state", {"state": SessionState.SPEAKING.value})

            full_text = ""
            chunk_idx = 0
            sentence_buf = ""

            async def synthesize_and_send(sentence: str, is_final_chunk: bool = False):
                nonlocal chunk_idx
                s_clean = tts_prepare(sentence)
                if not s_clean:
                    return
                try:
                    delivered = plan_delivery(s_clean, topic_names)
                    audio_bytes, _, _ = await gnani.synthesize(delivered, lang, voice=session.voice, speed=session.speed)
                    await send_audio_chunk(audio_bytes, chunk_idx, is_final_chunk)
                    chunk_idx += 1
                except Exception as e:
                    logger.debug(f"WS audio chunk synthesis error: {e}")

            for p in providers:
                if p.name == "mock":
                    continue
                cleaner = StreamCleaner()
                try:
                    async for token_chunk in p.stream(system, msgs, s.llm_temperature, s.llm_max_tokens):
                        if current_task.cancelled():
                            return
                        out = cleaner.feed(token_chunk)
                        if out:
                            await send_event("token", {"t": out})
                            sentence_buf += out
                            m = re.search(r"([\s\S]+?[.!?।\n])\s+", sentence_buf)
                            if m and len(m.group(1).strip()) >= 25:
                                ready_sentence = m.group(1).strip()
                                sentence_buf = sentence_buf[m.end():]
                                await synthesize_and_send(ready_sentence, is_final_chunk=False)

                    tail = cleaner.flush()
                    if tail:
                        await send_event("token", {"t": tail})
                        sentence_buf += tail
                    full_text = cleaner.clean
                    break
                except Exception as e:
                    print(f"[Voice WS LLM Exception from {p.name}]: {e}", flush=True)
                    continue

            if not full_text:
                full_text, _ = prompts.extractive_reply(hits, lang, small)
                await send_event("token", {"t": full_text})
                sentence_buf = full_text

            if sentence_buf.strip() and not current_task.cancelled():
                await synthesize_and_send(sentence_buf.strip(), is_final_chunk=True)

            clean, issues = grounding.sanitize(full_text)
            session.add_history("user", user_text)
            session.add_history("assistant", clean)
            session.last_bot_text = clean

            await send_event("done", {"text": clean, "cited": [1] if cards else []})
            session.set_state(SessionState.LISTENING)
            await send_event("state", {"state": SessionState.LISTENING.value})

        # Main WebSocket loop
        try:
            await send_event("ready", {"session_id": session_id, "state": SessionState.LISTENING.value})
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    break

                if "text" in msg:
                    data = json.loads(msg["text"])
                    mtype = data.get("type")

                    if mtype == "barge_in":
                        cancelled = session.cancel_active_turn()
                        await send_event("barge_in_ack", {"cancelled": cancelled, "state": SessionState.LISTENING.value})

                    elif mtype == "init":
                        session.voice = data.get("voice", session.voice)
                        session.speed = float(data.get("speed", session.speed))
                        session.lang = data.get("lang", session.lang)
                        session.is_handsfree = bool(data.get("handsfree", False))
                        await send_event("init_ack", {"voice": session.voice, "speed": session.speed})

                    elif mtype == "text":
                        user_text = data.get("text", "").strip()
                        if user_text:
                            asyncio.create_task(process_voice_turn(user_text, data.get("lang", session.lang)))

                    elif mtype == "audio_base64":
                        raw_b64 = data.get("audio", "")
                        if raw_b64:
                            audio_bytes = base64.b64decode(raw_b64)
                            session.set_state(SessionState.HEARING)
                            await send_event("state", {"state": SessionState.HEARING.value})
                            stt_res = await gnani.transcribe(audio_bytes, language=session.lang if session.lang != "auto" else "indic-auto")
                            transcript = stt_res.get("transcript", "").strip()
                            det_lang = stt_res.get("language", "en-IN")
                            if transcript:
                                asyncio.create_task(process_voice_turn(transcript, det_lang))
                            else:
                                session.set_state(SessionState.LISTENING)
                                await send_event("state", {"state": SessionState.LISTENING.value})

                elif "bytes" in msg:
                    # Binary WAV from client worklet
                    audio_bytes = msg["bytes"]
                    session.set_state(SessionState.HEARING)
                    await send_event("state", {"state": SessionState.HEARING.value})
                    stt_res = await gnani.transcribe(audio_bytes, language=session.lang if session.lang != "auto" else "indic-auto")
                    transcript = stt_res.get("transcript", "").strip()
                    det_lang = stt_res.get("language", "en-IN")
                    if transcript:
                        asyncio.create_task(process_voice_turn(transcript, det_lang))
                    else:
                        session.set_state(SessionState.LISTENING)
                        await send_event("state", {"state": SessionState.LISTENING.value})

        except WebSocketDisconnect:
            pass
        finally:
            session.cancel_active_turn()

    @app.post("/api/stt")
    async def stt(request: Request, audio: UploadFile = File(...), language: str = Form("indic-auto")):
        limited(request)
        data = await audio.read()
        if not data or len(data) > 4_000_000:
            raise HTTPException(400, "audio missing or too large")
        try:
            return await gnani.transcribe(data, audio.filename or "speech.wav", language)
        except GnaniError as e:
            return JSONResponse({"error": str(e)}, status_code=e.status)

    @app.post("/api/tts")
    async def tts(body: TtsIn, request: Request):
        limited(request)
        text = tts_prepare(body.text)
        if not text:
            raise HTTPException(400, "nothing to speak")
        try:
            audio, ctype, cached = await gnani.synthesize(text, body.language, voice=body.voice, speed=body.speed)
        except GnaniError as e:
            logger.warning(f"[TTS Error] {e} (for text: {text[:40]!r})")
            return JSONResponse({"error": str(e)}, status_code=e.status)
        return Response(audio, media_type=ctype, headers={"X-Cache": "hit" if cached else "miss"})

    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="web")
    return app


app = create_app()

import json
from fastapi.testclient import TestClient
from app import grounding, safety
from app.lang import detect_language, resolve_language
from app.main import create_app
from app.rag.retriever import Retriever
from app.rag.topics import is_smalltalk
from app.textutil import StreamCleaner, chunk_for_tts, spoken_digits

c = TestClient(create_app())
R = Retriever()


def events(text):
    out = []
    for blk in text.strip().split("\n\n"):
        ev, data = blk.split("\n", 1)
        out.append((ev[7:], json.loads(data[6:])))
    return out


def test_crisis_bypasses_llm_and_shows_helpline():
    ev = events(c.post("/api/chat", json={"message": "I want to end my life"}).text)
    assert ev[0][1]["provider"] == "safety" and ev[-1][1]["crisis"]
    assert "14416" in ev[-1][1]["text"]


def test_crisis_hindi_and_hinglish():
    assert safety.assess("मैं मरना चाहता हूँ").level == "crisis"
    assert safety.assess("mujhe jeena nahi hai, suicide karna hai").level == "crisis"


def test_idiom_not_crisis():
    assert safety.assess("this exam is killing me, I'm dead tired").level != "crisis"


def test_retrieval_uses_real_gita_corpus():
    assert R.has_gita
    hits = R.retrieve("I'm so anxious about my exam result")
    ids = [h.chunk.id for h in hits]
    assert any(i in ids for i in ("gita-2-47", "gita-2-48", "gita-2-38"))
    assert any(i.startswith(("practice-", "tool-")) for i in ids)
    assert hits[0].chunk.extra.get("devanagari")  # verse card carries the Sanskrit
    assert "practice-sleep" in [h.chunk.id for h in R.retrieve("I can't sleep at night")]


def test_smalltalk():
    assert is_smalltalk("hi") and not is_smalltalk("breathing please")


def test_language_detection():
    assert detect_language("मुझे चिंता है") == "hi-IN"
    assert detect_language("mujhe bahut tension hai yaar") == "hi-en"
    assert detect_language("I am worried") == "en-IN"
    assert resolve_language("ta-IN", None, "hello") == "ta-IN"


def test_stream_cleaner_strips_think_and_markers():
    s = StreamCleaner()
    out = "".join(s.feed(x) for x in ["<thi", "nk>plan</think>Take a b", "reath [S", "1]. Slowly.[S2]"]) + s.flush()
    assert "think" not in out and "[S" not in out and s.cited == [1, 2]


def test_grounding_strips_invented_refs():
    t, issues = grounding.sanitize("As Gita 2.47 says, act. कर्मण्येवाधिकारस्ते ॥")
    assert "2.47" not in t and "ॐ" not in t and issues
    assert grounding.valid_citations([1, 5, 1, 2], 2) == [1, 2]


def test_tts_helpers():
    assert spoken_digits("call 14416") == "call 1 4 4 1 6"
    assert all(len(x) <= 260 for x in chunk_for_tts("word " * 200))


def test_api_basics():
    assert c.get("/api/health").json()["ok"]
    assert c.get("/api/breathe/box").json()["phases"]
    assert c.get("/api/breathe/nope").status_code == 404
    assert c.post("/api/tts", json={"text": "hello"}).status_code == 503  # no Gnani key


def test_chat_fallback_is_grounded():
    ev = events(c.post("/api/chat", json={"message": "I feel very lonely", "language": "en-IN"}).text)
    done = ev[-1][1]
    assert done["provider"] == "extractive" and done["text"]


def test_voice_intents():
    from app.voice import match_intent
    # Slower
    res = match_intent("please speak slower", current_speed=1.0)
    assert res and res.intent == "slower" and res.new_speed == 0.9
    # Faster in Hindi
    res = match_intent("thoda tez bolo", current_speed=0.9)
    assert res and res.intent == "faster" and res.new_speed == 1.0
    # Stop
    res = match_intent("ruko", current_speed=1.0)
    assert res and res.intent == "stop"
    # Repeat
    res = match_intent("repeat that", last_response="Peace comes from within.")
    assert res and res.intent == "repeat" and "Peace comes from within." in res.response_text


def test_delivery_planner():
    from app.voice import plan_delivery, strip_tags
    # Crisis delivery
    d_crisis = plan_delivery("Help is available.", ["crisis"], is_crisis=True)
    assert "<slow>" in d_crisis
    # Verse delivery
    d_verse = plan_delivery("karmany evadhikaras te", ["peace"], is_verse=True)
    assert "<slow>" in d_verse and "<pauses>" in d_verse
    # Sleep delivery
    d_sleep = plan_delivery("Breathe out slowly.", ["sleep"])
    assert "<whispers>" in d_sleep
    # Tag stripping
    clean = strip_tags("<slow> <pauses> Take a breath. </slow>")
    assert clean == "Take a breath."


def test_voice_catalog_and_voices():
    r = c.get("/api/voices").json()
    assert "voices" in r
    voice_ids = {v["id"] for v in r["voices"]}
    assert "Chetana" in voice_ids and "Shivani" in voice_ids
    assert len(voice_ids) == 13


def test_tts_empty_validation():
    # Pure commas / punctuation should return 400 Bad Request
    assert c.post("/api/tts", json={"text": ",,, ..."}).status_code == 400


def test_retriever_backend_dir_fallback():
    from app.config import get_settings
    s = get_settings()
    # Test initialization with empty chroma_dir to verify BACKEND_DIR fallback
    ret = Retriever(chunks=[], settings=s, load_index=False)
    assert len(ret) == 0

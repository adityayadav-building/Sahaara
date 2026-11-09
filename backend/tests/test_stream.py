"""End-to-end: Qwen-style NDJSON stream from a fake Ollama -> SSE tokens, cleaned, with citations."""
import json
import socket
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

fake = FastAPI()
REPLY = ["<think>x</think>I can feel how heavy this is", " for you. [S1] Do your best without", " clinging to the result. [S1]", " Try one slow breath. [S3]"]


@fake.post("/api/chat")
async def chat(body: dict):
    async def gen():
        for t in REPLY:
            yield json.dumps({"message": {"role": "assistant", "content": t}, "done": False}) + "\n"
        yield json.dumps({"done": True}) + "\n"
    if body.get("stream") is False:
        return {"done": True}
    return StreamingResponse(gen(), media_type="application/x-ndjson")


@pytest.fixture(scope="module")
def ollama():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(fake, port=port, log_level="error"))
    th = threading.Thread(target=srv.run, daemon=True); th.start(); time.sleep(0.8)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True


def test_ollama_stream_to_sse(ollama, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama"); monkeypatch.setenv("OLLAMA_HOST", ollama)
    from app.main import create_app
    c = TestClient(create_app())
    r = c.post("/api/chat", json={"message": "I am anxious about my exam", "language": "en-IN"})
    events = [(b.split("\n", 1)[0][7:], json.loads(b.split("\n", 1)[1][6:])) for b in r.text.strip().split("\n\n")]
    kinds = [k for k, _ in events]
    assert kinds[0] == "meta" and "sources" in kinds and kinds[-1] == "done"
    done = events[-1][1]
    assert done["provider"] == "ollama" and "<think>" not in done["text"] and "[S" not in done["text"]
    assert done["cited"] and done["timing"]["ttft_ms"] is not None
    assert "".join(d["t"] for k, d in events if k == "token").strip() == done["text"]

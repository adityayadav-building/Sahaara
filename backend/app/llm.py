"""Swappable LLM providers. Switch with LLM_PROVIDER=groq|gemini|ollama|openai_compat|mock in .env.

Every provider exposes: `async stream(system, messages, temperature, max_tokens) -> AsyncIterator[str]`
where messages = [{"role": "user"|"assistant", "content": str}, ...].
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from .config import PROVIDER_PRESETS, Settings


class LLMError(RuntimeError):
    pass


_TIMEOUT = httpx.Timeout(60.0, connect=5.0)
_CLIENT: httpx.AsyncClient | None = None


def client() -> httpx.AsyncClient:
    """One shared connection pool: no TLS/TCP handshake on every request."""
    global _CLIENT
    if _CLIENT is None or _CLIENT.is_closed:
        _CLIENT = httpx.AsyncClient(timeout=_TIMEOUT, limits=httpx.Limits(max_keepalive_connections=8))
    return _CLIENT


async def _sse_lines(resp: httpx.Response) -> AsyncIterator[str]:
    async for line in resp.aiter_lines():
        if line.startswith("data:"):
            yield line[5:].strip()


class OpenAICompatProvider:
    """Groq, Ollama (Qwen2.5 7B etc.), vLLM, Together, OpenRouter: anything speaking /chat/completions."""

    def __init__(self, name: str, base_url: str, model: str, api_key: str = "") -> None:
        if not base_url or not model:
            raise LLMError(f"{name}: base URL and model are required (set LLM_BASE_URL / LLM_MODEL)")
        self.name, self.base_url, self.model, self.api_key = name, base_url.rstrip("/"), model, api_key

    async def stream(self, system: str, messages: list[dict], temperature: float = 0.7,
                     max_tokens: int = 260) -> AsyncIterator[str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {"model": self.model, "stream": True, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, *messages]}
        try:
            cx = client()
            async with cx.stream("POST", f"{self.base_url}/chat/completions", json=body, headers=headers) as r:
                if r.status_code >= 400:
                    detail = (await r.aread()).decode("utf-8", "ignore")[:200]
                    raise LLMError(f"{self.name} HTTP {r.status_code}: {detail}")
                async for data in _sse_lines(r):
                    if data == "[DONE]":
                        return
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content")
                    except (ValueError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta
        except httpx.HTTPError as e:
            raise LLMError(f"{self.name} network error: {e}") from e


class OllamaProvider:
    """Native Ollama /api/chat: keeps the model resident (keep_alive) and fixes the context size."""

    def __init__(self, host: str, model: str) -> None:
        self.name, self.host, self.model = "ollama", host.rstrip("/"), model

    def _body(self, system: str, messages: list[dict], temperature: float, max_tokens: int, stream: bool = True) -> dict:
        return {"model": self.model, "stream": stream, "keep_alive": "60m",
                "messages": [{"role": "system", "content": system}, *messages],
                "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 4096, "top_p": 0.9}}

    async def warm(self) -> None:
        try:
            await client().post(f"{self.host}/api/chat", json=self._body("Reply with OK.", [{"role": "user", "content": "hi"}], 0.0, 1, False))
        except httpx.HTTPError:
            pass

    async def stream(self, system: str, messages: list[dict], temperature: float = 0.7,
                     max_tokens: int = 260) -> AsyncIterator[str]:
        try:
            async with client().stream("POST", f"{self.host}/api/chat",
                                       json=self._body(system, messages, temperature, max_tokens)) as r:
                if r.status_code >= 400:
                    detail = (await r.aread()).decode("utf-8", "ignore")[:200]
                    raise LLMError(f"ollama HTTP {r.status_code}: {detail}")
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if d.get("error"):
                        raise LLMError(f"ollama: {d['error']}")
                    if d.get("message", {}).get("content"):
                        yield d["message"]["content"]
                    if d.get("done"):
                        return
        except httpx.HTTPError as e:
            raise LLMError(f"ollama unreachable at {self.host} ({e}). Is `ollama serve` running?") from e


class GeminiProvider:
    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        if not api_key:
            raise LLMError("gemini: GEMINI_API_KEY is not set")
        self.name, self.base_url, self.model, self.api_key = "gemini", base_url.rstrip("/"), model, api_key

    async def stream(self, system: str, messages: list[dict], temperature: float = 0.7,
                     max_tokens: int = 260) -> AsyncIterator[str]:
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                    for m in messages]
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens,
                                     "thinkingConfig": {"thinkingBudget": 0}}}
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse"
        try:
            cx = client()
            async with cx.stream("POST", url, json=body,
                                 headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"}) as r:
                if r.status_code >= 400:
                    detail = (await r.aread()).decode("utf-8", "ignore")[:200]
                    raise LLMError(f"gemini HTTP {r.status_code}: {detail}")
                async for data in _sse_lines(r):
                    try:
                        parts = json.loads(data)["candidates"][0]["content"]["parts"]
                    except (ValueError, KeyError, IndexError):
                        continue
                    for p in parts:
                        if p.get("text") and not p.get("thought"):
                            yield p["text"]
        except httpx.HTTPError as e:
            raise LLMError(f"gemini network error: {e}") from e


class MockProvider:
    """No model: the app answers from retrieved items (see prompts.extractive_reply)."""
    name = "mock"
    model = "extractive"

    async def stream(self, system, messages, temperature=0.7, max_tokens=260):
        raise LLMError("mock provider has no generative model")
        yield ""  # pragma: no cover


def build_provider(name: str, s: Settings):
    name = (name or "mock").lower()
    if name == "mock":
        return MockProvider()
    if name == "gemini":
        base, model, _ = PROVIDER_PRESETS["gemini"]
        return GeminiProvider(s.llm_base_url or base, s.llm_model or model, s.gemini_api_key)
    if name == "ollama":
        return OllamaProvider(s.llm_base_url or s.ollama_host, s.llm_model or PROVIDER_PRESETS["ollama"][1])
    if name in ("groq", "openai_compat"):
        base, model, key_env = PROVIDER_PRESETS[name]
        key = {"groq": s.groq_api_key, "ollama": "", "openai_compat": s.llm_api_key}[name]
        if name == "groq" and not key:
            raise LLMError("groq: GROQ_API_KEY is not set")
        return OpenAICompatProvider(name, s.llm_base_url or base, s.llm_model or model, key)
    raise LLMError(f"unknown LLM_PROVIDER '{name}'")


def build_providers(s: Settings) -> list:
    """Primary first, then the optional fallback. A provider that cannot be built is skipped."""
    out = []
    for n in (s.llm_provider, s.llm_fallback_provider):
        if not n:
            continue
        try:
            out.append(build_provider(n, s))
        except LLMError:
            continue
    return out or [MockProvider()]

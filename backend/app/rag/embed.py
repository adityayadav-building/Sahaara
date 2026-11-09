"""Dense embeddings through a local Ollama server (default model: bge-m3, multilingual)."""
from __future__ import annotations

import httpx


class OllamaEmbedder:
    def __init__(self, host: str, model: str) -> None:
        self.host, self.model = host.rstrip("/"), model
        self._client: httpx.AsyncClient | None = None

    def _body(self, texts: list[str]) -> dict:
        return {"model": self.model, "input": texts, "keep_alive": "60m", "truncate": True}

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Blocking batch call (index building)."""
        r = httpx.post(f"{self.host}/api/embed", json=self._body(texts), timeout=300)
        r.raise_for_status()
        return r.json()["embeddings"]

    async def aencode(self, texts: list[str]) -> list[list[float]]:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=3.0))
        r = await self._client.post(f"{self.host}/api/embed", json=self._body(texts))
        r.raise_for_status()
        return r.json()["embeddings"]

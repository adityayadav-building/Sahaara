"""Embed every corpus chunk with bge-m3 (via Ollama) and save the dense index.

    ollama pull bge-m3
    python scripts/build_index.py            # ~1500 chunks, a few minutes on an M-series Mac
Writes data/index/{embeddings.npy, ids.json, meta.json}. Re-run after changing the corpus.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import get_settings  # noqa: E402
from app.rag.embed import OllamaEmbedder  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402


def main() -> None:
    s = get_settings()
    r = Retriever(load_index=False)
    emb = OllamaEmbedder(s.ollama_host, s.embed_model)
    texts = [c.search_text()[:6000] for c in r.chunks]
    out, t0, B = [], time.time(), 16
    for i in range(0, len(texts), B):
        out += emb.encode(texts[i:i + B])
        print(f"\r{min(i + B, len(texts))}/{len(texts)}  {time.time() - t0:.0f}s", end="", flush=True)
    mat = np.asarray(out, dtype="float32")
    mat /= np.linalg.norm(mat, axis=1, keepdims=True).clip(1e-9)
    d = Path(s.index_dir)
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / "embeddings.npy", mat)
    (d / "ids.json").write_text(json.dumps([c.id for c in r.chunks]), encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"model": s.embed_model, "dim": int(mat.shape[1]), "n": len(r.chunks)}))
    print(f"\nsaved {mat.shape} to {d}")


if __name__ == "__main__":
    main()

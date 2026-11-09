import json

import numpy as np

from app.gitatext import ascii_for_tts, fix_diacritics, to_devanagari
from app.rag.retriever import Retriever

R = Retriever(load_index=False)


def test_diacritics_and_scripts():
    assert fix_diacritics("Kåñëa dhåtaräñöra") == "Kṛṣṇa dhṛtarāṣṭra"
    assert ascii_for_tts("Kṛṣṇa said: O Arjuna") == "Krishna said: O Arjuna"
    assert to_devanagari("dharma-kṣetre kuru-kṣetre") == "धर्म-क्षेत्रे कुरु-क्षेत्रे"


def test_corpus_shape():
    verses = [c for c in R.chunks if c.type == "shloka"]
    purports = [c for c in R.chunks if c.type == "purport"]
    assert len(verses) > 450 and len(purports) > 800
    v = R.get("gita-2-47")
    assert "fruits" in v.text_en and v.extra["chapter"] == 2 and "कर्म" in v.extra["devanagari"]
    p = next(c for c in purports if c.extra["verse_id"] == "gita-2-47")
    assert "Bhagavad Gita 2.47" in p.search_text() and "fruits" in p.search_text()  # contextual header


def test_cross_lingual_topic_expansion_reaches_english_corpus():
    assert any(h.chunk.type == "shloka" for h in R.retrieve("मुझे बहुत डर लगता है"))
    assert any(h.chunk.id.startswith("gita-6") for h in R.retrieve("mera mann bahut bhatakta hai, overthinking"))


def test_dense_list_is_fused(tmp_path):
    """A fake embedder that makes one chosen verse the nearest neighbour must lift it into the selection."""
    target = R.get("gita-3-37")
    dim = 8
    mat = np.random.default_rng(0).normal(size=(len(R.chunks), dim)).astype("float32")
    mat[R.id2i[target.id]] = np.ones(dim)
    mat /= np.linalg.norm(mat, axis=1, keepdims=True)
    d = tmp_path
    np.save(d / "embeddings.npy", mat)
    (d / "ids.json").write_text(json.dumps([c.id for c in R.chunks]))
    (d / "meta.json").write_text(json.dumps({"model": "fake"}))

    class Fake:
        async def aencode(self, texts):
            return [[1.0] * dim for _ in texts]

    r2 = Retriever(chunks=R.chunks, embedder=Fake(), index_dir=d)
    assert r2.dense_ready
    import asyncio
    hits = asyncio.run(r2.aretrieve("something unrelated entirely"))
    assert target.id in [h.chunk.id for h in hits]

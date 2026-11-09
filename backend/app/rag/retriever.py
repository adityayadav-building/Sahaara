"""Hybrid retriever over the real Bhagavad-gita As It Is corpus (+ practices, tools, stories, your books).

Pipeline
  1. Contextual chunking (done at build time): every purport chunk is indexed together with its chapter title,
     verse reference and the verse's translation, so a chunk is never an orphan paragraph.
  2. Lexical: BM25 over an inverted index. The query is expanded with an English gloss of the detected
     emotional topics, so Hindi / Hinglish / Indic messages still match the English corpus.
  3. Semantic: bge-m3 (multilingual) embeddings via Ollama, cosine similarity, cross-lingual by design.
  4. A small curated "mental-health prior": hand-tagged anchor verses (2.14, 2.47, 6.35 ...) get a rank list of
     their own so the classics surface even when the wording of the message is far from the Sanskrit idea.
  5. Reciprocal Rank Fusion of the three lists, then type-aware selection: up to 2 verses from different
     chapters, the best purport passage of the chosen verses, one practice/tool, and (rarely) one story.
Dense search is optional: without an index (scripts/build_index.py) it degrades to BM25 + prior.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..config import BACKEND_DIR, CORPUS_DIR, Settings, get_settings
from ..lang import is_hindi_family
from . import starter
from .topics import EXPAND, detect_topics

_TOKEN = re.compile(r"[\wऀ-෿]+", re.UNICODE)
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "i", "me", "my", "am", "are", "was", "be", "so",
    "that", "this", "for", "on", "with", "as", "at", "by", "do", "not", "have", "has", "can", "you", "your",
    "hai", "hain", "ho", "ka", "ki", "ke", "ko", "se", "mai", "main", "mujhe", "nahi", "aur", "yeh", "ye",
    "है", "हैं", "का", "की", "के", "को", "से", "में", "मैं", "मुझे", "और", "यह", "नहीं", "भी", "पर", "तो",
}

# (chapter, verse) -> topics. A focused mental health prior for classic verses.
CURATED: dict[tuple[int, int], list[str]] = {
    (1, 28): ["fear", "overwhelm"],
    (1, 30): ["anxiety", "fear"],
    (2, 3): ["low_motivation", "self_worth"],
    (2, 7): ["overwhelm", "anxiety"],
    (2, 11): ["grief", "sadness"],
    (2, 13): ["grief"],
    (2, 14): ["sadness", "burnout"],
    (2, 15): ["anxiety", "peace"],
    (2, 20): ["grief", "fear"],
    (2, 22): ["grief", "sadness"],
    (2, 27): ["grief"],
    (2, 38): ["failure", "exam_pressure"],
    (2, 40): ["fear", "low_motivation"],
    (2, 47): ["exam_pressure", "anxiety", "overwhelm"],
    (2, 48): ["failure"],
    (2, 56): ["sadness", "anger"],
    (2, 62): ["anger", "relationships"],
    (2, 63): ["anger"],
    (2, 65): ["sadness", "peace"],
    (2, 66): ["overthinking", "anxiety"],
    (2, 70): ["anxiety", "overwhelm"],
    (2, 71): ["peace", "anxiety"],
    (3, 37): ["anger"],
    (3, 43): ["self_worth"],
    (5, 23): ["anger"],
    (5, 29): ["peace", "anxiety"],
    (6, 5): ["self_worth", "low_motivation"],
    (6, 6): ["self_worth", "guilt"],
    (6, 7): ["overthinking", "peace"],
    (6, 16): ["sleep", "burnout"],
    (6, 17): ["sleep", "burnout"],
    (6, 26): ["overthinking", "anxiety"],
    (6, 34): ["overthinking"],
    (6, 35): ["overthinking"],
    (6, 40): ["failure", "guilt"],
    (9, 22): ["loneliness", "fear"],
    (12, 13): ["relationships", "anger"],
    (12, 14): ["relationships", "peace"],
    (12, 15): ["anxiety", "relationships"],
}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


@dataclass
class Chunk:
    id: str
    type: str  # shloka | purport | practice | tool | story | book
    source: str
    ref: str = ""
    title_en: str = ""
    title_hi: str = ""
    text_en: str = ""
    text_hi: str = ""
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    index_text: str = ""  # what BM25 and the embedder see (contextual header + content)

    def text_for(self, lang: str) -> str:
        return (self.text_hi or self.text_en) if is_hindi_family(lang) and self.text_hi else (self.text_en or self.text_hi)

    def title_for(self, lang: str) -> str:
        return (self.title_hi or self.title_en) if is_hindi_family(lang) and self.title_hi else (self.title_en or self.title_hi)

    def search_text(self) -> str:
        if self.index_text:
            return self.index_text
        return " ".join([self.title_en, self.title_hi, self.text_en, self.text_hi, " ".join(self.keywords),
                         " ".join(self.topics), self.ref, self.source])


def _curated_topics(chapter: int, v1: int, v2: int) -> list[str]:
    out: list[str] = []
    for (c, v), tp in CURATED.items():
        if c == chapter and v1 <= v <= v2:
            out += [t for t in tp if t not in out]
    return out


def _gloss(topics: list[str]) -> str:
    return " ".join(EXPAND.get(t, "") for t in topics)


def _gita_chunks(gita_dir: Path) -> list[Chunk]:
    vf, pf = gita_dir / "verses.jsonl", gita_dir / "purports.jsonl"
    if not vf.exists():
        return []
    out: list[Chunk] = []
    topics_of: dict[str, list[str]] = {}
    for line in vf.open(encoding="utf-8"):
        d = json.loads(line)
        ch, v1 = d["chapter"], d["verse"]
        v2 = int(re.split(r"[–-]", d["ref"].split(".", 1)[1])[-1]) if "–" in d["ref"] else v1
        tp = _curated_topics(ch, v1, v2)
        topics_of[d["id"]] = tp
        head = f"Bhagavad Gita {d['ref']}, chapter {ch}, {d['chapter_title']}."
        out.append(Chunk(
            id=d["id"], type="shloka", source="Bhagavad Gita", ref=d["ref"], title_en=f"Bhagavad Gita {d['ref']}",
            title_hi=f"भगवद्गीता {d['ref']}", text_en=d["translation"], topics=tp,
            extra={"iast": d["iast"], "devanagari": d["devanagari"], "chapter": ch, "chapter_title": d["chapter_title"],
                   "verse_id": d["id"]},
            index_text=f"{head} {d['translation']}"))
    if pf.exists():
        for line in pf.open(encoding="utf-8"):
            d = json.loads(line)
            tp = topics_of.get(d["verse_id"], [])
            head = f"Bhagavad Gita {d['ref']}, chapter {d['chapter']}, {d['chapter_title']}. Verse: {d['verse_translation']}"
            out.append(Chunk(
                id=d["id"], type="purport", source="Bhagavad Gita (purport)", ref=d["ref"],
                title_en=f"Purport to Gita {d['ref']}", text_en=d["text"], topics=tp,
                extra={"verse_id": d["verse_id"], "chapter": d["chapter"]},
                index_text=f"{head} Purport: {d['text']}"))
    return out


def _starter_chunks(with_shlokas: bool) -> list[Chunk]:
    out: list[Chunk] = []
    if with_shlokas:  # hand-typed fallback, used only when the real corpus is not built
        for s in starter.SHLOKAS:
            out.append(Chunk(
                id=s["id"], type="shloka", source=starter.SOURCE_GITA, ref=s["ref"],
                title_en=f"Bhagavad Gita {s['ref']}", title_hi=f"भगवद्गीता {s['ref']}",
                text_en=s["meaning_en"], text_hi=s["meaning_hi"], topics=s["topics"], keywords=s.get("keywords", []),
                extra={"devanagari": s["sanskrit"], "iast": s["iast"], "note": s.get("note", "")}))
    for p in starter.PRACTICES:
        out.append(Chunk(
            id=p["id"], type="practice", source="Practice", title_en=p["title_en"], title_hi=p["title_hi"],
            text_en=" ".join(p["steps_en"]), text_hi=" ".join(p["steps_hi"]), topics=p["topics"],
            keywords=p.get("keywords", []),
            extra={"steps_en": p["steps_en"], "steps_hi": p["steps_hi"], "breath": p.get("breath"),
                   "minutes": p.get("minutes")}))
    for t in starter.CBT_TOOLS:
        out.append(Chunk(
            id=t["id"], type="tool", source="Thinking tool", title_en=t["title_en"], title_hi=t["title_hi"],
            text_en=" ".join(t["steps_en"]), text_hi=" ".join(t["steps_hi"]), topics=t["topics"],
            keywords=t.get("keywords", []), extra={"steps_en": t["steps_en"], "steps_hi": t["steps_hi"]}))
    for s in starter.STORIES:
        out.append(Chunk(
            id=s["id"], type="story", source="Panchatantra", title_en=s["title_en"], title_hi=s["title_hi"],
            text_en=s["summary_en"] + " " + s["moral_en"], text_hi=s["summary_hi"] + " " + s["moral_hi"],
            topics=s["topics"], keywords=s.get("keywords", []),
            extra={"summary_en": s["summary_en"], "summary_hi": s["summary_hi"],
                   "moral_en": s["moral_en"], "moral_hi": s["moral_hi"]}))
    return out


def _user_chunks(corpus_dir: Path) -> list[Chunk]:
    out: list[Chunk] = []
    user_dir = corpus_dir / "user"
    if not user_dir.is_dir():
        return out
    for f in sorted(user_dir.glob("*.jsonl")):
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(Chunk(
                    id=d["id"], type=d.get("type", "book"), source=d.get("source", f.stem), ref=d.get("ref", ""),
                    title_en=d.get("title", d.get("title_en", "")), title_hi=d.get("title_hi", ""),
                    text_en=d.get("text", d.get("text_en", "")), text_hi=d.get("text_hi", ""),
                    topics=d.get("topics", []), keywords=d.get("keywords", []), extra=d.get("extra", {}),
                    index_text=f"{d.get('source', f.stem)}. {d.get('text', d.get('text_en', ''))}"))
            except (KeyError, ValueError):
                continue
    return out


@dataclass
class Hit:
    chunk: Chunk
    score: float


class Retriever:
    K = 60  # RRF constant
    W_BM25, W_DENSE, W_PRIOR = 1.2, 1.25, 0.35
    K1, B = 1.4, 0.75

    def __init__(self, chunks: list[Chunk] | None = None, settings: Settings | None = None, embedder=None,
                 index_dir: Path | None = None, load_index: bool = True) -> None:
        s = settings or get_settings()
        if chunks is None:
            gita = _gita_chunks(Path(s.gita_dir))
            chunks = gita + _starter_chunks(with_shlokas=not gita) + _user_chunks(CORPUS_DIR)
            self.has_gita = bool(gita)
        else:
            self.has_gita = any(c.id.startswith("gita-") for c in chunks)
        self.chunks = chunks
        self.embedder = embedder
        self.id2i = {c.id: i for i, c in enumerate(chunks)}
        self._qcache: dict[str, list[float]] = {}
        self._build_bm25()
        self.mat = None  # normalised embedding matrix aligned with self.chunks, or None
        self.chroma_collection = None
        if load_index:
            if index_dir is not None:
                self._load_dense(Path(index_dir))
            else:
                self._load_chroma(Path(getattr(s, "chroma_dir", "") or (BACKEND_DIR / "data" / "chroma_db")))
                if self.chroma_collection is None:
                    self._load_dense(Path(s.index_dir))

    # ---- build ----
    def _build_bm25(self) -> None:
        self.tf: list[Counter] = []
        self.dl: list[int] = []
        df: Counter = Counter()
        self.postings: dict[str, list[int]] = defaultdict(list)
        for i, c in enumerate(self.chunks):
            toks = tokenize(c.search_text())
            cnt = Counter(toks)
            self.tf.append(cnt)
            self.dl.append(len(toks))
            for t in cnt:
                df[t] += 1
                self.postings[t].append(i)
        n = max(len(self.chunks), 1)
        self.avgdl = (sum(self.dl) / n) if self.chunks else 1.0
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def _load_dense(self, index_dir: Path) -> None:
        try:
            import numpy as np
            meta = json.loads((index_dir / "meta.json").read_text(encoding="utf-8"))
            ids = json.loads((index_dir / "ids.json").read_text(encoding="utf-8"))
            mat = np.load(index_dir / "embeddings.npy")
        except Exception:
            return
        rows = {cid: k for k, cid in enumerate(ids)}
        if sum(1 for c in self.chunks if c.id in rows) < 0.9 * len(self.chunks):
            return  # stale index (corpus changed): rebuild with scripts/build_index.py
        out = np.zeros((len(self.chunks), mat.shape[1]), dtype="float32")
        for i, c in enumerate(self.chunks):
            if c.id in rows:
                out[i] = mat[rows[c.id]]
        self.mat, self.dense_model = out, meta.get("model", "")

    def _load_chroma(self, chroma_dir: Path) -> None:
        if not chroma_dir.exists():
            return
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            client = chromadb.PersistentClient(path=str(chroma_dir))
            ef = embedding_functions.DefaultEmbeddingFunction()
            col = client.get_collection(name="sahaara_wisdom", embedding_function=ef)
            if col and col.count() > 0:
                self.chroma_collection = col
        except Exception:
            self.chroma_collection = None

    def __len__(self) -> int:
        return len(self.chunks)

    @property
    def dense_ready(self) -> bool:
        return self.chroma_collection is not None or (self.mat is not None and self.embedder is not None)

    # ---- scoring ----
    def _bm25(self, q_tokens: list[str]) -> dict[int, float]:
        scores: dict[int, float] = defaultdict(float)
        for t in set(q_tokens):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i in self.postings[t]:
                f = self.tf[i][t]
                scores[i] += idf * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * self.dl[i] / self.avgdl))
        return scores

    def _chroma_scores(self, query: str, limit: int = 60) -> dict[int, float]:
        if not self.chroma_collection:
            return {}
        try:
            res = self.chroma_collection.query(
                query_texts=[query],
                n_results=min(limit, self.chroma_collection.count())
            )
            scores: dict[int, float] = {}
            ids = res.get("ids", [[]])[0]
            distances = res.get("distances", [[]])[0] if res.get("distances") else []
            for r, cid in enumerate(ids):
                idx = self.id2i.get(cid)
                if idx is not None:
                    dist = distances[r] if r < len(distances) else 1.0
                    scores[idx] = float(1.0 / (1.0 + max(dist, 0.0)))
            return scores
        except Exception:
            return {}

    def _dense_scores(self, qvec) -> dict[int, float]:
        import numpy as np
        q = np.asarray(qvec, dtype="float32")
        q /= (np.linalg.norm(q) or 1.0)
        sims = self.mat @ q
        return {int(i): float(sims[i]) for i in np.argsort(-sims)[:80]}

    async def embed_query(self, text: str):
        if not self.dense_ready:
            return None
        if self.chroma_collection is not None:
            return None  # handled synchronously and offline in _chroma_scores!
        if text in self._qcache:
            return self._qcache[text]
        try:
            vec = (await self.embedder.aencode([text]))[0]
        except Exception:
            return None  # Ollama down: fall back to BM25 + prior
        if len(self._qcache) > 256:
            self._qcache.clear()
        self._qcache[text] = vec
        return vec

    @staticmethod
    def _ranks(scores: dict[int, float], limit: int = 100) -> dict[int, int]:
        order = sorted((i for i, s in scores.items() if s > 0), key=lambda i: -scores[i])[:limit]
        return {i: r for r, i in enumerate(order)}

    def fuse(self, query: str, topics: list[tuple[str, float]], qvec=None) -> list[Hit]:
        expanded = query + " " + " ".join(EXPAND.get(t, "") for t, _ in topics)
        lists: list[tuple[float, dict[int, int]]] = [(self.W_BM25, self._ranks(self._bm25(tokenize(expanded))))]
        
        # Dense ChromaDB search (runs locally on CPU in < 4ms)
        if self.chroma_collection is not None:
            c_scores = self._chroma_scores(query)
            if c_scores:
                lists.append((self.W_DENSE, self._ranks(c_scores)))
        elif qvec is not None and self.mat is not None:
            lists.append((self.W_DENSE, self._ranks(self._dense_scores(qvec))))

        tw = dict(topics)
        if tw:
            prior = {i: sum(tw.get(tp, 0.0) for tp in c.topics) for i, c in enumerate(self.chunks) if c.topics}
            lists.append((self.W_PRIOR, self._ranks(prior)))
        fused: dict[int, float] = defaultdict(float)
        for w, ranks in lists:
            for i, r in ranks.items():
                fused[i] += w / (self.K + r)
        return sorted((Hit(self.chunks[i], s) for i, s in fused.items()), key=lambda h: -h.score)

    # ---- selection ----
    def select(self, hits: list[Hit], topics, allow_book: bool = True, want_story: bool | None = None) -> list[Hit]:
        by: dict[str, list[Hit]] = defaultdict(list)
        for h in hits:
            by[h.chunk.type].append(h)
        picks: list[Hit] = []
        verses = by["shloka"]
        if verses:
            picks.append(verses[0])
            second = next((h for h in verses[1:6] if h.chunk.extra.get("chapter") != verses[0].chunk.extra.get("chapter")
                           and h.score >= 0.45 * verses[0].score), None)
            if second is not None:
                picks.append(second)
        picked_v = {h.chunk.id for h in picks}
        pur = next((h for h in by["purport"] if h.chunk.extra.get("verse_id") in picked_v), None)
        if pur is not None:
            picks.append(pur)
        action = sorted(by["practice"][:2] + by["tool"][:2], key=lambda h: -h.score)
        if action:
            picks.append(action[0])
        story_ok = want_story if want_story is not None else bool(topics)
        if story_ok and by["story"] and hits.index(by["story"][0]) < 8:
            picks.append(by["story"][0])
        if allow_book:
            picks += [h for h in by["book"][:2]]
        return picks

    def retrieve(self, query: str, topics: list[tuple[str, float]] | None = None, qvec=None, **kw) -> list[Hit]:
        topics = topics if topics is not None else detect_topics(query)
        hits = self.fuse(query, topics, qvec)
        return self.select(hits, topics, **kw) if hits else []

    async def aretrieve(self, query: str, topics: list[tuple[str, float]] | None = None, **kw) -> list[Hit]:
        qvec = await self.embed_query(query)
        return self.retrieve(query, topics, qvec=qvec, **kw)

    def get(self, chunk_id: str) -> Chunk | None:
        i = self.id2i.get(chunk_id)
        return self.chunks[i] if i is not None else None

    def by_type(self, t: str) -> list[Chunk]:
        return [c for c in self.chunks if c.type == t]


def to_card(c: Chunk, lang: str, idx: int, show_excerpt: bool = True) -> dict:
    """Frontend-safe card for a retrieved chunk. idx is the 1-based [S#] number."""
    from ..gitatext import ascii_for_tts
    hi = is_hindi_family(lang)
    card: dict = {"n": idx, "id": c.id, "type": c.type, "source": c.source, "ref": c.ref, "title": c.title_for(lang)}
    if c.type == "shloka":
        card.update(devanagari=c.extra.get("devanagari", ""), iast=c.extra.get("iast", ""), meaning=c.text_en or c.text_for(lang),
                    chapter=c.extra.get("chapter"), chapter_title=c.extra.get("chapter_title", ""),
                    meaning_tts=ascii_for_tts(c.text_en) if c.text_en else "")
        if c.text_hi:
            card["meaning_hi"] = c.text_hi
    elif c.type == "purport":
        card["text"] = c.text_en[:420].rsplit(" ", 1)[0] + "…" if len(c.text_en) > 420 else c.text_en
    elif c.type in ("practice", "tool"):
        card["steps"] = c.extra.get("steps_hi" if hi else "steps_en") or c.extra.get("steps_en", [])
        if c.extra.get("breath"):
            card["breath"] = c.extra["breath"]
        if c.extra.get("minutes"):
            card["minutes"] = c.extra["minutes"]
    elif c.type == "story":
        card["summary"] = c.extra.get("summary_hi" if hi else "summary_en") or c.extra.get("summary_en", "")
        card["moral"] = c.extra.get("moral_hi" if hi else "moral_en") or c.extra.get("moral_en", "")
    else:  # user book
        card["text"] = (c.text_for(lang) or c.text_en)[:600]
        card["hidden"] = False
        if c.extra.get("author"):
            card["author"] = c.extra["author"]
        if c.extra.get("book"):
            card["book"] = c.extra["book"]
    return card

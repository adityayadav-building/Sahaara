"""Ingest the 4 wisdom books (PDFs) into Sahaara corpus and build the ChromaDB index.

Books:
1. Raja Yoga by Swami Vivekananda (Patanjali Yoga Sutras, Prana, Meditation)
2. Doing What Matters in Times of Stress (WHO - Grounding, Unhooking, Making Room)
3. Man's Search for Meaning by Viktor E. Frankl (Logotherapy, Tragic Optimism, Suffering)
4. Karma Yoga by Swami Vivekananda (Non-attachment, Duty, Work as Worship)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import pypdf

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.rag.topics import detect_topics
from app.rag import starter

DATA_DIR = BACKEND_DIR / "data"
GITA_DIR = DATA_DIR / "gita"
USER_CORPUS_DIR = DATA_DIR / "corpus" / "user"
USER_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR = DATA_DIR / "chroma_db"

PDF_PATHS = {
    "raja_yoga": {
        "path": Path("/Users/simpli.adi/.gemini/antigravity/brain/4b1b326d-f9a4-4495-bb05-a037ac180a08/.user_uploaded/media_1794075194290_29973b16.pdf"),
        "title": "Raja Yoga",
        "author": "Swami Vivekananda",
        "source": "Raja Yoga (Swami Vivekananda)",
        "output": USER_CORPUS_DIR / "raja_yoga.jsonl",
        "default_topics": ["overthinking", "anxiety", "peace"],
        "min_page": 8,
        "max_page": 225,
    },
    "who_stress": {
        "path": Path("/Users/simpli.adi/.gemini/antigravity/brain/4b1b326d-f9a4-4495-bb05-a037ac180a08/.user_uploaded/media_1794075338455_c5fd39c1.pdf"),
        "title": "Doing What Matters in Times of Stress",
        "author": "World Health Organization",
        "source": "WHO Stress Guide",
        "output": USER_CORPUS_DIR / "who_stress_guide.jsonl",
        "default_topics": ["anxiety", "overwhelm", "burnout"],
        "min_page": 10,
        "max_page": 128,
    },
    "frankl": {
        "path": Path("/Users/simpli.adi/.gemini/antigravity/brain/4b1b326d-f9a4-4495-bb05-a037ac180a08/.user_uploaded/media_1794075446467_1e0108e1.pdf"),
        "title": "Man's Search for Meaning",
        "author": "Viktor E. Frankl",
        "source": "Man's Search for Meaning (Viktor Frankl)",
        "output": USER_CORPUS_DIR / "mans_search_for_meaning.jsonl",
        "default_topics": ["grief", "sadness", "loneliness", "self_worth"],
        "min_page": 12,
        "max_page": 145,
    },
    "karma_yoga": {
        "path": Path("/Users/simpli.adi/.gemini/antigravity/brain/4b1b326d-f9a4-4495-bb05-a037ac180a08/.user_uploaded/media_1794075522998_7ff55655.pdf"),
        "title": "Karma Yoga: The Secret of Work",
        "author": "Swami Vivekananda",
        "source": "Karma Yoga (Swami Vivekananda)",
        "output": USER_CORPUS_DIR / "karma_yoga.jsonl",
        "default_topics": ["burnout", "failure", "exam_pressure", "overwhelm"],
        "min_page": 5,
        "max_page": 85,
    },
}


def clean_text(raw: str) -> str:
    # Normalize whitespaces, hyphens, and line breaks
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", raw)
    text = re.sub(r"\s+", " ", text).strip()
    # Remove page numbers and isolated headers
    text = re.sub(r"^(page\s+\d+|\d+\s*)\b", "", text, flags=re.IGNORECASE)
    return text.strip()


def chunk_paragraphs(paragraphs: list[str], max_len: int = 550, overlap: int = 60) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for p in paragraphs:
        p = p.strip()
        if not p or len(p) < 25:
            continue
        p_len = len(p)
        if current_len + p_len > max_len and current:
            chunks.append(" ".join(current))
            # retain the last paragraph or tail for overlap
            tail = current[-1]
            if len(tail) > overlap:
                tail = tail[-overlap:]
            current = [tail, p]
            current_len = len(tail) + p_len
        else:
            current.append(p)
            current_len += p_len

    if current:
        chunks.append(" ".join(current))
    return chunks


def extract_and_chunk_pdf(cfg: dict) -> list[dict]:
    pdf_path = cfg["path"]
    if not pdf_path.exists():
        print(f"Warning: {pdf_path} does not exist!")
        return []

    print(f"Reading {cfg['title']} from {pdf_path.name}...")
    reader = pypdf.PdfReader(str(pdf_path))
    num_pages = len(reader.pages)
    min_p = min(cfg["min_page"], num_pages - 1)
    max_p = min(cfg["max_page"], num_pages)

    full_paras: list[tuple[int, str]] = []  # (page_num, para)
    for p_no in range(min_p, max_p):
        try:
            page = reader.pages[p_no]
            raw_text = page.extract_text() or ""
            # Split by double newline or sentence groups
            paras = re.split(r"\n\s*\n", raw_text)
            for p in paras:
                cleaned = clean_text(p)
                if len(cleaned) > 35:
                    full_paras.append((p_no + 1, cleaned))
        except Exception:
            continue

    # Create semantic chunks
    chunks: list[dict] = []
    chunk_idx = 0
    i = 0
    while i < len(full_paras):
        p_no, text_acc = full_paras[i]
        curr_text = [text_acc]
        curr_len = len(text_acc)
        j = i + 1
        while j < len(full_paras) and curr_len + len(full_paras[j][1]) < 650:
            curr_text.append(full_paras[j][1])
            curr_len += len(full_paras[j][1])
            j += 1

        chunk_str = " ".join(curr_text)
        if len(chunk_str) >= 80:
            chunk_idx += 1
            # Detect emotional topics
            detected = [t for t, score in detect_topics(chunk_str) if score > 0.4]
            topics = list(set(detected + cfg["default_topics"][:2]))

            # Determine type: if containing grounding/breathing steps, tag as 'tool'
            c_type = "book"
            if any(k in chunk_str.lower() for k in ["breathe", "grounding", "unhook", "exercise", "notice"]):
                c_type = "tool" if "who" in cfg["source"].lower() else "book"

            chunks.append({
                "id": f"{cfg['output'].stem}-{chunk_idx:04d}",
                "type": c_type,
                "source": cfg["source"],
                "ref": f"{cfg['title']}, p.{p_no}",
                "title_en": f"{cfg['title']} (p. {p_no})",
                "title_hi": cfg["title"],
                "text_en": chunk_str,
                "topics": topics,
                "keywords": [w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", chunk_str)[:10]],
                "extra": {
                    "author": cfg["author"],
                    "book": cfg["title"],
                    "page": p_no,
                }
            })
        i = max(j, i + 1)

    print(f"Generated {len(chunks)} chunks for {cfg['title']}")
    # Write to JSONL
    with open(cfg["output"], "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return chunks


def build_chroma_database():
    """Build persistent ChromaDB collection with all Gita chunks + Book chunks."""
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Initializing ChromaDB client at {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name="sahaara_wisdom",
        embedding_function=ef,
        metadata={"description": "Gita, Vivekananda, Frankl, WHO wisdom corpus"}
    )

    # Gather all items to index
    docs: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    # 1. Gita verses
    vf = GITA_DIR / "verses.jsonl"
    if vf.exists():
        print("Reading Gita verses...")
        for line in vf.open(encoding="utf-8"):
            d = json.loads(line)
            cid = d["id"]
            head = f"Bhagavad Gita {d['ref']}, chapter {d['chapter']}, {d['chapter_title']}. Translation: {d['translation']}"
            docs.append(head)
            ids.append(cid)
            metadatas.append({
                "type": "shloka",
                "ref": d["ref"],
                "chapter": int(d["chapter"]),
                "source": "Bhagavad Gita"
            })

    # 2. Gita purports
    pf = GITA_DIR / "purports.jsonl"
    if pf.exists():
        print("Reading Gita purports...")
        for line in pf.open(encoding="utf-8"):
            d = json.loads(line)
            cid = d["id"]
            head = f"Bhagavad Gita {d['ref']} Purport: {d['text']}"
            docs.append(head[:1000])
            ids.append(cid)
            metadatas.append({
                "type": "purport",
                "ref": d["ref"],
                "chapter": int(d["chapter"]),
                "source": "Bhagavad Gita (purport)"
            })

    # 3. Starter tools & practices
    print("Reading starter tools...")
    for p in starter.PRACTICES:
        head = f"Practice: {p['title_en']}. " + " ".join(p["steps_en"])
        docs.append(head)
        ids.append(p["id"])
        metadatas.append({"type": "practice", "ref": p["id"], "source": "Practice"})

    for t in starter.CBT_TOOLS:
        head = f"Tool: {t['title_en']}. " + " ".join(t["steps_en"])
        docs.append(head)
        ids.append(t["id"])
        metadatas.append({"type": "tool", "ref": t["id"], "source": "Thinking tool"})

    # 4. User books
    print("Reading book chunks...")
    for f in sorted(USER_CORPUS_DIR.glob("*.jsonl")):
        for line in f.open(encoding="utf-8"):
            if not line.strip():
                continue
            d = json.loads(line)
            head = f"{d['source']} ({d.get('ref', '')}): {d['text_en']}"
            docs.append(head[:1000])
            ids.append(d["id"])
            metadatas.append({
                "type": d.get("type", "book"),
                "ref": d.get("ref", ""),
                "source": d["source"]
            })

    print(f"Total documents to index in ChromaDB: {len(docs)}")

    # Add in batches of 200
    batch_size = 200
    for idx in range(0, len(docs), batch_size):
        end = min(idx + batch_size, len(docs))
        b_ids = ids[idx:end]
        b_docs = docs[idx:end]
        b_meta = metadatas[idx:end]
        collection.upsert(
            ids=b_ids,
            documents=b_docs,
            metadatas=b_meta
        )
        print(f"Indexed {end}/{len(docs)} documents in ChromaDB...")

    print(f"ChromaDB indexing complete! Collection count: {collection.count()}")


def main():
    print("=== Starting Ingestion of Wisdom Books ===")
    for key, cfg in PDF_PATHS.items():
        extract_and_chunk_pdf(cfg)
    print("=== Building ChromaDB Vector Index ===")
    build_chroma_database()
    print("=== All Wisdom Corpus and ChromaDB Indexed Successfully! ===")


if __name__ == "__main__":
    main()

"""Ingest your own books into the RAG corpus.

    python scripts/ingest.py path/to/book.pdf --source "Man's Search for Meaning" --topics grief,failure
    python scripts/ingest.py notes.txt --source "My notes"

Writes backend/data/corpus/user/<slug>.jsonl (gitignored). Restart the server afterwards.
Only ingest material you are allowed to use; excerpts stay hidden in the UI unless SHOW_BOOK_EXCERPTS=1.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import CORPUS_DIR  # noqa: E402
from app.rag.topics import detect_topics  # noqa: E402


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk(text: str, target: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, buf = [], ""
    for p in paras:
        if buf and len(buf) + len(p) > target:
            out.append(buf)
            buf = buf[-overlap:] + " " + p
        else:
            buf = f"{buf}\n{p}".strip()
    if buf:
        out.append(buf)
    return [c for c in out if len(c) > 200]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--source", required=True, help="book title shown as the citation")
    ap.add_argument("--topics", default="", help="comma separated topics to force on every chunk (optional)")
    a = ap.parse_args()
    forced = [t.strip() for t in a.topics.split(",") if t.strip()]
    slug = re.sub(r"[^a-z0-9]+", "-", a.source.lower()).strip("-") or "book"
    out_dir = CORPUS_DIR / "user"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    with (out_dir / f"{slug}.jsonl").open("w", encoding="utf-8") as fh:
        for i, c in enumerate(chunk(read_text(a.file))):
            topics = forced or [t for t, _ in detect_topics(c, 3)]
            fh.write(json.dumps({"id": f"{slug}-{i}", "type": "book", "source": a.source, "ref": f"part {i + 1}",
                                 "text": c, "topics": topics}, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} chunks to {out_dir / (slug + '.jsonl')}")


if __name__ == "__main__":
    main()

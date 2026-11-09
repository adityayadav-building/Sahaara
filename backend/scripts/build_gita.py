"""Parse the three 'Bhagavad-gita As It Is' text files into a structured JSONL corpus.

    python scripts/build_gita.py f1.txt f2.txt f3.txt        # in page order
Writes backend/data/gita/verses.jsonl and purports.jsonl. Each record carries chapter, verse, IAST,
Devanagari, translation, synonyms and (for purports) a *contextual header* used for retrieval.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import BACKEND_DIR  # noqa: E402
from app.gitatext import fix_diacritics, to_devanagari  # noqa: E402

WORDS = ["ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN", "ELEVEN", "TWELVE",
         "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN"]
CH_RE = re.compile(r"^CHAPTER (" + "|".join(WORDS) + r")\s*$")
TEXT_RE = re.compile(r"^TEXTS? (\d+)(?:\s*[–\-]\s*(\d+))?\s*$")
PURPORT_TARGET = 900
CHAPTER_TITLES = {1: "Observing the Armies on the Battlefield of Kurukṣetra", 2: "Contents of the Gītā Summarized",
                  3: "Karma-yoga", 4: "Transcendental Knowledge", 5: "Karma-yoga: Action in Kṛṣṇa Consciousness",
                  6: "Dhyāna-yoga", 7: "Knowledge of the Absolute", 8: "Attaining the Supreme",
                  9: "The Most Confidential Knowledge", 10: "The Opulence of the Absolute", 11: "The Universal Form",
                  12: "Devotional Service", 13: "Nature, the Enjoyer and Consciousness",
                  14: "The Three Modes of Material Nature", 15: "The Yoga of the Supreme Person",
                  16: "The Divine and Demoniac Natures", 17: "The Divisions of Faith", 18: "Conclusion: The Perfection of Renunciation"}


def parse(raw: str) -> tuple[list[dict], dict[int, str]]:
    lines = raw.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Foreword"))  # skip table of contents
    lines = lines[start:]
    chapter, titles, verses, cur = 0, {}, [], None

    def flush():
        nonlocal cur
        if cur:
            verses.append(cur)
        cur = None

    i = 0
    while i < len(lines):
        l = lines[i].rstrip()
        m = CH_RE.match(l.strip())
        if m:
            flush()
            chapter = WORDS.index(m.group(1)) + 1
            title = " ".join(x.strip() for x in lines[i + 1:i + 3] if x.strip() and not TEXT_RE.match(x.strip()))
            titles[chapter] = fix_diacritics(title)
            i += 1
            continue
        t = TEXT_RE.match(l.strip())
        if t and chapter:
            flush()
            cur = {"chapter": chapter, "v1": int(t.group(1)), "v2": int(t.group(2) or t.group(1)), "body": []}
        elif cur is not None:
            cur["body"].append(l)
        i += 1
    flush()
    return verses, titles


def split_verse(v: dict) -> dict | None:
    body = v["body"]
    try:
        ti = next(i for i, l in enumerate(body) if l.strip() == "TRANSLATION")
    except StopIteration:
        return None
    pi = next((i for i, l in enumerate(body) if i > ti and l.strip() == "PURPORT"), len(body))
    head, trans, purport = body[:ti], body[ti + 1:pi], body[pi + 1:]
    last_mark = max((i for i, l in enumerate(head) if "))" in l), default=-1)
    rest = head[last_mark + 1:]
    syn_start = next((i for i, l in enumerate(rest) if "—" in l), len(rest))
    translit = [fix_diacritics(l.strip()) for l in rest[:syn_start] if l.strip()]
    synonyms = fix_diacritics(" ".join(l.strip() for l in rest[syn_start:] if l.strip()))
    translation = fix_diacritics(" ".join(l.strip() for l in trans if l.strip()))
    paras, buf = [], []
    for l in purport:
        s = l.strip()
        if not s:
            continue
        buf.append(s)
        if s.endswith((".", "”", "?", "!", ":")) and len(" ".join(buf)) > 160:
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))
    iast = "\n".join(translit)
    return {"chapter": v["chapter"], "v1": v["v1"], "v2": v["v2"], "iast": iast, "devanagari": to_devanagari(iast),
            "synonyms": synonyms, "translation": translation, "purport": [fix_diacritics(p) for p in paras]}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    raw = "\n".join(Path(p).read_text(encoding="utf-8") for p in sys.argv[1:])
    verses, titles = parse(raw)
    out = BACKEND_DIR / "data" / "gita"
    out.mkdir(parents=True, exist_ok=True)
    nv = npc = 0
    with (out / "verses.jsonl").open("w", encoding="utf-8") as fv, (out / "purports.jsonl").open("w", encoding="utf-8") as fp:
        for raw_v in verses:
            v = split_verse(raw_v)
            if not v or not v["translation"]:
                continue
            ref = f"{v['chapter']}.{v['v1']}" + (f"–{v['v2']}" if v["v2"] != v["v1"] else "")
            vid = f"gita-{v['chapter']}-{v['v1']}" + (f"-{v['v2']}" if v["v2"] != v["v1"] else "")
            title = CHAPTER_TITLES.get(v["chapter"], titles.get(v["chapter"], ""))
            fv.write(json.dumps({"id": vid, "ref": ref, "chapter": v["chapter"], "verse": v["v1"], "chapter_title": title,
                                 "iast": v["iast"], "devanagari": v["devanagari"], "synonyms": v["synonyms"],
                                 "translation": v["translation"]}, ensure_ascii=False) + "\n")
            nv += 1
            buf = ""
            n = 0
            for p in v["purport"] + [None]:
                if p is not None and len(buf) + len(p) < PURPORT_TARGET * 1.4:
                    buf = f"{buf} {p}".strip()
                    continue
                if buf:
                    n += 1
                    fp.write(json.dumps({"id": f"{vid}-p{n}", "verse_id": vid, "ref": ref, "chapter": v["chapter"],
                                         "chapter_title": title, "verse_translation": v["translation"], "text": buf},
                                        ensure_ascii=False) + "\n")
                    npc += 1
                buf = p or ""
    print(f"verses: {nv}, purport chunks: {npc}; chapters seen: {sorted(titles)}")


if __name__ == "__main__":
    main()

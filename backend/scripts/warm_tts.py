"""Pre-generate Timbre audio for the curated verses so they play instantly in the demo.

Start the server first, then:  python scripts/warm_tts.py [http://localhost:8000]
Audio lands in data/tts_cache/ (disk cache, survives restarts).
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.gitatext import ascii_for_tts  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402

base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
r = Retriever(load_index=False)


def tts(text, lang):
    req = urllib.request.Request(f"{base}/api/tts", json.dumps({"text": text, "language": lang}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.headers.get("X-Cache", "?")


verses = [c for c in r.by_type("shloka") if c.topics]
for i, c in enumerate(verses, 1):
    ch, v = c.ref.split(".")
    v = v.replace("–", " to ")
    jobs = [(f"From the Bhagavad Gita, chapter {ch}, verse {v}.", "en-IN"),
            (f"भगवद्गीता, अध्याय {ch}, श्लोक {v}।", "hi-IN"),
            (c.extra["devanagari"].replace("\n", "। "), "hi-IN"), (ascii_for_tts(c.text_en), "en-IN")]
    for text, lang in jobs:
        try:
            tts(text, lang)
        except Exception as e:  # keep going
            print("fail", c.ref, lang, e)
    print(f"{i}/{len(verses)} {c.ref}")

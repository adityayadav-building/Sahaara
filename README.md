# Sahaara (सहारा): Gita-inspired multilingual voice companion

Voice-first emotional-wellbeing companion for India, built for the Gnani **Great Indian AI Internship Challenge**.
**Gnani Prisma** (speech-to-text) and **Gnani Timbre** (text-to-speech) power the voice loop; a **hybrid RAG** over the Bhagavad Gita, CBT-style tools, practices and your own books grounds every reply.

## What makes it different
- **Verse grounding**: the LLM never writes Sanskrit. The app shows the verse from its own library and the model only cites `[S#]`, so shlokas cannot be hallucinated.
- **Safety before the LLM**: crisis phrases (10 languages + Hinglish) bypass the model and return a fixed, localized message with Tele-MANAS 14416 / 112.
- **Swap the LLM in one line**: Groq, Gemini, Ollama (Qwen2.5-7B) or any OpenAI-compatible server; optional fallback; works with no LLM at all (extractive mode).
- **Voice**: browser-side 16 kHz WAV recording with silence auto-stop (Prisma needs WAV, max 30 s), codemix output, auto language, sentence-pipelined Timbre playback, browser-speech fallback, calls serialised for one-request accounts.
- Guided breathing coach, local-only mood journal, verse of the day, large-text mode.

## Run (Mac)
```bash
cd sahaara && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:7b && ollama pull bge-m3
cp .env.example .env   # then put GNANI_API_KEY in it
cd backend && python scripts/build_index.py     # one-time: embeds ~1,500 chunks with bge-m3
cd .. && OLLAMA_KEEP_ALIVE=-1 uvicorn app.main:app --app-dir backend --port 8000
```
Open http://localhost:8000 (add `?debug=1` to see retrieval / first-token / first-audio timings).
`GET /api/health` shows the active LLM, whether the Gita corpus and dense index are loaded, and whether Gnani is configured.

## How the RAG works (real Bhagavad-gita As It Is text, chapters 1-15 provided)
1. `scripts/build_gita.py` parses the PDF text into 524 verse records (Devanagari from IAST, translation, synonyms) and 932 purport chunks.
2. Contextual chunking: every purport chunk is indexed with its chapter title, verse reference and the verse translation.
3. Hybrid retrieval: BM25 (query expanded with an English gloss of the detected emotion so Hindi/Hinglish messages match) + bge-m3 dense vectors + a small curated prior of classic verses, merged with Reciprocal Rank Fusion; then 2 verses from different chapters, the best purport passage, one practice/tool, rarely a story.
4. The LLM (Qwen) writes the reply from that context and cites `[S#]`; the cards show the actual verse text. Late chunking was not used: it needs a long-context embedder with token-level pooling, which Ollama does not expose.

## Voice latency design
Replies are spoken while the model is still writing (sentence-by-sentence TTS pipeline), the first chunk is kept short, one persistent connection pool per service, models stay loaded (`keep_alive`), TTS results are cached on disk (verses and phrases are instant the second time; `python scripts/warm_tts.py` pre-fills them), the recording is trimmed of trailing silence before STT. Cited verses are spoken too (intro, Sanskrit, translation). Not done: Gnani's streaming SSE TTS and streaming STT, whose chunk formats I could not verify without live access.

## Add books
```bash
cd backend && python scripts/ingest.py book.pdf --source "Man's Search for Meaning"
```
Chunks go to `backend/data/corpus/user/` (gitignored). Excerpts stay hidden in the UI unless `SHOW_BOOK_EXCERPTS=1`; only the citation shows. Use only material you may use.

## Test and evaluate
```bash
cd backend && python -m pytest -q tests && python eval/run_eval.py
```
Results on the small hand-made set: retrieval hit 13/14, topic detection 14/14, crisis recall 8/8, false alarms 0/5. The set is tiny and written by the author: a smoke test, not a benchmark. Grow it before quoting numbers.

## Before you submit
1. **Verify every Sanskrit verse** in `backend/app/rag/starter.py` against a trusted edition (typed by hand). Meanings are original paraphrases.
2. **Verify helpline numbers** and have a counsellor review the crisis wording in `safety.py`.
3. Test live Gnani STT/TTS and your LLM with your keys. They follow the docs but were not run against the live APIs.
4. Demo with synthetic or consented audio only. Never commit `.env`.
5. Deadline **10 Nov 2026, 11:59 PM IST**: public LinkedIn/X demo (~60 s: Hindi voice query, verse + breathing, crisis safety, LLM switch), tags `#GreatIndianAIInternshipChallenge #GnaniAI`, name Prisma and Timbre, link the repo.

Not a medical device; not a substitute for professional care.

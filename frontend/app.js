'use strict';
/* Sahaara frontend. Model text is rendered with textContent only (never innerHTML). */
const $ = (id) => document.getElementById(id);
const h = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) { if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); }
  for (const k of kids.flat()) if (k != null) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
};
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};
const DEBUG = new URLSearchParams(location.search).has('debug');
const S = { history: [], busy: false, voice: store.get('voice', true), large: store.get('large', false), lang: store.get('lang', 'auto'), replyLang: 'en-IN' };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chatBox = $('chatBox'), statusEl = $('status');
const IDLE = 'Threaded in Tradition';
const setStatus = (t) => { statusEl.textContent = t || IDLE; };
const mainEl = document.querySelector('main');
const scrollDown = () => requestAnimationFrame(() => mainEl.scrollTo({ top: mainEl.scrollHeight, behavior: 'smooth' }));

/* ================= settings ================= */
function applySettings() {
  $('languageSelector').value = S.lang;
  $('voiceToggle').setAttribute('aria-pressed', S.voice);
  $('voiceToggle').firstElementChild.className = S.voice ? 'fas fa-volume-up' : 'fas fa-volume-mute';
  $('textSize').setAttribute('aria-pressed', S.large); document.body.classList.toggle('large', S.large);
}
$('languageSelector').onchange = (e) => { S.lang = e.target.value; store.set('lang', S.lang); loadWelcome(); };
$('voiceToggle').onclick = () => { S.voice = !S.voice; store.set('voice', S.voice); if (!S.voice) speaker.reset(); applySettings(); };
$('textSize').onclick = () => { S.large = !S.large; store.set('large', S.large); applySettings(); };

/* ================= speech output: pipelined Gnani Timbre, browser fallback ================= */
const playUrl = (url) => new Promise((res) => {
  const a = new Audio(url); speaker.audio = a;
  a.onended = a.onerror = () => { URL.revokeObjectURL(url); res(); }; a.play().catch(res);
});
const browserSpeak = (text, lang) => new Promise((res) => {
  try { const u = new SpeechSynthesisUtterance(text); u.lang = lang === 'hi-en' ? 'hi-IN' : lang; u.rate = 0.92; u.onend = u.onerror = res; speechSynthesis.speak(u); } catch { res(); }
});
const speaker = {
  q: [], playing: false, token: 0, audio: null, firstAt: 0,
  fetch(text, lang) {
    return fetch('/api/tts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, language: lang }) })
      .then((r) => (r.ok ? r.blob() : Promise.reject(new Error('tts')))).then((b) => URL.createObjectURL(b)).catch(() => null);
  },
  say(text, lang) {
    text = (text || '').trim(); if (!S.voice || !text) return;
    this.q.push({ text, lang, p: this.fetch(text, lang) }); this.pump();   // request starts NOW, plays in order
  },
  async pump() {
    if (this.playing) return; this.playing = true; const tok = this.token; $('micBtn').classList.add('speaking');
    while (this.q.length && tok === this.token) {
      const it = this.q.shift(), url = await it.p; if (tok !== this.token) return;
      if (this.firstAt === 0) { this.firstAt = performance.now(); onFirstAudio(); }
      if (url) await playUrl(url); else await browserSpeak(it.text, it.lang);
    }
    if (tok === this.token) { this.playing = false; $('micBtn').classList.remove('speaking'); }
  },
  reset() {
    this.token++; this.q = []; this.playing = false; this.firstAt = 0; $('micBtn').classList.remove('speaking');
    if (this.audio) { this.audio.pause(); this.audio = null; } try { speechSynthesis.cancel(); } catch { /* none */ }
  },
};
let sendT0 = 0, lastTiming = null, timingEl = null;
function onFirstAudio() { if (DEBUG && timingEl) timingEl.textContent = fmtTiming(lastTiming, Math.round(performance.now() - sendT0)); }
const fmtTiming = (t, audio) => [t && `retrieve ${t.retrieve_ms}ms`, t && t.ttft_ms != null && `first token ${t.ttft_ms}ms`, t && `total ${t.total_ms}ms`, audio && `first audio ${audio}ms`].filter(Boolean).join(' · ');

/* Cut the streaming reply into speakable chunks: the first chunk is short so audio starts early. */
function makeChunker() {
  let buf = '', first = true;
  const take = () => {
    const out = [];
    for (;;) {
      const m = /^([\s\S]*?[.!?।]["”']?)\s+/.exec(buf); if (!m) break;
      let piece = m[1], used = m[0].length;
      if (piece.length < (first ? 24 : 70)) {
        const m2 = /^([\s\S]*?[.!?।]["”']?)\s+([\s\S]*?[.!?।]["”']?)\s+/.exec(buf); if (!m2) break;
        piece = `${m2[1]} ${m2[2]}`; used = m2[0].length;
      }
      out.push(piece); buf = buf.slice(used); first = false;
    }
    return out;
  };
  return { push(t) { buf += t; return take(); }, flush() { const r = buf.trim(); buf = ''; return r ? [r] : []; } };
}

/* Every cited verse is also spoken: intro, the Sanskrit, then the translation (English/Hinglish users). */
function verseSegments(card, lang) {
  const hi = lang === 'hi-IN' || lang === 'mr-IN', [ch, v] = (card.ref || '').split('.');
  const verse = (v || '').replace('–', ' to ');
  const segs = [[hi ? `भगवद्गीता, अध्याय ${ch}, श्लोक ${verse}।` : `From the Bhagavad Gita, chapter ${ch}, verse ${verse}.`, hi ? 'hi-IN' : 'en-IN']];
  if (card.devanagari) segs.push([card.devanagari.replace(/\n/g, '। '), 'hi-IN']);
  if ((lang === 'en-IN' || lang === 'hi-en') && card.meaning_tts) segs.push([card.meaning_tts, 'en-IN']);
  return segs;
}
function speakVerse(card, lang) { for (const [t, l] of verseSegments(card, lang)) speaker.say(t, l); }

/* ================= cards ================= */
function listenBtn(card) {
  return h('button', { class: 'pill', onclick: () => { speaker.reset(); S.voice ? speakVerse(card, S.replyLang) : (() => { S.voice = true; applySettings(); speakVerse(card, S.replyLang); })(); } },
    h('i', { class: 'fas fa-volume-up' }), ' Listen');
}
function sourceCard(c) {
  const tag = h('span', { class: 'tag' }, `S${c.n}`);
  if (c.type === 'shloka') return h('article', { class: 'card verse' },
    h('h4', {}, tag, c.title, c.chapter_title ? ` · ${c.chapter_title}` : ''),
    c.devanagari ? h('div', { class: 'sk', lang: 'sa' }, c.devanagari) : null, c.iast ? h('div', { class: 'iast' }, c.iast) : null,
    h('p', {}, c.meaning), h('div', { class: 'row' }, listenBtn(c)));
  if (c.type === 'purport') return h('article', { class: 'card purport' }, h('h4', {}, tag, c.title), h('p', {}, c.text));
  if (c.type === 'practice' || c.type === 'tool') {
    const go = c.breath ? h('button', { class: 'pill primary', onclick: () => startBreath(c.breath) }, S.replyLang.startsWith('hi') ? 'साथ में साँस लें' : 'Breathe with me') : null;
    return h('article', { class: `card ${c.type}` }, h('h4', {}, tag, c.title), h('ol', {}, (c.steps || []).map((s) => h('li', {}, s))), go ? h('div', { class: 'row' }, go) : null);
  }
  if (c.type === 'story') return h('article', { class: 'card story' }, h('h4', {}, tag, c.title), h('p', {}, c.summary), h('p', {}, h('b', {}, c.moral)));
  return h('article', { class: 'card book' }, h('h4', {}, tag, c.source + (c.ref ? ` · ${c.ref}` : '')), c.text ? h('p', {}, c.text) : h('p', {}, 'Ideas in this reply draw on this book.'));
}

/* ================= chat ================= */
function addUser(text) { chatBox.append(h('div', { class: 'message user-message' }, text)); scrollDown(); }
function addBot() {
  const bubble = h('div', { class: 'message bot-message' }, h('div', { class: 'typing-indicator' }, h('span', { class: 'typing-dot' }), h('span', { class: 'typing-dot' }), h('span', { class: 'typing-dot' })));
  const cards = h('div', { class: 'cards', style: 'display:flex;flex-direction:column;gap:8px' }), timing = h('div', { class: 'timing' });
  chatBox.append(h('div', { class: 'bot-wrap' }, bubble, cards, timing)); scrollDown();
  return { bubble, cards, timing };
}
function showCrisis(helplines) {
  $('crisis').replaceChildren(h('b', {}, 'You are not alone. '), ...helplines.flatMap((x) => [`${x.name}: `, h('a', { href: `tel:${x.number}` }, x.number), '  ']));
  $('crisis').hidden = false;
}

async function send(text, sttLang) {
  text = text.trim(); if (!text || S.busy) return;
  S.busy = true; speaker.reset(); sendT0 = performance.now(); addUser(text); $('textInput').value = '';
  const { bubble, cards, timing } = addBot(); timingEl = timing; lastTiming = null;
  const chunker = makeChunker(); let acc = '', sources = [], doneEvt = null, first = true, lang = S.replyLang;
  setStatus('Sahaara is thinking…');
  try {
    const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: S.history.slice(-10), language: S.lang, stt_language: sttLang || null }) });
    if (!r.ok) throw new Error(r.status === 429 ? 'rate' : 'http');
    const reader = r.body.getReader(), dec = new TextDecoder(); let buf = '';
    for (;;) {
      const { value, done } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let i; while ((i = buf.indexOf('\n\n')) !== -1) {
        const raw = buf.slice(0, i); buf = buf.slice(i + 2);
        const ev = /^event: (.+)$/m.exec(raw)?.[1], dm = /^data: (.+)$/m.exec(raw); if (!ev || !dm) continue;
        const d = JSON.parse(dm[1]);
        if (ev === 'meta') { lang = S.replyLang = d.lang; if (d.helplines) showCrisis(d.helplines); if (d.provider === 'extractive') setStatus('Offline mode'); }
        else if (ev === 'sources') { sources = d.sources; }
        else if (ev === 'token') {
          if (first) { bubble.textContent = ''; first = false; }
          acc += d.t; bubble.textContent = acc; scrollDown();
          for (const s of chunker.push(d.t)) speaker.say(s, lang);          // speak while the model is still writing
        } else if (ev === 'done') doneEvt = d;
      }
    }
  } catch (e) {
    bubble.textContent = e.message === 'rate' ? 'Please give me a moment and try again.' : 'I could not reach the server. Please check your connection and try again. If you need someone now, call 14416.';
    S.busy = false; setStatus(); return;
  }
  for (const s of chunker.flush()) speaker.say(s, lang);
  const final = doneEvt?.text ?? acc; bubble.textContent = final; lastTiming = doneEvt?.timing || null;
  const cited = doneEvt?.cited || [];
  if (cited.length) bubble.append(h('span', { class: 'cites' }, cited.map((n) => `[${n}]`).join('')));
  const shown = sources.filter((c) => !c.hidden && !doneEvt?.crisis);
  for (const c of shown) cards.append(sourceCard(c));
  if (DEBUG) timing.textContent = fmtTiming(lastTiming, speaker.firstAt ? Math.round(speaker.firstAt - sendT0) : 0);
  // speak the verse(s) the answer cites (or the lead verse when the model cited none)
  const verses = shown.filter((c) => c.type === 'shloka');
  const spoken = (cited.length ? verses.filter((c) => cited.includes(c.n)) : []).concat(cited.length ? [] : verses.slice(0, 1)).slice(0, 2);
  for (const v of spoken) speakVerse(v, lang);
  S.history.push({ role: 'user', content: text }, { role: 'assistant', content: final });
  S.busy = false; setStatus(); scrollDown();
}
$('form').onsubmit = (e) => { e.preventDefault(); send($('textInput').value); };

/* ================= speech input: 16 kHz WAV, silence auto-stop, Gnani Prisma ================= */
const rec = { ctx: null, stream: null, proc: null, chunks: [], on: false, silentFor: 0, heard: false, t0: 0, lastVoiced: -1 };
function encodeWav(f32, rate) {
  const buf = new ArrayBuffer(44 + f32.length * 2), v = new DataView(buf), w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); v.setUint32(4, 36 + f32.length * 2, true); w(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, f32.length * 2, true);
  for (let i = 0; i < f32.length; i++) { const s = Math.max(-1, Math.min(1, f32[i])); v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true); }
  return new Blob([buf], { type: 'audio/wav' });
}
function downsample(d, from, to) {
  if (from === to) return d; const ratio = from / to, out = new Float32Array(Math.floor(d.length / ratio));
  for (let i = 0; i < out.length; i++) { const a = Math.floor(i * ratio), b = Math.max(a + 1, Math.floor((i + 1) * ratio)); let s = 0; for (let j = a; j < b; j++) s += d[j]; out[i] = s / (b - a); }
  return out;
}
async function startRec() {
  if (S.busy || rec.on) return; speaker.reset();
  try { rec.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } }); }
  catch { setStatus('Allow the microphone, or type'); return; }
  rec.ctx = new (window.AudioContext || window.webkitAudioContext)();
  const src = rec.ctx.createMediaStreamSource(rec.stream); rec.proc = rec.ctx.createScriptProcessor(2048, 1, 1);
  Object.assign(rec, { chunks: [], silentFor: 0, heard: false, t0: Date.now(), on: true, lastVoiced: -1 });
  rec.proc.onaudioprocess = (e) => {
    const d = new Float32Array(e.inputBuffer.getChannelData(0)); rec.chunks.push(d);
    let sum = 0; for (let i = 0; i < d.length; i++) sum += d[i] * d[i];
    const rms = Math.sqrt(sum / d.length), dt = d.length / rec.ctx.sampleRate;
    if (rms > 0.015) { rec.heard = true; rec.silentFor = 0; rec.lastVoiced = rec.chunks.length - 1; } else if (rec.heard) rec.silentFor += dt;
    if (rec.silentFor > 1.1 || Date.now() - rec.t0 > 27000) stopRec(true);
  };
  src.connect(rec.proc); rec.proc.connect(rec.ctx.destination);
  $('micBtn').classList.add('listening'); setStatus('Listening…');
}
async function stopRec(submit) {
  if (!rec.on) return; rec.on = false; $('micBtn').classList.remove('listening');
  const rate = rec.ctx.sampleRate; rec.proc.disconnect(); rec.stream.getTracks().forEach((t) => t.stop()); await rec.ctx.close();
  if (!submit || !rec.heard) { setStatus(); return; }
  const keep = rec.chunks.slice(0, rec.lastVoiced + 4);                      // trim the silent tail: smaller upload, faster STT
  const n = keep.reduce((a, c) => a + c.length, 0), all = new Float32Array(n); let o = 0; for (const c of keep) { all.set(c, o); o += c.length; }
  setStatus('Understanding…'); const t0 = performance.now();
  try {
    const fd = new FormData(); fd.append('audio', encodeWav(downsample(all, rate, 16000), 16000), 'speech.wav');
    fd.append('language', S.lang === 'auto' ? 'indic-auto' : S.lang.replace('hi-en', 'hi-IN'));
    const r = await fetch('/api/stt', { method: 'POST', body: fd }); const j = await r.json();
    if (!r.ok || !j.transcript) throw new Error(j.error || 'empty');
    if (DEBUG) console.log('STT ms', Math.round(performance.now() - t0), j);
    send(j.transcript, j.language);
  } catch (e) { setStatus('Could not hear that. Try again or type.'); console.warn(e); }
}
$('micBtn').onclick = () => (rec.on ? stopRec(true) : startRec());

/* ================= guided breathing ================= */
let breathRun = 0;
async function startBreath(key) {
  const p = await (await fetch(`/api/breathe/${key}?language=${S.replyLang}`)).json(), run = ++breathRun, orb = $('orb');
  speaker.reset(); $('bTitle').textContent = p.name; $('breath').hidden = false; $('bCue').textContent = p.start; speaker.say(p.start, S.replyLang); await sleep(3500);
  for (let c = 0; c < p.cycles && run === breathRun; c++) for (const ph of p.phases) {
    if (run !== breathRun) break; $('bCue').textContent = ph.cue;
    orb.style.transitionDuration = `${ph.seconds}s`; orb.style.transform = ph.kind === 'in' ? 'scale(1.15)' : ph.kind === 'hold' ? orb.style.transform : 'scale(.6)';
    for (let s = ph.seconds; s > 0 && run === breathRun; s--) { $('bCount').textContent = s; await sleep(1000); }
  }
  if (run === breathRun) { $('bCue').textContent = p.done; $('bCount').textContent = ''; speaker.say(p.done, S.replyLang); }
}
$('bStop').onclick = () => { breathRun++; $('breath').hidden = true; speaker.reset(); $('orb').style.transform = 'scale(.6)'; };

/* ================= mood journal (device only) ================= */
const MOODS = ['😞', '😟', '😐', '🙂', '😊'];
function renderMood() {
  $('moodPick').replaceChildren(...MOODS.map((m, i) => h('button', { 'aria-label': `Mood ${i + 1} of 5`, onclick: () => { const log = store.get('moods', []); log.push({ d: new Date().toISOString(), v: i }); store.set('moods', log.slice(-60)); renderMood(); } }, m)));
  $('moodBars').replaceChildren(...store.get('moods', []).slice(-7).map((e) => h('div', { style: `height:${20 + e.v * 17}px`, title: new Date(e.d).toLocaleDateString() }, MOODS[e.v])));
}
$('moodBtn').onclick = () => { renderMood(); $('mood').hidden = false; }; $('moodClose').onclick = () => { $('mood').hidden = true; };

/* ================= helplines ================= */
async function openHelp() {
  let items = [{ name: 'Tele-MANAS', number: '14416', note: 'Free mental health helpline' }, { name: 'Emergency', number: '112', note: '' }];
  try { items = (await (await fetch('/api/helplines')).json()).helplines; } catch { /* defaults */ }
  $('helpList').replaceChildren(...items.map((x) => h('div', { class: 'hl' }, h('div', {}, h('b', {}, x.name), h('div', {}, x.note || '')), h('a', { href: `tel:${x.number}` }, `Call ${x.number}`))));
  $('help').hidden = false;
}
$('helpBtn').onclick = openHelp; $('helpClose').onclick = () => { $('help').hidden = true; };
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { $('help').hidden = true; $('mood').hidden = true; if (!$('breath').hidden) $('bStop').click(); } });

/* ================= welcome ================= */
async function loadWelcome() {
  const lang = S.lang === 'auto' ? (navigator.language || 'en-IN') : S.lang, hi = lang.startsWith('hi');
  try {
    const sg = await (await fetch(`/api/suggestions?language=${hi ? 'hi-IN' : 'en-IN'}`)).json();
    $('chips').replaceChildren(...sg.suggestions.map((t) => h('button', { class: 'chip', onclick: () => send(t) }, t)));
    const v = await (await fetch(`/api/verse/daily?language=${hi ? 'hi-IN' : 'en-IN'}`)).json(), box = $('votd');
    box.replaceChildren(h('h4', {}, hi ? 'आज का श्लोक' : 'Verse of the day', ' · ', v.title), v.devanagari ? h('div', { class: 'sk', lang: 'sa' }, v.devanagari) : null, h('p', {}, v.meaning), h('div', { class: 'row' }, listenBtn(v)));
    box.hidden = false;
  } catch { /* optional */ }
}
fetch('/api/health').then((r) => r.json()).then((j) => { if (DEBUG) console.log('health', j); }).catch(() => {});
applySettings(); loadWelcome();

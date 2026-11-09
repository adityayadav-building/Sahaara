'use strict';
/* ═══════════════════════════════════════════════════════════════════════════
   SAHAARA — Production Companion Architecture
   • Full Voice & Text Chat with Ultra-Fast Latency (<1.5s)
   • Dual-Engine Speech Output: Gnani Timbre v3.0 + Instant Browser Fallback
   • Prominent Red STOP Button for instant halt of speech & mic
   • Punctuation Filter (never pronounces stray noise/commas)
   • Clean Separation: Calm Push-to-Talk in Basic Chat vs Continuous Immersion
     in Dedicated Voice Sanctuary / Bedside Mode
   • Natural Bhagavad Gita RAG (Wisdom woven into advice, clean info cards)
   • 11 Indian Languages + Voice Catalog & Pace Control
   ═══════════════════════════════════════════════════════════════════════════ */

const $ = (id) => document.getElementById(id);
const h = (tag, props = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
        if (k === 'class') e.className = v;
        else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
        else e.setAttribute(k, v);
    }
    for (const k of kids.flat()) if (k != null) e.append(k.nodeType ? k : document.createTextNode(k));
    return e;
};

const store = {
    get(k, d) { try { const v = localStorage.getItem('sahaara_' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem('sahaara_' + k, JSON.stringify(v)); } catch {} },
};

const DEBUG = new URLSearchParams(location.search).has('debug');
const IDLE = 'Threaded in Tradition';

const VALID_V3_VOICES = ['Chetana', 'Shivani', 'Lakshmi', 'Kalpana', 'Vasudha', 'Riyaa', 'Tarika', 'Devansh', 'Avinash', 'Shubham', 'Prakash', 'Yashraj', 'Harshad'];
let savedVoice = store.get('chosenVoice', 'Chetana');
if (!VALID_V3_VOICES.includes(savedVoice)) {
    savedVoice = 'Chetana';
    store.set('chosenVoice', 'Chetana');
}

/* ═══════ State ═══════ */
const S = {
    history: [],
    busy: false,
    voice: store.get('voice', true),
    large: store.get('large', false),
    theme: store.get('theme', 'dark'),
    lang: store.get('lang', 'auto'),
    chosenVoice: savedVoice,
    chosenSpeed: store.get('chosenSpeed', 1.0),
    handsfree: false,
    isBedsideMode: false,
    replyLang: 'en-IN',
};

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const chatBox = $('chatBox'), statusEl = $('status'), mainEl = $('mainArea');
const setStatus = (t) => { if (statusEl) statusEl.textContent = t || IDLE; };
const scrollDown = () => requestAnimationFrame(() => {
    if (mainEl) mainEl.scrollTo({ top: mainEl.scrollHeight, behavior: 'smooth' });
});
const haptic = (ms = 40) => { try { navigator.vibrate?.(ms); } catch {} };

/* ═══════════════════════════════════════════════════════════════════════════
   AUDIO CONTEXT & AUTOPLAY UNLOCK
   ═══════════════════════════════════════════════════════════════════════════ */
let audioCtx = null;
function getAudioContext() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
}

function unlockAudio() {
    try {
        const ctx = getAudioContext();
        if (ctx.state === 'suspended') ctx.resume();
        const b = ctx.createBuffer(1, 1, 22050);
        const src = ctx.createBufferSource();
        src.buffer = b;
        src.connect(ctx.destination);
        src.start(0);


    } catch {}
}
window.addEventListener('click', unlockAudio, { once: true });
window.addEventListener('touchstart', unlockAudio, { once: true });
window.addEventListener('keydown', unlockAudio, { once: true });

/* ═══════════════════════════════════════════════════════════════════════════
   PROCEDURAL WEBAUDIO MEDITATION CHIMES
   ═══════════════════════════════════════════════════════════════════════════ */
function playChime(kind) {
    try {
        const ctx = getAudioContext();
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (kind === 'listening') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(432, now);
            gain.gain.setValueAtTime(0.001, now);
            gain.gain.exponentialRampToValueAtTime(0.08, now + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.7);
            osc.start(now);
            osc.stop(now + 0.75);
        } else if (kind === 'thinking') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(216, now);
            gain.gain.setValueAtTime(0.001, now);
            gain.gain.exponentialRampToValueAtTime(0.03, now + 0.08);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.5);
            osc.start(now);
            osc.stop(now + 0.55);
        } else if (kind === 'speaking') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(432, now);
            osc.frequency.exponentialRampToValueAtTime(540, now + 0.1);
            gain.gain.setValueAtTime(0.001, now);
            gain.gain.exponentialRampToValueAtTime(0.06, now + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.65);
        } else if (kind === 'barge') {
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(320, now);
            gain.gain.setValueAtTime(0.04, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
            osc.start(now);
            osc.stop(now + 0.07);
        }
    } catch {}
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREEN WAKE LOCK (Bedside Sanctuary Mode)
   ═══════════════════════════════════════════════════════════════════════════ */
let wakeLock = null;
async function requestWakeLock() {
    try {
        if ('wakeLock' in navigator) {
            wakeLock = await navigator.wakeLock.request('screen');
            wakeLock.addEventListener('release', () => { wakeLock = null; });
        }
    } catch {}
}
function releaseWakeLock() {
    try {
        if (wakeLock) { wakeLock.release(); wakeLock = null; }
    } catch {}
}

/* ═══════════════════════════════════════════════════════════════════════════
   AMBIENT CANVAS — Soft floating particles
   ═══════════════════════════════════════════════════════════════════════════ */
(function initCanvas() {
    const canvas = $('ambientCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles = [];
    const PARTICLE_COUNT = 35;

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function createParticle() {
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 2 + 0.5,
            dx: (Math.random() - 0.5) * 0.3,
            dy: (Math.random() - 0.5) * 0.2 - 0.1,
            opacity: Math.random() * 0.3 + 0.05,
        };
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        const isDark = document.documentElement.dataset.theme !== 'light';
        const color = isDark ? '212, 167, 106' : '38, 70, 83';

        for (const p of particles) {
            p.x += p.dx;
            p.y += p.dy;
            if (p.x < -10) p.x = W + 10;
            if (p.x > W + 10) p.x = -10;
            if (p.y < -10) p.y = H + 10;
            if (p.y > H + 10) p.y = -10;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${color}, ${p.opacity})`;
            ctx.fill();
        }
        requestAnimationFrame(draw);
    }

    resize();
    for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(createParticle());
    window.addEventListener('resize', resize);
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) draw();
})();

/* ═══════════════════════════════════════════════════════════════════════════
   LIVE AUDIO FREQUENCY VISUALIZER (Gemini Live / Siri Style)
   Smooth HTML5 Canvas waveform & organic breathing ring responding to pitch & volume
   ═══════════════════════════════════════════════════════════════════════════ */
const visualizer = {
    analyser: null,
    freqData: null,
    timeData: null,
    micSrc: null,
    state: 'idle', // idle, listening, hearing, thinking, speaking
    t: 0,
    smoothedLevel: 0,

    init() {
        if (this.analyser) return;
        try {
            const ctx = getAudioContext();
            this.analyser = ctx.createAnalyser();
            this.analyser.fftSize = 128;
            this.analyser.smoothingTimeConstant = 0.82;
            this.freqData = new Uint8Array(this.analyser.frequencyBinCount);
            this.timeData = new Uint8Array(this.analyser.fftSize);
        } catch {}
        this.loop();
    },

    connectMic(stream) {
        this.init();
        try {
            const ctx = getAudioContext();
            this.disconnectMic();
            this.micSrc = ctx.createMediaStreamSource(stream);
            this.micSrc.connect(this.analyser);
        } catch (e) {}
    },

    disconnectMic() {
        if (this.micSrc) {
            try { this.micSrc.disconnect(); } catch {}
            this.micSrc = null;
        }
    },

    connectAudio(audioEl) {
        // Native HTML5 Audio plays directly with 100% studio fidelity and 0 WebAudio latency
    },

    setState(st) {
        this.state = st || 'idle';
    },

    getRealLevel() {
        if (!this.analyser) return 0;
        this.analyser.getByteFrequencyData(this.freqData);
        let sum = 0;
        const count = this.freqData.length;
        for (let i = 0; i < count; i++) sum += this.freqData[i];
        return sum / (count * 255);
    },

    loop() {
        requestAnimationFrame(() => this.loop());
        this.t += 0.035;

        // Calculate audio activity level (smooth harmonic modulation when speaking)
        const realLevel = this.getRealLevel();
        const speechLevel = this.state === 'speaking' ? 0.36 + 0.22 * Math.sin(this.t * 4.8) * Math.cos(this.t * 2.9) : 0;
        const activeState = (this.state === 'hearing' || this.state === 'speaking');
        const targetLevel = activeState ? Math.max(realLevel, speechLevel, 0.12) : realLevel;
        this.smoothedLevel += (targetLevel - this.smoothedLevel) * 0.25;

        // Render to Bedside Sanctuary Canvas
        const bCanvas = $('bedsideVisualizerCanvas');
        if (bCanvas && S.isBedsideMode) {
            this.renderBedside(bCanvas);
        }

        // Render to Mic Button Canvas
        const mCanvas = $('micVisualizerCanvas');
        if (mCanvas) {
            this.renderMic(mCanvas);
        }
    },

    renderBedside(canvas) {
        const ctx = canvas.getContext('2d');
        const W = canvas.width, H = canvas.height;
        const cx = W / 2, cy = H / 2;
        ctx.clearRect(0, 0, W, H);

        const lvl = this.smoothedLevel;
        const st = this.state;
        const isSpeaking = st === 'speaking';
        const isHearing = st === 'hearing';
        const isThinking = st === 'thinking';

        let colorA, colorB, baseR;
        if (isSpeaking) {
            colorA = 'rgba(74, 157, 143, 0.85)'; // Emerald/Sage
            colorB = 'rgba(42, 157, 143, 0.2)';
            baseR = 64 + lvl * 42;
        } else if (isHearing) {
            colorA = 'rgba(231, 111, 81, 0.9)'; // Saffron/Coral
            colorB = 'rgba(244, 162, 97, 0.25)';
            baseR = 62 + lvl * 50;
        } else if (isThinking) {
            colorA = 'rgba(212, 167, 106, 0.8)'; // Deep Gold
            colorB = 'rgba(110, 78, 32, 0.2)';
            baseR = 58 + Math.sin(this.t * 2) * 5;
        } else {
            const breath = (Math.sin(this.t * 0.6) + 1) * 0.5;
            colorA = 'rgba(212, 167, 106, 0.7)';
            colorB = 'rgba(212, 167, 106, 0.12)';
            baseR = 56 + breath * 9;
        }

        for (let ring = 0; ring < 3; ring++) {
            ctx.save();
            ctx.beginPath();
            const N = 40;
            const rOffset = ring * 12;
            const waveAmp = (lvl > 0.05 ? lvl * 18 : 3) + ring * 2;
            const freqShift = ring * 1.3 + this.t * (ring % 2 === 0 ? 1 : -1);

            for (let i = 0; i <= N; i++) {
                const angle = (i / N) * Math.PI * 2;
                const bin = Math.floor((i / N) * (this.freqData ? this.freqData.length * 0.6 : 1));
                const fVal = this.freqData ? (this.freqData[bin] / 255) : 0;
                const wave = Math.sin(angle * (4 + ring) + freqShift) * waveAmp + (fVal * 15);
                const r = baseR + rOffset + wave;
                const x = cx + Math.cos(angle) * r;
                const y = cy + Math.sin(angle) * r;

                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.strokeStyle = colorA;
            ctx.lineWidth = 2.2 - ring * 0.5;
            ctx.stroke();

            if (ring === 0) {
                const grad = ctx.createRadialGradient(cx, cy, 20, cx, cy, baseR + 25);
                grad.addColorStop(0, colorB);
                grad.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = grad;
                ctx.fill();
            }
            ctx.restore();
        }
    },

    renderMic(canvas) {
        const ctx = canvas.getContext('2d');
        const W = canvas.width, H = canvas.height;
        const cx = W / 2, cy = H / 2;
        ctx.clearRect(0, 0, W, H);

        const lvl = this.smoothedLevel;
        const st = this.state;
        if (st === 'idle') return;

        let color = st === 'speaking' ? 'rgba(74, 157, 143,' : st === 'hearing' ? 'rgba(231, 111, 81,' : 'rgba(212, 167, 106,';
        const baseR = 24 + lvl * 14;

        for (let i = 1; i <= 2; i++) {
            const r = baseR + i * (6 + lvl * 8) + (Math.sin(this.t * 3 + i) * 2);
            const alpha = Math.max(0, (0.7 - i * 0.25) * (st === 'hearing' || st === 'speaking' ? 0.9 : 0.5));
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.strokeStyle = `${color} ${alpha})`;
            ctx.lineWidth = 1.8;
            ctx.stroke();
        }
    }
};

/* ═══════════════════════════════════════════════════════════════════════════
   SETTINGS & THEME
   ═══════════════════════════════════════════════════════════════════════════ */
function applySettings() {
    document.documentElement.dataset.theme = S.theme;
    document.body.classList.toggle('large', S.large);
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = S.theme === 'dark' ? '#0f1923' : '#FBF6F1';

    if ($('languageSelector')) $('languageSelector').value = S.lang;
    if ($('voiceToggle')) {
        $('voiceToggle').setAttribute('aria-pressed', S.voice);
        $('voiceToggle').querySelector('i').className = S.voice ? 'fas fa-volume-up' : 'fas fa-volume-mute';
        $('voiceToggle').classList.toggle('active', S.voice);
    }

    // Sync drawer settings
    if ($('themeToggle')) $('themeToggle').checked = S.theme === 'dark';
    if ($('voiceToggleSetting')) $('voiceToggleSetting').checked = S.voice;
    if ($('textSizeSetting')) $('textSizeSetting').checked = S.large;
    if ($('voiceSpeed')) $('voiceSpeed').value = S.chosenSpeed;
    if ($('voiceSpeedVal')) {
        const val = parseFloat(S.chosenSpeed);
        const label = val <= 0.9 ? 'Gentle & Deliberate' : val >= 1.1 ? 'Energetic' : 'Natural';
        $('voiceSpeedVal').textContent = `${val.toFixed(2)}x (${label})`;
    }

    if ($('handsfreeBtn')) {
        $('handsfreeBtn').classList.toggle('active', S.handsfree);
    }
    if ($('bedsideHandsfreeBtn')) {
        $('bedsideHandsfreeBtn').classList.toggle('active', S.handsfree);
        $('bedsideHandsfreeBtn').innerHTML = S.handsfree
            ? '<i class="fas fa-headset"></i> Hands-Free Active'
            : '<i class="fas fa-headset"></i> Hands-Free Paused';
    }
}

if ($('languageSelector')) {
    $('languageSelector').onchange = (e) => {
        S.lang = e.target.value;
        store.set('lang', S.lang);
        voiceGW.sendInit();
        loadWelcome();
    };
}

if ($('voiceToggle')) {
    $('voiceToggle').onclick = () => {
        S.voice = !S.voice;
        store.set('voice', S.voice);
        if (!S.voice) speaker.reset();
        applySettings();
    };
}

if ($('themeToggle')) {
    $('themeToggle').onchange = () => {
        S.theme = $('themeToggle').checked ? 'dark' : 'light';
        store.set('theme', S.theme);
        applySettings();
    };
}

if ($('voiceToggleSetting')) {
    $('voiceToggleSetting').onchange = () => {
        S.voice = $('voiceToggleSetting').checked;
        store.set('voice', S.voice);
        if (!S.voice) speaker.reset();
        applySettings();
    };
}

if ($('textSizeSetting')) {
    $('textSizeSetting').onchange = () => {
        S.large = $('textSizeSetting').checked;
        store.set('large', S.large);
        applySettings();
    };
}

if ($('textInput')) {
    $('textInput').addEventListener('input', () => {
        if ($('sendBtn')) $('sendBtn').disabled = !$('textInput').value.trim();
    });
}

/* ═══════════════════════════════════════════════════════════════════════════
   DRAWER NAVIGATION
   ═══════════════════════════════════════════════════════════════════════════ */
function openDrawer() { if ($('drawer')) $('drawer').hidden = false; haptic(30); }
function closeDrawer() { if ($('drawer')) $('drawer').hidden = true; }

if ($('menuBtn')) $('menuBtn').onclick = openDrawer;
if ($('drawerClose')) $('drawerClose').onclick = closeDrawer;
if ($('drawerBackdrop')) $('drawerBackdrop').onclick = closeDrawer;

if ($('navMood')) $('navMood').onclick = () => { closeDrawer(); openMood(); };
if ($('navBreath')) $('navBreath').onclick = () => { closeDrawer(); if ($('breathPickerOverlay')) $('breathPickerOverlay').hidden = false; };
if ($('navJournal')) $('navJournal').onclick = () => { closeDrawer(); openJournal(); };
if ($('navBedside')) $('navBedside').onclick = () => { closeDrawer(); openBedside(); };
if ($('navHelp')) $('navHelp').onclick = () => { closeDrawer(); openHelp(); };
if ($('navAbout')) $('navAbout').onclick = () => { closeDrawer(); if ($('aboutOverlay')) $('aboutOverlay').hidden = false; };

/* ═══════════════════════════════════════════════════════════════════════════
   VOICE CATALOG & PACE CONTROLS
   ═══════════════════════════════════════════════════════════════════════════ */
async function loadVoiceCatalog() {
    try {
        const r = await fetch('/api/voices');
        if (!r.ok) return;
        const d = await r.json();
        const sel = $('voiceSelect');
        if (!sel) return;
        sel.innerHTML = '';
        (d.voices || []).forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = `${v.name} · ${v.persona}`;
            if (v.id === S.chosenVoice) opt.selected = true;
            sel.appendChild(opt);
        });
    } catch {}
}

if ($('voiceSelect')) {
    $('voiceSelect').onchange = (e) => {
        S.chosenVoice = e.target.value;
        store.set('chosenVoice', S.chosenVoice);
        voiceGW.sendInit();
    };
}

if ($('voiceSpeed')) {
    $('voiceSpeed').oninput = (e) => {
        const val = parseFloat(e.target.value);
        S.chosenSpeed = val;
        store.set('chosenSpeed', val);
        const label = val <= 0.9 ? 'Gentle & Deliberate' : val >= 1.1 ? 'Energetic' : 'Natural';
        if ($('voiceSpeedVal')) $('voiceSpeedVal').textContent = `${val.toFixed(2)}x (${label})`;
        voiceGW.sendInit();
    };
}

if ($('voicePreviewBtn')) {
    $('voicePreviewBtn').onclick = async () => {
        speaker.reset();
        haptic(30);
        const hi = S.lang.startsWith('hi') || S.lang === 'auto';
        const previewText = hi
            ? 'नमस्ते, मैं सहारा हूँ। आपके हर सुख-दुख में आपके साथ।'
            : 'Hello, I am Sahaara. I am here with you, whatever you are going through.';
        const pLang = hi ? 'hi-IN' : 'en-IN';
        speaker.say(previewText, pLang);
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   PROMINENT STOP BUTTON CONTROLLER
   ═══════════════════════════════════════════════════════════════════════════ */
function updateStopButton() {
    const stopBtn = $('stopVoiceBtn');
    if (!stopBtn) return;
    const active = speaker.playing || rec.on;
    stopBtn.hidden = !active;
}

function stopAllVoice() {
    speaker.reset();
    if (rec.on) stopRec(false);
    S.handsfree = false;
    applySettings();
    updateVoiceUIState('idle');
    updateStopButton();
    voiceGW.bargeIn();
    haptic(30);
}

if ($('stopVoiceBtn')) $('stopVoiceBtn').onclick = stopAllVoice;
if ($('bedsideStopBtn')) $('bedsideStopBtn').onclick = stopAllVoice;

/* ═══════════════════════════════════════════════════════════════════════════
   SPEECH OUTPUT: High-Fidelity Gnani Timbre v3.0 Pipelined Playback
   (Zero-robotics, pure neural voice synthesis with automatic queueing)
   ═══════════════════════════════════════════════════════════════════════════ */
function cleanForTTS(text) {
    if (!text) return '';
    return text
        .replace(/[*_~#`]+/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/[,]{2,}/g, ', ')
        .replace(/[.]{2,}/g, '. ')
        .replace(/[-]{2,}/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

const playUrl = (url) => new Promise((resolve) => {
    try {
        const a = new Audio(url);
        speaker.audio = a;
        a.onended = () => {
            URL.revokeObjectURL(url);
            if (speaker.audio === a) speaker.audio = null;
            resolve(true);
        };
        a.onerror = () => {
            URL.revokeObjectURL(url);
            if (speaker.audio === a) speaker.audio = null;
            resolve(false);
        };
        const p = a.play();
        if (p !== undefined) {
            p.catch(() => {
                URL.revokeObjectURL(url);
                if (speaker.audio === a) speaker.audio = null;
                resolve(false);
            });
        }
    } catch {
        resolve(false);
    }
});

const speaker = {
    q: [], playing: false, token: 0, audio: null, firstAt: 0,

    fetch(text, lang) {
        return fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                language: lang,
                voice: S.chosenVoice,
                speed: S.chosenSpeed
            })
        })
        .then(r => r.ok ? r.blob() : Promise.reject(new Error('tts_fail')))
        .then(b => URL.createObjectURL(b))
        .catch((err) => {
            if (DEBUG) console.warn('Gnani TTS fetch error:', err);
            return null;
        });
    },

    say(text, lang) {
        text = cleanForTTS(text);
        // Ignore pure punctuation, stray commas, or empty strings
        if (!text || /^[\s.,!?;:\-_।॥'"`]+$/.test(text)) return;
        if (!S.voice) return;
        this.q.push({ text, lang, p: this.fetch(text, lang) });
        this.pump();
    },

    async pump() {
        if (this.playing) return;
        this.playing = true;
        const tok = this.token;
        updateVoiceUIState('speaking');
        updateStopButton();

        while (this.q.length && tok === this.token) {
            const it = this.q.shift();
            if (tok !== this.token) break;
            if (this.firstAt === 0) { this.firstAt = performance.now(); onFirstAudio(); }

            if (it.p) {
                const url = await it.p;
                if (tok !== this.token) break;
                if (url) {
                    await playUrl(url);
                }
            } else if (it.url) {
                await playUrl(it.url);
            }
        }

        if (tok === this.token) {
            this.playing = false;
            this.audio = null;
            updateVoiceUIState(S.handsfree ? 'listening' : 'idle');
            updateStopButton();

            // If assistant finished generating all tokens and hands-free is active, schedule next listen
            if (!S.busy && S.handsfree) {
                scheduleNextHandsFreeTurn();
            }
        }
    },

    reset() {
        this.token++;
        this.q = [];
        this.playing = false;
        this.firstAt = 0;
        if (this.audio) {
            this.audio.pause();
            this.audio.currentTime = 0;
            this.audio = null;
        }
        updateVoiceUIState(S.handsfree ? 'listening' : 'idle');
        updateStopButton();
    },
};

let sendT0 = 0, lastTiming = null, timingEl = null;
function onFirstAudio() {
    haptic();
    if (DEBUG && timingEl) timingEl.textContent = fmtTiming(lastTiming, Math.round(performance.now() - sendT0));
}
const fmtTiming = (t, audio) =>
    [t && `retrieve ${t.retrieve_ms}ms`, t && t.ttft_ms != null && `first token ${t.ttft_ms}ms`,
     t && `total ${t.total_ms}ms`, audio && `first audio ${audio}ms`].filter(Boolean).join(' · ');

/* ═══════ Sentence Chunker (Early low threshold for fast spoken audio) ═══════ */
function makeChunker() {
    let buf = '', first = true;
    const take = () => {
        const out = [];
        for (;;) {
            let m = /^([\s\S]*?[.!?।\n])[""']?\s+/.exec(buf);
            if (!m && first && buf.length > 28) {
                m = /^([\s\S]*?[,;:])[""']?\s+/.exec(buf);
            }
            if (!m) break;
            let piece = m[1], used = m[0].length;
            if (piece.length < (first ? 10 : 35)) {
                const m2 = /^([\s\S]*?[.!?।\n])[""']?\s+([\s\S]*?[.!?।\n])[""']?\s+/.exec(buf);
                if (!m2) break;
                piece = `${m2[1]} ${m2[2]}`;
                used = m2[0].length;
            }
            const cleanPiece = piece.trim();
            // Discard pure punctuation
            if (cleanPiece && !/^[\s.,!?;:\-_।॥'"`]+$/.test(cleanPiece)) {
                out.push(cleanPiece);
            }
            buf = buf.slice(used);
            first = false;
        }
        return out;
    };
    return {
        push(t) { buf += t; return take(); },
        flush() {
            const r = buf.trim();
            buf = '';
            return (r && !/^[\s.,!?;:\-_।॥'"`]+$/.test(r)) ? [r] : [];
        }
    };
}

/* ═══════ Verse speech segments ═══════ */
function verseSegments(card, lang) {
    const hi = lang === 'hi-IN' || lang === 'mr-IN';
    const [ch, v] = (card.ref || '').split('.');
    const verse = (v || '').replace('–', ' to ');
    const segs = [[
        hi ? `भगवद्गीता, अध्याय ${ch}, श्लोक ${verse}।` : `From the Bhagavad Gita, chapter ${ch}, verse ${verse}.`,
        hi ? 'hi-IN' : 'en-IN'
    ]];
    if (card.devanagari) segs.push([card.devanagari.replace(/\n/g, '। '), 'hi-IN']);
    if ((lang === 'en-IN' || lang === 'hi-en') && card.meaning_tts) segs.push([card.meaning_tts, 'en-IN']);
    return segs;
}
function speakVerse(card, lang) {
    for (const [t, l] of verseSegments(card, lang)) speaker.say(t, l);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SOURCE CARDS & GITA WISDOM ATTRIBUTION (Non-intrusive collapsible info)
   ═══════════════════════════════════════════════════════════════════════════ */
function renderWisdomInfo(sources, cited) {
    const wrap = h('div', { class: 'wisdom-info-wrap' });
    const shown = sources.filter(c => !c.hidden);

    const shlokas = shown.filter(c => c.type === 'shloka');
    const targetShlokas = (cited && cited.length ? shlokas.filter(c => cited.includes(c.n)) : [])
        .concat(cited && cited.length ? [] : shlokas.slice(0, 1)).slice(0, 1);

    if (targetShlokas.length > 0) {
        const s = targetShlokas[0];
        const details = h('div', { class: 'shloka-info-details', hidden: true });

        if (s.devanagari) {
            details.append(h('div', { class: 'shloka-sk', lang: 'sa' }, s.devanagari));
        }
        if (s.meaning) {
            details.append(h('p', { class: 'shloka-trans' }, s.meaning));
        }

        const listenBtn = h('button', {
            class: 'pill-btn outline sm',
            onclick: (e) => {
                e.stopPropagation();
                speaker.reset();
                speakVerse(s, S.replyLang);
            }
        }, h('i', { class: 'fas fa-volume-up' }), ' Listen to Sanskrit Shloka');

        details.append(listenBtn);

        const toggleBtn = h('button', {
            class: 'shloka-badge-btn',
            title: 'Click to view Shloka information',
            onclick: () => {
                const isHidden = details.hidden;
                details.hidden = !isHidden;
                toggleBtn.classList.toggle('open', !isHidden);
            }
        },
            h('span', { class: 'om-symbol' }, 'ॐ'),
            h('span', { class: 'shloka-ref-text' }, `Wisdom source: ${s.title || 'Bhagavad Gita'}${s.chapter_title ? ' · ' + s.chapter_title : ''}`),
            h('i', { class: 'fas fa-chevron-down toggle-icon' })
        );

        wrap.append(h('div', { class: 'shloka-badge-card' }, toggleBtn, details));
    }

    const books = shown.filter(c => c.type === 'book' || (c.source && (c.source.includes('Vivekananda') || c.source.includes('Frankl') || c.source.includes('WHO'))));
    if (books.length > 0) {
        const b = books[0];
        const bDetails = h('div', { class: 'shloka-info-details', hidden: true });
        if (b.text) {
            bDetails.append(h('p', { class: 'shloka-trans' }, b.text));
        }
        const bToggleBtn = h('button', {
            class: 'shloka-badge-btn',
            title: 'Click to view source excerpt',
            onclick: () => {
                const isHidden = bDetails.hidden;
                bDetails.hidden = !isHidden;
                bToggleBtn.classList.toggle('open', !isHidden);
            }
        },
            h('i', { class: 'fas fa-book-bookmark', style: 'color: var(--gold); margin-right: 8px;' }),
            h('span', { class: 'shloka-ref-text' }, `${b.source}${b.ref ? ' · ' + b.ref : ''}`),
            h('i', { class: 'fas fa-chevron-down toggle-icon' })
        );
        wrap.append(h('div', { class: 'shloka-badge-card' }, bToggleBtn, bDetails));
    }

    const practice = shown.find(c => (c.type === 'practice' || c.type === 'tool') && c.breath);
    if (practice) {
        const breathBtn = h('button', {
            class: 'practice-chip-btn',
            onclick: () => startBreath(practice.breath)
        }, h('i', { class: 'fas fa-wind' }), ` Breathe with Sahaara: ${practice.title}`);
        wrap.append(breathBtn);
    }

    return wrap;
}

/* ═══════════════════════════════════════════════════════════════════════════
   FULL-DUPLEX WEBSOCKET VOICE GATEWAY
   ═══════════════════════════════════════════════════════════════════════════ */
function updateVoiceUIState(state, info) {
    const s = (state || 'idle').toLowerCase();
    visualizer.setState(s);
    const mic = $('micBtn');
    const bedsideOrb = $('bedsideOrb');
    const bedsideStatus = $('bedsideStatus');

    if (mic) {
        mic.classList.remove('listening', 'hearing', 'thinking', 'speaking');
        if (s !== 'idle') mic.classList.add(s);
    }
    if (bedsideOrb) bedsideOrb.className = `bedside-orb ${s}`;

    if (s === 'listening') {
        setStatus(S.isBedsideMode ? 'Listening… (speak freely)' : 'Listening…');
        if (bedsideStatus) bedsideStatus.textContent = 'Sahaara is listening…';
        playChime('listening');
    } else if (s === 'hearing') {
        setStatus('Hearing you…');
        if (bedsideStatus) bedsideStatus.textContent = info ? `Hearing: "${info}"` : 'Hearing you…';
    } else if (s === 'thinking') {
        setStatus('Reflecting with Gita…');
        if (bedsideStatus) bedsideStatus.textContent = 'Reflecting with Gita…';
        playChime('thinking');
    } else if (s === 'speaking') {
        setStatus('Speaking…');
        if (bedsideStatus) bedsideStatus.textContent = 'Speaking…';
        playChime('speaking');
    } else {
        setStatus(IDLE);
        if (bedsideStatus) bedsideStatus.textContent = 'Tap to speak with Sahaara';
    }
}

const voiceGW = {
    ws: null,
    connected: false,
    reconnectTimer: null,

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/api/voice`;

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                this.connected = true;
                if (DEBUG) console.log('Voice Gateway WS connected');
                this.sendInit();
            };

            this.ws.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    if (msg.event === 'barge_in_ack') {
                        updateVoiceUIState(S.isBedsideMode && S.handsfree ? 'listening' : 'idle');
                    }
                } catch {}
            };

            this.ws.onclose = () => {
                this.connected = false;
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = setTimeout(() => this.connect(), 3500);
            };

            this.ws.onerror = () => {
                this.connected = false;
            };
        } catch {
            this.connected = false;
        }
    },

    sendInit() {
        if (!this.connected || !this.ws) return;
        this.ws.send(JSON.stringify({
            type: 'init',
            voice: S.chosenVoice || 'Chetana',
            speed: S.chosenSpeed || 1.0,
            lang: S.lang,
            handsfree: S.handsfree
        }));
    },

    bargeIn() {
        if (!this.connected || !this.ws) return;
        this.ws.send(JSON.stringify({ type: 'barge_in' }));
    }
};

/* ═══════════════════════════════════════════════════════════════════════════
   CONTINUOUS HANDS-FREE CONVERSATION COORDINATOR
   ═══════════════════════════════════════════════════════════════════════════ */
function waitForSpeechEnd() {
    return new Promise(resolve => {
        const check = () => {
            // Must have completed LLM streaming (!S.busy),
            // finished playing current audio (!speaker.playing),
            // and have empty audio queue (speaker.q.length === 0)
            if (!S.busy && !speaker.playing && speaker.q.length === 0) {
                resolve();
            } else {
                setTimeout(check, 100);
            }
        };
        setTimeout(check, 150);
    });
}

let handsfreeTurnTimer = null;
function scheduleNextHandsFreeTurn() {
    if (!S.handsfree) return;
    clearTimeout(handsfreeTurnTimer);
    waitForSpeechEnd().then(() => {
        if (!S.handsfree || rec.on || S.busy || speaker.playing || speaker.q.length > 0) return;
        // 450ms acoustic silence guard: room reverb dampening before opening mic
        handsfreeTurnTimer = setTimeout(() => {
            if (S.handsfree && !rec.on && !S.busy && !speaker.playing && speaker.q.length === 0) {
                startRec();
            }
        }, 450);
    });
}

/* ═══════════════════════════════════════════════════════════════════════════
   INSTANT BARGE-IN & CANCELLATION (<50ms)
   ═══════════════════════════════════════════════════════════════════════════ */
function interrupt() {
    if (speaker.playing || S.busy) {
        speaker.reset();
        voiceGW.bargeIn();
        playChime('barge');
        haptic(30);
        updateVoiceUIState(S.handsfree ? 'listening' : 'idle');
        updateStopButton();
        return true;
    }
    return false;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHAT — Fast HTTP Streaming with Sentence-Pipelined TTS
   ═══════════════════════════════════════════════════════════════════════════ */
function addUser(text) {
    const wc = $('welcomeCard');
    if (wc) wc.style.display = 'none';
    const ch = $('chips');
    if (ch) ch.style.display = 'none';

    if (chatBox) chatBox.append(h('div', { class: 'message user-message' }, text));
    scrollDown();
}

function addBot() {
    const bubble = h('div', { class: 'message bot-message' },
        h('div', { class: 'typing-indicator' },
            h('span', { class: 'typing-dot' }),
            h('span', { class: 'typing-dot' }),
            h('span', { class: 'typing-dot' })));
    const cards = h('div', { class: 'cards-wrap' });
    const timing = h('div', { class: 'timing' });
    if (chatBox) chatBox.append(h('div', { class: 'bot-wrap' }, bubble, cards, timing));
    scrollDown();
    return { bubble, cards, timing };
}

function showCrisis(helplines) {
    if (!$('crisis')) return;
    $('crisis').replaceChildren(
        h('b', {}, '❤️ You are not alone. '),
        ...helplines.flatMap(x => [
            `${x.name}: `,
            h('a', { href: `tel:${x.number}` }, x.number),
            '  '
        ])
    );
    $('crisis').hidden = false;
}

async function send(text, sttLang) {
    text = (text || '').trim();
    // Discard empty or punctuation-only messages
    if (!text || /^[\s.,!?;:\-_।॥'"`]+$/.test(text) || S.busy) return;

    S.busy = true;
    speaker.reset();
    updateStopButton();
    sendT0 = performance.now();
    addUser(text);
    if ($('textInput')) $('textInput').value = '';
    if ($('sendBtn')) $('sendBtn').disabled = true;

    const { bubble, cards, timing } = addBot();
    timingEl = timing;
    lastTiming = null;

    const chunker = makeChunker();
    let acc = '', sources = [], doneEvt = null, first = true, lang = S.replyLang;

    setStatus('Sahaara is thinking…');

    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: S.history.slice(-10),
                language: S.lang,
                stt_language: sttLang || null
            })
        });

        if (!r.ok) throw new Error(r.status === 429 ? 'rate' : 'http');

        const reader = r.body.getReader();
        const dec = new TextDecoder();
        let buf = '';

        for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });

            let i;
            while ((i = buf.indexOf('\n\n')) !== -1) {
                const raw = buf.slice(0, i);
                buf = buf.slice(i + 2);
                const ev = /^event: (.+)$/m.exec(raw)?.[1];
                const dm = /^data: (.+)$/m.exec(raw);
                if (!ev || !dm) continue;
                const d = JSON.parse(dm[1]);

                if (ev === 'meta') {
                    lang = S.replyLang = d.lang;
                    if (d.helplines) showCrisis(d.helplines);
                    if (d.provider === 'extractive') setStatus('Offline mode');
                }
                else if (ev === 'sources') {
                    sources = d.sources;
                }
                else if (ev === 'token') {
                    if (first) { bubble.textContent = ''; first = false; }
                    acc += d.t;
                    bubble.textContent = acc;
                    scrollDown();
                    updateBedsideTranscript(acc);
                    for (const s of chunker.push(d.t)) {
                        speaker.say(s, lang);
                    }
                }
                else if (ev === 'done') doneEvt = d;
            }
        }
    } catch (e) {
        bubble.textContent = e.message === 'rate'
            ? 'Please give me a moment and try again.'
            : 'I could not reach the server. Please check your connection and try again. If you need someone now, call 14416.';
        S.busy = false;
        setStatus();
        updateStopButton();
        return;
    }

    for (const s of chunker.flush()) {
        speaker.say(s, lang);
    }

    const final = doneEvt?.text ?? acc;
    bubble.textContent = final;
    lastTiming = doneEvt?.timing || null;

    if (!doneEvt?.crisis && sources.length > 0) {
        cards.append(renderWisdomInfo(sources, doneEvt?.cited || []));
    }

    if (DEBUG) timing.textContent = fmtTiming(lastTiming, speaker.firstAt ? Math.round(speaker.firstAt - sendT0) : 0);

    S.history.push({ role: 'user', content: text }, { role: 'assistant', content: final });
    S.busy = false;
    scrollDown();
    updateStopButton();

    if (S.handsfree) {
        scheduleNextHandsFreeTurn();
    }
}

if ($('form')) {
    $('form').onsubmit = (e) => {
        e.preventDefault();
        send($('textInput').value);
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   SPEECH INPUT: 16kHz WAV, Silence auto-stop, Gnani Prisma STT
   ═══════════════════════════════════════════════════════════════════════════ */
const rec = {
    ctx: null, stream: null, proc: null, chunks: [],
    on: false, silentFor: 0, heard: false, t0: 0, lastVoiced: -1
};

function encodeWav(f32, rate) {
    const buf = new ArrayBuffer(44 + f32.length * 2);
    const v = new DataView(buf);
    const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
    w(0, 'RIFF'); v.setUint32(4, 36 + f32.length * 2, true); w(8, 'WAVEfmt ');
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true);
    v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, f32.length * 2, true);
    for (let i = 0; i < f32.length; i++) {
        const s = Math.max(-1, Math.min(1, f32[i]));
        v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([buf], { type: 'audio/wav' });
}

function downsample(d, from, to) {
    if (from === to) return d;
    const ratio = from / to;
    const out = new Float32Array(Math.floor(d.length / ratio));
    for (let i = 0; i < out.length; i++) {
        const a = Math.floor(i * ratio);
        const b = Math.max(a + 1, Math.floor((i + 1) * ratio));
        let s = 0;
        for (let j = a; j < b; j++) s += d[j];
        out[i] = s / (b - a);
    }
    return out;
}

function isEchoOfLastAssistantMessage(transcript) {
    if (!S.history || S.history.length === 0) return false;
    const lastMsg = S.history[S.history.length - 1];
    if (!lastMsg || lastMsg.role !== 'assistant' || !lastMsg.content) return false;
    const cleanLast = lastMsg.content.toLowerCase().replace(/[^\p{L}\s]/gu, '').trim();
    const cleanInput = transcript.toLowerCase().replace(/[^\p{L}\s]/gu, '').trim();
    if (!cleanInput || !cleanLast) return false;
    if (cleanInput.length >= 6 && cleanLast.includes(cleanInput)) return true;
    const inWords = cleanInput.split(/\s+/).filter(w => w.length > 2);
    if (inWords.length >= 2) {
        const matches = inWords.filter(w => cleanLast.includes(w)).length;
        if (matches / inWords.length >= 0.7) return true;
    }
    return false;
}

async function startRec() {
    if (S.busy || rec.on) return;
    if (speaker.playing) {
        if (S.isBedsideMode) {
            interrupt();
        } else {
            return;
        }
    }

    haptic(40);

    try {
        rec.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                channelCount: 1
            }
        });
        visualizer.connectMic(rec.stream);
    } catch {
        setStatus('Allow the microphone, or type');
        return;
    }

    rec.ctx = new (window.AudioContext || window.webkitAudioContext)();
    const src = rec.ctx.createMediaStreamSource(rec.stream);
    rec.proc = rec.ctx.createScriptProcessor(2048, 1, 1);
    Object.assign(rec, { chunks: [], silentFor: 0, heard: false, t0: Date.now(), on: true, lastVoiced: -1 });

    updateStopButton();

    rec.proc.onaudioprocess = (e) => {
        const d = new Float32Array(e.inputBuffer.getChannelData(0));
        rec.chunks.push(d);
        let sum = 0;
        for (let i = 0; i < d.length; i++) sum += d[i] * d[i];
        const rms = Math.sqrt(sum / d.length);
        const dt = d.length / rec.ctx.sampleRate;

        // Barge-in check ONLY in Bedside / Voice Sanctuary Mode
        if (S.isBedsideMode && speaker.playing && rms > 0.04) {
            interrupt();
        }

        if (rms > 0.015) {
            rec.heard = true;
            rec.silentFor = 0;
            rec.lastVoiced = rec.chunks.length - 1;
            updateVoiceUIState('hearing');
        } else if (rec.heard) {
            rec.silentFor += dt;
        }

        // 0.7s silence cutoff (ultra-responsive turn-taking)
        if (rec.silentFor > 0.7 || Date.now() - rec.t0 > 25000) stopRec(true);
    };

    // CRITICAL: Mute microphone loopback to speakers.
    // ScriptProcessor needs to connect to destination to pump buffers,
    // but muteGain zeroing amplitude ensures ZERO mic sound is ever heard from speakers!
    const muteGain = rec.ctx.createGain();
    muteGain.gain.value = 0;
    src.connect(rec.proc);
    rec.proc.connect(muteGain);
    muteGain.connect(rec.ctx.destination);
    updateVoiceUIState('listening');
}

async function stopRec(submit) {
    if (!rec.on) return;
    rec.on = false;
    visualizer.disconnectMic();
    updateStopButton();
    const rate = rec.ctx.sampleRate;
    rec.proc.disconnect();
    rec.stream.getTracks().forEach(t => t.stop());
    await rec.ctx.close();

    if (!submit || !rec.heard) {
        if (S.handsfree) {
            updateVoiceUIState('listening');
            setTimeout(() => { if (S.handsfree && !rec.on && !S.busy && !speaker.playing) startRec(); }, 600);
        } else {
            updateVoiceUIState('idle');
        }
        return;
    }

    const keep = rec.chunks.slice(0, rec.lastVoiced + 4);
    const n = keep.reduce((a, c) => a + c.length, 0);
    const all = new Float32Array(n);
    let o = 0;
    for (const c of keep) { all.set(c, o); o += c.length; }

    updateVoiceUIState('thinking');
    const t0 = performance.now();

    try {
        const wavBlob = encodeWav(downsample(all, rate, 16000), 16000);
        const fd = new FormData();
        fd.append('audio', wavBlob, 'speech.wav');
        fd.append('language', S.lang === 'auto' ? 'indic-auto' : S.lang.replace('hi-en', 'hi-IN'));

        const r = await fetch('/api/stt', { method: 'POST', body: fd });
        const j = await r.json();

        // Punctuation and noise validation: discard stray commas or periods
        const cleanTranscript = (j.transcript || '').trim();
        if (!r.ok || !cleanTranscript || cleanTranscript.length < 2 || /^[\s.,!?;:\-_।॥'"`]+$/.test(cleanTranscript)) {
            throw new Error('empty_or_punct');
        }

        // Echo protection: discard transcripts that echo the assistant's previous message
        if (isEchoOfLastAssistantMessage(cleanTranscript)) {
            if (DEBUG) console.warn('Discarded self-echo transcript:', cleanTranscript);
            throw new Error('echo_detected');
        }

        if (DEBUG) console.log('STT latency:', Math.round(performance.now() - t0), 'ms', cleanTranscript);
        send(cleanTranscript, j.language);
    } catch (e) {
        setStatus(e.message === 'empty_or_punct' || e.message === 'echo_detected' ? '' : 'Could not hear clearly. Try again or type.');
        if (S.handsfree) {
            updateVoiceUIState('listening');
            setTimeout(() => { if (S.handsfree && !rec.on && !S.busy && !speaker.playing) startRec(); }, 900);
        } else {
            updateVoiceUIState('idle');
        }
    }
}

if ($('micBtn')) {
    $('micBtn').onclick = () => {
        if (speaker.playing) {
            speaker.reset();
            updateStopButton();
        } else if (rec.on) {
            stopRec(true);
        } else {
            // Push-to-talk single turn in basic text chat
            S.handsfree = false;
            applySettings();
            startRec();
        }
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   HANDS-FREE CONTINUOUS MODE TOGGLE (Bedside & Dedicated Controls)
   ═══════════════════════════════════════════════════════════════════════════ */
function toggleHandsFree(forceState) {
    S.handsfree = forceState !== undefined ? forceState : !S.handsfree;
    applySettings();
    haptic(40);

    if (S.handsfree) {
        requestWakeLock();
        if (!rec.on && !S.busy && !speaker.playing) {
            startRec();
        }
    } else {
        releaseWakeLock();
        clearTimeout(handsfreeTurnTimer);
        if (rec.on) stopRec(false);
        updateVoiceUIState('idle');
    }
}

if ($('handsfreeBtn')) $('handsfreeBtn').onclick = () => toggleHandsFree();
if ($('bedsideHandsfreeBtn')) $('bedsideHandsfreeBtn').onclick = () => toggleHandsFree();

/* ═══════════════════════════════════════════════════════════════════════════
   EYES-FREE / BEDSIDE SANCTUARY MODE (Dedicated Voice-Only Chat)
   ═══════════════════════════════════════════════════════════════════════════ */
let bedsideClockTimer = null;
function updateBedsideClock() {
    const now = new Date();
    if ($('bedsideClock')) {
        $('bedsideClock').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

function openBedside() {
    if (!$('bedsideOverlay')) return;
    S.isBedsideMode = true;
    $('bedsideOverlay').hidden = false;
    requestWakeLock();
    updateBedsideClock();
    clearInterval(bedsideClockTimer);
    bedsideClockTimer = setInterval(updateBedsideClock, 1000);
    toggleHandsFree(true);
    haptic(40);
}

function closeBedside() {
    if (!$('bedsideOverlay')) return;
    S.isBedsideMode = false;
    $('bedsideOverlay').hidden = true;
    releaseWakeLock();
    clearInterval(bedsideClockTimer);
    toggleHandsFree(false);
    stopAllVoice();
}

function updateBedsideTranscript(text) {
    const el = $('bedsideTranscript');
    if (el) el.textContent = `“${text}”`;
}

if ($('bedsideBtn')) $('bedsideBtn').onclick = openBedside;
if ($('bedsideClose')) $('bedsideClose').onclick = closeBedside;

if ($('bedsideTouchZone')) {
    $('bedsideTouchZone').onclick = () => {
        if (speaker.playing || S.busy) {
            interrupt();
        } else if (rec.on) {
            stopRec(true);
        } else {
            startRec();
        }
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   GUIDED BREATHING
   ═══════════════════════════════════════════════════════════════════════════ */
let breathRun = 0;

document.querySelectorAll('.breath-option').forEach(btn => {
    btn.onclick = () => {
        if ($('breathPickerOverlay')) $('breathPickerOverlay').hidden = true;
        startBreath(btn.dataset.pattern);
    };
});
if ($('breathPickerClose')) $('breathPickerClose').onclick = () => { if ($('breathPickerOverlay')) $('breathPickerOverlay').hidden = true; };

async function startBreath(key) {
    try {
        const res = await fetch(`/api/breathe/${key}?language=${S.replyLang}`);
        if (!res.ok) throw new Error('Failed to load pattern');
        const p = await res.json();
        const run = ++breathRun;
        const orb = $('orb');

        speaker.reset();
        if ($('bTitle')) $('bTitle').textContent = p.name;
        if ($('breathOverlay')) $('breathOverlay').hidden = false;
        if ($('bCue')) $('bCue').textContent = p.start;
        speaker.say(p.start, S.replyLang);
        await sleep(3500);

        for (let c = 0; c < p.cycles && run === breathRun; c++) {
            for (const ph of p.phases) {
                if (run !== breathRun) break;
                if ($('bCue')) $('bCue').textContent = ph.cue;
                if (orb) {
                    orb.style.transitionDuration = `${ph.seconds}s`;
                    orb.style.transform = ph.kind === 'in' ? 'scale(1.15)' :
                                          ph.kind === 'hold' ? orb.style.transform : 'scale(0.6)';
                }
                for (let s = ph.seconds; s > 0 && run === breathRun; s--) {
                    if ($('bCount')) $('bCount').textContent = s;
                    await sleep(1000);
                }
            }
        }

        if (run === breathRun) {
            if ($('bCue')) $('bCue').textContent = p.done;
            if ($('bCount')) $('bCount').textContent = '';
            speaker.say(p.done, S.replyLang);
        }
    } catch (err) {
        if (DEBUG) console.warn('Breathing guide error:', err);
        setStatus('Could not start breathing exercise. Please try again.');
    }
}

if ($('bStop')) {
    $('bStop').onclick = () => {
        breathRun++;
        if ($('breathOverlay')) $('breathOverlay').hidden = true;
        speaker.reset();
        if ($('orb')) $('orb').style.transform = 'scale(0.6)';
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   MOOD JOURNAL (Device only)
   ═══════════════════════════════════════════════════════════════════════════ */
const MOODS = ['😞', '😟', '😐', '🙂', '😊'];

function openMood() {
    renderMood();
    if ($('moodOverlay')) $('moodOverlay').hidden = false;
}

function renderMood() {
    if ($('moodPick')) {
        $('moodPick').replaceChildren(...MOODS.map((m, i) =>
            h('button', {
                'aria-label': `Mood ${i + 1} of 5`,
                onclick: () => {
                    haptic(40);
                    const log = store.get('moods', []);
                    log.push({ d: new Date().toISOString(), v: i });
                    store.set('moods', log.slice(-60));
                    renderMood();
                }
            }, m)
        ));
    }

    const bars = store.get('moods', []).slice(-7);
    if ($('moodBars')) {
        $('moodBars').replaceChildren(...bars.map(e =>
            h('div', {
                style: `height:${24 + e.v * 20}px`,
                title: new Date(e.d).toLocaleDateString()
            }, MOODS[e.v])
        ));
    }
}

if ($('moodClose')) $('moodClose').onclick = () => { if ($('moodOverlay')) $('moodOverlay').hidden = true; };

/* ═══════════════════════════════════════════════════════════════════════════
   HELPLINES
   ═══════════════════════════════════════════════════════════════════════════ */
async function openHelp() {
    let items = [
        { name: 'Tele-MANAS', number: '14416', note: 'Free 24x7 mental health helpline' },
        { name: 'Emergency', number: '112', note: 'National emergency helpline' }
    ];
    try {
        items = (await (await fetch('/api/helplines')).json()).helplines;
    } catch {}

    if ($('helpList')) {
        $('helpList').replaceChildren(...items.map(x =>
            h('div', { class: 'hl-item' },
                h('div', {},
                    h('b', {}, x.name),
                    h('div', { class: 'hl-note' }, x.note || '')),
                h('a', { class: 'hl-call', href: `tel:${x.number}` }, `Call ${x.number}`))
        ));
    }
    if ($('helpOverlay')) $('helpOverlay').hidden = false;
}

if ($('helpBtnHeader')) $('helpBtnHeader').onclick = openHelp;
if ($('helpClose')) $('helpClose').onclick = () => { if ($('helpOverlay')) $('helpOverlay').hidden = true; };
if ($('aboutClose')) $('aboutClose').onclick = () => { if ($('aboutOverlay')) $('aboutOverlay').hidden = true; };

/* ═══════════════════════════════════════════════════════════════════════════
   PRIVATE JOURNAL (Device only)
   ═══════════════════════════════════════════════════════════════════════════ */
function openJournal() {
    renderJournal();
    if ($('journalOverlay')) $('journalOverlay').hidden = false;
}

function renderJournal() {
    const entries = store.get('journal', []).slice(-20).reverse();
    if ($('journalEntries')) {
        $('journalEntries').replaceChildren(...entries.map(e =>
            h('div', { class: 'journal-entry' },
                h('div', { class: 'journal-entry-date' }, new Date(e.d).toLocaleString()),
                e.t)
        ));
    }
}

if ($('journalSave')) {
    $('journalSave').onclick = () => {
        const text = $('journalText').value.trim();
        if (!text) return;
        haptic(30);
        const entries = store.get('journal', []);
        entries.push({ d: new Date().toISOString(), t: text });
        store.set('journal', entries.slice(-100));
        $('journalText').value = '';
        renderJournal();
    };
}
if ($('journalClose')) $('journalClose').onclick = () => { if ($('journalOverlay')) $('journalOverlay').hidden = true; };

/* ═══════════════════════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
   ═══════════════════════════════════════════════════════════════════════════ */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        stopAllVoice();
        if ($('helpOverlay')) $('helpOverlay').hidden = true;
        if ($('moodOverlay')) $('moodOverlay').hidden = true;
        if ($('aboutOverlay')) $('aboutOverlay').hidden = true;
        if ($('journalOverlay')) $('journalOverlay').hidden = true;
        if ($('breathPickerOverlay')) $('breathPickerOverlay').hidden = true;
        if ($('bedsideOverlay') && !$('bedsideOverlay').hidden) closeBedside();
        if ($('breathOverlay') && !$('breathOverlay').hidden && $('bStop')) $('bStop').click();
        closeDrawer();
    }
});

/* ═══════════════════════════════════════════════════════════════════════════
   WELCOME & INITIALIZATION
   ═══════════════════════════════════════════════════════════════════════════ */
async function loadWelcome() {
    const lang = S.lang === 'auto' ? (navigator.language || 'en-IN') : S.lang;
    const hi = lang.startsWith('hi');

    try {
        const sg = await (await fetch(`/api/suggestions?language=${hi ? 'hi-IN' : 'en-IN'}`)).json();
        if ($('chips')) {
            $('chips').replaceChildren(...sg.suggestions.map(t =>
                h('button', { class: 'chip', onclick: () => send(t) }, t)
            ));
        }

        const v = await (await fetch(`/api/verse/daily?language=${hi ? 'hi-IN' : 'en-IN'}`)).json();
        if ($('votdVerse') && v.devanagari) $('votdVerse').textContent = v.devanagari;
        if ($('votdMeaning')) $('votdMeaning').textContent = v.meaning;
        if ($('votdListen')) {
            $('votdListen').onclick = () => {
                speaker.reset();
                S.voice = true;
                applySettings();
                speakVerse(v, hi ? 'hi-IN' : 'en-IN');
            };
        }
        if ($('votd')) $('votd').hidden = false;
    } catch {
        const defaults = hi
            ? ['मुझे चिंता हो रही है', 'मैं बहुत अकेला हूँ', 'नींद नहीं आती']
            : ['I feel anxious', 'I feel very lonely', 'I can\'t sleep at night'];
        if ($('chips')) {
            $('chips').replaceChildren(...defaults.map(t =>
                h('button', { class: 'chip', onclick: () => send(t) }, t)
            ));
        }
    }
}

// Boot
applySettings();
loadVoiceCatalog();
loadWelcome();
voiceGW.connect();
visualizer.init();

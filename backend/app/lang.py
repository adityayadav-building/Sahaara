"""Language handling: script/Hinglish detection, prompt instructions, TTS voice map.

Language codes follow Gnani's: hi-IN, en-IN, hi-en (Hinglish), ta-IN, te-IN,
kn-IN, ml-IN, mr-IN, pa-IN, bn-IN, gu-IN.
"""
from __future__ import annotations

import re

LANGUAGES = {
    "hi-IN": "Hindi",
    "en-IN": "English",
    "hi-en": "Hinglish",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "pa-IN": "Punjabi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
}

# Legacy values used by the first version of the dropdown.
_LEGACY = {
    "hindi": "hi-IN", "english": "en-IN", "hinglish": "hi-en", "tamil": "ta-IN",
    "bengali": "bn-IN", "punjabi": "pa-IN", "gujarati": "gu-IN", "telugu": "te-IN",
    "kannada": "kn-IN", "malayalam": "ml-IN", "marathi": "mr-IN",
    "hi": "hi-IN", "en": "en-IN",
}

_SCRIPT_RANGES = {
    "hi-IN": (0x0900, 0x097F),  # Devanagari (Marathi handled separately)
    "bn-IN": (0x0980, 0x09FF),
    "pa-IN": (0x0A00, 0x0A7F),
    "gu-IN": (0x0A80, 0x0AFF),
    "ta-IN": (0x0B80, 0x0BFF),
    "te-IN": (0x0C00, 0x0C7F),
    "kn-IN": (0x0C80, 0x0CFF),
    "ml-IN": (0x0D00, 0x0D7F),
}

_MARATHI_MARKERS = ("आहे", "काय", "मला", "नाही", "तुम्ही", "माझ", "आणि")

# Romanised Hindi function words that rarely occur in English text.
_HINGLISH_MARKERS = {
    "hai", "hain", "nahi", "nahin", "mujhe", "mera", "meri", "mere", "main", "mai", "kya", "kyun", "kyu",
    "bahut", "bohot", "bhot", "kuch", "kuchh", "aur", "yaar", "yar", "samajh", "mann", "man", "dil", "hoon",
    "hu", "tha", "thi", "raha", "rahi", "rahe", "karna", "karta", "karti", "kar", "lag", "lagta", "lagti",
    "toh", "to", "bhi", "se", "ko", "ka", "ki", "ke", "ab", "abhi", "jaise", "bas", "sab", "koi", "apna",
    "apni", "hum", "tum", "aap", "ghar", "dost", "thoda", "zindagi", "pareshan", "tension", "ghabrahat",
    "gussa", "udaas", "akela", "neend", "thak", "thaka", "chinta", "darr", "mujhko", "unhe", "unka",
}
# Words that are also common English and shouldn't count on their own.
_AMBIGUOUS = {"to", "man", "kar", "me", "hu", "so", "the", "do", "he", "ab"}

_TOKEN = re.compile(r"[A-Za-z']+")


def normalize_lang(value: str | None) -> str:
    """Map UI/legacy values to a supported code, or 'auto'."""
    if not value:
        return "auto"
    v = value.strip()
    if v.lower() == "auto":
        return "auto"
    if v in LANGUAGES:
        return v
    return _LEGACY.get(v.lower(), "auto")


def detect_language(text: str) -> str:
    """Best-effort language of a user utterance (script first, Hinglish by markers)."""
    counts: dict[str, int] = {}
    latin = 0
    for ch in text:
        cp = ord(ch)
        if ch.isascii() and ch.isalpha():
            latin += 1
            continue
        for code, (lo, hi) in _SCRIPT_RANGES.items():
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
    if counts:
        best = max(counts, key=counts.get)
        if counts[best] >= latin * 0.5 or counts[best] >= 3:
            if best == "hi-IN" and any(m in text for m in _MARATHI_MARKERS):
                return "mr-IN"
            return best
    if latin:
        words = [w.lower() for w in _TOKEN.findall(text)]
        if words:
            hits = [w for w in words if w in _HINGLISH_MARKERS]
            strong = [w for w in hits if w not in _AMBIGUOUS]
            if len(strong) >= 2 or (strong and len(hits) / len(words) >= 0.3):
                return "hi-en"
    return "en-IN"


def resolve_language(user_pref: str | None, stt_detected: str | None, text: str) -> str:
    """Reply language: explicit user choice > own detection (STT code is a tie-breaker)."""
    pref = normalize_lang(user_pref)
    if pref != "auto":
        return pref
    detected = detect_language(text)
    if detected == "en-IN" and stt_detected in LANGUAGES and stt_detected not in ("en-IN",):
        # Transcript was Latin script but the speech model heard an Indian language.
        return "hi-en" if stt_detected == "hi-IN" else stt_detected
    return detected


LANG_INSTRUCTION = {
    "hi-IN": "Reply ONLY in simple, everyday Hindi written in Devanagari. Avoid heavy Sanskritised or bookish words.",
    "hi-en": "Reply ONLY in Hinglish: simple Hindi written in English (Roman) letters, the way people text each other.",
    "en-IN": "Reply in simple, warm, plain English (Indian English is fine).",
    "mr-IN": "Reply ONLY in simple, spoken Marathi in Devanagari.",
    "ta-IN": "Reply ONLY in simple, spoken Tamil in Tamil script.",
    "te-IN": "Reply ONLY in simple, spoken Telugu in Telugu script.",
    "kn-IN": "Reply ONLY in simple, spoken Kannada in Kannada script.",
    "ml-IN": "Reply ONLY in simple, spoken Malayalam in Malayalam script.",
    "pa-IN": "Reply ONLY in simple, spoken Punjabi in Gurmukhi script.",
    "bn-IN": "Reply ONLY in simple, spoken Bengali in Bengali script.",
    "gu-IN": "Reply ONLY in simple, spoken Gujarati in Gujarati script.",
}

# Timbre v2.5 voices have one preferred language each (docs.gnani.ai, voice catalog).
# Chosen for warm / calm personas where the catalog offers a choice.
TTS_VOICES_V25 = {
    "hi-IN": ("hi-IN", "Shivani"),
    "hi-en": ("hi-en", "Chetana"),
    "en-IN": ("en-IN", "Chetana"),
    "mr-IN": ("mr-IN", "Kalpana"),
    "ta-IN": ("ta-IN", "Riyaa"),
    "te-IN": ("te-IN", "Tarika"),
    "kn-IN": ("kn-IN", "Kalpana"),
    "ml-IN": ("ml-IN", "Lakshmi"),
    "pa-IN": ("pa-IN", "Devansh"),
    "bn-IN": ("bn-IN", "Shivani"),
    "gu-IN": ("gu-IN", "Chetana"),
}
# Timbre v3.0: every voice speaks all languages; also supports audio tags like <pauses>.
TTS_VOICE_V30 = "Chetana"


def tts_voice(lang: str, model: str) -> tuple[str, str]:
    """(language param, voice) for the Gnani TTS request."""
    if model.startswith("timbre-v3"):
        api_lang = "auto" if lang == "hi-en" else lang
        return api_lang, TTS_VOICE_V30
    return TTS_VOICES_V25.get(lang, TTS_VOICES_V25["en-IN"])


def is_hindi_family(lang: str) -> bool:
    return lang in ("hi-IN", "hi-en", "mr-IN")

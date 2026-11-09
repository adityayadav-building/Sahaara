"""Clean-up helpers for the Bhaktivedanta 'Bhagavad-gita As It Is' text export.

The PDF text uses the old 'Balaram' font encoding for diacritics (a-umlaut = long a, n-tilde = s-underdot,
and so on). `fix_diacritics` converts it to proper IAST. `to_devanagari` turns IAST into Devanagari for
display and for the Hindi TTS voice. `ascii_for_tts` makes English text speakable (Krishna, not Kr-s-na).
"""
from __future__ import annotations

import re

_BALARAM = str.maketrans({
    "ä": "ā", "é": "ī", "ü": "ū", "å": "ṛ", "ñ": "ṣ", "ö": "ṭ", "ò": "ḍ", "ë": "ṇ", "ç": "ś", "ï": "ñ",
    "ì": "ṅ", "ù": "ḥ", "à": "ṁ", "Ä": "Ā", "É": "Ī", "Ü": "Ū", "Å": "Ṛ", "Ñ": "Ṣ", "Ö": "Ṭ", "Ò": "Ḍ",
    "Ë": "Ṇ", "Ç": "Ś", "Ï": "Ñ", "Ì": "Ṅ", "Ù": "Ḥ", "À": "Ṁ", "ê": "ṝ", "í": "ḹ",
})


def fix_diacritics(s: str) -> str:
    return s.translate(_BALARAM).replace("\u0002", "-").replace("\u00ad", "")


def to_devanagari(iast: str) -> str:
    try:
        from indic_transliteration import sanscript
    except ImportError:  # optional dependency; display falls back to IAST
        return ""
    out = sanscript.transliterate(iast.replace("’", "'").replace("ṁ", "ṃ"), sanscript.IAST, sanscript.DEVANAGARI)
    return out.replace("ꣳ", "ं")


_NAMES = [("Kṛṣṇa", "Krishna"), ("Kṛṣṇ", "Krishn"), ("Dhṛtarāṣṭra", "Dhritarashtra"), ("Pāṇḍu", "Pandu"),
          ("Pāṇḍava", "Pandava"), ("Bhagavad-gītā", "Bhagavad Gita"), ("gītā", "Gita"), ("Gītā", "Gita"),
          ("Saṅjaya", "Sanjaya"), ("Sañjaya", "Sanjaya"), ("Bhīṣma", "Bhishma"), ("Droṇa", "Drona")]
_PLAIN = str.maketrans({"ā": "a", "ī": "i", "ū": "u", "ṛ": "ri", "ṝ": "ri", "ṣ": "sh", "ś": "sh", "ṭ": "t", "ḍ": "d",
                        "ṇ": "n", "ñ": "n", "ṅ": "n", "ḥ": "h", "ṁ": "m", "Ā": "A", "Ī": "I", "Ū": "U", "Ś": "Sh",
                        "Ṣ": "Sh", "Ṭ": "T", "Ḍ": "D", "Ṇ": "N", "Ṛ": "Ri", "“": '"', "”": '"', "’": "'", "‘": "'",
                        "—": ", ", "―": ", ", "–": "-"})


def ascii_for_tts(s: str) -> str:
    for a, b in _NAMES:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s.translate(_PLAIN)).strip()

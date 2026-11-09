"""Guided breathing patterns. Phases are (kind, seconds); the frontend animates and speaks the cues."""
from __future__ import annotations

PATTERNS = {
    "long_exhale": {"name": {"en": "Long-exhale breathing", "hi": "लंबी साँस छोड़ना"},
                    "phases": [("in", 4), ("out", 6)], "cycles": 8},
    "box": {"name": {"en": "Box breathing", "hi": "चौकोर साँस"},
            "phases": [("in", 4), ("hold", 4), ("out", 4), ("rest", 4)], "cycles": 6},
    "nadi": {"name": {"en": "Calm breathing", "hi": "शांत साँस"},
             "phases": [("in", 4), ("out", 6)], "cycles": 6},
    "bhramari": {"name": {"en": "Humming-bee breath", "hi": "भ्रामरी"},
                 "phases": [("in", 4), ("hum", 8)], "cycles": 6},
}

CUES = {
    "en": {"in": "Breathe in", "out": "Breathe out", "hold": "Hold gently", "rest": "Rest", "hum": "Breathe out, humming",
           "start": "Let's breathe together. Sit comfortably.", "done": "Well done. Notice how you feel now."},
    "hi": {"in": "साँस अंदर लीजिए", "out": "साँस छोड़िए", "hold": "हल्के से रोकिए", "rest": "ठहरिए",
           "hum": "साँस छोड़िए, गुनगुनाते हुए", "start": "चलिए साथ में साँस लेते हैं। आराम से बैठिए।",
           "done": "बहुत अच्छा। अब महसूस कीजिए कि कैसा लग रहा है।"},
}


def get_pattern(key: str, lang: str = "en") -> dict | None:
    p = PATTERNS.get(key)
    if not p:
        return None
    k = "hi" if lang in ("hi-IN", "hi-en", "mr-IN") else "en"
    return {"key": key, "name": p["name"][k], "cycles": p["cycles"],
            "phases": [{"kind": kind, "seconds": sec, "cue": CUES[k][kind]} for kind, sec in p["phases"]],
            "start": CUES[k]["start"], "done": CUES[k]["done"]}

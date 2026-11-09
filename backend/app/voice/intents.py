"""Multilingual voice intent matcher.
Handles commands like 'slower', 'repeat that', 'read the verse again', 'in Hindi'
instantly BEFORE calling the LLM, reducing latency to near-zero for common actions.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class IntentResult:
    intent: str  # "repeat" | "slower" | "faster" | "read_verse" | "in_hindi" | "in_english" | "stop"
    response_text: str
    action: Optional[str] = None
    new_speed: Optional[float] = None
    new_lang: Optional[str] = None

# Multilingual regexes
_PATTERNS = {
    "repeat": re.compile(
        r"\b(repeat|say that again|what did you say|say again|come again|pardon|dobara|dobaara|phir se|fir se|ek baar aur|wapas bolo|திரும்ப சொல்|మళ్ళీ చెప్పు|ಮತ್ತೆ ಹೇಳು)\b",
        re.IGNORECASE
    ),
    "slower": re.compile(
        r"\b(slower|speak slow|slow down|too fast|dhire|dheere|thoda slow|halke bolo|மெதுவாக|నెమ్మదిగా|ನಿಧಾನವಾಗಿ)\b",
        re.IGNORECASE
    ),
    "faster": re.compile(
        r"\b(faster|speed up|too slow|jaldi|tez bolo|thoda fast|வேகமாக|వేగంగా|ವೇಗವಾಗಿ)\b",
        re.IGNORECASE
    ),
    "read_verse": re.compile(
        r"\b(read the verse|recite the shloka|shloka again|verse again|shloka sunao|shlok sunao|verse padho|shloka padho|श्लोक सुनाओ|श्लोक पढ़ो|श्लोक फिर से)\b",
        re.IGNORECASE
    ),
    "in_hindi": re.compile(
        r"\b(in hindi|hindi mein|hindi me bolo|hindi me batao|हिन्दी में|हिंदी में बोलो)\b",
        re.IGNORECASE
    ),
    "in_english": re.compile(
        r"\b(in english|english mein|english me bolo|अंग्रेजी में)\b",
        re.IGNORECASE
    ),
    "stop": re.compile(
        r"\b(stop|shanti|ruko|bas karo|chup|pause|be quiet|staph|शांत|रुको|बस)\b",
        re.IGNORECASE
    ),
}

def match_intent(text: str, current_speed: float = 0.95, last_response: str = "", last_verse: str = "") -> Optional[IntentResult]:
    """Inspects text for common voice shortcuts. If matched, returns immediate response without LLM."""
    clean = text.strip().lower()
    
    # Check stop
    if _PATTERNS["stop"].search(clean) and len(clean.split()) <= 4:
        return IntentResult(
            intent="stop",
            response_text="I am pausing here. Whenever you wish to speak, I am listening.",
            action="stop"
        )
        
    # Check repeat
    if _PATTERNS["repeat"].search(clean) and len(clean.split()) <= 6:
        reply = last_response if last_response else "I am right here with you. What is on your mind?"
        return IntentResult(
            intent="repeat",
            response_text=reply,
            action="replay"
        )
        
    # Check slower
    if _PATTERNS["slower"].search(clean) and len(clean.split()) <= 5:
        target = max(0.80, round(current_speed - 0.10, 2))
        return IntentResult(
            intent="slower",
            response_text="I have slowed down my pace. Please take your time.",
            action="set_speed",
            new_speed=target
        )
        
    # Check faster
    if _PATTERNS["faster"].search(clean) and len(clean.split()) <= 5:
        target = min(1.15, round(current_speed + 0.10, 2))
        return IntentResult(
            intent="faster",
            response_text="I will speak a little faster now.",
            action="set_speed",
            new_speed=target
        )
        
    # Check read verse
    if _PATTERNS["read_verse"].search(clean) and len(clean.split()) <= 6:
        if last_verse:
            return IntentResult(
                intent="read_verse",
                response_text=last_verse,
                action="read_verse"
            )
        return IntentResult(
            intent="read_verse",
            response_text="Share what you are feeling, and I will share a calming shloka with you.",
            action="none"
        )
        
    # Language switch intents
    if _PATTERNS["in_hindi"].search(clean) and len(clean.split()) <= 5:
        return IntentResult(
            intent="in_hindi",
            response_text="हाँ, बिल्कुल। अब हम हिन्दी में बात करेंगे। आप कैसा महसूस कर रहे हैं?",
            action="set_lang",
            new_lang="hi-IN"
        )
        
    if _PATTERNS["in_english"].search(clean) and len(clean.split()) <= 5:
        return IntentResult(
            intent="in_english",
            response_text="Certainly. We can continue in English. How can I support you right now?",
            action="set_lang",
            new_lang="en-IN"
        )
        
    return None

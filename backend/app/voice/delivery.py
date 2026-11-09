"""Delivery planner for expressive empathetic voice synthesis.
Injects Timbre v3.0 emotional tags (<slow>, <pauses>, <whispers>, <exhales>, <sigh>)
based on emotional topics and sentence context, while providing clean display text.
"""
from __future__ import annotations
import re
from typing import List

_TAG_RE = re.compile(r"</?(slow|pauses|whispers|exhales|sigh|excited|fast)>", re.IGNORECASE)

def strip_tags(text: str) -> str:
    """Strips audio delivery tags so display text and transcripts remain clean."""
    clean = _TAG_RE.sub("", text)
    return re.sub(r"[ \t]+", " ", clean).strip()

def plan_delivery(sentence: str, topics: List[str], is_crisis: bool = False, is_verse: bool = False) -> str:
    """Adds expressive delivery tags to a sentence based on its emotional context."""
    s = sentence.strip()
    if not s:
        return ""
        
    # Crisis replies are always spoken slowly and calmly
    if is_crisis:
        return f"<slow> {s}"
        
    # Sanskrit verses get slow, measured pacing with breathing pauses
    if is_verse:
        return f"<slow> <pauses> {s}"
        
    topic_set = set(topics)
    
    # Sleep wind-down: soft, whispery, calm
    if "sleep" in topic_set or "burnout" in topic_set:
        return f"<whispers> <slow> {s}"
        
    # Grief, sadness, loss: gentle, slow, holding space
    if "grief" in topic_set or "sadness" in topic_set:
        return f"<slow> <pauses> {s}"
        
    # High anxiety, panic, overwhelm: slow, grounding, calming exhale
    if "anxiety" in topic_set or "fear" in topic_set or "overwhelm" in topic_set:
        if any(w in s.lower() for w in ("breath", "pause", "gentle", "calm")):
            return f"<slow> <exhales> {s}"
        return f"<slow> {s}"
        
    # Anger, frustration: soothing, steady, grounded
    if "anger" in topic_set:
        return f"<slow> <pauses> {s}"
        
    return s

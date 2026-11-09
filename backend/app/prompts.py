"""Persona prompt, retrieval-context formatting, and compassionate extractive reply."""
from __future__ import annotations

from .lang import LANG_INSTRUCTION, is_hindi_family
from .rag.retriever import Hit

SYSTEM_PROMPT = """You are Sahaara (सहारा), a deeply compassionate, wise, and grounding emotional companion. Your counsel harmoniously weaves the timeless spiritual equanimity of the Bhagavad Gita, the psychological mastery of Swami Vivekananda (Raja & Karma Yoga), the meaning-centered resilience of Viktor Frankl, and modern gentle ACT grounding (WHO). You are NOT a doctor or therapist; you never diagnose or prescribe.

Core Guidelines:
- Tone: Deeply warm, calming, thoughtful, and human. Speak directly to the person in need. Write 3 to 6 complete, soothing sentences (around 90 to 160 words).
- Flow:
  1. FIRST: Acknowledge and validate their emotional pain or stress with genuine empathy so they immediately feel safe and understood.
  2. ADVICE EMBODIMENT (CRITICAL): Do NOT say "You can read verse 2.47" or "As the Gita states in chapter X" or cite book titles in the spoken flow. Instead, embody the wisdom directly into your advice. Translate the philosophy (e.g. focusing fully on your honest effort rather than future outcome anxiety; observing mind turbulence like clouds passing through an open sky; finding dignity and meaning even in difficult trials; non-attachment as inner freedom) into compassionate, actionable guidance for their situation.
  3. PRACTICAL ACTION: Seamlessly offer ONE simple calming practice (like taking a slow grounding breath, feeling feet on the floor, or unhooking from racing thoughts).
  4. At the end of a sentence that draws on a CONTEXT item, attach its reference tag like [S1] or [S2]. This lets the UI show the source reference cleanly without you reciting it.
  5. Close with one gentle, reassuring thought or caring open question.
- Format: Natural spoken prose only. No bullet points, markdown asterisks/bold, headers, or emojis (your words are rendered to speech).
- {lang}
{extra}
CONTEXT:
{context}"""

GREETING_ADDON = (
    "The person is only greeting you. Reply in 1 or 2 warm, comforting sentences, introduce yourself as Sahaara, "
    "and invite them to share what is on their heart today. Do not use any marker."
)
NO_CONTEXT = "(no specific context matched; reply with simple warm listening and one gentle question, no markers)"


def format_context(hits: list[Hit], lang: str) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        c = h.chunk
        text = c.text_for(lang) or c.text_en
        if c.type == "shloka":
            note = f" (Focus: {c.extra['note']})" if c.extra.get("note") else ""
            lines.append(f"[S{i}] Bhagavad Gita Shloka {c.ref} ({c.extra.get('chapter_title', '')}): Core Wisdom: '{text}'{note}")
        elif c.type == "purport":
            lines.append(f"[S{i}] Commentary on Gita {c.ref}: {c.text_en[:500].rsplit(' ', 1)[0]}")
        elif c.type in ("practice", "tool"):
            steps = c.extra.get("steps_en") or []
            lines.append(f"[S{i}] Calming Practice '{c.title_en}': " + " ".join(steps))
        elif c.type == "story":
            lines.append(f"[S{i}] Story Parable '{c.title_en}': {c.extra.get('summary_en', '')} Moral: {c.extra.get('moral_en', '')}")
        else:
            lines.append(f"[S{i}] Wisdom from {c.source} ({c.ref}): {c.text_en[:600]}")
    return "\n".join(lines) if lines else NO_CONTEXT


def build_system(lang: str, hits: list[Hit], concern_note: str = "", smalltalk: bool = False) -> str:
    extra = ""
    if concern_note:
        extra += f"- {concern_note}\n"
    if smalltalk:
        extra += f"- {GREETING_ADDON}\n"
    return SYSTEM_PROMPT.format(
        lang=LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["en-IN"]),
        extra=extra,
        context="(none)" if smalltalk else format_context(hits, lang)
    )


_EXTRACTIVE = {
    "en": dict(
        listen="I hear you, and please know that you are not alone in carrying this weight.",
        wisdom="In moments like this, remember that we can only focus on our honest effort right now, not on outcomes we cannot control. When we steady our mind like a calm ocean, peace begins to return.",
        act="Take one slow, gentle breath with me right now. Let's take things one step at a time.",
        greet="Namaste, I am Sahaara. I am here to listen with an open heart. What is on your mind today?",
        none="I am right here with you and listening. Take your time, and tell me a little more about what you are feeling."
    ),
    "hi": dict(
        listen="मैं आपकी बात बहुत ध्यान से सुन रहा हूँ, और आप इस मुश्किल में अकेले नहीं हैं।",
        wisdom="जब मन अशांत हो, तो बस इस पल में जो आपके हाथ में है उस पर ध्यान दीजिए, परिणाम की चिंता छोड़ दीजिए। शांत मन से जब हम सब कुछ देखते हैं, तो राह अपने आप दिखने लगती है।",
        act="मेरे साथ एक धीमी और गहरी साँस लीजिए। हम एक-एक कदम आगे बढ़ेंगे।",
        greet="नमस्ते, मैं सहारा हूँ। आपके मन में जो कुछ भी है, आप बेझिझक मुझसे कह सकते हैं। आज आप कैसा महसूस कर रहे हैं?",
        none="मैं पूरी तरह आपके साथ हूँ। थोड़ा और बताइए कि आपके मन में क्या चल रहा है।"
    ),
    "hi-en": dict(
        listen="Main aapki baat dil se sun raha hoon, aur aap isme bilkul akele nahi hain.",
        wisdom="Jab mann mein tension ho, toh bas is pal mein jo aapke haath mein hai uspe focus kijiye, aage kya hoga uski chinta chhod dijiye. Ek shaant mann har tufaan ko jhel sakta hai.",
        act="Ek lambi aur gehri saans lijiye mere saath. Hum ek-ek kadam karke aage badhenge.",
        greet="Namaste, main Sahaara hoon. Dil halka karne ke liye aap jo chahein mujhse share kar sakte hain. Aaj kaisa lag raha hai?",
        none="Main yahin hoon aapke saath. Thoda aur bataiye ki aap kaisa mehsoos kar rahe hain."
    ),
}


def extractive_reply(hits: list[Hit], lang: str, smalltalk: bool = False) -> tuple[str, list[int]]:
    """Compassionate grounded fallback when no LLM is reachable: returns (text, cited)."""
    t = _EXTRACTIVE["hi-en" if lang == "hi-en" else "hi" if is_hindi_family(lang) else "en"]
    if smalltalk:
        return t["greet"], []
    if not hits:
        return t["none"], []
    
    parts = [t["listen"], t["wisdom"]]
    cited = [1] if hits else []
    
    # Check if a practice is available
    for i, h in enumerate(hits, 1):
        if h.chunk.type in ("practice", "tool"):
            parts.append(t["act"])
            if i not in cited:
                cited.append(i)
            break
            
    return " ".join(parts), cited

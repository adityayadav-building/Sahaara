"""Safety layer. Runs BEFORE retrieval and the LLM.

Levels:
  crisis  - explicit self-harm / suicidal intent. The LLM is bypassed entirely; a fixed,
            reviewed message pointing to human help is returned (no coaching, no verses).
  concern - hopelessness / burden language. Normal reply, but the helpline stays visible and
            the prompt is told to gently encourage reaching out to a person.
  none    - normal flow.

This is a keyword safety net, not a classifier: it will miss indirect phrasing. It exists so the
worst-case behaviour is predictable. Have a clinician review the wording before real-world use.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .lang import LANGUAGES

HELPLINES = [
    {
        "name": "Tele-MANAS",
        "number": "14416",
        "alt": "1800-891-4416",
        "note": "Government of India mental health helpline: talk to a trained counsellor.",
    },
    {
        "name": "Emergency",
        "number": "112",
        "alt": "",
        "note": "If you may act on thoughts of harming yourself, call now or go to the nearest hospital.",
    },
]

_CRISIS = [
    # English
    "kill myself", "killing myself", "end my life", "end it all", "want to die", "wanna die", "wish i was dead",
    "wish i were dead", "suicide", "suicidal", "better off dead", "take my own life", "don't want to live",
    "dont want to live", "do not want to live", "don't want to be alive", "no reason to live", "hurt myself",
    "harm myself", "cut myself", "self harm", "self-harm", "end my own life",
    # Hinglish
    "marna chahta", "marna chahti", "mar jana chahta", "mar jaana chahta", "mar jana chahti", "mar jaunga",
    "mar jaungi", "jeena nahi chahta", "jeena nahi chahti", "jeene ka mann nahi", "jine ka mann nahi",
    "jeene ka man nahi", "zindagi khatam", "khud ko khatam", "khudkushi", "aatmahatya", "apni jaan",
    "jaan de dunga", "jaan de dungi", "jaan dena chahta", "khud ko nuksan", "khud ko hurt", "sab khatam kar",
    "suicide kar", "mar jaun", "marna hai", "mujhe marna", "mar jana hai", "mar jaana hai", "jeena nahi hai",
    "jeena nahi", "jine ka koi", "jeene ka koi",
    # Hindi / Marathi (Devanagari)
    "मरना चाहता", "मरना चाहती", "मर जाना चाहता", "मर जाना चाहती", "मर जाऊं", "मर जाऊँ", "जीना नहीं चाहता",
    "जीना नहीं चाहती", "जीने का मन नहीं", "आत्महत्या", "खुदकुशी", "अपनी जान", "ज़िंदगी खत्म", "जिंदगी खत्म",
    "जिंदगी खतम", "खुद को खत्म", "खुद को नुकसान", "खुद को चोट", "मला मरायचं", "जगायचं नाही",
    # Tamil
    "தற்கொலை", "சாக வேண்டும்", "சாகணும்", "இறக்க வேண்டும்", "வாழ பிடிக்கவில்லை", "வாழ விருப்பமில்லை",
    # Bengali
    "আত্মহত্যা", "মরে যেতে চাই", "বাঁচতে চাই না", "মরতে চাই", "নিজেকে শেষ",
    # Punjabi
    "ਖੁਦਕੁਸ਼ੀ", "ਮਰਨਾ ਚਾਹੁੰਦਾ", "ਮਰਨਾ ਚਾਹੁੰਦੀ", "ਜੀਣਾ ਨਹੀਂ ਚਾਹੁੰਦਾ", "ਜੀਣਾ ਨਹੀਂ ਚਾਹੁੰਦੀ",
    # Gujarati
    "આત્મહત્યા", "મરી જવું છે", "મરી જવું", "જીવવું નથી",
    # Telugu / Kannada / Malayalam
    "ఆత్మహత్య", "చచ్చిపోవాలి", "ಆತ್ಮಹತ್ಯೆ", "ಸಾಯಬೇಕು", "ആത്മഹത്യ", "മരിക്കണം",
]

# Idioms that contain trigger words but are not about self-harm.
_CRISIS_EXCLUDE = [
    r"die of (embarrassment|shame|laughter|boredom)", r"dying of (embarrassment|shame|laughter|boredom)",
    r"die laughing", r"(want|wanna) to die for (this|that)",
]

_CONCERN = [
    "hopeless", "no point", "can't go on", "cant go on", "can't take it anymore", "cant take it anymore",
    "worthless", "i'm a burden", "im a burden", "am a burden", "give up on life", "nobody cares", "no one cares",
    "tired of everything", "tired of living", "can't do this anymore", "cant do this anymore", "no way out",
    "sab bekar", "koi fayda nahi", "koi faayda nahi", "zindagi se thak", "haar gaya", "haar gayi", "sab chhod",
    "kisi ko meri parwah nahi", "main bojh", "बेकार हूँ", "बेकार हूं", "कोई फायदा नहीं", "ज़िंदगी से थक",
    "जिंदगी से थक", "हार गया", "हार गई", "मैं बोझ", "कोई परवाह नहीं", "सब खत्म", "कोई रास्ता नहीं",
    "நம்பிக்கை இல்லை", "பயனற்றவன்", "பயனற்றவள்", "আমি বোঝা", "আশা নেই", "ਕੋਈ ਫਾਇਦਾ ਨਹੀਂ", "કોઈ ફાયદો નથી",
]

_CRISIS_RE = re.compile("|".join(re.escape(p) for p in _CRISIS), re.IGNORECASE)
_CONCERN_RE = re.compile("|".join(re.escape(p) for p in _CONCERN), re.IGNORECASE)
_EXCLUDE_RE = re.compile("|".join(_CRISIS_EXCLUDE), re.IGNORECASE)


@dataclass(frozen=True)
class SafetyResult:
    level: str  # "crisis" | "concern" | "none"
    matched: str = ""

    @property
    def show_helpline(self) -> bool:
        return self.level in ("crisis", "concern")


def _norm(text: str) -> str:
    t = text.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", t)


def assess(text: str, prior_user_turns: list[str] | None = None) -> SafetyResult:
    """Classify the latest user message (prior turns only raise concern, never crisis)."""
    t = _norm(text)
    scrubbed = _EXCLUDE_RE.sub(" ", t)
    m = _CRISIS_RE.search(scrubbed)
    if m:
        return SafetyResult("crisis", m.group(0))
    m = _CONCERN_RE.search(scrubbed)
    if m:
        return SafetyResult("concern", m.group(0))
    # Repeated low-grade distress across recent turns also keeps the helpline visible.
    if prior_user_turns:
        recent = [_norm(x) for x in prior_user_turns[-3:]]
        if sum(1 for x in recent if _CONCERN_RE.search(x)) >= 2:
            return SafetyResult("concern", "repeated")
    return SafetyResult("none")


# Reviewed fixed responses. No coaching, no verses, no method details, no questions that pull
# the person deeper; they point to a human and stay warm.
_CRISIS_TEXT = {
    "en-IN": (
        "Thank you for telling me. What you are feeling sounds very heavy, and you do not have to carry it alone "
        "right now. Please reach out to a person who can be with you. You can call Tele-MANAS on 14416 to talk to "
        "a trained counsellor. If you think you might act on these thoughts, call 112 now or go to the nearest "
        "hospital. If someone is close by, tell them, or ask them to stay with you. I am here with you too."
    ),
    "hi-IN": (
        "आपने मुझे बताया, इसके लिए शुक्रिया। आप जो महसूस कर रहे हैं वह बहुत भारी लगता है, और इसे अभी अकेले उठाना "
        "ज़रूरी नहीं है। कृपया किसी ऐसे इंसान से बात कीजिए जो आपके साथ रह सके। आप टेली-मानस 14416 पर कॉल करके "
        "प्रशिक्षित काउंसलर से बात कर सकते हैं। अगर आपको लगता है कि आप खुद को नुकसान पहुँचा सकते हैं, तो अभी 112 "
        "पर कॉल कीजिए या पास के अस्पताल जाइए। अगर कोई पास में है, तो उसे बताइए या उससे अपने पास रुकने को कहिए। "
        "मैं भी आपके साथ हूँ।"
    ),
    "hi-en": (
        "Aapne mujhe bataya, uske liye shukriya. Aap jo feel kar rahe hain wo bahut bhaari lagta hai, aur ise abhi "
        "akele uthana zaroori nahi hai. Please kisi aise insaan se baat kijiye jo aapke saath reh sake. Aap Tele-MANAS "
        "14416 par call karke trained counsellor se baat kar sakte hain. Agar aapko lagta hai ki aap khud ko nuksan "
        "pahuncha sakte hain, to abhi 112 par call kijiye ya paas ke hospital jaaiye. Agar koi paas hai, to use "
        "bataiye ya usse apne paas rukne ko kahiye. Main bhi aapke saath hoon."
    ),
    "ta-IN": (
        "என்னிடம் சொன்னதற்கு நன்றி. நீங்கள் உணர்வது மிகவும் கனமாக இருக்கிறது, இதை இப்போது தனியாகச் சுமக்க "
        "வேண்டியதில்லை. தயவுசெய்து உங்களுடன் இருக்கக்கூடிய ஒருவரிடம் பேசுங்கள். பயிற்சி பெற்ற ஆலோசகரிடம் பேச "
        "டெலி-மானஸ் 14416 எண்ணை அழைக்கலாம். உங்களை நீங்களே காயப்படுத்திக் கொள்வீர்கள் என்று தோன்றினால், "
        "உடனே 112 ஐ அழைக்கவும் அல்லது அருகிலுள்ள மருத்துவமனைக்குச் செல்லவும். அருகில் யாராவது இருந்தால் "
        "அவர்களிடம் சொல்லுங்கள். நானும் உங்களுடன் இருக்கிறேன்."
    ),
    "bn-IN": (
        "আমাকে বলার জন্য ধন্যবাদ। আপনি যা অনুভব করছেন তা খুব ভারী, আর এখন এটা একা বহন করতে হবে না। দয়া করে "
        "এমন কারও সঙ্গে কথা বলুন যে আপনার পাশে থাকতে পারে। প্রশিক্ষিত কাউন্সেলরের সঙ্গে কথা বলতে টেলি-মানস 14416 "
        "নম্বরে ফোন করতে পারেন। যদি মনে হয় আপনি নিজের ক্ষতি করতে পারেন, এখনই 112 নম্বরে ফোন করুন বা কাছের "
        "হাসপাতালে যান। কাছে কেউ থাকলে তাকে জানান। আমিও আপনার সঙ্গে আছি।"
    ),
    "pa-IN": (
        "ਮੈਨੂੰ ਦੱਸਣ ਲਈ ਧੰਨਵਾਦ। ਜੋ ਤੁਸੀਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ ਉਹ ਬਹੁਤ ਭਾਰੀ ਹੈ, ਅਤੇ ਹੁਣੇ ਇਸ ਨੂੰ ਇਕੱਲੇ ਚੁੱਕਣ ਦੀ ਲੋੜ ਨਹੀਂ। "
        "ਕਿਰਪਾ ਕਰਕੇ ਕਿਸੇ ਅਜਿਹੇ ਨਾਲ ਗੱਲ ਕਰੋ ਜੋ ਤੁਹਾਡੇ ਨਾਲ ਰਹਿ ਸਕੇ। ਸਿਖਲਾਈ ਪ੍ਰਾਪਤ ਕਾਊਂਸਲਰ ਨਾਲ ਗੱਲ ਕਰਨ ਲਈ ਤੁਸੀਂ "
        "ਟੈਲੀ-ਮਾਨਸ 14416 'ਤੇ ਕਾਲ ਕਰ ਸਕਦੇ ਹੋ। ਜੇ ਤੁਹਾਨੂੰ ਲੱਗਦਾ ਹੈ ਕਿ ਤੁਸੀਂ ਆਪਣੇ ਆਪ ਨੂੰ ਨੁਕਸਾਨ ਪਹੁੰਚਾ ਸਕਦੇ ਹੋ, ਤਾਂ "
        "ਹੁਣੇ 112 'ਤੇ ਕਾਲ ਕਰੋ ਜਾਂ ਨੇੜੇ ਦੇ ਹਸਪਤਾਲ ਜਾਓ। ਜੇ ਕੋਈ ਨੇੜੇ ਹੈ ਤਾਂ ਉਸਨੂੰ ਦੱਸੋ। ਮੈਂ ਵੀ ਤੁਹਾਡੇ ਨਾਲ ਹਾਂ।"
    ),
    "gu-IN": (
        "મને કહ્યું તે બદલ આભાર. તમે જે અનુભવો છો તે ઘણું ભારે છે, અને હમણાં તેને એકલા ઉપાડવાની જરૂર નથી. કૃપા કરીને "
        "એવી વ્યક્તિ સાથે વાત કરો જે તમારી સાથે રહી શકે. પ્રશિક્ષિત કાઉન્સેલર સાથે વાત કરવા તમે ટેલિ-માનસ 14416 પર કૉલ "
        "કરી શકો છો. જો તમને લાગે કે તમે પોતાને નુકસાન પહોંચાડી શકો છો, તો હમણાં 112 પર કૉલ કરો અથવા નજીકની હોસ્પિટલમાં "
        "જાઓ. જો નજીકમાં કોઈ હોય તો તેમને જણાવો. હું પણ તમારી સાથે છું."
    ),
}
# Marathi reuses Hindi (Devanagari); Telugu/Kannada/Malayalam fall back to English until reviewed.
_CRISIS_TEXT["mr-IN"] = _CRISIS_TEXT["hi-IN"]


def crisis_message(lang: str) -> str:
    return _CRISIS_TEXT.get(lang, _CRISIS_TEXT["en-IN"])


CONCERN_PROMPT_NOTE = (
    "The person may be in real distress. Be extra gentle and slow. Gently encourage them to be with, or talk to, "
    "someone they trust, and mention that Tele-MANAS (14416) is there to talk to. Do not diagnose, do not "
    "minimise, and do not ask probing questions about self-harm methods."
)

assert set(_CRISIS_TEXT) <= set(LANGUAGES)

"""Multilingual emotion/topic lexicon used to route retrieval.

Matching is substring-based for Indic scripts (no reliable stemming) and prefix-with-word-boundary
for Latin text, so "ghabrahat" matches the stem "ghabra" and "responsibilities" matches
"responsibilit". It is intentionally simple and auditable: every topic hit can be explained.
Extend the lists freely; the eval harness in backend/eval will show if a change helps or hurts.
"""
from __future__ import annotations

import re

LEXICON: dict[str, list[str]] = {
    "anxiety": [
        "anxious", "anxiety", "worried", "worry", "worries", "nervous", "panic", "tension", "stressed", "stress",
        "on edge", "can't relax", "cant relax", "heart racing", "ghabra", "ghabrahat", "chinta", "chintit",
        "bechain", "pareshan", "tension",
        "चिंता", "घबराहट", "घबरा", "तनाव", "बेचैन", "परेशान", "टेंशन",
        "கவலை", "பதட்டம்", "மன அழுத்தம்", "চিন্তা", "উদ্বেগ", "দুশ্চিন্তা", "ਚਿੰਤਾ", "ਘਬਰਾਹਟ", "ਤਣਾਅ",
        "ચિંતા", "ગભરાટ", "તણાવ",
    ],
    "overthinking": [
        "overthink", "can't stop thinking", "cant stop thinking", "racing thoughts", "restless mind",
        "mind won't", "mind wont", "can't focus", "cant focus", "focus nahi", "dhyan nahi", "mann nahi lagta",
        "soch soch", "zyada soch", "bahut soch", "mann bhatak", "mann restless",
        "ज्यादा सोच", "ज़्यादा सोच", "बहुत सोच", "सोच सोच", "मन भटक", "ध्यान नहीं", "मन शांत नहीं", "एकाग्र", "मन चंचल",
        "அதிகமாக யோசி", "மனம் அலைபாய", "বেশি ভাবি", "ਬਹੁਤ ਸੋਚ", "વધારે વિચાર",
    ],
    "fear": [
        "afraid", "scared", "fear", "terrified", "frightened", "phobia", "darr", "dar lag", "dara hua", "darta",
        "darti", "डर", "भय", "डरा", "பயம்", "அச்சம்", "ভয়", "ਡਰ", "ડર",
    ],
    "anger": [
        "angry", "anger", "furious", "rage", "irritat", "frustrat", "hate", "gussa", "gusse", "chidh", "krodh",
        "गुस्सा", "ग़ुस्सा", "क्रोध", "चिढ़", "चिड़चिड़", "கோபம்", "எரிச்சல்", "রাগ", "ਗੁੱਸਾ", "ગુસ્સો",
    ],
    "sadness": [
        "sad", "depress", "feeling low", "feeling down", "crying", "i cry", "empty inside", "udaas", "udas", "rona",
        "ro raha", "ro rahi", "dukhi", "dukh",
        "उदास", "दुखी", "दुख", "रोना", "रो रहा", "रो रही", "निराश", "खालीपन", "வருத்தம்", "சோகம்",
        "அழுகை", "দুঃখ", "মন খারাপ", "ਉਦਾਸ", "ਦੁੱਖ", "ઉદાસ", "દુઃખ",
    ],
    "grief": [
        "passed away", "died", "death of", "funeral", "miss him", "miss her", "grief", "mourning", "guzar gaye",
        "guzar gayi", "nahi rahe", "chal base",
        "मृत्यु", "गुज़र", "गुजर गए", "गुजर गई", "निधन", "चल बसे", "नहीं रहे", "शोक",
        "இறந்து", "மரணம்", "মৃত্যু", "মারা গেছেন", "ਮੌਤ", "ਗੁਜ਼ਰ", "મૃત્યુ",
    ],
    "loneliness": [
        "lonely", "loneliness", "i am alone", "i'm alone", "no friends", "nobody understands", "no one understands",
        "isolated", "akela", "akeli", "akelapan", "koi nahi hai", "koi samajh",
        "अकेला", "अकेली", "अकेलापन", "कोई समझता नहीं", "कोई नहीं है", "தனிமை", "தனியாக", "একা", "একাকী",
        "ਇਕੱਲ", "ਇਕੱਲਾ", "એકલ", "એકલતા",
    ],
    "failure": [
        "failed", "failure", "rejected", "rejection", "lost my job", "lost job", "didn't get", "didnt get",
        "not selected", "backlog", "asafal", "fail ho", "reject ho", "naukri chali", "नौकरी चली",
        "असफल", "फेल", "रिजेक्ट", "நிராகரிக்க", "தோல்வி", "ব্যর্থ", "ফেল", "ਅਸਫਲ", "ਫੇਲ", "નિષ્ફળ", "નાપાસ",
    ],
    "exam_pressure": [
        "exam", "result", "marks", "percentile", "jee", "neet", "upsc", "board exam", "interview", "pressure",
        "expectations", "pariksha", "parikshaa", "padhai",
        "परीक्षा", "रिज़ल्ट", "रिजल्ट", "अंक", "इंटरव्यू", "दबाव", "पढ़ाई",
        "தேர்வு", "முடிவு", "পরীক্ষা", "ফলাফল", "ਪ੍ਰੀਖਿਆ", "ਨਤੀਜਾ", "પરીક્ષા", "પરિણામ",
    ],
    "self_worth": [
        "worthless", "useless", "not good enough", "hate myself", "stupid", "loser", "burden", "nafrat",
        "khud se nafrat", "bekaar", "bekar", "nikamma", "kaabil nahi",
        "बेकार", "निकम्मा", "खुद से नफ़रत", "खुद से नफरत", "काबिल नहीं", "बोझ",
        "பயனற்ற", "தகுதியற்ற", "অকেজো", "নিজেকে ঘৃণা", "ਬੇਕਾਰ", "નકામો", "નકામી",
    ],
    "low_motivation": [
        "no motivation", "unmotivated", "lazy", "procrastinat", "can't start", "cant start", "stuck in life",
        "mann nahi karta", "kuch karne ka mann", "aalas", "motivation nahi",
        "आलस", "मन नहीं करता", "कुछ करने का मन", "प्रेरणा नहीं", "ஊக்கம் இல்லை", "சோம்பல்", "উৎসাহ নেই", "ਮਨ ਨਹੀਂ",
        "પ્રેરણા નથી",
    ],
    "burnout": [
        "burnout", "burned out", "burnt out", "exhausted", "overworked", "drained", "thak", "thakan",
        "थकान", "थक गया", "थक गई", "थका", "बर्नआउट", "சோர்வு", "களைப்பு", "ক্লান্ত", "ক্লান্তি", "ਥਕਾਵਟ", "થાક",
    ],
    "overwhelm": [
        "overwhelm", "too much", "can't cope", "cant cope", "too many things", "responsibilit", "bojh", "zimmedari",
        "bahut kaam", "जिम्मेदारी", "जिम्मेदारियाँ", "बहुत काम", "सब कुछ ज्यादा", "सब कुछ ज़्यादा",
        "சுமை", "பொறுப்பு", "বোঝা", "দায়িত্ব", "ਬੋਝ", "ਜ਼ਿੰਮੇਵਾਰੀ", "બોજ", "જવાબદારી",
    ],
    "sleep": [
        "can't sleep", "cant sleep", "cannot sleep", "insomnia", "sleepless", "awake all night", "neend",
        "raat bhar", "नींद", "रात भर", "தூக்கம்", "தூங்க", "ঘুম", "ਨੀਂਦ", "ઊંઘ",
    ],
    "relationships": [
        "breakup", "broke up", "fight with", "argument", "girlfriend", "boyfriend", "husband", "wife", "parents",
        "family pressure", "betrayed", "cheated", "divorce", "rishta", "jhagda", "dhokha",
        "ब्रेकअप", "झगड़ा", "रिश्ता", "धोखा", "माँ बाप", "परिवार", "பிரிவு", "சண்டை", "உறவு", "ব্রেকআপ", "ঝগড়া",
        "সম্পর্ক", "ਝਗੜਾ", "ਰਿਸ਼ਤਾ", "ઝઘડો", "સંબંધ",
    ],
    "guilt": [
        "guilty", "guilt", "regret", "ashamed", "shame", "my fault", "pachtava", "galti", "sharm",
        "पछतावा", "गलती", "शर्म", "अपराधबोध", "மன்னிப்பு", "குற்ற", "வெட்கம்", "অনুতাপ", "লজ্জা", "ਪਛਤਾਵਾ", "ਸ਼ਰਮ",
        "પસ્તાવો", "શરમ",
    ],
}

ALL_TOPICS = tuple(LEXICON) + ("general",)

_LATIN = re.compile(r"^[\x00-\x7f]+$")
_COMPILED: dict[str, list[tuple[str, re.Pattern | None]]] = {}
for _topic, _terms in LEXICON.items():
    _items = []
    for _t in dict.fromkeys(x.lower() for x in _terms if x):
        if _LATIN.match(_t):
            _items.append((_t, re.compile(r"(?<![a-z])" + re.escape(_t))))
        else:
            _items.append((_t, None))
    _COMPILED[_topic] = _items


def detect_topics(text: str, max_topics: int = 3) -> list[tuple[str, float]]:
    """Return [(topic, weight)] ordered by strength. Weight is the number of distinct hits (capped)."""
    t = text.lower().replace("’", "'")
    scored: list[tuple[str, float]] = []
    for topic, items in _COMPILED.items():
        hits = 0
        for term, rx in items:
            if rx is not None:
                if rx.search(t):
                    hits += 1
            elif term in t:
                hits += 1
        if hits:
            scored.append((topic, float(min(hits, 3))))
    scored.sort(key=lambda x: -x[1])
    return scored[:max_topics]


_GREETINGS = {
    "hi", "hello", "hey", "namaste", "namaskar", "good morning", "good evening", "good night", "thanks",
    "thank you", "ok", "okay", "hii", "hiii", "helo", "shukriya", "dhanyavad", "नमस्ते", "नमस्कार", "धन्यवाद",
    "शुक्रिया", "हेलो", "हाय", "वणक्कम", "நன்றி", "நமஸ்காரம்",
}


def is_smalltalk(text: str) -> bool:
    t = re.sub(r"[^\w\sऀ-෿]", " ", text.lower()).strip()
    t = re.sub(r"\s+", " ", t)
    words = t.split()
    return bool(t) and (t in _GREETINGS or (len(words) <= 2 and all(w in _GREETINGS for w in words)))


_BREATH_WORDS = (
    "breath", "pranayam", "pranayama", "breathing", "saans", "sans", "साँस", "सांस", "प्राणायाम", "ब्रीद",
    "மூச்சு", "শ্বাস", "ਸਾਹ", "શ્વાસ",
)


def wants_breathing(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in _BREATH_WORDS)


# Focused semantic synonyms for emotional topics to guide BM25 without overriding user intent
EXPAND = {
    "anxiety": "anxiety anxious worry nervous panic uneasiness restless tension calm peace steady undisturbed",
    "overthinking": "restless mind racing thoughts wandering focus concentration steady still peaceful meditation",
    "fear": "fear afraid scared terror courage strength fearless protection",
    "anger": "anger wrath rage irritated upset krodh patience tolerance forgive calm",
    "sadness": "sad sorrow grief lamenting distress misery crying solace comfort hope",
    "grief": "mourning death departed lost bereavement eternal soul lamentation",
    "loneliness": "lonely alone abandoned shelter friend companion support",
    "failure": "failure setback defeat lost mistake learn rise resilient",
    "exam_pressure": "exam test marks result results preparation performance interview career pressure effort duty action",
    "self_worth": "confidence dignity self-worth respect capable strength worthy",
    "low_motivation": "unmotivated inaction lethargy tired enthusiasm energy purpose action",
    "burnout": "exhaustion tired overworked rest balance moderation peace",
    "overwhelm": "overwhelmed burden too much ocean calm still breath shelter",
    "sleep": "sleep insomnia night awake rest deep sleep relaxation",
    "relationships": "breakup conflict family friend partner love compassion harmony forgive",
    "guilt": "guilt regret fault shame remorse forgive cleanse free peace",
}

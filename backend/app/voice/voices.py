"""Gnani Timbre voice catalog and metadata.
Official 13 multilingual studio voices for timbre-v3.0.
All voices support Hindi, English, Hinglish, Marathi, Tamil, Telugu, Kannada, Malayalam, Punjabi, Bengali, Gujarati.
"""
from __future__ import annotations
from typing import Dict, Any, List

VOICES: List[Dict[str, Any]] = [
    {
        "id": "Chetana",
        "name": "Chetana (चेतना)",
        "gender": "Female",
        "persona": "Calm, empathetic, therapeutic",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Bedtime", "Meditation", "Anxiety"]
    },
    {
        "id": "Shivani",
        "name": "Shivani (शिवानी)",
        "gender": "Female",
        "persona": "Warm, gentle, reassuring",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Daily check-in", "Comfort", "Heart-to-heart"]
    },
    {
        "id": "Lakshmi",
        "name": "Lakshmi (लक्ष्मी)",
        "gender": "Female",
        "persona": "Grounded, motherly, serene",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Grief", "Peace", "Healing"]
    },
    {
        "id": "Kalpana",
        "name": "Kalpana (कल्पना)",
        "gender": "Female",
        "persona": "Thoughtful, articulate, wise",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Clarity", "Overthinking", "Philosophy"]
    },
    {
        "id": "Vasudha",
        "name": "Vasudha (वसुधा)",
        "gender": "Female",
        "persona": "Soft, peaceful, soothing whisper",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Sleep", "Bedside mode", "Deep relaxation"]
    },
    {
        "id": "Riyaa",
        "name": "Riyaa (रिया)",
        "gender": "Female",
        "persona": "Youthful, friendly, warm companion",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Casual sharing", "Students", "Exam stress"]
    },
    {
        "id": "Tarika",
        "name": "Tarika (तारिका)",
        "gender": "Female",
        "persona": "Uplifting, encouraging, bright",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Low motivation", "Self-worth"]
    },
    {
        "id": "Devansh",
        "name": "Devansh (देवांश)",
        "gender": "Male",
        "persona": "Warm, deep, reassuring brotherly tone",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Comfort", "Listening", "Patience"]
    },
    {
        "id": "Avinash",
        "name": "Avinash (अविनाश)",
        "gender": "Male",
        "persona": "Calm, steady, grounded mentor",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Gita wisdom", "Steadying mind"]
    },
    {
        "id": "Shubham",
        "name": "Shubham (शुभम)",
        "gender": "Male",
        "persona": "Gentle, compassionate, patient",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Stress relief", "Grounding"]
    },
    {
        "id": "Prakash",
        "name": "Prakash (प्रकाश)",
        "gender": "Male",
        "persona": "Wise, mature, contemplative",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Deeper reflections", "Life guidance"]
    },
    {
        "id": "Yashraj",
        "name": "Yashraj (यशराज)",
        "gender": "Male",
        "persona": "Strong, comforting, serene",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Overcoming fear", "Confidence"]
    },
    {
        "id": "Harshad",
        "name": "Harshad (हर्षद)",
        "gender": "Male",
        "persona": "Kind, peaceful, steady friend",
        "languages": ["hi-IN", "en-IN", "hi-en", "mr-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "pa-IN", "bn-IN", "gu-IN"],
        "recommended_for": ["Everyday companion", "Peace"]
    }
]

def get_voice_catalog() -> List[Dict[str, Any]]:
    return VOICES

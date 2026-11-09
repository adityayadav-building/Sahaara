"""Voice session state machine and turn coordinator with instant barge-in cancellation.
States: LISTENING -> HEARING -> THINKING -> SPEAKING
"""
from __future__ import annotations
import asyncio
from enum import Enum
from typing import Optional, List, Dict

class SessionState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    HEARING = "HEARING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"

class VoiceSession:
    def __init__(self, session_id: str, voice: str = "Chetana", speed: float = 0.95, lang: str = "auto") -> None:
        self.session_id = session_id
        self.state: SessionState = SessionState.IDLE
        self.voice = voice
        self.speed = speed
        self.lang = lang
        self.history: List[Dict[str, str]] = []
        self.active_task: Optional[asyncio.Task] = None
        self.last_user_text: str = ""
        self.last_bot_text: str = ""
        self.last_verse_text: str = ""
        self.is_handsfree: bool = False

    def set_state(self, new_state: SessionState) -> None:
        self.state = new_state

    def cancel_active_turn(self) -> bool:
        """Instantly aborts current generation or speech on barge-in."""
        if self.active_task and not self.active_task.done():
            self.active_task.cancel()
            self.active_task = None
            self.state = SessionState.LISTENING
            return True
        return False

    def add_history(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > 20:
            self.history = self.history[-20:]

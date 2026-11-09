"""Text helpers: sentence chunking for TTS, speech-safe cleanup, streaming output cleaner."""
from __future__ import annotations

import re

_SENT_SPLIT = re.compile(r"(?<=[.!?।॥])\s+|\n+")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️‍]")
_HELPLINE_DIGITS = re.compile(r"\b(14416|112)\b")


def spoken_digits(text: str) -> str:
    """Helpline numbers are read digit by digit ('1 4 4 1 6') so TTS does not say 'fourteen thousand'."""
    return _HELPLINE_DIGITS.sub(lambda m: " ".join(m.group(1)), text)


def tts_prepare(text: str) -> str:
    t = re.sub(r"\[S\d+\]", "", text)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*_#`>~|]+", "", t)
    t = _EMOJI.sub("", t)
    t = t.replace("॥", "।")
    t = spoken_digits(t)
    # Strip repeated punctuation that TTS might pronounce as words (e.g. 'comma comma')
    t = re.sub(r"[,]{2,}", ", ", t)
    t = re.sub(r"[\.]{2,}", ". ", t)
    t = re.sub(r"[-]{2,}", " ", t)
    t = re.sub(r"[ \t]+", " ", t).strip()
    # If the text has no word characters / alphanumeric letters, there is nothing meaningful to synthesize
    if not re.search(r"\w", t, re.UNICODE):
        return ""
    # Strip any leading or trailing punctuation
    t = re.sub(r"^[\s,.\-;:!?।॥'\"]+", "", t).strip()
    t = re.sub(r"[\s,]+$", ".", t).strip()
    return t


def split_sentences(text: str) -> list[str]:
    return [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]


def chunk_for_tts(text: str, min_len: int = 60, max_len: int = 260) -> list[str]:
    """Group sentences into chunks of roughly min_len..max_len characters.

    Fewer, larger requests suit accounts limited to one active TTS request at a time.
    """
    pieces: list[str] = []
    for s in split_sentences(text):
        while len(s) > max_len:
            cut = s.rfind(" ", 0, max_len)
            cut = cut if cut > 40 else max_len
            pieces.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            pieces.append(s)
    out: list[str] = []
    buf = ""
    for p in pieces:
        if not buf:
            buf = p
        elif len(buf) < min_len and len(buf) + 1 + len(p) <= max_len:
            buf = f"{buf} {p}"
        else:
            out.append(buf)
            buf = p
    if buf:
        out.append(buf)
    return out


_MARK = re.compile(r"\[S(\d+)\]")
_PARTIAL_MARK = re.compile(r"\[S?\d*$")


class StreamCleaner:
    """Strips <think>…</think> blocks and [S#] markers from a token stream.

    Markers are collected in `cited` (1-based source numbers). Tags that straddle chunk
    boundaries are held back until they can be classified.
    """

    def __init__(self) -> None:
        self.buf = ""
        self.in_think = False
        self.cited: list[int] = []
        self.clean = ""
        self._lead = True  # drop leading whitespace (reasoning models emit blank lines)
        self._skip_ws = False  # after a removed [S#] marker that followed a space, drop the next space

    def _emit(self, s: str, out: list[str]) -> None:
        if self._skip_ws:
            s = s.lstrip()
            if not s:
                return
            self._skip_ws = False
        if self._lead:
            s = s.lstrip()
            if not s:
                return
            self._lead = False
        out.append(s)

    def feed(self, chunk: str) -> str:
        self.buf += chunk
        out: list[str] = []
        while self.buf:
            if self.in_think:
                j = self.buf.find("</think>")
                if j == -1:
                    self.buf = self.buf[-7:]
                    break
                self.buf = self.buf[j + 8:]
                self.in_think = False
                continue
            idxs = [k for k in (self.buf.find("["), self.buf.find("<")) if k != -1]
            if not idxs:
                self._emit(self.buf, out)
                self.buf = ""
                break
            i = min(idxs)
            if i:
                self._emit(self.buf[:i], out)
                self.buf = self.buf[i:]
            if self.buf.startswith("<think>"):
                self.in_think = True
                self.buf = self.buf[7:]
                continue
            m = _MARK.match(self.buf)
            if m:
                self.cited.append(int(m.group(1)))
                self.buf = self.buf[m.end():]
                last = (out[-1] if out else self.clean)[-1:]
                self._skip_ws = last.isspace()
                continue
            if "<think>".startswith(self.buf) or _PARTIAL_MARK.fullmatch(self.buf):
                break  # might still become a tag: wait for more input
            self._emit(self.buf[0], out)
            self.buf = self.buf[1:]
        text = "".join(out)
        self.clean += text
        return text

    def flush(self) -> str:
        tail = "" if self.in_think else self.buf
        self.buf = ""
        if tail and (_PARTIAL_MARK.fullmatch(tail.strip()) or "<think>".startswith(tail.strip())):
            tail = ""
        out: list[str] = []
        if tail:
            self._emit(tail, out)
        text = "".join(out)
        self.clean += text
        self.clean = re.sub(r"\[S?\d*$", "", self.clean).rstrip()
        return text

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import LearningPack
from .summarizer import EducationalSummarizer
from .transcript import read_transcript


class Summarizer(Protocol):
    def build(self, transcript: str, title: str = "Video learning pack", summary_sentences: int = 5, quiz_size: int = 5) -> LearningPack: ...


class LearningService:
    def __init__(self, summarizer: Summarizer | None = None) -> None:
        self.summarizer = summarizer or EducationalSummarizer()

    def from_text(self, transcript: str, title: str = "Video learning pack", quiz_size: int = 5) -> LearningPack:
        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("transcript is required")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title is required")
        if isinstance(quiz_size, bool) or not isinstance(quiz_size, int) or not 1 <= quiz_size <= 10:
            raise ValueError("quiz_size must be between 1 and 10")
        return self.summarizer.build(transcript, title=title, quiz_size=quiz_size)

    def from_transcript(self, path: str | Path, title: str | None = None, quiz_size: int = 5) -> LearningPack:
        path = Path(path)
        return self.from_text(read_transcript(path), title or path.stem.replace("_", " ").title(), quiz_size)

    def from_media(self, path: str | Path, transcriber=None, title: str | None = None, quiz_size: int = 5) -> LearningPack:
        if transcriber is None:
            from .providers import WhisperTranscriber
            transcriber = WhisperTranscriber()
        return self.from_text(transcriber.transcribe(path), title or Path(path).stem.replace("_", " ").title(), quiz_size)

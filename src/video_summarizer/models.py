from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    prompt: str
    choices: tuple[str, ...]
    answer_index: int
    explanation: str
    evidence: str

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("answer_index")
        return data


@dataclass(frozen=True)
class LearningPack:
    title: str
    summary: str
    key_concepts: tuple[str, ...]
    study_notes: tuple[str, ...]
    quiz: tuple[QuizQuestion, ...]
    word_count: int
    estimated_read_minutes: int
    mode: str = "local-extractive"

    def to_dict(self, include_answers: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if not include_answers:
            data["quiz"] = [question.public_dict() for question in self.quiz]
        return data

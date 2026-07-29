from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from ..models import LearningPack, QuizQuestion


class WhisperTranscriber:
    def __init__(self, model: str = "base", device: str = "cpu", compute_type: str = "int8") -> None:
        self.model, self.device, self.compute_type = model, device, compute_type

    def transcribe(self, media: str | Path) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Install faster-whisper for audio/video transcription") from exc
        model = WhisperModel(self.model, device=self.device, compute_type=self.compute_type)
        segments, _ = model.transcribe(str(media), vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip())


class MixtralSummarizer:
    """Optional OpenAI-compatible endpoint for a hosted/local Mixtral deployment."""

    def __init__(self, base_url: str, api_key: str, model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1") -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai for the OpenAI-compatible Mixtral adapter") from exc
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def build(self, transcript: str, title: str = "Video learning pack", summary_sentences: int = 5, quiz_size: int = 5) -> LearningPack:
        if len(transcript.split()) < 20:
            raise ValueError("transcript must contain at least 20 words")
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Return JSON with summary, key_concepts, study_notes, and quiz. Each quiz item needs prompt, choices, answer_index, explanation, and an exact evidence quote from the transcript. Use only the transcript."},
                {"role": "user", "content": json.dumps({"title": title, "summary_sentences": summary_sentences, "quiz_size": quiz_size, "transcript": transcript})},
            ],
            temperature=0.2,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return self._validated_pack(payload, transcript, title, quiz_size)

    def _validated_pack(self, payload: object, transcript: str, title: str, quiz_size: int) -> LearningPack:
        if not isinstance(payload, dict):
            raise ValueError("Mixtral returned a non-object response")

        def required_text(key: str, row: dict[str, Any] | None = None) -> str:
            source = row if row is not None else payload
            value = source.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Mixtral field {key!r} must be a non-empty string")
            return value.strip()

        def string_list(key: str) -> tuple[str, ...]:
            value = payload.get(key)
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(f"Mixtral field {key!r} must be a non-empty string list")
            return tuple(dict.fromkeys(item.strip() for item in value))

        quiz_rows = payload.get("quiz")
        if not isinstance(quiz_rows, list) or not quiz_rows:
            raise ValueError("Mixtral must return at least one quiz question")
        normalized_transcript = re.sub(r"\s+", " ", transcript).casefold()
        questions: list[QuizQuestion] = []
        for index, row in enumerate(quiz_rows[:quiz_size], 1):
            if not isinstance(row, dict):
                raise ValueError("Mixtral quiz items must be objects")
            choices = row.get("choices")
            answer_index = row.get("answer_index")
            if not isinstance(choices, list) or not 2 <= len(choices) <= 6 or any(not isinstance(choice, str) or not choice.strip() for choice in choices):
                raise ValueError("Mixtral quiz choices must contain two to six non-empty strings")
            if isinstance(answer_index, bool) or not isinstance(answer_index, int) or not 0 <= answer_index < len(choices):
                raise ValueError("Mixtral answer_index is outside the choices")
            evidence = required_text("evidence", row)
            if re.sub(r"\s+", " ", evidence).casefold() not in normalized_transcript:
                raise ValueError("Mixtral quiz evidence must be an exact transcript quote")
            questions.append(QuizQuestion(
                id=f"q{index}",
                prompt=required_text("prompt", row),
                choices=tuple(choice.strip() for choice in choices),
                answer_index=answer_index,
                explanation=required_text("explanation", row),
                evidence=evidence,
            ))
        summary = required_text("summary")
        word_count = len(transcript.split())
        return LearningPack(
            title=title.strip() or "Video learning pack",
            summary=summary,
            key_concepts=string_list("key_concepts"),
            study_notes=string_list("study_notes"),
            quiz=tuple(questions),
            word_count=word_count,
            estimated_read_minutes=max(1, math.ceil(len(summary.split()) / 220)),
            mode=f"mixtral:{self.model}",
        )

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from .models import LearningPack, QuizQuestion

STOPWORDS = {
    "about", "after", "again", "against", "also", "among", "and", "are", "because", "been", "before", "being", "between", "both", "but", "can", "could", "does", "each", "for", "from", "have", "into", "its", "more", "most", "not", "other", "our", "out", "over", "same", "should", "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those", "through", "under", "very", "was", "were", "what", "when", "where", "which", "while", "will", "with", "would", "you", "your"
}


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if len(part.split()) >= 4]


def tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text) if token.lower() not in STOPWORDS]


class EducationalSummarizer:
    """Frequency-weighted extractive summarizer and evidence-backed quiz maker."""

    def build(self, transcript: str, title: str = "Video learning pack", summary_sentences: int = 5, quiz_size: int = 5) -> LearningPack:
        all_sentences = sentences(transcript)
        if len(all_sentences) < 2:
            raise ValueError("transcript needs at least two complete sentences")
        counts = Counter(tokens(transcript))
        if not counts:
            raise ValueError("transcript does not contain enough meaningful language")
        max_count = max(counts.values())
        weights = {word: count / max_count for word, count in counts.items()}
        scored: list[tuple[float, int, str]] = []
        for index, sentence in enumerate(all_sentences):
            sentence_tokens = tokens(sentence)
            score = sum(weights.get(token, 0) for token in sentence_tokens) / math.sqrt(max(1, len(sentence_tokens)))
            # Give openings/conclusions a slight pedagogical boost.
            position = 0.12 if index in {0, len(all_sentences) - 1} else 0
            scored.append((score + position, index, sentence))
        selected = sorted(sorted(scored, reverse=True)[: min(summary_sentences, len(scored))], key=lambda row: row[1])
        summary = " ".join(row[2] for row in selected)
        concepts = tuple(word for word, _ in counts.most_common(12))
        notes = tuple(self._note(sentence) for _, _, sentence in sorted(scored, reverse=True)[:8])
        quiz = self._quiz(all_sentences, concepts, quiz_size)
        word_count = len(transcript.split())
        return LearningPack(
            title=title,
            summary=summary,
            key_concepts=concepts,
            study_notes=notes,
            quiz=tuple(quiz),
            word_count=word_count,
            estimated_read_minutes=max(1, math.ceil(len(summary.split()) / 220)),
        )

    @staticmethod
    def _note(sentence: str) -> str:
        return sentence[0].upper() + sentence[1:].rstrip() + ("" if sentence.endswith((".", "!", "?")) else ".")

    def _quiz(self, all_sentences: list[str], concepts: tuple[str, ...], size: int) -> list[QuizQuestion]:
        questions: list[QuizQuestion] = []
        used: set[str] = set()
        concept_pool = list(concepts)
        for sentence in all_sentences:
            candidates = [word for word in tokens(sentence) if word in concept_pool and word not in used and len(word) >= 5]
            if not candidates:
                continue
            answer = max(candidates, key=lambda word: (concept_pool.index(word) * -1, len(word)))
            distractors = [word for word in concept_pool if word != answer and word not in sentence.lower() and len(word) >= 4][:3]
            if len(distractors) < 3:
                continue
            masked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1, flags=re.IGNORECASE)
            choices = [answer, *distractors]
            seed = int(hashlib.sha1(sentence.encode()).hexdigest()[:8], 16)
            shift = seed % len(choices)
            choices = choices[shift:] + choices[:shift]
            answer_index = choices.index(answer)
            questions.append(
                QuizQuestion(
                    id=f"q{len(questions) + 1}",
                    prompt=f"Complete the idea from the lesson: {masked}",
                    choices=tuple(choice.title() for choice in choices),
                    answer_index=answer_index,
                    explanation=f"The transcript uses “{answer}” in this statement.",
                    evidence=sentence,
                )
            )
            used.add(answer)
            if len(questions) >= size:
                break
        return questions


def grade(pack: LearningPack, answers: dict[str, int]) -> dict[str, object]:
    details = []
    score = 0
    for question in pack.quiz:
        chosen = answers.get(question.id)
        correct = chosen == question.answer_index
        score += int(correct)
        details.append({"id": question.id, "correct": correct, "answer_index": question.answer_index, "explanation": question.explanation})
    return {"score": score, "total": len(pack.quiz), "percent": round(score / max(1, len(pack.quiz)) * 100), "details": details}

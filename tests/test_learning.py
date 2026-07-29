import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from video_summarizer.feedback import FeedbackRepository
from video_summarizer.service import LearningService
from video_summarizer.summarizer import grade
from video_summarizer.transcript import read_transcript


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.sample = Path(__file__).resolve().parents[1] / "data" / "sample_lesson.txt"

    def test_end_to_end_pack(self):
        pack = LearningService().from_transcript(self.sample, quiz_size=4)
        self.assertTrue(pack.summary)
        self.assertGreaterEqual(len(pack.quiz), 3)
        self.assertIn("regression", pack.key_concepts)
        json.dumps(pack.to_dict())

    def test_grading(self):
        pack = LearningService().from_transcript(self.sample, quiz_size=3)
        answers = {question.id: question.answer_index for question in pack.quiz}
        outcome = grade(pack, answers)
        self.assertEqual(outcome["score"], outcome["total"])
        self.assertEqual(outcome["percent"], 100)

    def test_feedback_sqlite_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = FeedbackRepository(Path(folder) / "feedback.db")
            identifier = repo.add("session-1", 5, "Useful", 80)
            self.assertGreater(identifier, 0)
            self.assertEqual(repo.summary(), {"count": 1, "average_rating": 5.0})
            repo.save_pack("session-1", {"title": "Private answer key", "quiz": [{"answer_index": 2}]})
            self.assertEqual(repo.load_pack("session-1")["quiz"][0]["answer_index"], 2)
            self.assertIsNone(repo.load_pack("missing"))

    def test_short_transcript_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "short.txt"
            path.write_text("Too short.", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_transcript(path)

    def test_selected_summarizer_is_invoked(self):
        class FakeSummarizer:
            def __init__(self):
                self.calls = []

            def build(self, transcript, title="Video learning pack", summary_sentences=5, quiz_size=5):
                self.calls.append((transcript, title, quiz_size))
                from video_summarizer.summarizer import EducationalSummarizer
                return EducationalSummarizer().build(transcript, title=title, summary_sentences=summary_sentences, quiz_size=quiz_size)

        provider = FakeSummarizer()
        pack = LearningService(provider).from_transcript(self.sample, title="Provider test", quiz_size=2)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0][1], "Provider test")
        self.assertTrue(pack.summary)


if __name__ == "__main__":
    unittest.main()

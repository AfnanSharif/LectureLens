"""Educational video summaries, quizzes, and feedback."""

from .models import LearningPack, QuizQuestion
from .service import LearningService

__all__ = ["LearningPack", "QuizQuestion", "LearningService"]
__version__ = "1.0.0"

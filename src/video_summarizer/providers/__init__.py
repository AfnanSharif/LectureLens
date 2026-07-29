import os

from .models import MixtralSummarizer, WhisperTranscriber

from ..summarizer import EducationalSummarizer

__all__ = ["MixtralSummarizer", "WhisperTranscriber"]


def create_summarizer(name: str | None = None):
    selected = (name or os.getenv("SUMMARY_PROVIDER", "local")).strip().lower()
    if selected in {"", "local", "extractive"}:
        return EducationalSummarizer()
    if selected == "mixtral":
        base_url = os.getenv("MIXTRAL_BASE_URL", "").strip()
        if not base_url:
            raise ValueError("MIXTRAL_BASE_URL is required for Mixtral mode")
        return MixtralSummarizer(
            base_url,
            os.getenv("MIXTRAL_API_KEY", "not-required") or "not-required",
            os.getenv("MIXTRAL_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
        )
    raise ValueError("SUMMARY_PROVIDER must be local or mixtral")


__all__.append("create_summarizer")

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv

load_dotenv()

from video_summarizer.feedback import FeedbackRepository
from video_summarizer.providers import create_summarizer
from video_summarizer.service import LearningService
from video_summarizer.summarizer import grade

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_MB", "200")) * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
feedback = FeedbackRepository(os.getenv("FEEDBACK_DB", str(ROOT / "instance" / "feedback.db")))
ALLOWED = {".txt", ".srt", ".vtt", ".json", ".mp3", ".wav", ".m4a", ".mp4", ".mov"}


def _session_id() -> str:
    if "id" not in session:
        session["id"] = secrets.token_urlsafe(16)
    return session["id"]


def _pack_from_upload():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        raise ValueError("Choose a transcript or media file")
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("Unsupported file type")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        upload.save(handle)
        temp_path = Path(handle.name)
    try:
        questions = max(1, min(10, int(request.form.get("questions", 5))))
        title = request.form.get("title") or Path(upload.filename).stem.replace("_", " ").title()
        provider_name = request.form.get("provider", os.getenv("SUMMARY_PROVIDER", "local"))
        service = LearningService(create_summarizer(provider_name))
        if suffix in {".mp3", ".wav", ".m4a", ".mp4", ".mov"}:
            from video_summarizer.providers import WhisperTranscriber
            transcriber = WhisperTranscriber(
                model=os.getenv("WHISPER_MODEL", "base"),
                device=os.getenv("WHISPER_DEVICE", "cpu"),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
            )
            return service.from_media(temp_path, transcriber=transcriber, title=title, quiz_size=questions)
        return service.from_transcript(temp_path, title=title, quiz_size=questions)
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/")
def index():
    return render_template("index.html", stats=feedback.summary(), summary_provider=os.getenv("SUMMARY_PROVIDER", "local"))


@app.post("/analyze")
def analyze():
    try:
        pack = _pack_from_upload()
        identifier = _session_id()
        feedback.save_pack(identifier, pack.to_dict())
        return render_template("result.html", pack=pack, session_id=identifier)
    except (ValueError, RuntimeError) as exc:
        return render_template("index.html", error=str(exc), stats=feedback.summary(), summary_provider=os.getenv("SUMMARY_PROVIDER", "local")), 400


@app.post("/grade")
def grade_quiz():
    from video_summarizer.models import LearningPack, QuizQuestion

    data = feedback.load_pack(_session_id())
    if not data:
        return jsonify({"error": "No active learning pack"}), 400
    quiz = tuple(QuizQuestion(**{**q, "choices": tuple(q["choices"])}) for q in data["quiz"])
    pack = LearningPack(**{**data, "key_concepts": tuple(data["key_concepts"]), "study_notes": tuple(data["study_notes"]), "quiz": quiz})
    answers = {key: int(value) for key, value in request.form.items() if key.startswith("q") and value.isdigit()}
    outcome = grade(pack, answers)
    session["quiz_score"] = outcome["percent"]
    return jsonify(outcome)


@app.post("/feedback")
def save_feedback():
    try:
        identifier = feedback.add(_session_id(), int(request.form.get("rating", 0)), request.form.get("comment", ""), session.get("quiz_score"))
        return jsonify({"ok": True, "id": identifier})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/v1/analyze")
def api_analyze():
    try:
        pack = _pack_from_upload()
        feedback.save_pack(_session_id(), pack.to_dict())
        return jsonify(pack.to_dict(include_answers=False))
    except (ValueError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Upload exceeds MAX_UPLOAD_MB"}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")

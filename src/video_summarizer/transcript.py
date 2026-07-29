from __future__ import annotations

import json
import re
from pathlib import Path


def _clean_caption_text(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if not stripped or stripped.isdigit() or stripped.upper() == "WEBVTT" or " --> " in stripped:
            continue
        stripped = re.sub(r"<[^>]+>", "", stripped)
        if stripped and (not lines or stripped != lines[-1]):
            lines.append(stripped)
    return " ".join(lines)


def read_transcript(path: str | Path) -> str:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
        rows = payload.get("segments", payload) if isinstance(payload, dict) else payload
        if isinstance(rows, list):
            text = " ".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in rows)
        else:
            raise ValueError("JSON transcript must contain a list of segments")
    elif suffix in {".srt", ".vtt"}:
        text = _clean_caption_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text.split()) < 20:
        raise ValueError("transcript must contain at least 20 words")
    return text

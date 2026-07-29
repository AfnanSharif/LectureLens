from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .providers import WhisperTranscriber, create_summarizer
from .service import LearningService


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        load_dotenv()

    parser = argparse.ArgumentParser(description="Build an educational summary and quiz")
    parser.add_argument("input", type=Path)
    parser.add_argument("--media", action="store_true", help="Transcribe with faster-whisper")
    parser.add_argument("--title")
    parser.add_argument("--questions", type=int, default=5, choices=range(1, 11))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--provider", choices=["local", "mixtral"], default=os.getenv("SUMMARY_PROVIDER", "local"))
    args = parser.parse_args(argv)
    service = LearningService(create_summarizer(args.provider))
    if args.media:
        transcriber = WhisperTranscriber(
            model=os.getenv("WHISPER_MODEL", "base"),
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        )
        pack = service.from_media(args.input, transcriber=transcriber, title=args.title, quiz_size=args.questions)
    else:
        pack = service.from_transcript(args.input, title=args.title, quiz_size=args.questions)
    payload = json.dumps(pack.to_dict(), indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

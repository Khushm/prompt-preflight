"""Command-line interface for inspecting prompts outside Codex."""

from __future__ import annotations

import argparse
import json
import sys

from .analyzer import analyze_prompt
from .hook import clarification_message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-preflight",
        description="Check a prompt locally before spending a model turn.",
    )
    parser.add_argument("prompt", nargs="*", help="Prompt text; reads stdin when omitted")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit structured JSON")
    parser.add_argument("--threshold", type=int, default=45, help="Clarification threshold (default: 45)")
    parser.add_argument("--max-questions", type=int, default=3, help="Maximum questions to ask")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prompt = " ".join(args.prompt).strip() if args.prompt else sys.stdin.read().strip()
    analysis = analyze_prompt(
        prompt,
        threshold=max(0, min(100, args.threshold)),
        max_questions=max(1, min(5, args.max_questions)),
    )
    if args.as_json:
        print(json.dumps(analysis.to_dict(), indent=2))
    elif analysis.should_clarify:
        print(clarification_message(analysis))
    else:
        print(f"Clear to send (clarification score {analysis.score}/100).")
    return 2 if analysis.should_clarify else 0


if __name__ == "__main__":
    raise SystemExit(main())

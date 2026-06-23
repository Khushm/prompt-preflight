#!/usr/bin/env python3
"""Benchmark Prompt Preflight against a fixed set of vague prompts.

The benchmark is intentionally local and deterministic: no model calls, no API
keys, no network. It is meant to catch regressions in Prompt Preflight's ability
to pause prompts that are likely to create expensive clarification loops.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prompt_preflight.analyzer import analyze_prompt  # noqa: E402


BENCHMARK_VERSION = "2026-06-22"

VAGUE_PROMPTS: tuple[str, ...] = (
    "Fix it",
    "Make it better",
    "Improve the dashboard",
    "Clean up the code",
    "Optimize the database",
    "Deploy this to production",
    "Build a todo app",
    "Create an admin panel",
    "Implement auth",
    "Add better payments",
    "Rewrite the backend",
    "Refactor everything",
    "Modernize the UI",
    "Make the app faster",
    "Fix the login bug",
    "Update the API",
    "Upgrade the whole project",
    "Migrate the database",
    "Remove the bad code",
    "Rename things properly",
    "Replace this with a better version",
    "Integrate Stripe properly",
    "Build a chat feature",
    "Create a reporting system",
    "Design a better homepage",
    "Generate better documentation",
    "Polish the landing page",
    "Make onboarding user-friendly",
    "Improve error handling",
    "Fix the flaky tests",
    "Optimize performance",
    "Deploy the app",
    "Build a CRM",
    "Create a mobile app",
    "Implement permissions",
    "Add notifications everywhere",
    "Rewrite the frontend",
    "Refactor the auth flow",
    "Modernize the entire codebase",
    "Make the API robust",
    "Fix checkout",
    "Update the schema",
    "Upgrade dependencies",
    "Migrate users",
    "Remove unused stuff",
    "Rename this module",
    "Replace the old system",
    "Integrate analytics",
    "Build a settings page",
    "Create a billing system",
    "Design the dashboard",
    "Generate a nice report",
    "Polish the UI",
    "Make search better",
    "Improve scalability",
    "Fix production issue",
    "Optimize costs",
    "Deploy backend to prod",
    "Build an image generation API",
    "Create an image processing app",
    "Implement caching",
    "Add security everywhere",
    "Rewrite the whole repo",
    "Refactor database layer",
    "Modernize authentication",
    "Make forms nicer",
    "Fix accessibility",
    "Update permissions",
    "Upgrade infrastructure",
    "Migrate billing",
    "Remove security risk",
    "Rename bad variables",
    "Replace auth",
    "Integrate OAuth",
    "Build a workflow",
    "Create a plugin",
    "Design a better settings screen",
    "Generate more tests",
    "Polish docs",
    "Make deployment safer",
    "Improve this component",
    "Fix this bug",
    "Optimize this query",
    "Deploy everything",
    "Build the full app",
    "Create a good API",
    "Implement the feature",
    "Add robust validation",
    "Rewrite all tests",
    "Refactor this",
    "Create a car image",
    "Generate a logo",
    "Draw a cat",
    "Illustrate a hero image",
    "Make a product photo",
    "Paint a portrait",
    "Render a house",
    "Create a poster",
    "Generate an icon",
    "Draw a landscape",
)


def _rate(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def _average(values: list[int]) -> float:
    return round(statistics.fmean(values), 2) if values else 0.0


def run_benchmark(
    prompts: tuple[str, ...] = VAGUE_PROMPTS,
    *,
    threshold: int = 45,
    max_questions: int = 3,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    by_intent: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "blocked": 0})

    for index, prompt in enumerate(prompts, start=1):
        analysis = analyze_prompt(
            prompt,
            threshold=max(0, min(100, threshold)),
            max_questions=max(1, min(5, max_questions)),
        )
        by_intent[analysis.intent]["total"] += 1
        if analysis.should_clarify:
            by_intent[analysis.intent]["blocked"] += 1
        rows.append(
            {
                "number": index,
                "prompt": prompt,
                "blocked": analysis.should_clarify,
                "intent": analysis.intent,
                "score": analysis.score,
                "ambiguity": analysis.ambiguity,
                "impact": analysis.impact,
                "reasons": list(analysis.reasons),
                "questions": list(analysis.questions),
                "suggested_prompt": analysis.suggested_prompt,
            }
        )

    total = len(rows)
    blocked = sum(1 for row in rows if row["blocked"])
    missed = [row for row in rows if not row["blocked"]]

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "threshold": max(0, min(100, threshold)),
        "max_questions": max(1, min(5, max_questions)),
        "total_prompts": total,
        "blocked_prompts": blocked,
        "missed_prompts": len(missed),
        "block_rate": round(_rate(blocked, total), 4),
        "average_score": _average([row["score"] for row in rows]),
        "average_ambiguity": _average([row["ambiguity"] for row in rows]),
        "average_impact": _average([row["impact"] for row in rows]),
        "by_intent": {
            intent: {
                **counts,
                "block_rate": round(_rate(counts["blocked"], counts["total"]), 4),
            }
            for intent, counts in sorted(by_intent.items())
        },
        "missed": missed,
        "results": rows,
    }


def print_summary(summary: dict[str, Any], *, show_missed: int = 10) -> None:
    block_rate_percent = summary["block_rate"] * 100
    print("Prompt Preflight vague-prompt benchmark")
    print(f"Version: {summary['benchmark_version']}")
    print(f"Threshold: {summary['threshold']}")
    print(f"Prompts: {summary['total_prompts']}")
    print(f"Blocked: {summary['blocked_prompts']} ({block_rate_percent:.1f}%)")
    print(f"Missed: {summary['missed_prompts']}")
    print(f"Average score: {summary['average_score']}/100")
    print(f"Average ambiguity: {summary['average_ambiguity']}/100")
    print(f"Average impact: {summary['average_impact']}/100")
    print()
    print("By intent:")
    for intent, counts in summary["by_intent"].items():
        rate_percent = counts["block_rate"] * 100
        print(f"- {intent}: {counts['blocked']}/{counts['total']} blocked ({rate_percent:.1f}%)")

    if summary["missed"] and show_missed:
        print()
        print(f"Missed prompts, first {min(show_missed, len(summary['missed']))}:")
        for row in summary["missed"][:show_missed]:
            print(
                f"- #{row['number']} {row['prompt']!r} "
                f"(intent={row['intent']}, score={row['score']}, "
                f"ambiguity={row['ambiguity']}, impact={row['impact']})"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the fixed 100-prompt vague-prompt benchmark.",
    )
    parser.add_argument("--threshold", type=int, default=45, help="Clarification threshold")
    parser.add_argument("--max-questions", type=int, default=3, help="Maximum questions per prompt")
    parser.add_argument(
        "--min-block-rate",
        type=float,
        default=0.90,
        help="Fail when the vague-prompt block rate falls below this value",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for complete benchmark results as JSON",
    )
    parser.add_argument(
        "--show-missed",
        type=int,
        default=10,
        help="Number of missed prompts to show in the terminal summary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_benchmark(threshold=args.threshold, max_questions=args.max_questions)
    print_summary(summary, show_missed=max(0, args.show_missed))

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print()
        print(f"Wrote JSON results to {args.json_output}")

    if summary["block_rate"] < args.min_block_rate:
        print()
        print(
            "Benchmark failed: block rate "
            f"{summary['block_rate']:.2%} is below minimum {args.min_block_rate:.2%}."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

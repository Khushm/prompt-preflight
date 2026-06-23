"""Prompt Preflight: a local, deterministic prompt clarity gate."""

from .analyzer import Analysis, analyze_prompt, classify_intent, suggest_rewrite

__all__ = ["Analysis", "analyze_prompt", "classify_intent", "suggest_rewrite"]
__version__ = "0.3.0"

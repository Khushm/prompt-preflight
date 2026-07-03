import re
from pathlib import Path

content = Path('README.md').read_text()

old_config = """{
  "enabled": true,
  "mode": "block",
  "threshold": 45,
  "max_questions": 3,
  "telemetry": {
    "enabled": false,
    "path": ".prompt-preflight-telemetry.jsonl"
  }
}"""

new_config = """{
  "enabled": true,
  "mode": "block",
  "threshold": 45,
  "max_questions": 3,
  "checks": {
    "clarity": "nudge",
    "context": "nudge",
    "output_contract": "nudge",
    "template_contract": "block",
    "risk": "block",
    "plan_first": "block",
    "privacy": "block"
  },
  "severity_thresholds": {
    "block": "high",
    "nudge": "medium"
  },
  "telemetry": {
    "enabled": false,
    "path": ".prompt-preflight-telemetry.jsonl"
  }
}"""
content = content.replace(old_config, new_config)

old_list = """- `block`: stop the vague submission before model work.
- `nudge`: allow the turn while instructing the host assistant to clarify first.
- `threshold`: raise it to interrupt less often.
- `max_questions`: limit clarification questions from 1 to 5.
- `enabled`: disable Prompt Preflight for a project.
- `telemetry`: optional local-only counts; disabled by default."""

new_list = """- `mode`: legacy global behavior (block or nudge). Backward compatible if `checks` is missing.
- `threshold`: legacy global numeric threshold.
- `checks`: per-check policy ("block", "nudge", "disable", "off"). Evaluated before `mode`.
- `severity_thresholds`: defines the severity ("low", "medium", "high") needed to trigger a "block" or "nudge" per check.
- `max_questions`: limit clarification questions from 1 to 5.
- `enabled`: disable Prompt Preflight for a project.
- `telemetry`: optional local-only counts; disabled by default.

### Per-Check Safe Defaults
If a specific check is not explicitly set in `checks`, Prompt Preflight uses these safe defaults:
- `privacy`, `risk`, and `plan_first`: **block**
- `clarity`, `context`, `output_contract`, and `template_contract`: **nudge** (or the global `mode` if configured)"""

content = content.replace(old_list, new_list)

Path('README.md').write_text(content)
print("Done patching README")

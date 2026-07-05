import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# We need to add Config to the import
content = re.sub(
    r"from \.templates import questions_for_missing_fields, validate_structured_prompt",
    "from .config import Config\nfrom .templates import questions_for_missing_fields, validate_structured_prompt",
    content
)

# We need to add config parameter to analyze_prompt
content = re.sub(
    r"def analyze_prompt\(\n    prompt: str,\n    \*,\n    threshold: int = 45,",
    "def analyze_prompt(\n    prompt: str,\n    *,\n    config: Config | None = None,\n    threshold: int = 45,",
    content
)

content = re.sub(
    r"    max_questions: int = 3,\n    cwd: str \| Path \| None = None,\n    attachments: list\[str\] \| None = None,\n\) -> Analysis:",
    "    max_questions: int = 3,\n    cwd: str | Path | None = None,\n    attachments: list[str] | None = None,\n) -> Analysis:",
    content
)

# Inject _is_enabled
# After `is_action = bool(action_matches)` (around line 572)
insertion_point = "    is_action = bool(action_matches)\n"
helper_func = """
    def _is_enabled(cat: str) -> bool:
        return config.policy_for(cat) != "disable" if config else True
"""
content = content.replace(insertion_point, insertion_point + helper_func)

# Replace the specific `if` statements.
replacements = [
    (r"if vague_terms:", r"if vague_terms and _is_enabled('clarity'):"),
    (r"if is_action and not has_anchor and not is_image_request and not is_content_request:", 
     r"if is_action and not has_anchor and not is_image_request and not is_content_request and _is_enabled('context'):"),
    (r"if \(\n        is_action\n        and not has_format\n        and not has_anchor\n        and not is_image_request\n        and not is_content_request\n        and \(vague_terms or len\(words\) <= 10 or has_broad_scope\)\n    \):",
     r"if (\n        is_action\n        and not has_format\n        and not has_anchor\n        and not is_image_request\n        and not is_content_request\n        and (vague_terms or len(words) <= 10 or has_broad_scope)\n        and _is_enabled('output_contract')\n    ):"),
    (r"if references_attachment and not has_anchor and len\(words\) <= 6 and not provided_attachments:",
     r"if references_attachment and not has_anchor and len(words) <= 6 and not provided_attachments and _is_enabled('context'):"),
    (r"if missing_files:", r"if missing_files and _is_enabled('context'):"),
    (r"if requires_plan_first:", r"if requires_plan_first and (_is_enabled('risk') or _is_enabled('plan_first')):"),
    
    # Image checks
    (r"if not has_subject_detail:", r"if not has_subject_detail and _is_enabled('context'):"),
    (r"if not has_image_style:", r"if not has_image_style and _is_enabled('output_contract'):"),
    (r"if not has_image_scene or not has_image_format:", r"if (not has_image_scene or not has_image_format) and _is_enabled('output_contract'):"),
    
    # Writing checks
    (r"if not has_audience:", r"if not has_audience and _is_enabled('context'):"),
    (r"if not has_goal or not has_source:", r"if (not has_goal or not has_source) and _is_enabled('context'):"),
    (r"if not has_tone_or_length:", r"if not has_tone_or_length and _is_enabled('output_contract'):"),
    
    # Research checks
    (r"if not has_goal:", r"if not has_goal and _is_enabled('context'):"),
    (r"if not has_sources:", r"if not has_sources and _is_enabled('context'):"),
    (r"if not has_criteria:", r"if not has_criteria and _is_enabled('output_contract'):"),
    
    # Data checks
    (r"if not has_dataset:", r"if not has_dataset and _is_enabled('context'):"),
    (r"if not has_metric:", r"if not has_metric and _is_enabled('context'):"),
    (r"if not has_output:", r"if not has_output and _is_enabled('output_contract'):"),
    
    # Presentation checks
    (r"if not has_audience:", r"if not has_audience and _is_enabled('context'):"),
    (r"if not has_goal or not has_story:", r"if (not has_goal or not has_story) and _is_enabled('context'):"),
    (r"if not has_deck_format:", r"if not has_deck_format and _is_enabled('output_contract'):"),
    
    # General risk checks
    (r"if has_broad_scope and not is_image_request and not is_content_request:", r"if has_broad_scope and not is_image_request and not is_content_request and _is_enabled('risk'):"),
    (r"if is_action and not is_image_request and not is_content_request and \(has_broad_scope or has_high_impact\) and not has_constraint:", r"if is_action and not is_image_request and not is_content_request and (has_broad_scope or has_high_impact) and not has_constraint and _is_enabled('risk'):"),
    (r"if is_action and not is_image_request and not is_content_request and \(has_broad_scope or has_high_impact or vague_terms\) and not has_success:", r"if is_action and not is_image_request and not is_content_request and (has_broad_scope or has_high_impact or vague_terms) and not has_success and _is_enabled('output_contract'):"),
]

for old, new in replacements:
    content = re.sub(old, new, content)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done patching analyzer.py")

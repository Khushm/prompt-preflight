import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# 1. Add `decision` to Analysis
content = re.sub(
    r"    severity: str = \"low\"\n    redacted_prompt: str \| None = None",
    "    severity: str = \"low\"\n    redacted_prompt: str | None = None\n    decision: str = \"allow\"",
    content
)

# 2. Fix template contract check
old_template = """    template_validation = validate_structured_prompt(raw_prompt, intent)
    if template_validation and template_validation.missing_required:"""
new_template = """    template_validation = validate_structured_prompt(raw_prompt, intent)
    if template_validation and template_validation.missing_required and (_is_enabled("template_contract") or _is_enabled("output_contract")):"""
content = content.replace(old_template, new_template)

# 3. Fix privacy check
old_privacy = """    secret_findings = sensitive_findings(text)
    redacted_text = redact_sensitive(text) if secret_findings else None
    if secret_findings:"""
new_privacy = """    secret_findings = sensitive_findings(text)
    redacted_text = redact_sensitive(text) if secret_findings else None
    if secret_findings and (not config or config.policy_for("privacy") != "disable"):"""
content = content.replace(old_privacy, new_privacy)

# 4. Add the decision engine logic at the end.
old_end = """    severity = "low"
    if should_clarify:
        if "risk" in checks or impact >= 80:
            severity = "high"
        elif score >= 55:
            severity = "medium"

    return Analysis("""

new_end = """    severity = "low"
    if should_clarify:
        if "risk" in checks or impact >= 80:
            severity = "high"
        elif score >= 55:
            severity = "medium"

    # Per-check decision engine
    decision = "allow"
    if should_clarify and config:
        sev_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 1)
        
        has_block = False
        has_nudge = False
        for chk in _unique(checks):
            policy = config.policy_for(chk)
            
            block_thresh = config.threshold_for("block")
            block_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(block_thresh, 3)
            
            nudge_thresh = config.threshold_for("nudge")
            nudge_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(nudge_thresh, 2)

            if policy == "block" and sev_val >= block_thresh_val:
                has_block = True
            elif policy == "nudge" and sev_val >= nudge_thresh_val:
                has_nudge = True

        if has_block:
            decision = "block"
        elif has_nudge:
            decision = "nudge"
        else:
            decision = "allow"
            should_clarify = False
            
    elif should_clarify and not config:
        # Legacy fallback if no Config passed
        decision = "block"
        
    return Analysis("""
content = content.replace(old_end, new_end)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done patching analyzer.py again")

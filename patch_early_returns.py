import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# Fix privacy early return to set decision="block" (since if we get here, it wasn't disabled)
content = re.sub(
    r"            severity=\"high\",\n            redacted_prompt=redacted_text,\n        \)",
    "            severity=\"high\",\n            redacted_prompt=redacted_text,\n            decision=\"block\",\n        )",
    content
)

# Fix bypassed early return
content = re.sub(
    r"            bypassed=True,\n        \)",
    "            bypassed=True,\n            decision=\"allow\",\n        )",
    content
)

# Fix template_contract early return to compute decision
old_template_ret = """            severity="medium" if len(missing) >= 2 or score >= threshold else "low",
            redacted_prompt=redacted_text,
        )"""

new_template_ret = """            severity="medium" if len(missing) >= 2 or score >= threshold else "low",
            redacted_prompt=redacted_text,
        )
        
        # Apply decision logic for template_contract
        if config:
            sev_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(ret.severity, 1)
            has_block = False
            has_nudge = False
            for chk in ret.checks:
                policy = config.policy_for(chk)
                block_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(config.threshold_for("block"), 3)
                nudge_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(config.threshold_for("nudge"), 2)
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
                ret = Analysis(**{**ret.to_dict(), "should_clarify": False, "decision": decision})
            if decision != "allow":
                ret = Analysis(**{**ret.to_dict(), "decision": decision})
            return ret
        else:
            return Analysis(**{**ret.to_dict(), "decision": "block"})"""

# wait, `ret` doesn't exist yet, I need to capture the `Analysis` in `ret`.
old_template_full = """        return Analysis(
            text,
            True,
            score,
            ambiguity,
            impact,
            (
                "structured prompt is missing required fields: "
                + ", ".join(missing),
            ),
            questions_for_missing_fields(missing)[: max(1, max_questions)],
            intent=intent,
            suggested_prompt=template_validation.suggested_template,
            checks=("template_contract", "output_contract"),
            severity="medium" if len(missing) >= 2 or score >= threshold else "low",
            redacted_prompt=redacted_text,
        )"""

new_template_full = """        ret = Analysis(
            text,
            True,
            score,
            ambiguity,
            impact,
            (
                "structured prompt is missing required fields: "
                + ", ".join(missing),
            ),
            questions_for_missing_fields(missing)[: max(1, max_questions)],
            intent=intent,
            suggested_prompt=template_validation.suggested_template,
            checks=("template_contract", "output_contract"),
            severity="medium" if len(missing) >= 2 or score >= threshold else "low",
            redacted_prompt=redacted_text,
        )
        if config:
            sev_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(ret.severity, 1)
            has_block = False
            has_nudge = False
            for chk in ret.checks:
                policy = config.policy_for(chk)
                block_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(config.threshold_for("block"), 3)
                nudge_thresh_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(config.threshold_for("nudge"), 2)
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
            
            # Since Analysis is frozen, we reconstruct it
            d = ret.to_dict()
            if decision == "allow":
                d["should_clarify"] = False
            d["decision"] = decision
            if ret.redacted_prompt:
                d["prompt"] = text # to_dict replaces prompt with redacted, we need the original back for constructor
            return Analysis(**d)
        else:
            d = ret.to_dict()
            if ret.redacted_prompt:
                d["prompt"] = text
            d["decision"] = "block"
            return Analysis(**d)"""
content = content.replace(old_template_full, new_template_full)

# Fix the end return Analysis
content = re.sub(
    r"        severity=severity,\n        redacted_prompt=redacted_text,\n    \)",
    "        severity=severity,\n        redacted_prompt=redacted_text,\n        decision=decision,\n    )",
    content
)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done patching early returns")

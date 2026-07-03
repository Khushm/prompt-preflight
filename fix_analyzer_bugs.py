import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# 1. Move _is_enabled up
# Extract it
helper_pattern = r"    def _is_enabled\(cat: str\) -> bool:\n        return config\.policy_for\(cat\) != \"disable\" if config else True\n"
content = content.replace(helper_pattern, "")

# Insert it at the top of analyze_prompt
insertion_point_func = "    text = \" \".join(raw_prompt.split())\n"
new_insertion = insertion_point_func + helper_pattern
content = content.replace(insertion_point_func, new_insertion, 1)

# 2. Fix the backward compatibility decision logic
old_decision = """    # Per-check decision engine
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
"""

new_decision = """    # Per-check decision engine
    decision = "allow"
    if should_clarify:
        if not config or config.checks is None:
            decision = config.mode if config else "block"
        else:
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
"""
content = content.replace(old_decision, new_decision)


# We also need to fix the template return block logic similarly.
old_template_decision = """        if config:
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
            return Analysis(**d)"""

new_template_decision = """        if not config or config.checks is None:
            decision = config.mode if config else "block"
            d = ret.to_dict()
            d["decision"] = decision
            if ret.redacted_prompt:
                d["prompt"] = text
            return Analysis(**d)
        else:
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
            
            d = ret.to_dict()
            if decision == "allow":
                d["should_clarify"] = False
            d["decision"] = decision
            if ret.redacted_prompt:
                d["prompt"] = text
            return Analysis(**d)"""
content = content.replace(old_template_decision, new_template_decision)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done fixing bugs in analyzer.py")

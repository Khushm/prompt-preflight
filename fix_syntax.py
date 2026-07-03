import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# Find the literal backslash-n and replace it
content = content.replace("def _is_enabled\\(cat: str\\) -> bool:\\n        return config\\.policy_for\\(cat\\) != \\\"disable\\\" if config else True\\n", "")

# We also need to add it properly
proper_helper = """
    def _is_enabled(cat: str) -> bool:
        return config.policy_for(cat) != "disable" if config else True
"""
content = content.replace("    text = \" \".join(raw_prompt.split())", "    text = \" \".join(raw_prompt.split())" + proper_helper)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done fixing syntax")

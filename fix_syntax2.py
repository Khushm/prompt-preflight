import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# Remove the broken helper from classify_intent
bad_helper = """    def _is_enabled(cat: str) -> bool:
        return config.policy_for(cat) != "disable" if config else True

        if IMAGE_REQUEST_RE.search(text) and not IMAGE_SOFTWARE_RE.search(text):"""
good_code = """    if IMAGE_REQUEST_RE.search(text) and not IMAGE_SOFTWARE_RE.search(text):"""
content = content.replace(bad_helper, good_code)

# Add the helper into analyze_prompt where it belongs
good_helper = """
    def _is_enabled(cat: str) -> bool:
        return config.policy_for(cat) != "disable" if config else True
"""
target_insertion = """    lowered = text.lower()
    words = _words(text)"""
content = content.replace(target_insertion, target_insertion + good_helper)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done fixing syntax2")

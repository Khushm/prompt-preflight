import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# We need to remove the extra else block at the end of template check
bad_part = """        else:
            d = ret.to_dict()
            if ret.redacted_prompt:
                d["prompt"] = text
            d["decision"] = "block"
            return Analysis(**d)

    is_image_request = intent == "image_generation\""""

good_part = """
    is_image_request = intent == "image_generation\""""
content = content.replace(bad_part, good_part)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done fixing syntax3")

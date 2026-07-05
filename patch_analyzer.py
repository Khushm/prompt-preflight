import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# We need to replace all instances of:
# checks.append("category")
# ambiguity += X
# reasons.append(...)
# questions.append(...)
# with a check if category is enabled.

# It is probably easier to just write a script that processes the AST, or carefully replace blocks.

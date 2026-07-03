import re
from pathlib import Path

content = Path('src/prompt_preflight/analyzer.py').read_text()

# Remove the module level import
content = content.replace("from .config import Config\n", "")

# Add TYPE_CHECKING import
old_typing = "from typing import Iterable"
new_typing = "from typing import Iterable, TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from .config import Config"
content = content.replace(old_typing, new_typing)

Path('src/prompt_preflight/analyzer.py').write_text(content)
print("Done fixing circular import")

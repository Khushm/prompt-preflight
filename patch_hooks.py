import re
from pathlib import Path

def patch_file(path, old, new):
    content = Path(path).read_text()
    Path(path).write_text(content.replace(old, new))

# 1. hook.py
old_hook_call = """    analysis = analyze_prompt(
        prompt,
        threshold=config.threshold,
        max_questions=config.max_questions,
        cwd=payload.get("cwd"),
        attachments=attachments,
    )"""
new_hook_call = """    analysis = analyze_prompt(
        prompt,
        config=config,
        threshold=config.threshold,
        max_questions=config.max_questions,
        cwd=payload.get("cwd"),
        attachments=attachments,
    )"""
patch_file('src/prompt_preflight/hook.py', old_hook_call, new_hook_call)
patch_file('src/prompt_preflight/hook.py', 'if config.mode == "nudge":', 'if analysis.decision == "nudge":')

# 2. claude_hook.py
patch_file('src/prompt_preflight/claude_hook.py', old_hook_call, new_hook_call)
patch_file('src/prompt_preflight/claude_hook.py', 'if config.mode == "nudge":', 'if analysis.decision == "nudge":')

# 3. kiro_hook.py
patch_file('src/prompt_preflight/kiro_hook.py', old_hook_call, new_hook_call)
patch_file('src/prompt_preflight/kiro_hook.py', 'if config.mode == "nudge":', 'if analysis.decision == "nudge":')

# 4. cli.py
old_cli_call = """    analysis = analyze_prompt(
        prompt,
        threshold=max(0, min(100, args.threshold)),
        max_questions=max(1, min(5, args.max_questions)),
        cwd=args.cwd or Path.cwd(),
    )"""
new_cli_call = """    # Load config to support per-check policies in CLI
    from .config import load_config
    config = load_config(args.cwd or Path.cwd())
    
    analysis = analyze_prompt(
        prompt,
        config=config,
        threshold=max(0, min(100, args.threshold)),
        max_questions=max(1, min(5, args.max_questions)),
        cwd=args.cwd or Path.cwd(),
    )"""
patch_file('src/prompt_preflight/cli.py', old_cli_call, new_cli_call)
print("Done patching hooks")

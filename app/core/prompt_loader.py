from pathlib import Path
from typing import List


def load_prompt(name: str, category: str = "system") -> str:
    """
    Dynamically loads an .md prompt file from the designated category folder.
    Falls back to 'default.md' if the specified file does not exist.
    """
    base_dir = Path(f"app/prompts/{category}")
    target_path = base_dir / f"{name}.md"

    # 1. Look for the exact requested markdown file
    if target_path.exists():
        return target_path.read_text(encoding="utf-8")

    # 2. Fallback strategy to protect runtime execution
    fallback_path = base_dir / "default.md"
    if fallback_path.exists():
        return fallback_path.read_text(encoding="utf-8")

    return ""


def get_available_prompts(category: str = "system") -> List[str]:
    """
    Scans the prompt directory and returns a clean list of available .md names.
    Perfect for populating the front-end dropdown menu.
    """
    dir_path = Path(f"app/prompts/{category}")
    if not dir_path.exists():
        return []

    # Grab all markdown files, ignoring private/init files
    return sorted(
        [f.stem for f in dir_path.glob("*.md") if not f.name.startswith("__")]
    )

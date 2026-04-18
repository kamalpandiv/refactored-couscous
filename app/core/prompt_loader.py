from pathlib import Path


def load_prompt(name: str, category: str = "system") -> str:
    path = Path(f"app/prompts/{category}/{name}.txt")
    return path.read_text() if path.exists() else ""

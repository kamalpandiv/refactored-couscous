from pathlib import Path


def load_prompt(name: str) -> str:
    path = Path(f"app/prompts/{name}.txt")
    return path.read_text() if path.exists() else ""

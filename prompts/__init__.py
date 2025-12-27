from pathlib import Path

SYSTEM_PROMPT = (
    Path(__file__).parent / "dental_assistant.txt"
).read_text(encoding="utf-8")
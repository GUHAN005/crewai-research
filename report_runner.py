"""Runs the crew for one topic and returns the finished report."""
import re
from datetime import datetime
from pathlib import Path

from crew_builder import build_crew

OUTPUT_DIR = Path("output")


def make_slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower())[:40].strip("-") or "report"


def load_report(folder: Path) -> dict:
    """Read a finished run from its folder."""
    report = folder / "report.md"
    draft = folder / "draft.md"
    return {
        "folder": str(folder),
        "name": folder.name,
        "report": report.read_text(encoding="utf-8") if report.exists() else "",
        "draft": draft.read_text(encoding="utf-8") if draft.exists() else "",
    }


def list_past_reports() -> list[str]:
    if not OUTPUT_DIR.exists():
        return []
    folders = [p for p in OUTPUT_DIR.iterdir()
               if p.is_dir() and (p / "report.md").exists()]
    return [p.name for p in sorted(folders, reverse=True)]


def run_report(topic: str, on_step=None) -> dict:
    """on_step(task_name) is called each time one task finishes."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    folder = OUTPUT_DIR / f"{stamp}_{make_slug(topic)}"
    folder.mkdir(parents=True, exist_ok=True)

    def task_callback(task_output):
        if on_step:
            on_step(getattr(task_output, "name", None) or "task")

    crew = build_crew(topic, str(folder), task_callback=task_callback)
    result = crew.kickoff()

    data = load_report(folder)
    if not data["report"]:               # safety net if file was not written
        data["report"] = str(result)
        (folder / "report.md").write_text(data["report"], encoding="utf-8")
    return data

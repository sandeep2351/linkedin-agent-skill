"""Run the two humanizer scripts that ship with /li-human. Nothing is uploaded."""

import importlib.util

from .config import REPO_ROOT

SKILL_DIR = REPO_ROOT / "skills" / "li-human"


def _load(module_name: str, filename: str):
    """Load a skill script by path so the runner can call it without installing a package."""
    path = SKILL_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_and_score(text: str) -> tuple[str, dict, dict, float, str]:
    """Humanize, then score. Returns clean text, change report, checks, score, verdict."""
    humanize_mod = _load("li_humanize", "humanize.py")
    detect_mod = _load("li_detect", "detect.py")
    lexicon = humanize_mod.load_lexicon(str(SKILL_DIR / "slop.json"))
    clean, report = humanize_mod.humanize(text, lexicon)
    results, overall, verdict = detect_mod.run(clean, lexicon)
    return clean, report, results, overall, verdict


def artefact_count(report: dict) -> int:
    """How many machine artefacts the cleaner actually removed."""
    return (
        sum(item["count"] for item in report.get("invisible", []))
        + sum(item["count"] for item in report.get("typographic", []))
        + sum(item["count"] for item in report.get("lexical", []))
    )


def format_panel(results: dict, overall: float, verdict: str) -> str:
    """Plain-text panel saved next to the draft."""
    lines = ["AI DETECTION PANEL", "These are local heuristics, not a detector API.", ""]
    for name in ("BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"):
        score, detail = results[name]
        lines.append(f"{name:<13} {score:5.1f}  {detail}")
    lines.append(f"HUMAN SCORE   {overall:5.1f}  {verdict}")
    if verdict != "PASS":
        weakest = min(results, key=lambda name: results[name][0])
        lines.append(f"Weakest signal: {weakest}.")
    return "\n".join(lines) + "\n"


def structure_notes(report: dict) -> list[str]:
    """Structural tells the regex refused to rewrite."""
    notes = []
    for item in report.get("structures", []):
        notes.append(f"{item['name']}: {item['fix']}")
    return notes

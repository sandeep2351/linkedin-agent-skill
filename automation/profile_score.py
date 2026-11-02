"""Score a pasted profile against the 12-part rubric. The model does not set the points."""

import json
import re

from .config import Config

EMPTY = {"", "none", "empty", "n/a", "na", "default", "not provided", "missing", "no"}

HEADINGS = (
    "headline",
    "about",
    "role",
    "featured",
    "banner",
    "photo",
    "experience",
    "skills",
    "recommendations",
    "activity",
    "contact",
)


def parse_profile(text: str) -> dict[str, str]:
    """Read `Headline:` style labels. A bare paste uses line 1 as the headline."""
    sections = {name: "" for name in HEADINGS}
    current: str | None = None
    labeled = False
    for line in text.splitlines():
        match = re.match(
            r"^(headline|about|role|featured|banner|photo|experience|skills|"
            r"recommendations|activity|contact)\s*:\s*(.*)$",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            labeled = True
            current = match.group(1).lower()
            sections[current] = match.group(2).strip()
            continue
        if current:
            sections[current] = (sections[current] + "\n" + line).strip()
    if not labeled:
        lines = [line for line in text.splitlines() if line.strip()]
        sections["headline"] = lines[0] if lines else ""
        sections["about"] = "\n".join(lines[1:])
    return sections


def _blank(text: str) -> bool:
    """Treat 'none', 'not described', and 'no banner' as missing."""
    low = text.strip().lower()
    return low in EMPTY or low.startswith("not ") or low.startswith("no ")


def _clamp(points: int, maximum: int) -> int:
    return max(0, min(maximum, points))


def score_profile(text: str) -> list[dict]:
    """Twelve rows. Missing sections score zero, which is the honest first pass."""
    sections = parse_profile(text)
    headline = sections["headline"].strip()
    about = sections["about"].strip()
    about_open = "\n".join(about.splitlines()[:2])[:280]
    headline_low = headline.lower()
    about_low = about.lower()

    # Headline: a job title alone is the usual miss. An outcome for a reader scores.
    if not headline:
        headline_points, headline_note = 0, "empty"
    elif "passionate" in headline_low:
        headline_points, headline_note = 2, "slogan, no reader outcome"
    elif len(headline) < 50 and not any(word in headline_low for word in ("help", "explain", "for ", "who ")):
        headline_points, headline_note = 3, "job title only"
    elif any(word in headline_low for word in ("help", "explain", "for ")) and len(headline) >= 80:
        headline_points, headline_note = 10, "names who it is for"
    elif any(word in headline_low for word in ("help", "explain", "for ")):
        headline_points, headline_note = 7, "has a reader, still short"
    else:
        headline_points, headline_note = 4, "no reader outcome"

    # The first two lines are all a visitor sees before See more.
    if not about_open:
        open_points, open_note = 0, "empty"
    elif "passionate about" in about_low[:180]:
        open_points, open_note = 2, "opens with passionate about"
    elif re.match(r"^(i am|i'm|my name)\b", about_open.strip(), re.IGNORECASE):
        open_points, open_note = 3, "opens as a biography"
    elif re.search(r"\b(you|your)\b", about_open, re.IGNORECASE):
        open_points, open_note = 8, "talks to the reader"
    else:
        open_points, open_note = 4, "history, not the reader's problem"

    # The rest of About should say what you do and what to do next.
    if len(about) < 40:
        body_points, body_note = 0, "too thin to be an offer"
    elif re.search(r"\b(you|your)\b", about, re.IGNORECASE) and len(about) < 1400:
        body_points, body_note = 7, "written to the reader, proof number still missing"
    elif len(about) > 1400:
        body_points, body_note = 4, "over 1,400 characters"
    else:
        body_points, body_note = 4, "reads as a history"

    def presence(section: str, full: int, good_note: str) -> tuple[int, str]:
        value = sections[section]
        if _blank(value):
            return 0, "not in the paste"
        if len(value.strip()) < 8:
            return 1, "mentioned, not described"
        return min(full - 1, max(2, full // 2)), good_note

    featured_points, featured_note = presence("featured", 8, "has items, check that one is proof")
    banner_points, banner_note = presence("banner", 6, "described, confirm it is not the default")
    photo_points, photo_note = presence("photo", 6, "described, confirm the face fills the frame")
    role_points, role_note = presence("role", 10, "has a role, look for outcome bullets")
    experience_points, experience_note = presence("experience", 8, "has older roles, check the compression")
    skills_points, skills_note = presence("skills", 6, "listed, top three should be the ones you want")
    recommendations_points, recommendations_note = presence(
        "recommendations", 8, "mentioned, each one should name an outcome"
    )
    activity_points, activity_note = presence("activity", 10, "mentioned, confirm it was in the last seven days")
    contact_points, contact_note = presence("contact", 6, "mentioned, confirm the URL and email work")

    rows = [
        ("headline", 12, headline_points, headline_note),
        ("about_open", 10, open_points, open_note),
        ("about_body", 10, body_points, body_note),
        ("featured", 8, featured_points, featured_note),
        ("banner", 6, banner_points, banner_note),
        ("photo", 6, photo_points, photo_note),
        ("current_role", 10, role_points, role_note),
        ("experience_depth", 8, experience_points, experience_note),
        ("skills", 6, skills_points, skills_note),
        ("recommendations", 8, recommendations_points, recommendations_note),
        ("activity", 10, activity_points, activity_note),
        ("contact", 6, contact_points, contact_note),
    ]
    scored = []
    for name, maximum, points, note in rows:
        scored.append(
            {
                "id": name,
                "points": _clamp(points, maximum),
                "max": maximum,
                "note": note,
            }
        )
    return scored


def format_score(rows: list[dict]) -> str:
    total = sum(row["points"] for row in rows)
    maximum = sum(row["max"] for row in rows)
    lines = [f"PROFILE SCORE  {total}/{maximum}", ""]
    for row in rows:
        lines.append(f"  {row['id']:<18} {row['points']:>2}/{row['max']:<2}  {row['note']}")
    lines.append("")
    lines.append("A section you did not paste scores zero. Paste it and run the score again.")
    return "\n".join(lines) + "\n"


def rubric_text(config: Config) -> str:
    payload = json.loads(config.rubric_path.read_text(encoding="utf-8"))
    lines = []
    for item in payload["items"]:
        lines.append(f"{item['id']} ({item['points']}): {item['full_marks']}")
    return "\n".join(lines)

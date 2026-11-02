"""Compute engagement rate, comment ratio, and reach multiple from a pasted export.

Impressions alone are not the ranking. The runner never logs into LinkedIn.
"""

import csv
from pathlib import Path

ALIASES = {
    "impressions": "impressions",
    "impression": "impressions",
    "views": "impressions",
    "reactions": "reactions",
    "reaction": "reactions",
    "likes": "reactions",
    "like": "reactions",
    "comments": "comments",
    "comment": "comments",
    "reposts": "reposts",
    "repost": "reposts",
    "shares": "reposts",
    "share": "reposts",
    "followers": "followers",
    "follower": "followers",
    "follower_count": "followers",
    "post": "text",
    "text": "text",
    "title": "text",
    "date": "date",
    "posted": "date",
}


def _number(value: str) -> float | None:
    raw = (value or "").strip().replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def load_rows(path: Path) -> list[dict]:
    """Read a CSV. Unknown columns are ignored. Rows with no impressions stay in the file but do not rank."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError("The CSV has no header row.")
        header_map = {}
        for field in reader.fieldnames:
            key = ALIASES.get((field or "").strip().lower())
            if key:
                header_map[field] = key
        if "impressions" not in header_map.values():
            raise RuntimeError("The CSV needs an impressions column (or views).")
        rows = []
        for index, raw in enumerate(reader, start=1):
            item = {"index": index, "text": "", "date": ""}
            for source, target in header_map.items():
                item[target] = (raw.get(source) or "").strip()
            impressions = _number(str(item.get("impressions", "")))
            reactions = _number(str(item.get("reactions", ""))) or 0
            comments = _number(str(item.get("comments", ""))) or 0
            reposts = _number(str(item.get("reposts", ""))) or 0
            followers = _number(str(item.get("followers", "")))
            item["impressions_n"] = impressions
            item["reactions_n"] = reactions
            item["comments_n"] = comments
            item["reposts_n"] = reposts
            item["followers_n"] = followers
            if impressions and impressions > 0:
                item["engagement_rate"] = (reactions + comments + reposts) / impressions
                item["reach_multiple"] = (impressions / followers) if followers else None
            else:
                item["engagement_rate"] = None
                item["reach_multiple"] = None
            item["comment_ratio"] = (comments / reactions) if reactions else None
            rows.append(item)
    return rows


def rank_rows(rows: list[dict]) -> list[dict]:
    """Highest engagement rate first. Rows with no impressions stay at the bottom."""
    scored = [row for row in rows if row["engagement_rate"] is not None]
    missing = [row for row in rows if row["engagement_rate"] is None]
    scored.sort(key=lambda row: row["engagement_rate"], reverse=True)
    return scored + missing


def format_audit(rows: list[dict]) -> str:
    ranked = rank_rows(rows)
    lines = [
        "AUDIT",
        "Engagement rate = (reactions + comments + reposts) / impressions.",
        "Comment ratio = comments / reactions.",
        "Reach multiple = impressions / followers, when the file has a follower count.",
        "",
    ]
    if len([row for row in ranked if row["engagement_rate"] is not None]) < 3:
        lines.append("Fewer than three scored posts. Treat the ranking as a hint, not a pattern.")
        lines.append("")
    for place, row in enumerate(ranked, start=1):
        title = (row.get("text") or f"row {row['index']}")[:80]
        if row["engagement_rate"] is None:
            lines.append(f"{place}. {title}")
            lines.append("   no impressions, so this row is not ranked")
            continue
        ratio = row["comment_ratio"]
        reach = row["reach_multiple"]
        ratio_text = f"{ratio:.2f}" if ratio is not None else "n/a"
        reach_text = f"{reach:.2f}" if reach is not None else "n/a"
        lines.append(f"{place}. {title}")
        lines.append(
            f"   engagement {row['engagement_rate'] * 100:.2f}%  "
            f"comments/reactions {ratio_text}  "
            f"reach multiple {reach_text}  "
            f"impressions {int(row['impressions_n'])}"
        )
    if ranked and ranked[0]["engagement_rate"] is not None:
        lines.append("")
        lines.append(f"Repeat the shape of rank 1: {ranked[0].get('text', '')[:120]}")
        if len(ranked) > 1 and ranked[-1]["engagement_rate"] is not None:
            lines.append(f"Stop repeating the shape of the lowest scored row: {ranked[-1].get('text', '')[:120]}")
    return "\n".join(lines) + "\n"

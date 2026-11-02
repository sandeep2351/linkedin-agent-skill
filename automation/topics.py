"""Pick the next LinkedIn topic from the local bank. The model may choose. It may not invent one."""

import json
import re
from pathlib import Path

from .config import Config


def load_topics(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_used(path: Path) -> list[str]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def available_topics(config: Config) -> list[dict]:
    """Topics that have not been used yet."""
    topics = load_topics(config.topics_path)
    used = set(load_used(config.used_topics_path))
    pool = [topic for topic in topics if topic["id"] not in used]
    if not pool:
        raise RuntimeError(
            "No unused topics left in automation/topics.json. "
            "Delete automation/state/used_topics.json when you want the bank to repeat."
        )
    return pool


def choose_topic(config: Config) -> dict:
    """Ask the small model to pick one allowed topic. Fall back to the first unused one."""
    pool = available_topics(config)
    if len(pool) == 1:
        return pool[0]
    menu = [
        {"id": topic["id"], "type": topic["type"], "title": topic["title_seed"]}
        for topic in pool
    ]
    prompt = (
        "Pick the single best next LinkedIn post for a beginner in DevOps or AI. "
        "Return JSON only: {\"id\": \"one id from the list\"}.\n"
        + json.dumps(menu)
    )
    try:
        from .bedrock import ask

        raw, _used = ask(config, config.model_title, prompt, max_tokens=120)
        start = raw.find("{")
        end = raw.rfind("}")
        picked = json.loads(raw[start : end + 1]).get("id", "")
        for topic in pool:
            if topic["id"] == picked:
                return topic
    except Exception as error:
        print(f"[pick-topic] Model pick failed ({error}). Using the next unused topic.", flush=True)
    return pool[0]


def topic_from_concept(text: str) -> dict:
    """A topic the user typed. This skips the bank."""
    title = " ".join(text.split())
    return {
        "id": slugify(title).lower()[:48] or "custom-concept",
        "type": "teach",
        "category": "custom",
        "title_seed": title,
        "angle": (
            "Explain this exact concept for a beginner. One mechanism. "
            "No invented client, revenue, or personal result. Use {{your number}} if a personal figure is required."
        ),
        "hook_id": 21,
    }


def pick_week(config: Config) -> list[dict]:
    """One proof, one opinion, one teach. A story is not invented when the proof list is empty."""
    pool = available_topics(config)
    chosen: list[dict] = []
    used_ids: set[str] = set()
    for kind in ("proof", "opinion", "teach"):
        for topic in pool:
            if topic["type"] == kind and topic["id"] not in used_ids:
                chosen.append(topic)
                used_ids.add(topic["id"])
                break
    if len(chosen) < 3:
        raise RuntimeError("The topic bank needs at least one proof, one opinion, and one teach topic.")
    return chosen


def slugify(text: str) -> str:
    """A file-safe topic name."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return cleaned[:70] or "topic"


def mark_used(config: Config, topic_id: str) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    used = load_used(config.used_topics_path)
    if topic_id not in used:
        used.append(topic_id)
    config.used_topics_path.write_text(json.dumps(used, indent=2), encoding="utf-8")

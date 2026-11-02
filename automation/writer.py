"""Turn one topic into three hooks and one humanized post."""

import json

from .config import Config
from .humanpass import artefact_count, clean_and_score, format_panel, structure_notes
from .textutil import (
    ask_json,
    first_line,
    limit_hashtags,
    personal_claims,
    placeholders,
    quality_issues,
)

RULES = """
Hard rules:
- Follow the voice profile.
- One idea.
- Line 1 stands alone and stays under 140 characters.
- Line 2 pays off line 1.
- Short paragraphs, blank line between them.
- 900 to 1,300 characters is the target.
- Contractions. No emoji. No em dash.
- At most three hashtags, on the last line, or none.
- No link in the post body.
- Do not invent clients, employers, revenue, salary, or personal results.
- If a personal number is required, keep the characters {{your number}} in the post.
- Public technical facts are allowed. A made-up personal experiment is not.
- Put at least four concrete markers in the body: a tool name mid-sentence, and real technical digits such as port 80, 2 containers, or 1 node.
- The closing question has to be one only this post could ask. Never "Thoughts?" or "Agree?".
- Return one JSON object and nothing else.
"""

# A known-good teach post so --demo can prove the humanizer with no model call.
DEMO_POST = """A container is not a tiny computer.

It's a packed lunch. The app, the libraries, and the start command sit in one box. The kitchen around that box can change. The lunch doesn't.

Docker builds the box from a Dockerfile. Three lines are enough to start: the base image, the files you copy in, and the command that starts the app.

Kubernetes doesn't replace Docker. It decides which machine runs the box, and it starts a new box when the first one dies. On AIOrbit Lab I draw that as 1 box with 2 labels: the app, and port 80.

People skip the boring part. A container still needs a port, a disk, and a secret. I open port 80 for a demo, then I lock it before anyone else can reach it.

When you explain this to a new teammate, do you start with the Dockerfile, or with the day the app worked on your laptop and died on the server?

#Docker #DevOps #Kubernetes
"""


def load_voice(config: Config) -> str:
    return config.voice_path.read_text(encoding="utf-8")


def hook_catalog(config: Config) -> str:
    """The 21 formulas, compressed to what the model needs to choose."""
    payload = json.loads(config.hooks_path.read_text(encoding="utf-8"))
    lines = []
    for hook in payload["hooks"]:
        lines.append(
            f"#{hook['id']} {hook['name']}: {hook['template']} | best for: {hook['best_for']} | trap: {hook['trap']}"
        )
    return "\n".join(lines)


def _context(voice: str, topic: dict) -> str:
    return (
        f"Voice profile:\n{voice}\n\n"
        f"Topic: {topic['title_seed']}\n"
        f"Type: {topic.get('type', 'teach')}\n"
        f"Angle: {topic['angle']}\n"
        f"Suggested hook id: {topic.get('hook_id', 21)}\n"
        f"{RULES}"
    )


def write_hooks(config: Config, topic: dict, voice: str) -> tuple[dict, str]:
    """Three different formulas, plus the one to ship."""
    prompt = (
        _context(voice, topic)
        + "\nHook catalog:\n"
        + hook_catalog(config)
        + '\n\nPick three different hook ids that fit this angle. '
        'JSON keys: "options" (list of {id, name, line, why}), "ship_id", "ship_why". '
        "Each line is a possible first line, under 140 characters. "
        "ship_id must be one of the three ids."
    )
    payload, used = ask_json(config, config.model_story, prompt, max_tokens=900)
    options = payload.get("options") or []
    cleaned = []
    seen: set[int] = set()
    for item in options:
        if not isinstance(item, dict):
            continue
        try:
            hook_id = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        line = " ".join(str(item.get("line", "")).split())
        if not line or hook_id in seen:
            continue
        seen.add(hook_id)
        cleaned.append(
            {
                "id": hook_id,
                "name": str(item.get("name", "")).strip(),
                "line": line,
                "why": str(item.get("why", "")).strip(),
            }
        )
        if len(cleaned) == 3:
            break
    if len(cleaned) < 3:
        raise RuntimeError("The hook pass did not return three different formulas.")
    try:
        ship_id = int(payload.get("ship_id"))
    except (TypeError, ValueError):
        ship_id = cleaned[0]["id"]
    if ship_id not in {item["id"] for item in cleaned}:
        ship_id = cleaned[0]["id"]
    return {
        "options": cleaned,
        "ship_id": ship_id,
        "ship_why": str(payload.get("ship_why", "")).strip(),
    }, used


def write_draft(config: Config, topic: dict, voice: str, hooks: dict) -> tuple[str, str, str]:
    """The full post on the chosen hook."""
    chosen = next(item for item in hooks["options"] if item["id"] == hooks["ship_id"])
    prompt = (
        _context(voice, topic)
        + f"\nShip this hook as line 1, or a tighter version of it under 140 characters:\n{chosen['line']}\n"
        + f"Hook #{chosen['id']} {chosen['name']}.\n"
        + 'JSON keys: "post" (the full post) and "first_comment" (empty string, or the link the user should paste as the first comment).'
    )
    payload, used = ask_json(config, config.model_script, prompt, max_tokens=1600)
    post = str(payload.get("post", "")).strip()
    if not post:
        raise RuntimeError("The draft pass returned an empty post.")
    return post, str(payload.get("first_comment", "")).strip(), used


def polish(config: Config, text: str, voice: str, topic: dict, *, rewrite: bool = True) -> dict:
    """Clean the draft, score it, and rewrite once or twice when the panel or the rules fail."""
    allowed = voice + "\n" + topic.get("angle", "") + "\n" + topic.get("title_seed", "")
    current = text
    last: dict = {}
    for attempt in range(3):
        # The humanizer strips characters and slop. It does not reshape sentences.
        clean, report, results, overall, verdict = clean_and_score(current)
        clean = limit_hashtags(clean)
        issues = quality_issues(clean)
        issues.extend(structure_notes(report))
        claims = personal_claims(clean, allowed)
        if claims:
            issues.append(
                "personal claim not in the voice profile: "
                + ", ".join(claims)
                + ". Replace it with {{your number}} or delete the claim."
            )
        # The panel's weakest check has to be named, or the rewrite cannot move it.
        if verdict != "PASS":
            weakest = min(results, key=lambda name: results[name][0])
            score, detail = results[weakest]
            issues.append(f"{weakest} scored {score:.1f}. {detail}")
            if weakest == "SPECIFICITY":
                issues.append(
                    "Add tool names in the middle of sentences and true technical digits "
                    "(port 80, 2 containers, 1 node). Do not invent a client or a personal result."
                )
        last = {
            "post": clean,
            "report": report,
            "results": results,
            "overall": overall,
            "verdict": verdict,
            "issues": issues,
            "artefacts": artefact_count(report),
            "placeholders": placeholders(clean),
        }
        # PASS with no hard issues is ready. A leftover structural tell still gets one rewrite.
        hard = [issue for issue in issues if not issue.startswith("Uniform")]
        if verdict == "PASS" and not hard:
            return last
        # The offline demo records the score. It does not ask a model to rewrite.
        if not rewrite or attempt == 2:
            return last
        current = _rewrite(config, clean, issues, voice, topic)
    return last


def _rewrite(config: Config, text: str, issues: list[str], voice: str, topic: dict) -> str:
    """One judged rewrite. The regex cleaner cannot fix sentence shape."""
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        f"Topic: {topic['title_seed']}\nAngle: {topic['angle']}\n"
        "Rewrite the post. Keep the same meaning. Fix every issue. "
        "Do not add a client, a revenue figure, or a personal result. "
        'JSON key: "post".\n\n'
        "Issues:\n- "
        + "\n- ".join(issues)
        + "\n\nPost:\n"
        + text
    )
    payload, _used = ask_json(config, config.model_longform, prompt, max_tokens=1600)
    rewritten = str(payload.get("post", "")).strip()
    if not rewritten:
        raise RuntimeError("The rewrite pass returned an empty post.")
    return rewritten


def format_hooks(hooks: dict) -> str:
    lines = ["HOOKS"]
    for index, item in enumerate(hooks["options"], start=1):
        lines.append(f"{index}. #{item['id']} {item['name']}  {item['line']}")
    lines.append("")
    lines.append(f"Shipping #{hooks['ship_id']}: {hooks['ship_why']}")
    return "\n".join(lines) + "\n"


def format_receipt(package: dict) -> str:
    """The block printed under a finished post."""
    hooks = package.get("hooks") or {}
    chosen = next(
        (item for item in hooks.get("options", []) if item["id"] == hooks.get("ship_id")),
        {},
    )
    post = package.get("post", "")
    name = chosen.get("name", "")
    hook_id = hooks.get("ship_id", "")
    lines = [
        "POST READY",
        f"hook:      #{hook_id} {name}".rstrip(),
        f"length:    {len(post.strip())} characters",
        (
            f"humanizer: {package.get('artefacts', 0)} artefacts stripped, "
            f"human score {package.get('overall', 0):.1f} {package.get('verdict', '')}"
        ),
        "saved:     the post.txt file in this run's folder",
        "next:      paste it into LinkedIn yourself",
    ]
    if package.get("placeholders"):
        lines.append("missing:   " + ", ".join(package["placeholders"]))
    if package.get("issues"):
        lines.append("still open:")
        for issue in package["issues"]:
            lines.append(f"  - {issue}")
    if package.get("first_comment"):
        lines.append("first comment (paste separately):")
        lines.append(package["first_comment"])
    return "\n".join(lines) + "\n"


def demo_package() -> dict:
    """The offline sample. Humanize and save still run on it."""
    return {
        "topic": {
            "id": "demo",
            "type": "teach",
            "category": "demo",
            "title_seed": "A container is a packed lunch",
            "angle": "Offline sample. No model call.",
            "hook_id": 11,
        },
        "hooks": {
            "options": [
                {
                    "id": 11,
                    "name": "Myth Bust",
                    "line": "A container is not a tiny computer.",
                    "why": "The first line is the correction.",
                },
                {
                    "id": 21,
                    "name": "The Direct Value",
                    "line": "Here are the three Dockerfile lines that are enough to start.",
                    "why": "The artifact is small enough to give away.",
                },
                {
                    "id": 16,
                    "name": "Good vs Great",
                    "line": "Good explanations name Docker. Great ones show the box.",
                    "why": "A distinction a beginner can repeat.",
                },
            ],
            "ship_id": 11,
            "ship_why": "Line 1 is the myth, and the post pays it off.",
        },
        "post_raw": DEMO_POST,
        "first_comment": "",
        "models": {"demo": "local sample"},
    }

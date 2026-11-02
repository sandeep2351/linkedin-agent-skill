"""Build the next LinkedIn GIF and the caption that goes under it.

No voice file. No short video. One roadmap, every two days.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from .boards import BOARDS
from .config import Config
from .gifboard import write_gif
from .humanpass import clean_and_score, format_panel
from .topics import load_used, mark_used, slugify


def board_by_id(board_id: str) -> dict | None:
    for board in BOARDS:
        if board["id"] == board_id:
            return board
    return None


def board_for_concept(text: str) -> dict | None:
    """Match a typed idea to a roadmap. Unknown ideas are not invented into a fake post."""
    lowered = text.lower()
    for board in BOARDS:
        if any(word in lowered for word in board["keywords"]):
            return board
    return None


def next_board(config: Config) -> dict:
    used = set(load_used(config.used_topics_path))
    for board in BOARDS:
        if board["id"] not in used:
            return board
    raise RuntimeError(
        "Every roadmap in the bank has been used. "
        "Delete automation/state/used_topics.json when you want the series to repeat."
    )


def _due(config: Config) -> tuple[bool, str]:
    """A scheduled run waits until two days after the previous GIF."""
    stamp = config.state_dir / "last_post.txt"
    if not stamp.exists():
        return True, "no post yet"
    last = date.fromisoformat(stamp.read_text(encoding="utf-8").strip())
    nxt = last + timedelta(days=2)
    if date.today() >= nxt:
        return True, nxt.isoformat()
    return False, nxt.isoformat()


def _remember(config: Config) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    (config.state_dir / "last_post.txt").write_text(date.today().isoformat(), encoding="utf-8")


def build_pack(config: Config, board: dict, *, mark: bool) -> Path:
    """Humanize the caption, draw the GIF, and save one folder you can upload."""
    clean, _report, results, overall, verdict = clean_and_score(board["post"])
    folder = config.output_dir / slugify(board["title"].replace("\n", " "))
    if folder.exists() and any(folder.iterdir()):
        folder = config.output_dir / f"{folder.name}-{date.today().isoformat()}"
    folder.mkdir(parents=True, exist_ok=True)
    gif_path = folder / "post.gif"
    preview_path = folder / "preview.png"
    write_gif(board, gif_path, preview_path)
    (folder / "post.txt").write_text(clean if clean.endswith("\n") else clean + "\n", encoding="utf-8")
    (folder / "first-comment.txt").write_text(board["comment"].strip() + "\n", encoding="utf-8")
    (folder / "detect.txt").write_text(format_panel(results, overall, verdict), encoding="utf-8")
    (folder / "meta.json").write_text(
        json.dumps(
            {
                "id": board["id"],
                "category": board["category"],
                "title": board["title"],
                "verdict": verdict,
                "score": round(overall, 1),
                "gif": gif_path.name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    steps = (
        "HOW TO PUBLISH\n"
        "1. Open LinkedIn and start a post.\n"
        "2. Upload post.gif.\n"
        "3. Paste post.txt as the caption.\n"
        "4. Publish.\n"
        "5. Paste first-comment.txt as the first comment so the portfolio link stays out of the caption.\n"
        "\n"
        "The runner does not log into LinkedIn. A browser login is a common way to get a recruiter-facing account restricted.\n"
    )
    (folder / "HOW-TO-POST.txt").write_text(steps, encoding="utf-8")
    if mark:
        mark_used(config, board["id"])
        _remember(config)
    print(clean, flush=True)
    print(format_panel(results, overall, verdict), flush=True)
    print(f"GIF: {gif_path}", flush=True)
    print(f"Saved {folder}", flush=True)
    print(steps, flush=True)
    return folder


def run_feed(config: Config, *, demo: bool, concept: str | None, count: int, scheduled: bool) -> int:
    """Create one or more GIF posts. The scheduled flag waits for the two-day gap."""
    if scheduled:
        ready, when = _due(config)
        if not ready:
            print(f"Next GIF is due on {when}. Nothing was created.", flush=True)
            return 0
    for index in range(max(1, count)):
        if count > 1:
            print(f"Post {index + 1} of {count}", flush=True)
        if demo:
            board = BOARDS[0]
            mark = False
        elif concept:
            board = board_for_concept(concept)
            if board is None:
                names = ", ".join(sorted({item["category"] for item in BOARDS}))
                print(f"No roadmap matches {concept!r}. Categories in the bank: {names}", flush=True)
                return 1
            mark = False
        else:
            board = next_board(config)
            mark = True
        print(f"Roadmap: {board['title'].replace(chr(10), ' ')} [{board['category']}]", flush=True)
        build_pack(config, board, mark=mark)
    return 0

"""Run one stage, or every stage, for a single LinkedIn post."""

import json
from datetime import date
from pathlib import Path

from .config import Config
from .humanpass import format_panel
from .stages import StageLog
from .topics import choose_topic, mark_used, slugify, topic_from_concept
from .writer import (
    demo_package,
    format_hooks,
    format_receipt,
    load_voice,
    polish,
    write_draft,
    write_hooks,
)


def stage_names(*, demo: bool, concept: bool) -> list[str]:
    """Ordered stages. A typed concept skips the bank. The demo skips the model."""
    if demo:
        return ["demo", "humanize", "save"]
    names = ["hooks", "draft", "humanize", "save"]
    if not concept:
        names.insert(0, "pick-topic")
        names.append("mark-used")
    return names


def _work_dir(config: Config) -> Path:
    path = config.state_dir / "post"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load(path: Path) -> dict:
    file_path = path / "package.json"
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


def _save(path: Path, package: dict) -> None:
    (path / "package.json").write_text(json.dumps(package, indent=2, default=str), encoding="utf-8")


def _require(package: dict, key: str, earlier: str) -> None:
    if not package.get(key):
        raise RuntimeError(f"Run --stage {earlier} before this stage.")


def _append_log(config: Config, package: dict, folder: Path) -> None:
    """Record the hook and the first line so a later audit has a history."""
    config.state_dir.mkdir(parents=True, exist_ok=True)
    hooks = package.get("hooks") or {}
    first = ""
    for line in str(package.get("post", "")).splitlines():
        if line.strip():
            first = line.strip()
            break
    entry = (
        f"\n## {date.today().isoformat()}\n"
        f"- hook: #{hooks.get('ship_id', '')}\n"
        f"- first line: {first}\n"
        f"- file: {folder}\n"
        f"- verdict: {package.get('verdict', '')} {package.get('overall', '')}\n"
    )
    with config.log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    try:
        config.home_dir.mkdir(parents=True, exist_ok=True)
        with (config.home_dir / "log.md").open("a", encoding="utf-8") as handle:
            handle.write(entry)
    except OSError as error:
        print(f"Could not mirror the log to {config.home_dir}: {error}", flush=True)


def _step(config: Config, name: str, package: dict, folder: Path) -> dict:
    """Do one stage and return the updated package."""
    if name == "demo":
        package = demo_package()
        print(f"Topic: {package['topic']['title_seed']} [demo]", flush=True)
        return package
    if name == "pick-topic":
        topic = choose_topic(config)
        package = {"topic": topic, "models": {}}
        print(f"Topic: {topic['title_seed']} [{topic['type']}]", flush=True)
        return package
    if name == "hooks":
        _require(package, "topic", "pick-topic, or pass --concept")
        voice = load_voice(config)
        hooks, used = write_hooks(config, package["topic"], voice)
        package["hooks"] = hooks
        package.setdefault("models", {})["hooks"] = used
        print(format_hooks(hooks), flush=True)
        return package
    if name == "draft":
        _require(package, "hooks", "hooks")
        voice = load_voice(config)
        raw, first_comment, used = write_draft(config, package["topic"], voice, package["hooks"])
        package["post_raw"] = raw
        package["first_comment"] = first_comment
        package.setdefault("models", {})["draft"] = used
        return package
    if name == "humanize":
        _require(package, "post_raw", "draft")
        voice = load_voice(config)
        rewrite = (package.get("topic") or {}).get("category") != "demo"
        polished = polish(config, package["post_raw"], voice, package["topic"], rewrite=rewrite)
        package.update(polished)
        print(format_panel(polished["results"], polished["overall"], polished["verdict"]), flush=True)
        return package
    if name == "save":
        _require(package, "post", "humanize")
        topic = package.get("topic") or {}
        slug = slugify(str(topic.get("title_seed") or "post"))
        out = config.output_dir / slug
        if out.exists() and any(out.iterdir()):
            out = config.output_dir / f"{slug}-{date.today().isoformat()}"
        out.mkdir(parents=True, exist_ok=True)
        post = package["post"]
        (out / "post.txt").write_text(post, encoding="utf-8")
        (out / "hooks.txt").write_text(format_hooks(package.get("hooks") or {"options": [], "ship_id": "", "ship_why": ""}), encoding="utf-8")
        (out / "detect.txt").write_text(
            format_panel(package.get("results") or {}, package.get("overall") or 0, package.get("verdict") or ""),
            encoding="utf-8",
        )
        (out / "receipt.txt").write_text(format_receipt(package), encoding="utf-8")
        (out / "meta.json").write_text(json.dumps(package, indent=2, default=str), encoding="utf-8")
        package["slug"] = out.name
        _append_log(config, package, out)
        print(post, flush=True)
        print(format_receipt(package), flush=True)
        print(f"Saved {out}", flush=True)
        return package
    if name == "mark-used":
        topic = package.get("topic") or {}
        topic_id = topic.get("id")
        if topic_id and topic.get("category") not in {"custom", "demo"}:
            mark_used(config, topic_id)
        return package
    raise KeyError(name)


def run_jobs(
    config: Config,
    *,
    only: str | None,
    demo: bool,
    count: int,
    concept: str | None,
) -> int:
    """Run the selected stages. `only` None means every stage, in order."""
    names = stage_names(demo=demo, concept=bool(concept))
    if only and only != "all" and only not in names:
        print(f"Unknown stage {only}. Choose one of: {', '.join(names)}", flush=True)
        return 1
    selected = names if only in (None, "all") else [only]
    folder = _work_dir(config)
    for index in range(count):
        if count > 1:
            print(f"Post {index + 1} of {count}", flush=True)
        stages = StageLog(names)
        fresh = only in (None, "all") or "pick-topic" in selected or "demo" in selected
        if concept and only == "hooks":
            fresh = True
        package = {} if fresh else _load(folder)
        if concept:
            package["topic"] = topic_from_concept(concept)
            package.setdefault("models", {})
            print(f"Concept: {concept}", flush=True)
        for name in selected:
            with stages.stage(name):
                package = _step(config, name, package, folder)
                _save(folder, package)
    return 0

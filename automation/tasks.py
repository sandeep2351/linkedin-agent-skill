"""The commands that are not the single-post pipeline: week, comment, reply, profile, carousel, DM, inbox, repurpose."""

import json
from datetime import date, timedelta
from pathlib import Path

from .audit_math import format_audit, load_rows
from .carousel_pdf import build_slides, render_html, write_pdf
from .config import Config
from .humanpass import clean_and_score, format_panel
from .profile_score import format_score, parse_profile, rubric_text, score_profile
from .textutil import ask_json, personal_claims, placeholders, split_blocks
from .topics import pick_week, slugify
from .writer import format_receipt, load_voice, polish, write_draft, write_hooks

BANNED_COMMENT_STARTS = (
    "great post",
    "love this",
    "so true",
    "couldn't agree more",
    "could not agree more",
    "this resonates",
)


def _folder(config: Config, name: str) -> Path:
    folder = config.output_dir / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _write(folder: Path, filename: str, text: str) -> Path:
    path = folder / filename
    path.write_text(text, encoding="utf-8")
    print(f"Saved {path}", flush=True)
    return path


def _mirror(config: Config, filename: str, text: str) -> None:
    """Keep a copy where the skills look: ~/.claude/linkedin/."""
    try:
        config.home_dir.mkdir(parents=True, exist_ok=True)
        (config.home_dir / filename).write_text(text, encoding="utf-8")
    except OSError as error:
        print(f"Could not copy {filename} to {config.home_dir}: {error}", flush=True)


def load_engage(path: Path) -> list[dict]:
    """Read `reach | Name | why` lines. Blank lines and comments are skipped."""
    if not path.exists():
        return []
    people = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            continue
        kind = parts[0].lower()
        if kind not in {"reach", "peer", "buyer"}:
            continue
        people.append({"kind": kind, "name": parts[1], "why": parts[2] if len(parts) > 2 else ""})
    return people


def week_plan(config: Config, *, draft: bool) -> int:
    """Four-post shape, with the story slot left blank until a real scene is on file."""
    voice = load_voice(config)
    slots = pick_week(config)
    labels = [
        ("TUE", "8:15", slots[0]),
        ("THU", "8:00", slots[1]),
        ("FRI", "8:30", slots[2]),
    ]
    monday = date.today() - timedelta(days=date.today().weekday())
    people = load_engage(config.engage_path)
    lines = [
        f"WEEK OF {monday.strftime('%b').upper()} {monday.day}",
        "",
        "Times are local, aimed at an India audience (IST).",
        "The day matters less than the first line. Fix a weak hook before you move the clock.",
        "",
        "MON  engage only  (20 min, list below)",
    ]
    for day, clock, topic in labels:
        lines.append(
            f"{day}  {clock}  {topic['type'].upper():<8} #{topic['hook_id']:<3} {topic['title_seed']}"
        )
        lines.append(f"     angle: {topic['angle']}")
    lines.extend(
        [
            "SAT  -",
            "SUN  -   STORY skipped. The proof list in the voice profile is empty, so no scene was invented.",
            "",
            "ENGAGE",
        ]
    )
    if not people:
        lines.append(
            "No names are listed in automation/engage.txt. "
            "Add lines like `reach | Name | why you can add something`. Names are not invented."
        )
    else:
        counts = {kind: 0 for kind in ("reach", "peer", "buyer")}
        for person in people:
            counts[person["kind"]] += 1
            why = f"  {person['why']}" if person["why"] else ""
            lines.append(f"  {person['kind']:<6} {person['name']}{why}")
        lines.append(
            f"  counts: {counts['reach']} reach / {counts['peer']} peers / {counts['buyer']} buyers "
            "(the working mix is 5 / 3 / 2)"
        )
    lines.extend(["", "Say write Tuesday, or run --week --draft, to draft the three posts.", ""])
    text = "\n".join(lines)
    config.state_dir.mkdir(parents=True, exist_ok=True)
    config.plan_path.write_text(text, encoding="utf-8")
    _mirror(config, "plan.md", text)
    print(text, flush=True)
    print(f"Saved {config.plan_path}", flush=True)
    if not draft:
        return 0
    # Drafts are a second step so a plan can be reviewed before any model call.
    gaps = config.missing(need_model=True)
    if gaps:
        for gap in gaps:
            print(f"- {gap}", flush=True)
        return 1
    folder = _folder(config, f"week-{monday.isoformat()}")
    _write(folder, "plan.md", text)
    for day, _clock, topic in labels:
        hooks, hook_model = write_hooks(config, topic, voice)
        raw, first_comment, draft_model = write_draft(config, topic, voice, hooks)
        polished = polish(config, raw, voice, topic)
        package = {
            "topic": topic,
            "hooks": hooks,
            "post": polished["post"],
            "first_comment": first_comment,
            "artefacts": polished["artefacts"],
            "overall": polished["overall"],
            "verdict": polished["verdict"],
            "issues": polished["issues"],
            "placeholders": polished["placeholders"],
            "models": {"hooks": hook_model, "draft": draft_model},
        }
        stem = f"{day.lower()}-{slugify(topic['title_seed'])}"
        _write(folder, f"{stem}.txt", polished["post"])
        _write(folder, f"{stem}.json", json.dumps(package, indent=2))
        print(format_receipt(package), flush=True)
    print("Drafts are saved. Paste the ones you want. Nothing was sent to LinkedIn.", flush=True)
    return 0


def _clean_piece(text: str) -> tuple[str, str]:
    clean, _report, results, overall, verdict = clean_and_score(text)
    return clean.strip() + "\n", f"{overall:.1f} {verdict}"


def comment_on(config: Config, path: Path) -> int:
    """Two comments of different types for one pasted post."""
    post = path.read_text(encoding="utf-8").strip()
    if not post:
        print("The file is empty.", flush=True)
        return 1
    voice = load_voice(config)
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        "Write two LinkedIn comments on the post below. Different types. "
        "Types: add a datum, add the missing case, respectful disagree, extend one line, "
        "ask the real question, the receipt, the correction, the reframe, the one-liner. "
        "2 to 4 sentences, or under 12 words for a one-liner. "
        "Never open with Great post, Love this, So true, or the author's name and an exclamation. "
        "Do not invent a number. Use {{your number}} if you need one. "
        'JSON: {"options": [{"type": "", "text": ""}], "ship": 0, "why": ""}\n\n'
        f"POST:\n{post}"
    )
    payload, used = ask_json(config, config.model_script, prompt, max_tokens=900)
    options = []
    for item in payload.get("options") or []:
        if not isinstance(item, dict):
            continue
        raw = str(item.get("text", "")).strip()
        if not raw:
            continue
        opener = raw.lower()
        if any(opener.startswith(banned) for banned in BANNED_COMMENT_STARTS):
            continue
        clean, score = _clean_piece(raw)
        options.append({"type": str(item.get("type", "")).strip(), "text": clean.strip(), "score": score})
        if len(options) == 2:
            break
    if len(options) < 2:
        raise RuntimeError("The comment pass did not return two usable comments.")
    lines = [f"COMMENTS  model {used}", ""]
    for index, item in enumerate(options, start=1):
        lines.append(f"{index}. {item['type']}  human {item['score']}")
        lines.append(item["text"])
        lines.append("")
    lines.append(f"Ship {int(payload.get('ship', 0)) + 1}: {payload.get('why', '')}")
    lines.append("Paste the one you mean. Nothing was posted.")
    text = "\n".join(lines) + "\n"
    folder = _folder(config, "comment-" + date.today().isoformat())
    _write(folder, "comments.txt", text)
    print(text, flush=True)
    return 0


def keyword_bucket(text: str) -> tuple[str, str]:
    """Offline inbox sort. The tell is the phrase that fired."""
    low = text.lower()
    spam_tells = (
        "bitcoin",
        "crypto",
        "seo agency",
        "lead gen",
        "quick question",
        "i noticed you're",
        "i noticed you are",
        "calendly.com",
        "book a time",
    )
    for tell in spam_tells:
        if tell in low:
            return "SPAM", tell
    recruiter_tells = ("recruiter", "hiring", "this role", "salary", "opportunity at")
    for tell in recruiter_tells:
        if tell in low:
            return "RECRUITER", tell
    lead_tells = ("work together", "need help with", "looking for someone", "our pipeline", "can you build")
    for tell in lead_tells:
        if tell in low:
            return "LEAD", tell
    ask_tells = ("pick your brain", "quick favor", "quick favour", "intro to", "can you review")
    for tell in ask_tells:
        if tell in low:
            return "ASK", tell
    if "?" in text:
        return "ASK", "a question, no stronger tell"
    return "PEER", "no spam tell, same-field until you say otherwise"


def inbox_triage(config: Config, path: Path) -> int:
    """Sort pasted messages. A model reply is drafted only when the key is set."""
    blocks = split_blocks(path.read_text(encoding="utf-8"))
    if not blocks:
        print("The file is empty.", flush=True)
        return 1
    rows = []
    for block in blocks:
        bucket, tell = keyword_bucket(block)
        rows.append({"text": block, "bucket": bucket, "tell": tell, "reply": ""})
    if config.bedrock_token:
        voice = load_voice(config)
        prompt = (
            f"Voice profile:\n{voice}\n\n"
            "Confirm or correct the bucket for each message. Buckets: LEAD, RECRUITER, PEER, ASK, SPAM. "
            "Write a reply only for LEAD, RECRUITER, PEER, and a cheap ASK. SPAM gets an empty reply. "
            "Do not invent a meeting you did not have. "
            'JSON: {"items": [{"bucket": "", "tell": "", "reply": ""}]}\n\n'
            + json.dumps([{"bucket": row["bucket"], "tell": row["tell"], "text": row["text"]} for row in rows])
        )
        try:
            payload, _used = ask_json(config, config.model_script, prompt, max_tokens=1600)
            items = payload.get("items") or []
            for index, item in enumerate(items):
                if index >= len(rows) or not isinstance(item, dict):
                    continue
                bucket = str(item.get("bucket", "")).upper()
                if bucket in {"LEAD", "RECRUITER", "PEER", "ASK", "SPAM"}:
                    rows[index]["bucket"] = bucket
                if item.get("tell"):
                    rows[index]["tell"] = str(item["tell"])
                reply = str(item.get("reply") or "").strip()
                if reply and rows[index]["bucket"] != "SPAM":
                    clean, _score = _clean_piece(reply)
                    rows[index]["reply"] = clean.strip()
        except RuntimeError as error:
            print(f"Model triage failed ({error}). Keeping the keyword sort.", flush=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["bucket"]] = counts.get(row["bucket"], 0) + 1
    lines = ["INBOX  " + ", ".join(f"{count} {name.lower()}" for name, count in sorted(counts.items()))]
    lines.append("")
    for row in rows:
        lines.append(f"{row['bucket']}  tell: {row['tell']}")
        lines.append(row["text"].splitlines()[0][:160])
        if row["reply"]:
            lines.append("reply:")
            lines.append(row["reply"])
        elif row["bucket"] == "SPAM":
            lines.append("reply: none")
        lines.append("")
    text = "\n".join(lines)
    folder = _folder(config, "inbox-" + date.today().isoformat())
    _write(folder, "inbox.txt", text)
    print(text, flush=True)
    return 0


def reply_to(config: Config, path: Path) -> int:
    """Sort comments under your own post, then draft the ones worth answering."""
    comments = split_blocks(path.read_text(encoding="utf-8"))
    if not comments:
        print("The file is empty.", flush=True)
        return 1
    voice = load_voice(config)
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        "Sort each comment into LEAD, SUBSTANCE, PEER, SUPPORT, or NOISE. "
        "Write a reply for LEAD and SUBSTANCE, a short reply for PEER, at most eight words for SUPPORT, "
        "and an empty reply for NOISE. Answer the question in the thread. Do not invent a result. "
        'JSON: {"items": [{"bucket": "", "reply": ""}]}\n\n'
        + json.dumps(comments)
    )
    payload, _used = ask_json(config, config.model_script, prompt, max_tokens=1600)
    items = payload.get("items") or []
    counts: dict[str, int] = {}
    lines = ["REPLIES", ""]
    for index, comment in enumerate(comments):
        item = items[index] if index < len(items) and isinstance(items[index], dict) else {}
        bucket = str(item.get("bucket", "PEER")).upper()
        if bucket not in {"LEAD", "SUBSTANCE", "PEER", "SUPPORT", "NOISE"}:
            bucket = "PEER"
        counts[bucket] = counts.get(bucket, 0) + 1
        reply = str(item.get("reply") or "").strip()
        if reply and bucket != "NOISE":
            reply, score = _clean_piece(reply)
            reply = reply.strip()
            score_note = f"  human {score}"
        else:
            score_note = ""
        lines.append(f"{bucket}{score_note}")
        lines.append(comment.splitlines()[0][:160])
        if reply:
            lines.append(reply)
        lines.append("")
    lines.insert(1, ", ".join(f"{count} {name.lower()}" for name, count in sorted(counts.items())))
    text = "\n".join(lines) + "\n"
    folder = _folder(config, "reply-" + date.today().isoformat())
    _write(folder, "replies.txt", text)
    print(text, flush=True)
    return 0


def profile_report(config: Config, path: Path) -> int:
    """Local score first. A rewrite is requested only for the rows that lost most of their points."""
    raw = path.read_text(encoding="utf-8")
    rows = score_profile(raw)
    text = format_score(rows)
    folder = _folder(config, "profile-" + date.today().isoformat())
    _write(folder, "score.txt", text)
    print(text, flush=True)
    weak = [row for row in rows if row["points"] * 2 < row["max"]]
    if not weak:
        print("No section scored under half. No rewrite was requested.", flush=True)
        return 0
    if not config.bedrock_token:
        print("Rewrite skipped. Add the Bedrock key when you want new headline and about copy.", flush=True)
        return 0
    voice = load_voice(config)
    sections = parse_profile(raw)
    prompt = (
        f"Voice profile:\n{voice}\n\nRubric:\n{rubric_text(config)}\n\n"
        "Rewrite only the weak sections. Do not invent employers, numbers, or recommendations. "
        'JSON keys: "headline", "about", "role". Use an empty string for a section you cannot improve honestly.\n\n'
        f"Weak rows:\n{json.dumps(weak)}\n\nCurrent:\n{json.dumps(sections)}"
    )
    try:
        payload, _used = ask_json(config, config.model_longform, prompt, max_tokens=1400)
    except RuntimeError as error:
        print(f"Rewrite skipped ({error}). The score above is already saved.", flush=True)
        return 0
    blocks = []
    for key in ("headline", "about", "role"):
        value = str(payload.get(key) or "").strip()
        if not value:
            continue
        clean, _score = _clean_piece(value)
        claims = personal_claims(clean, voice)
        if claims:
            clean = clean.rstrip() + "\n{{your number}}  (a claim was removed: " + ", ".join(claims) + ")\n"
        blocks.append(f"{key.upper()}\n{clean.strip()}")
    rewrite = "\n\n".join(blocks) + "\n"
    _write(folder, "rewrite.txt", rewrite)
    print(rewrite, flush=True)
    return 0


def carousel(config: Config, concept: str) -> int:
    """Slide copy, the feed post above it, and a PDF when Chrome is available."""
    voice = load_voice(config)
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        f"Build a LinkedIn carousel for: {concept}\n"
        "8 to 12 slides total. Cover headline is 6 words or fewer. "
        "Each point slide has a headline of 3 to 7 words and a body of at most 25 words. "
        "One idea per slide. No invented metric. "
        'JSON keys: "cover" ({headline, promise}), "stake", "slides" (list of {headline, body}), '
        '"recap" (list of short lines), "cta", "post" (the 2 or 3 lines that sit above the PDF).'
    )
    payload, used = ask_json(config, config.model_longform, prompt, max_tokens=1800)
    slides = build_slides(payload)
    post = str(payload.get("post") or "").strip()
    if post:
        post, _score = _clean_piece(post)
    lines = [f"CAROUSEL  {len(slides)} slides  model {used}", ""]
    if len(slides) < 8:
        lines.append("Under 8 slides. This idea may be a text post. The copy is still saved.")
        lines.append("")
    for index, slide in enumerate(slides, start=1):
        lines.append(f"{index}/{len(slides)}  {slide['headline']}")
        if slide["body"]:
            lines.append(slide["body"])
        lines.append("")
    if post:
        lines.append("POST ABOVE THE PDF")
        lines.append(post.strip())
    text = "\n".join(lines) + "\n"
    folder = _folder(config, "carousel-" + slugify(concept).lower())
    _write(folder, "slides.txt", text)
    html = render_html(slides)
    html_path = _write(folder, "slides.html", html)
    write_pdf(html_path, folder / "slides.pdf")
    print(text, flush=True)
    print("Upload the PDF yourself if you want it on LinkedIn.", flush=True)
    return 0


def repurpose(config: Config, path: Path) -> int:
    """Pull standalone posts out of a transcript. A summary is not a post."""
    source = path.read_text(encoding="utf-8").strip()
    words = source.split()
    if len(words) < 80:
        print("The source is under 80 words. Four posts from it would be thin. Paste a longer transcript.", flush=True)
        return 1
    voice = load_voice(config)
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        "Extract claims, numbers, stories, mechanisms, mistakes, and quotable lines from the source. "
        "Then write up to four LinkedIn posts. Each post must stand alone. "
        "Every number in a post must appear in the source. Otherwise use {{your number}} or omit it. "
        'JSON: {"counts": {"claims": 0, "numbers": 0, "stories": 0, "mechanisms": 0, "mistakes": 0, "lines": 0}, '
        '"posts": [{"angle": "", "post": ""}]}\n\nSOURCE:\n'
        + source[:12000]
    )
    payload, _used = ask_json(config, config.model_longform, prompt, max_tokens=2500)
    folder = _folder(config, "repurpose-" + date.today().isoformat())
    counts = payload.get("counts") or {}
    lines = ["EXTRACT", json.dumps(counts), ""]
    posts = payload.get("posts") or []
    if len(posts) < 4:
        lines.append(f"Only {len(posts)} posts came out of this source. Fewer than four means it was thin.")
        lines.append("")
    for index, item in enumerate(posts[:4], start=1):
        if not isinstance(item, dict):
            continue
        raw = str(item.get("post") or "").strip()
        if not raw:
            continue
        clean, _score = _clean_piece(raw)
        claims = personal_claims(clean, source + "\n" + voice)
        if claims:
            clean = clean.rstrip() + "\n"
        lines.append(f"POST {index}  {item.get('angle', '')}")
        if claims:
            lines.append("Check these claims against the source: " + ", ".join(claims))
        if placeholders(clean):
            lines.append("Placeholders: " + ", ".join(placeholders(clean)))
        lines.append(clean.strip())
        lines.append("")
        _write(folder, f"post-{index}.txt", clean)
    text = "\n".join(lines) + "\n"
    _write(folder, "extract.txt", text)
    print(text, flush=True)
    return 0


def write_dm(config: Config, who: str, reason: str, want: str) -> int:
    """Invite note under 200 characters, then a first message and two follow-ups."""
    if not who.strip() or not reason.strip() or not want.strip():
        print("A DM needs --who, --reason, and --want. A message with no reason is what everyone sends.", flush=True)
        return 1
    voice = load_voice(config)
    prompt = (
        f"Voice profile:\n{voice}\n\n"
        f"Who: {who}\nWhy now: {reason}\nWhat I want, internally: {want}\n"
        "Write a LinkedIn invite note of at most 200 characters, including spaces. "
        "It references them, says who I am in one line, and asks for nothing. "
        "Then a first DM that does not pitch, and two follow-ups. Two, not five. "
        "The follow-ups add a new specific detail. They do not say just bumping this. "
        'JSON: {"invite": "", "first": "", "followup_1": "", "followup_2": ""}'
    )
    payload, _used = ask_json(config, config.model_script, prompt, max_tokens=900)
    invite = " ".join(str(payload.get("invite") or "").split())
    if len(invite) > 200:
        shorten, _used_model = ask_json(
            config,
            config.model_script,
            'Shorten this invite note to 200 characters or fewer, including spaces. JSON key "invite".\n' + invite,
            max_tokens=300,
        )
        invite = " ".join(str(shorten.get("invite") or invite).split())
    lines = [
        f"INVITE  {len(invite)} / 200 characters",
        invite,
        "",
        "FIRST",
        str(payload.get("first") or "").strip(),
        "",
        "FOLLOW-UP 1",
        str(payload.get("followup_1") or "").strip(),
        "",
        "FOLLOW-UP 2",
        str(payload.get("followup_2") or "").strip(),
        "",
        "Send these yourself. The runner does not open LinkedIn messages.",
    ]
    if len(invite) > 200:
        lines.insert(2, "Still over 200 characters. Cut it before you paste.")
    text = "\n".join(lines) + "\n"
    folder = _folder(config, "dm-" + date.today().isoformat())
    _write(folder, "dm.txt", text)
    print(text, flush=True)
    return 0


def humanize_file(path: Path) -> int:
    """Clean one file and print the five-check panel. No model call."""
    raw = path.read_text(encoding="utf-8")
    clean, report, results, overall, verdict = clean_and_score(raw)
    panel = format_panel(results, overall, verdict)
    out = path.with_name(path.stem + ".clean.txt")
    out.write_text(clean, encoding="utf-8")
    print(clean, flush=True)
    print(panel, flush=True)
    removed = sum(item["count"] for group in ("invisible", "typographic", "lexical") for item in report.get(group, []))
    print(f"{removed} artefacts stripped. Clean copy: {out}", flush=True)
    if verdict != "PASS":
        print("Structural tells were flagged in the panel. Rewrite those lines, then run --human again.", flush=True)
    return 0

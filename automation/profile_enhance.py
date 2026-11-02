"""Enhance the full profile with Claude, one section at a time.

The profile is the resume record. Nothing is read from a request body, and nothing is written to LinkedIn.
A section is kept only when its facts, keywords, and tone checks pass.
The dry run stores that review in dry-run.json. The original call writes the paste files only after every section passes.
"""

import json
import re
from pathlib import Path

from .bedrock import ask
from .config import Config
from .humanpass import clean_and_score
from .profile_kit import source_profile
from .resume_facts import ALLOWED_NUMBERS, KEYWORD_ORDER, SEARCH_TITLES, source_text
from .textutil import extract_json

# Claude may rewrite these, and no others. The order is the fallback when the model skips one.
SECTION_ORDER = (
    "headline",
    "banner",
    "about",
    "experience",
    "skills",
    "education",
    "featured",
    "contact",
)

SYSTEM = (
    "You rewrite one LinkedIn profile section so a recruiter can match it to a DevOps, cloud, SRE, or platform role. "
    "Reply with one JSON object and no markdown. "
    "Use only the facts, employers, dates, and numbers in the source. "
    "Do not invent tools, seniority, or years of experience. "
    "Sound like a person. No 'passionate', no 'results-driven', no emoji, no hashtag."
)

# Numbers are captured as a whole token so 80% is not stored as 80, and 10+ is not stored as 10.
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%|\d+GB\+?|\d+\+|\d+(?:\.\d+)?", re.IGNORECASE)
BANNED = ("passionate", "results-driven", "results driven", "team player", "synergy")
PASTE_ORDER = (
    "PASTE ORDER\n"
    "1. Photo, if the current one is older than two years or the face is small.\n"
    "2. banner.txt\n"
    "3. headline.txt\n"
    "4. about.txt\n"
    "5. One current SproutsAI role, from experience.txt.\n"
    "6. Techin IT, then education.txt.\n"
    "7. Pin the skills in skills.txt, top of the list first.\n"
    "8. featured.txt: portfolio, then one project, then the newest roadmap post.\n"
    "9. contact.txt. Open to work for the roles listed there.\n"
    "\n"
    "LinkedIn was not edited. Paste a section only after you have read enhanced.json.\n"
)


def recruiter_keywords(source: dict) -> list[str]:
    """Job titles and tools that already appear on the resume, in recruiter search order."""
    blob = (json.dumps(source) + "\n" + source_text()).lower()
    found: list[str] = []
    for phrase in list(SEARCH_TITLES) + list(KEYWORD_ORDER):
        if phrase.lower() in blob and phrase not in found:
            found.append(phrase)
    return found


def _allowed_blob(source: dict) -> str:
    """Every fact the rewrite is allowed to repeat."""
    return json.dumps(source) + "\n" + source_text() + "\n" + " ".join(ALLOWED_NUMBERS)


def _numbers(text: str) -> set[str]:
    return {token.lower() for token in NUMBER_RE.findall(text)}


def _polish(text: str) -> tuple[str, str, float]:
    """Strip machine characters, then keep the human-check verdict beside the section."""
    clean, _report, _results, overall, verdict = clean_and_score(text)
    return clean.strip(), verdict, round(overall, 1)


def _call(ask_fn, prompt: str, max_tokens: int) -> tuple[dict, str]:
    """Accept either a raw JSON object or the (object, model id) pair the live client returns."""
    result = ask_fn(prompt, max_tokens)
    if isinstance(result, tuple):
        return result[0], str(result[1])
    return result, "stub"


def normalize_selection(raw) -> list[str]:
    """Keep Claude's order, then append any profile section it left out."""
    chosen: list[str] = []
    for item in raw or []:
        name = str(item).strip().lower()
        if name in SECTION_ORDER and name not in chosen:
            chosen.append(name)
    for name in SECTION_ORDER:
        if name not in chosen:
            chosen.append(name)
    return chosen


def _before(source: dict, name: str):
    """The current copy for one section. Headline and banner are empty until a rewrite exists."""
    if name == "headline":
        return source.get("headline") or ""
    if name == "banner":
        return source.get("banner") or ""
    if name == "about":
        return source.get("about") or ""
    if name == "experience":
        return source.get("experience") or []
    if name == "skills":
        return source.get("skills") or []
    if name == "education":
        return source.get("education") or []
    if name == "featured":
        return source.get("featured") or []
    return {
        "custom_url": source.get("contact", {}).get("linkedin", ""),
        "portfolio": source.get("contact", {}).get("portfolio", ""),
        "email": source.get("contact", {}).get("email", ""),
        "phone": source.get("contact", {}).get("phone", ""),
    }


def _shape(name: str) -> str:
    """The JSON object Claude must return for this section."""
    if name in {"headline", "about", "banner"}:
        return '{"text": "..."}'
    if name == "experience":
        return (
            '{"roles": [{"current": true, "title": "", "company": "", "location": "", '
            '"start": "", "end": "", "bullets": [""]}]}'
        )
    if name == "skills":
        return '{"pin_first": [""], "then": [""]}'
    if name == "education":
        return '{"schools": [{"school": "", "degree": "", "start": "", "end": "", "detail": ""}]}'
    if name == "featured":
        return '{"items": [{"title": "", "url": ""}]}'
    return (
        '{"custom_url": "", "portfolio": "", "keep_existing_email_and_phone": true, '
        '"open_to_work": [""]}'
    )


def _canonical(name: str, payload: dict):
    """Pull the section body out of Claude's object."""
    if name in {"headline", "about", "banner"}:
        return " ".join(str(payload.get("text") or "").split()) if name != "about" else str(payload.get("text") or "").strip()
    if name == "experience":
        return payload.get("roles") or []
    if name == "skills":
        return {"pin_first": payload.get("pin_first") or [], "then": payload.get("then") or []}
    if name == "education":
        return payload.get("schools") or []
    if name == "featured":
        return payload.get("items") or []
    return {
        "custom_url": str(payload.get("custom_url") or "").strip(),
        "portfolio": str(payload.get("portfolio") or "").strip(),
        "keep_existing_email_and_phone": bool(payload.get("keep_existing_email_and_phone", True)),
        "open_to_work": payload.get("open_to_work") or [],
    }


def _banned(text: str) -> list[str]:
    low = text.lower()
    return [phrase for phrase in BANNED if phrase in low]


def _invented_numbers(text: str, allowed: set[str]) -> list[str]:
    bad = []
    for token in _numbers(text):
        if token not in allowed:
            bad.append(token)
    return bad


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    low = text.lower()
    return [phrase for phrase in keywords if phrase.lower() in low]


def validate_section(name: str, content, allowed_numbers: set[str], keywords: list[str]) -> list[str]:
    """Return the reasons a section cannot be saved. An empty list means it passed."""
    errors: list[str] = []
    if name in {"headline", "about", "banner"}:
        text = str(content or "")
        # Tone and facts apply to every prose section.
        errors.extend(f"banned phrase: {phrase}" for phrase in _banned(text))
        invented = _invented_numbers(text, allowed_numbers)
        if invented:
            errors.append("invented numbers: " + ", ".join(invented))
        if re.search(r"\b(senior|staff|principal)\b", text, re.IGNORECASE):
            errors.append("do not claim a senior title")
        if re.search(r"\b\d+\+?\s+years\b", text, re.IGNORECASE):
            errors.append("do not invent years of experience")
        if "#" in text:
            errors.append("no hashtags")
    if name == "headline":
        text = str(content or "")
        if not 40 <= len(text) <= 220:
            errors.append(f"headline length {len(text)} is outside 40 to 220")
        if len(_keyword_hits(text, keywords)) < 2:
            errors.append("headline needs at least two resume keywords a recruiter would search")
    elif name == "banner":
        text = str(content or "")
        if not text or "\n" in text or len(text) > 120:
            errors.append("banner must be one line of 120 characters or fewer")
        if not _keyword_hits(text, keywords):
            errors.append("banner needs one resume keyword")
    elif name == "about":
        text = str(content or "")
        if not 200 <= len(text) <= 1600:
            errors.append(f"about length {len(text)} is outside 200 to 1600")
        if "sandeep" in text[:80].lower():
            errors.append("about must not open with your name")
        if not any(word in text.lower() for word in ("devops", "cloud", "sre", "platform")):
            errors.append("about must name DevOps, cloud, SRE, or platform")
        if len(_keyword_hits(text, keywords)) < 2:
            errors.append("about needs at least two resume keywords")
    elif name == "experience":
        roles = content if isinstance(content, list) else []
        if len(roles) != 2:
            errors.append("experience must be one SproutsAI role and one Techin IT role")
        for role in roles:
            if not isinstance(role, dict):
                errors.append("a role must be an object")
                continue
            company = str(role.get("company") or "")
            low = company.lower()
            # Only the two employers on the resume are allowed.
            if "sproutsai" not in low and "techin" not in low:
                errors.append(f"unknown company: {company}")
            bullets = role.get("bullets") or []
            if not isinstance(bullets, list) or len(bullets) < 2:
                errors.append(f"{company or 'role'} needs at least two bullets")
            for bullet in bullets:
                bullet_text = str(bullet)
                errors.extend(f"banned phrase: {phrase}" for phrase in _banned(bullet_text))
                invented = _invented_numbers(bullet_text, allowed_numbers)
                if invented:
                    errors.append("invented numbers: " + ", ".join(invented))
    elif name == "skills":
        pin = content.get("pin_first") if isinstance(content, dict) else None
        if not isinstance(pin, list) or not 3 <= len(pin) <= 12:
            errors.append("pin_first must list 3 to 12 skills")
    elif name == "education":
        schools = content if isinstance(content, list) else []
        if len(schools) != 2:
            errors.append("education must keep both schools from the resume")
        for school in schools:
            label = str(school.get("school") if isinstance(school, dict) else "")
            low = label.lower()
            if "vishnu" not in low and "seetha" not in low:
                errors.append(f"unknown school: {label}")
            detail = json.dumps(school)
            invented = _invented_numbers(detail, allowed_numbers)
            if invented:
                errors.append("invented numbers: " + ", ".join(invented))
    elif name == "featured":
        items = content if isinstance(content, list) else []
        if not 1 <= len(items) <= 3:
            errors.append("featured needs one to three items")
        for item in items:
            url = str(item.get("url") or "") if isinstance(item, dict) else ""
            if url and "sandeepkalyan-portfolio.vercel.app" not in url:
                errors.append(f"featured url is not the portfolio: {url}")
    elif name == "contact":
        if not isinstance(content, dict):
            errors.append("contact must be an object")
        else:
            url = str(content.get("custom_url") or "")
            portfolio = str(content.get("portfolio") or "")
            if "sandeep-kalyan" not in url:
                errors.append("custom url must stay linkedin.com/in/sandeep-kalyan")
            if "sandeepkalyan-portfolio.vercel.app" not in portfolio:
                errors.append("portfolio must stay the vercel portfolio")
            if content.get("keep_existing_email_and_phone") is not True:
                errors.append("keep the email and phone already on the profile")
            roles = content.get("open_to_work") or []
            if not isinstance(roles, list) or not roles:
                errors.append("open_to_work needs at least one target role")
            for role in roles:
                if role not in SEARCH_TITLES:
                    errors.append(f"open_to_work role is not a target title: {role}")
    return errors


def validate_against_source(name: str, content, source: dict, keywords: list[str]) -> list[str]:
    """Fact check against the resume, including dates that are not bare numbers."""
    allowed = _numbers(_allowed_blob(source))
    errors = validate_section(name, content, allowed, keywords)
    if name == "experience" and isinstance(content, list):
        # Each role's start and end must appear inside a resume date range for that company.
        ranges = []
        for role in source.get("experience") or []:
            ranges.append((str(role.get("company") or "").lower(), str(role.get("when") or "")))
        for role in content:
            if not isinstance(role, dict):
                continue
            company = str(role.get("company") or "").lower()
            start = str(role.get("start") or "")
            end = str(role.get("end") or "")
            matched = False
            for source_company, when in ranges:
                same = ("sproutsai" in company and "sproutsai" in source_company) or (
                    "techin" in company and "techin" in source_company
                )
                if same and start and end and start in when and end in when:
                    matched = True
            if not matched:
                errors.append(f"dates do not match the resume: {start} {end}")
    if name == "skills" and isinstance(content, dict):
        blob = _allowed_blob(source).lower()
        for skill in list(content.get("pin_first") or []) + list(content.get("then") or []):
            if str(skill).lower() not in blob:
                errors.append(f"skill is not on the resume: {skill}")
    if name == "about":
        _clean, verdict, overall = _polish(str(content))
        if verdict == "FLAGGED":
            errors.append(f"about reads as machine copy ({overall})")
    return errors


def _polish_content(name: str, content):
    """Clean prose. Structured fields keep their keys and only the sentences are cleaned."""
    if name in {"headline", "banner"}:
        text, verdict, overall = _polish(str(content))
        return " ".join(text.split()), verdict, overall
    if name == "about":
        text, verdict, overall = _polish(str(content))
        return text, verdict, overall
    if name == "experience" and isinstance(content, list):
        cleaned = []
        verdicts = []
        for role in content:
            if not isinstance(role, dict):
                cleaned.append(role)
                continue
            role = dict(role)
            bullets = []
            for bullet in role.get("bullets") or []:
                text, verdict, _overall = _polish(str(bullet))
                bullets.append(" ".join(text.split()))
                verdicts.append(verdict)
            role["bullets"] = bullets
            cleaned.append(role)
        verdict = "FLAGGED" if "FLAGGED" in verdicts else "PASS"
        return cleaned, verdict, 0
    return content, "PASS", 0


def _rewrite_prompt(name: str, source: dict, keywords: list[str], errors: list[str]) -> str:
    """One section, the facts it may use, and the recruiter keywords that are already true."""
    feedback = ""
    if errors:
        feedback = "The previous draft failed these checks:\n- " + "\n- ".join(errors) + "\nFix only those points.\n"
    return (
        f"TASK: rewrite\nSECTION: {name}\n"
        f"{feedback}"
        "Use recruiter keywords from this list when they are true for this section. Do not add the rest.\n"
        f"KEYWORDS: {json.dumps(keywords)}\n"
        "Collapse the two SproutsAI titles that share Apr 2025 - Present into one current DevOps Engineer role. "
        "Keep Techin IT as the previous role. Copy dates exactly.\n"
        f"SOURCE SECTION:\n{json.dumps(_before(source, name), indent=2)}\n"
        f"ALLOWED FACTS:\n{source_text()}\n"
        f"Return { _shape(name) }"
    )


def _select_prompt(source: dict) -> str:
    """Ask which sections to rewrite. Missing names are added back in normalize_selection."""
    brief = {
        "headline": _before(source, "headline"),
        "about": str(_before(source, "about"))[:500],
        "experience": [
            {"title": role.get("title"), "company": role.get("company"), "when": role.get("when")}
            for role in source.get("experience") or []
        ],
        "education": [school.get("school") for school in source.get("education") or []],
        "skills": [item.get("name") for item in source.get("skills") or [] if isinstance(item, dict)],
    }
    return (
        "TASK: select\n"
        "Choose the order in which to rewrite this LinkedIn profile for a recruiter. "
        f"Sections: {', '.join(SECTION_ORDER)}. "
        'Return {"sections": ["headline"]}.\n'
        + json.dumps(brief)
    )


def _flush(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _render_experience(roles: list) -> str:
    blocks = []
    for role in roles:
        label = "CURRENT ROLE" if role.get("current") else "PREVIOUS ROLE"
        place = f" · {role['location']}" if role.get("location") else ""
        bullets = "\n".join(f"- {bullet}" for bullet in role.get("bullets") or [])
        blocks.append(
            f"{label}\n\n{role.get('title')}\n{role.get('company')}{place}\n"
            f"{role.get('start')} - {role.get('end')}\n\n{bullets}"
        )
    return "\n\n".join(blocks) + "\n"


def _render_skills(skills: dict) -> str:
    pin = "\n".join(skills.get("pin_first") or [])
    rest = "\n".join(skills.get("then") or [])
    return f"PIN FIRST\n{pin}\n\nTHEN\n{rest}\n"


def _render_education(schools: list) -> str:
    blocks = []
    for school in schools:
        blocks.append(
            f"{school.get('degree')}\n{school.get('school')}\n"
            f"{school.get('start')} - {school.get('end')}\n{school.get('detail') or ''}".rstrip()
        )
    return "\n\n".join(blocks) + "\n"


def _render_featured(items: list) -> str:
    lines = []
    for index, item in enumerate(items, start=1):
        url = f" {item.get('url')}" if item.get("url") else ""
        lines.append(f"{index}. {item.get('title')}{url}")
    return "\n".join(lines) + "\n"


def _render_contact(contact: dict) -> str:
    roles = ", ".join(contact.get("open_to_work") or [])
    return (
        f"Custom URL: {contact.get('custom_url')}\n"
        f"Portfolio: {contact.get('portfolio')}\n"
        "Keep the email and phone already on the profile.\n"
        f"Open to work: {roles}\n"
    )


def _write_section_file(folder: Path, name: str, content) -> Path:
    """Write one paste file. The caller invokes this once per section, after every check has passed."""
    if name == "headline":
        path, text = folder / "headline.txt", str(content).strip() + "\n"
    elif name == "about":
        path, text = folder / "about.txt", str(content).strip() + "\n"
    elif name == "banner":
        path, text = folder / "banner.txt", str(content).strip() + "\n"
    elif name == "experience":
        path, text = folder / "experience.txt", _render_experience(content)
    elif name == "skills":
        path, text = folder / "skills.txt", _render_skills(content)
    elif name == "education":
        path, text = folder / "education.txt", _render_education(content)
    elif name == "featured":
        path, text = folder / "featured.txt", _render_featured(content)
    else:
        path, text = folder / "contact.txt", _render_contact(content)
    path.write_text(text, encoding="utf-8")
    return path


def _live_ask(config: Config):
    """Claude on Bedrock. The model id is the long-form Claude already configured for this runner."""

    def ask_fn(prompt: str, max_tokens: int) -> tuple[dict, str]:
        raw, used = ask(config, config.model_longform, prompt, max_tokens=max_tokens, system=SYSTEM)
        return extract_json(raw), used

    return ask_fn


def run_profile_enhance(config: Config, *, dry_run: bool, ask_fn=None, folder: Path | None = None) -> dict:
    """Collect the resume profile, enhance every section, and save only a fully valid result."""
    folder = folder or (config.output_dir / "profile")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("dry-run.json" if dry_run else "enhanced.json")
    source = source_profile()
    keywords = recruiter_keywords(source)
    payload = {
        "dry_run": dry_run,
        "linkedin_changed": False,
        "drive_uploaded": False,
        "applied": False,
        "status": "running",
        "file": str(path),
        "keywords": keywords,
        "source": source,
        "selected_sections": [],
        "sections": [],
        "updated": [],
        "enhanced": None,
    }
    _flush(path, payload)

    # No request body. The full profile is the resume already stored for this account.
    if ask_fn is None and not config.bedrock_token:
        payload["status"] = "failed"
        payload["error"] = "AWS_BEARER_TOKEN_BEDROCK is empty. Add it to automation/.env before enhancing the profile."
        _flush(path, payload)
        return payload
    if ask_fn is None:
        ask_fn = _live_ask(config)

    # Claude picks the order. Any section it skips is still rewritten, so the file covers the whole profile.
    try:
        selected_raw, model = _call(ask_fn, _select_prompt(source), 400)
        payload["model"] = model
        selected = normalize_selection(selected_raw.get("sections") if isinstance(selected_raw, dict) else [])
    except Exception as error:
        payload["status"] = "failed"
        payload["error"] = str(error)
        _flush(path, payload)
        return payload
    payload["selected_sections"] = selected
    _flush(path, payload)

    drafted = []
    for name in selected:
        errors: list[str] = []
        content = None
        verdict = ""
        overall = 0
        model = payload.get("model", "")
        # One retry sends the failed checks back. A third guess is not taken.
        for _attempt in range(2):
            try:
                raw, model = _call(ask_fn, _rewrite_prompt(name, source, keywords, errors), 1600)
                content = _canonical(name, raw if isinstance(raw, dict) else {})
                content, verdict, overall = _polish_content(name, content)
                errors = validate_against_source(name, content, source, keywords)
            except Exception as error:
                errors = [str(error)]
                content = None
            if not errors:
                break
        entry = {
            "name": name,
            "status": "validated" if not errors else "failed",
            "errors": errors,
            "model": model,
            "human_verdict": verdict,
            "human_score": overall,
            "before": _before(source, name),
            "after": content,
        }
        drafted.append(entry)
        # The review file grows section by section. applied stays false until every section has passed.
        payload["sections"] = drafted
        _flush(path, payload)

    if any(entry["status"] != "validated" for entry in drafted):
        payload["status"] = "failed"
        payload["enhanced"] = None
        payload["note"] = (
            "One or more sections failed validation. Nothing was saved as the profile to paste, "
            "nothing was uploaded, and LinkedIn was not changed."
        )
        _flush(path, payload)
        return payload

    # Every section passed. Write the enhanced object one section at a time, then the paste files.
    payload["status"] = "writing"
    payload["enhanced"] = {}
    _flush(path, payload)
    files: list[str] = []
    for entry in drafted:
        payload["enhanced"][entry["name"]] = entry["after"]
        payload["updated"].append(entry["name"])
        if not dry_run:
            files.append(str(_write_section_file(folder, entry["name"], entry["after"])))
        _flush(path, payload)
    if not dry_run:
        order_path = folder / "PASTE-ORDER.txt"
        order_path.write_text(PASTE_ORDER, encoding="utf-8")
        files.append(str(order_path))
        files.append(str(path))
    payload["files"] = files
    payload["applied"] = True
    payload["status"] = "ready"
    payload["headline"] = payload["enhanced"].get("headline", "")
    payload["about"] = payload["enhanced"].get("about", "")
    payload["local_folder"] = str(folder)
    payload["note"] = (
        "Every section passed. LinkedIn was not changed. "
        + (
            "Read dry-run.json and paste the enhanced sections yourself if they look right."
            if dry_run
            else "The paste files were written. Drive upload runs only after this point."
        )
    )
    _flush(path, payload)
    return payload

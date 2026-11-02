"""Find 0-3 year roles, tailor a resume from the source facts, and record the apply link.

Public job boards supply the listings. Claude ranks them when the Bedrock key is set.
The apply link is saved with the PDF. The server does not submit the application.
"""

import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from .config import Config
from .resume_facts import (
    ADDITIONAL,
    CERTIFICATIONS,
    EDUCATION,
    EXPERIENCES,
    LEADERSHIP,
    PROJECTS,
    SEARCH_TITLES,
    SKILL_GROUPS,
    SKILLS,
    SUMMARY,
    matched_keywords,
    source_text,
)
from .resume_pdf import write_resume_pdf

SENIOR = re.compile(
    r"\b(senior|sr\.?|staff|principal|director|head of|vp\b|vice president|architect)\b",
    re.IGNORECASE,
)
LEAD = re.compile(r"\b(lead|manager)\b", re.IGNORECASE)
YEARS = re.compile(r"\b(\d+)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)
PERCENT = re.compile(r"\b\d+(?:\.\d+)?%|\b\d+\+|500GB\+|8\.89|99\.9%")
FIT_WORDS = (
    "devops",
    "sre",
    "reliability",
    "platform",
    "kubernetes",
    "k8s",
    "cloud",
    "terraform",
    "observability",
    "monitoring",
    "mlops",
    "llmops",
    "cicd",
    "ci/cd",
    "release",
    "infrastructure",
    "devsecops",
    "gitops",
    "aws",
    "azure",
    "gcp",
    "automation",
)


def linkedin_searches() -> list[dict]:
    """Search links for the user to open. Entry level and Associate cover about 0-3 years."""
    links = []
    for title in SEARCH_TITLES:
        query = urllib.parse.quote(title)
        links.append(
            {
                "title": title,
                "experience": "0-3 years (LinkedIn Entry level and Associate)",
                "url": (
                    "https://www.linkedin.com/jobs/search/?keywords="
                    f"{query}&location=India&f_E=2%2C3&f_TPR=r604800&f_WT=2"
                ),
            }
        )
    return links


def too_senior(title: str, description: str) -> bool:
    """Drop senior, lead, and 4-year-plus asks. Plain 'engineer' titles stay."""
    if SENIOR.search(title) or LEAD.search(title):
        return True
    # Scan the whole posting. A 5-year requirement often sits below the opening paragraph.
    window = f"{title}\n{description}"
    for match in YEARS.finditer(window):
        if int(match.group(1)) >= 4:
            return True
    return False


def title_matches(title: str) -> bool:
    low = title.lower()
    return any(word in low for word in FIT_WORDS)


def _get_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; sandeep-job-assist/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _remotive(query: str) -> list[dict]:
    payload = _get_json("https://remotive.com/api/remote-jobs?search=" + urllib.parse.quote(query))
    rows = []
    for job in payload.get("jobs") or []:
        rows.append(
            {
                "source": "Remotive",
                "company": str(job.get("company_name") or "").strip(),
                "title": str(job.get("title") or "").strip(),
                "location": str(job.get("candidate_required_location") or "Remote"),
                "apply_url": str(job.get("url") or "").strip(),
                "description": re.sub(r"<[^>]+>", " ", str(job.get("description") or "")),
            }
        )
    return rows


def _jobicy(tag: str) -> list[dict]:
    payload = _get_json(f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={urllib.parse.quote(tag)}")
    rows = []
    for job in payload.get("jobs") or []:
        level = str(job.get("jobLevel") or "")
        rows.append(
            {
                "source": "Jobicy",
                "company": str(job.get("companyName") or "").strip(),
                "title": str(job.get("jobTitle") or "").strip(),
                "location": str(job.get("jobGeo") or "Remote"),
                "apply_url": str(job.get("url") or "").strip(),
                "description": f"{level} " + re.sub(r"<[^>]+>", " ", str(job.get("jobDescription") or "")),
            }
        )
    return rows


def _remoteok() -> list[dict]:
    payload = _get_json("https://remoteok.com/api")
    rows = []
    # The first element is a legal notice, not a job.
    for job in payload if isinstance(payload, list) else []:
        if not isinstance(job, dict):
            continue
        title = str(job.get("position") or "").strip()
        if not title:
            continue
        rows.append(
            {
                "source": "RemoteOK",
                "company": str(job.get("company") or "").strip(),
                "title": title,
                "location": str(job.get("location") or "Remote"),
                "apply_url": str(job.get("apply_url") or job.get("url") or "").strip(),
                "description": re.sub(r"<[^>]+>", " ", str(job.get("description") or "")),
            }
        )
    return rows


def _arbeitnow(query: str) -> list[dict]:
    payload = _get_json("https://www.arbeitnow.com/api/job-board-api")
    rows = []
    needle = query.lower()
    for job in payload.get("data") or []:
        title = str(job.get("title") or "")
        if needle.split()[0].lower() not in title.lower() and needle not in title.lower():
            continue
        rows.append(
            {
                "source": "Arbeitnow",
                "company": str(job.get("company_name") or "").strip(),
                "title": title.strip(),
                "location": str(job.get("location") or "Remote"),
                "apply_url": str(job.get("url") or "").strip(),
                "description": re.sub(r"<[^>]+>", " ", str(job.get("description") or "")),
            }
        )
    return rows


def collect_jobs(limit: int = 8) -> tuple[list[dict], list[str]]:
    """Public listings that match the title list and the 0-3 year band."""
    found: list[dict] = []
    errors: list[str] = []
    # Public boards, not a LinkedIn login. LinkedIn itself is returned as search links.
    for query in ("devops", "kubernetes", "sre", "cloud"):
        try:
            found.extend(_remotive(query))
        except Exception as error:
            errors.append(f"Remotive {query}: {error}")
        try:
            found.extend(_jobicy(query))
        except Exception as error:
            errors.append(f"Jobicy {query}: {error}")
    try:
        found.extend(_remoteok())
    except Exception as error:
        errors.append(f"RemoteOK: {error}")
    try:
        found.extend(_arbeitnow("devops"))
    except Exception as error:
        errors.append(f"Arbeitnow: {error}")
    kept = []
    seen = set()
    for job in found:
        key = (job["company"].lower(), job["title"].lower())
        if key in seen or not job["company"] or not job["title"]:
            continue
        if not title_matches(job["title"]) or too_senior(job["title"], job["description"]):
            continue
        seen.add(key)
        job["description"] = " ".join(job["description"].split())[:4000]
        job["fit"] = "unranked"
        kept.append(job)
        if len(kept) >= max(limit, 1) * 3:
            break
    return kept[: max(limit, 1)], errors


def rank_jobs(config: Config, jobs: list[dict]) -> list[dict]:
    """Ask Claude to order the list. The fallback keeps the filtered order."""
    if not jobs or not config.bedrock_token:
        return jobs
    brief = [
        {"i": index, "title": job["title"], "company": job["company"], "blurb": job["description"][:280]}
        for index, job in enumerate(jobs)
    ]
    prompt = (
        "The candidate has about 1 to 2 years of DevOps experience (started mid-2024) plus a B.Tech ending April 2026. "
        "He should apply to entry, associate, and junior roles, not senior roles. "
        "Rank the jobs that fit. Drop a poor fit by leaving it out. "
        'Return JSON: {"keep": [{"i": 0, "fit": "strong|good|stretch", "why": "one sentence"}]}.\n'
        + json.dumps(brief)
    )
    try:
        from .bedrock import ask
        from .textutil import extract_json

        raw, _used = ask(
            config,
            config.model_longform,
            prompt,
            max_tokens=900,
            system="You rank jobs against a resume. Reply with one JSON object and no markdown.",
        )
        payload = extract_json(raw)
        ordered = []
        for item in payload.get("keep") or []:
            index = item.get("i")
            if not isinstance(index, int) or not 0 <= index < len(jobs):
                continue
            job = dict(jobs[index])
            fit = str(item.get("fit") or "good")
            if fit not in {"strong", "good", "stretch"}:
                fit = "good"
            job["fit"] = fit
            job["why"] = str(item.get("why") or "").strip()
            ordered.append(job)
        return ordered or jobs
    except Exception:
        return jobs


def _overlap(bullet: str, description: str) -> int:
    words = set(re.findall(r"[a-z0-9+#]{3,}", description.lower()))
    return sum(1 for word in re.findall(r"[a-z0-9+#]{3,}", bullet.lower()) if word in words)


def _pick(bullets: list[str], description: str, count: int) -> list[str]:
    ranked = sorted(bullets, key=lambda bullet: _overlap(bullet, description), reverse=True)
    chosen = ranked[:count]
    # Keep original order so the resume still reads top to bottom.
    return [bullet for bullet in bullets if bullet in chosen]


def tailor_offline(company: str, title: str, description: str) -> dict:
    """Full original resume, plus job keywords that already appear on that resume."""
    keywords = matched_keywords(description)
    return {
        "company": company.strip() or "Company",
        "title": title.strip() or "DevOps Engineer",
        "summary": SUMMARY,
        "keywords": keywords,
        "roles": [
            {
                "title": role["title"],
                "company": role["company"],
                "when": role["when"],
                "where": role["where"],
                "bullets": list(role["bullets"]),
            }
            for role in EXPERIENCES
        ],
        "projects": PROJECTS,
        "skills": SKILLS,
        "skill_groups": SKILL_GROUPS,
        "education": [f"{item['detail']} — {item['school']} ({item['when']})" for item in EDUCATION],
        "education_blocks": EDUCATION,
        "certifications": CERTIFICATIONS,
        "leadership": LEADERSHIP,
        "additional": ADDITIONAL,
        "source": "original-resume",
    }


def invented_claims(summary_and_bullets: str) -> list[str]:
    """Percentages and plus-figures that are not on the source resume."""
    source = source_text()
    bad = []
    for match in PERCENT.findall(summary_and_bullets):
        if match not in source and match not in ALLOWED_LOOKUP(match, source):
            bad.append(match)
    return bad


def ALLOWED_LOOKUP(token: str, source: str) -> str:
    """80 and 80% are the same fact. Accept the form that appears in the source."""
    bare = token.replace("%", "").replace("+", "")
    if bare and bare in source:
        return token
    return ""


def tailor(config: Config, company: str, title: str, description: str) -> dict:
    """Build the resume from the original document. The model is not asked to rewrite it."""
    del config
    return tailor_offline(company, title, description)


def assess_apply(apply_url: str) -> dict:
    """Check the apply page and say whether a form was actually submitted.

    submitted stays false until an employer form accepts the PDF. Job boards in this
    pipeline put Apply behind an account dialog or a browser-only redirect, so this
    records the blocker instead of marking a resume as sent.
    """
    url = (apply_url or "").strip()
    if not url:
        return {
            "submitted": False,
            "submit_status": "not_submitted",
            "submit_reason": "This listing had no apply link. The PDF is saved and was not sent.",
        }
    host = urllib.parse.urlparse(url).netloc.lower()
    # These boards take an application only inside a logged-in session. There is no form to post.
    board_block = {
        "instahyre.com": "Instahyre accepts an application only from a logged-in candidate profile. The PDF was saved and was not sent.",
        "naukri.com": "Naukri accepts an application only from a logged-in account. The PDF was saved and was not sent.",
        "indeed.com": "Indeed accepts an application only from a logged-in account. The PDF was saved and was not sent.",
        "wellfound.com": "Wellfound accepts an application only from a logged-in account behind a browser check. The PDF was saved and was not sent.",
        "simplify.jobs": "Simplify accepts an application only inside a logged-in Simplify session. The PDF was saved and was not sent.",
    }
    for domain, reason in board_block.items():
        if domain in host:
            return {
                "submitted": False,
                "submit_status": "not_submitted",
                "submit_reason": reason,
                "checked_url": url,
            }
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            final_url = response.geturl()
            html = response.read(520000).decode("utf-8", "replace").lower()
    except Exception as error:
        return {
            "submitted": False,
            "submit_status": "not_submitted",
            "submit_reason": f"The apply page could not be opened ({error}). The PDF was not sent.",
            "checked_url": url,
        }
    # Each board stops before a form this process can post to.
    if "jv-open-apply-auth" in html or "registrationgateopened" in html:
        reason = (
            "Jobicy opens an account registration dialog before Apply Now. "
            "The PDF was not sent. Open the link, sign in, and attach the PDF."
        )
    elif "remoteok.com" in final_url.lower() or "action-apply" in html:
        reason = (
            "RemoteOK does not take the resume on this page. Apply opens the employer site in a browser. "
            "The PDF was not sent. Open the link and attach it there."
        )
    elif "challenges.cloudflare.com" in html or "turnstile" in html:
        reason = "The apply page is behind a Cloudflare check. The PDF was not sent."
    else:
        reason = "No application form was available to submit from this process. The PDF was not sent. Open the link and attach it."
    return {
        "submitted": False,
        "submit_status": "not_submitted",
        "submit_reason": reason,
        "checked_url": final_url,
    }


def safe_filename(company: str, title: str) -> str:
    """Company - Job Title, with characters a Drive file name will accept."""

    def clean(part: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9]+", " ", part)).strip()

    name = f"{clean(company)} - {clean(title)}".strip(" -")
    return name[:90] or "Application"


def write_application(config: Config, resume: dict, submit: dict | None = None) -> dict:
    """Write the PDF and markdown locally and append the apply record."""
    name = safe_filename(resume["company"], resume["title"])
    folder = config.applications_dir / name
    folder.mkdir(parents=True, exist_ok=True)
    pdf_path = write_resume_pdf(resume, folder / f"{name}.pdf")
    lines = [
        f"# {resume['company']} - {resume['title']}",
        "",
        resume["summary"],
        "",
    ]
    for role in resume["roles"]:
        lines.append(f"## {role['title']} — {role['company']} ({role['when']})")
        for bullet in role["bullets"]:
            lines.append(f"- {bullet}")
        lines.append("")
    for project in resume.get("projects") or []:
        if isinstance(project, dict):
            lines.append(f"## {project['title']}")
            for bullet in project["bullets"]:
                lines.append(f"- {bullet}")
            lines.append("")
    md_path = folder / f"{name}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    outcome = submit or {
        "submitted": False,
        "submit_status": "not_submitted",
        "submit_reason": "The PDF was saved. The employer form was not sent.",
    }
    record = {
        "date": date.today().isoformat(),
        "company": resume["company"],
        "title": resume["title"],
        "apply_url": resume.get("apply_url") or "",
        "pdf": str(pdf_path),
        "markdown": str(md_path),
        "status": "submitted" if outcome.get("submitted") else "prepared",
        "submitted": bool(outcome.get("submitted")),
        "submit_status": outcome.get("submit_status", "not_submitted"),
        "submit_reason": outcome.get("submit_reason", ""),
        "checked_url": outcome.get("checked_url", ""),
    }
    config.state_dir.mkdir(parents=True, exist_ok=True)
    with (config.state_dir / "applications.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record

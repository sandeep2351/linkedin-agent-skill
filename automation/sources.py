"""Pull 0-3 year roles from Naukri, Wellfound, Simplify, Indeed, and Instahyre.

Each source is one endpoint. A resume is sent only when that site exposes an
application form. These five sites do not. The record says why.
"""

import json
import re
import urllib.parse
import urllib.request

from .openroles import title_matches, too_senior

# Boards that answered this machine without a logged-in session.
BLOCKED = {
    "naukri": (
        "Naukri",
        "https://www.naukri.com/devops-engineer-jobs?k=devops%20engineer&experience=0&experience=3",
        "Naukri returned a page shell and no job list to an unsigned request. It has no apply API. No resume was sent. Open search_url in a browser where you are logged in.",
    ),
    "wellfound": (
        "Wellfound",
        "https://wellfound.com/role/r/devops-engineer",
        "Wellfound stops the request on a Cloudflare check. The job list and the apply button are behind that check. No resume was sent. Open search_url in a browser.",
    ),
    "simplify": (
        "Simplify",
        "https://simplify.jobs/jobs?q=DevOps%20Engineer",
        "Simplify's public page does not include a job list or an apply form for an unsigned request. No resume was sent. Open search_url in a browser.",
    ),
    "indeed": (
        "Indeed",
        "https://in.indeed.com/jobs?q=DevOps+Engineer&l=India&fromage=14&sc=0kf%3Aexplvl%28ENTRY_LEVEL%29%3B",
        "Indeed refused the request (HTTP 403). There is no candidate apply API for this account. No resume was sent. Open search_url in a browser.",
    ),
}

YEAR_RANGE = re.compile(r"\b(\d+)\s*(?:-|–|to)\s*(\d+)\s*years\b", re.IGNORECASE)
YEAR_PLUS = re.compile(r"\b(\d+)\s*\+\s*years\b", re.IGNORECASE)


def year_floor(text: str) -> int | None:
    """Lowest years figure in a posting. None when the posting does not state one."""
    if not text:
        return None
    floors = [int(match.group(1)) for match in YEAR_RANGE.finditer(text)]
    floors.extend(int(match.group(1)) for match in YEAR_PLUS.finditer(text))
    return min(floors) if floors else None


def _get(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json,text/html",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", "replace")


def _instahyre(limit: int) -> tuple[list[dict], list[str]]:
    """Entry-level feed, then keep titles that match the resume."""
    found: list[dict] = []
    seen = set()
    errors: list[str] = []
    # Four pages of the entry-level feed. The API ignores a keyword and returns a fixed page size.
    for offset in (0, 35, 70, 105):
        url = "https://www.instahyre.com/api/v1/job_search/?experience_level=entry_level&offset=" + str(offset)
        try:
            payload = json.loads(_get(url))
        except Exception as error:
            errors.append(f"Instahyre: {error}")
            break
        for job in payload.get("objects") or []:
            title = str(job.get("title") or "").strip()
            company = str((job.get("employer") or {}).get("company_name") or "").strip()
            if not title or not company:
                continue
            key = (company.lower(), title.lower())
            if key in seen:
                continue
            keywords = ", ".join(str(word) for word in (job.get("keywords") or []))
            description = f"{title} at {company}. Instahyre entry level. {keywords}"
            if not title_matches(title) or too_senior(title, description):
                continue
            floor = year_floor(description)
            if floor is not None and floor >= 4:
                continue
            seen.add(key)
            found.append(
                {
                    "source": "Instahyre",
                    "company": company,
                    "title": title,
                    "location": str(job.get("locations") or ""),
                    "apply_url": str(job.get("public_url") or "").strip(),
                    "description": description,
                    "fit": "good",
                    "why": "Instahyre lists this in the entry-level feed and the title matches the resume.",
                }
            )
            if len(found) >= limit:
                return found, errors
    return found, errors


def collect_source(name: str, limit: int) -> dict:
    """Jobs this source will actually return, plus the reason an apply did or did not happen."""
    limit = max(1, min(int(limit), 5))
    if name == "instahyre":
        jobs, errors = _instahyre(limit)
        note = (
            "Instahyre entry-level roles whose titles match the resume. "
            "Instahyre accepts an application only from a logged-in candidate profile, so the PDF is saved and not sent."
        )
        return {
            "source": "Instahyre",
            "jobs": jobs,
            "errors": errors,
            "search_url": "https://www.instahyre.com/search-jobs/",
            "note": note,
        }
    if name not in BLOCKED:
        raise KeyError(name)
    label, search_url, reason = BLOCKED[name]
    return {
        "source": label,
        "jobs": [],
        "errors": [reason],
        "search_url": search_url,
        "note": reason,
    }

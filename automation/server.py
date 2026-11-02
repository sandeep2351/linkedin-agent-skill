"""Local API for the profile, LinkedIn GIF posts, and prepared job applications.

Start it from the linkedin-agent-skill folder:

    automation/.venv/bin/python -m automation.server

Default port is 8787. Set API_PORT to change it.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config import Config
from .drivebox import APPLICATIONS_FOLDER, POSTS_FOLDER, PROFILE_FOLDER, upload_many
from .feed import build_pack, next_board
from .openroles import assess_apply, collect_jobs, linkedin_searches, rank_jobs, tailor, write_application
from .sources import collect_source
from .profile_enhance import run_profile_enhance

ENDPOINTS = [
    {
        "method": "GET",
        "path": "/",
        "purpose": "List every endpoint and the one-line purpose of each.",
    },
    {
        "method": "GET",
        "path": "/health",
        "purpose": "Check that the API process is up.",
    },
    {
        "method": "POST",
        "path": "/profile/enhance",
        "purpose": "Collect the full resume profile, ask Claude to enhance each section with recruiter keywords, and write the paste files only after every section passes validation. Then upload those files to the Sandeep LinkedIn Profile Drive folder. Does not edit LinkedIn.",
    },
    {
        "method": "POST",
        "path": "/profile/enhance/dry-run",
        "purpose": "Same Claude pass as /profile/enhance, with no request body. Saves each section into dry-run.json and writes the enhanced object only after every section passes. Does not edit LinkedIn and does not upload.",
    },
    {
        "method": "POST",
        "path": "/posts/create",
        "purpose": "Create the next roadmap GIF and caption, then upload them to the Sandeep LinkedIn Posts Drive folder.",
    },
    {
        "method": "POST",
        "path": "/posts/upload",
        "purpose": "Upload an existing post folder (post.gif and post.txt) to the Sandeep LinkedIn Posts Drive folder.",
    },
    {
        "method": "POST",
        "path": "/jobs",
        "purpose": "One process: collect 0-3 year roles, rank them with Claude, tailor a resume for each from the source resume, upload Company - Job Title.pdf to Sandeep Job Applications, and store each apply link. LinkedIn search links are in the same reply.",
    },
    {
        "method": "POST",
        "path": "/jobs/naukri",
        "purpose": "Pull 0-3 year DevOps-style roles from Naukri and apply with a tailored resume. Naukri does not return jobs or an apply form to an unsigned request, so the reply explains that and sends nothing.",
    },
    {
        "method": "POST",
        "path": "/jobs/wellfound",
        "purpose": "Pull 0-3 year DevOps-style roles from Wellfound and apply with a tailored resume. Wellfound stops on a Cloudflare check, so the reply explains that and sends nothing.",
    },
    {
        "method": "POST",
        "path": "/jobs/simplify",
        "purpose": "Pull 0-3 year DevOps-style roles from Simplify and apply with a tailored resume. Simplify does not publish a job list or an apply form to an unsigned request, so the reply explains that and sends nothing.",
    },
    {
        "method": "POST",
        "path": "/jobs/indeed",
        "purpose": "Pull 0-3 year DevOps-style roles from Indeed and apply with a tailored resume. Indeed refuses the unsigned request, so the reply explains that and sends nothing.",
    },
    {
        "method": "POST",
        "path": "/jobs/instahyre",
        "purpose": "Pull Instahyre entry-level roles whose titles match the resume, write a tailored two-page resume for each, upload it to Sandeep Job Applications, and submit. Instahyre only accepts a logged-in application, so submitted stays false.",
    },
]


def _prepare_one(config: Config, job: dict) -> dict:
    """Tailor one listing, save Company - Job Title.pdf, and upload that PDF."""
    resume = tailor(config, job.get("company", ""), job.get("title", ""), job.get("description", ""))
    resume["apply_url"] = job.get("apply_url") or job.get("url") or ""
    # Check the apply page before writing the record, so submitted reflects a real send.
    submit = assess_apply(resume["apply_url"])
    record = write_application(config, resume, submit)
    record["location"] = job.get("location", "")
    record["source"] = job.get("source", "")
    record["fit"] = job.get("fit", "unranked")
    record["why"] = job.get("why", "")
    record["summary"] = resume["summary"]
    try:
        record["drive"] = upload_many(config, [Path(record["pdf"])], APPLICATIONS_FOLDER)
    except Exception as error:
        record["drive_error"] = str(error)
    record["next_step"] = "Open apply_url and attach the PDF."
    return record


def run_jobs(config: Config, limit: int) -> dict:
    """Collect, rank, tailor, upload, and store apply links in one pass."""
    # Public boards first. Claude then keeps the roles that fit 0-3 years.
    jobs, errors = collect_jobs(limit)
    ranked = rank_jobs(config, jobs)[:limit]
    prepared = [_prepare_one(config, job) for job in ranked]
    return {
        "experience_band": "0-3 years",
        "count": len(prepared),
        "submitted": False,
        "applications": prepared,
        "linkedin_searches": linkedin_searches(),
        "errors": errors,
        "how_to_verify": (
            "submitted is true only after an employer form accepts the PDF. "
            "Read submit_status and submit_reason on each application. "
            "A prepared PDF in Sandeep Job Applications is not an application by itself."
        ),
        "note": (
            "Each PDF is in Sandeep Job Applications, named Company - Job Title. "
            "Open each apply_url and attach that PDF when submit_status is not_submitted. "
            "linkedin_searches opens the same titles on LinkedIn (Entry level and Associate, India, past week, remote)."
        ),
    }


class Handler(BaseHTTPRequestHandler):
    config = Config()

    def log_message(self, fmt: str, *args) -> None:
        print(f"[api] {self.address_string()} {fmt % args}", flush=True)

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        if not raw.strip():
            return {}
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"ok": True})
            return
        if parsed.path == "/":
            self._send(200, {"service": "Sandeep LinkedIn and jobs API", "endpoints": ENDPOINTS})
            return
        self._send(404, {"error": "No such endpoint", "endpoints": ENDPOINTS})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
        except (json.JSONDecodeError, ValueError) as error:
            self._send(400, {"error": str(error)})
            return
        try:
            if parsed.path == "/profile/enhance/dry-run":
                self._send(200, _enhance_dry_run(self.config))
                return
            if parsed.path == "/profile/enhance":
                self._send(200, _enhance(self.config))
                return
            if parsed.path == "/posts/create":
                self._send(200, _create_post(self.config))
                return
            if parsed.path == "/posts/upload":
                self._send(200, _upload_post(self.config, body))
                return
            if parsed.path == "/jobs":
                limit = max(1, min(int(body.get("limit", 8)), 8))
                self._send(200, run_jobs(self.config, limit))
                return
            source_name = {
                "/jobs/naukri": "naukri",
                "/jobs/wellfound": "wellfound",
                "/jobs/simplify": "simplify",
                "/jobs/indeed": "indeed",
                "/jobs/instahyre": "instahyre",
            }.get(parsed.path)
            if source_name:
                limit = max(1, min(int(body.get("limit", 3)), 5))
                self._send(200, run_source(self.config, source_name, limit))
                return
        except Exception as error:
            self._send(500, {"error": str(error)})
            return
        self._send(404, {"error": "No such endpoint", "endpoints": ENDPOINTS})


def run_source(config: Config, name: str, limit: int) -> dict:
    """Pull one board, tailor each match, and record whether the apply form accepted the PDF."""
    pulled = collect_source(name, limit)
    applications = [_prepare_one(config, job) for job in pulled["jobs"]]
    submitted_count = sum(1 for item in applications if item.get("submitted"))
    return {
        "source": pulled["source"],
        "experience_band": "0-3 years",
        "count": len(applications),
        "submitted_count": submitted_count,
        "submitted": bool(applications) and submitted_count == len(applications),
        "applications": applications,
        "search_url": pulled["search_url"],
        "errors": pulled["errors"],
        "note": pulled["note"],
    }


def _enhance_dry_run(config: Config) -> dict:
    """Preview only. Claude rewrites every section. LinkedIn and Drive stay untouched."""
    return run_profile_enhance(config, dry_run=True)


def _enhance(config: Config) -> dict:
    """Same Claude pass as the dry run. Paste files and Drive update only after every section passes."""
    payload = run_profile_enhance(config, dry_run=False)
    if not payload.get("applied"):
        return payload
    # Upload happens after the last section file is on disk, never before validation.
    files = [Path(item) for item in payload.get("files") or []]
    try:
        payload["drive"] = upload_many(config, files, PROFILE_FOLDER)
        payload["drive_uploaded"] = True
    except Exception as error:
        payload["drive_error"] = str(error)
    report = Path(payload["file"])
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _create_post(config: Config) -> dict:
    board = next_board(config)
    folder = build_pack(config, board, mark=True)
    files = [folder / "post.gif", folder / "preview.png", folder / "post.txt", folder / "first-comment.txt"]
    payload = {"local_folder": str(folder), "files": [path.name for path in files if path.exists()]}
    try:
        payload["drive"] = upload_many(config, files, POSTS_FOLDER)
    except Exception as error:
        payload["drive_error"] = str(error)
    payload["note"] = "The GIF and caption are in Sandeep LinkedIn Posts. Upload post.gif on LinkedIn and paste post.txt."
    return payload


def _upload_post(config: Config, body: dict) -> dict:
    raw = str(body.get("folder") or "").strip()
    folder = Path(raw) if raw else _latest_post_folder(config)
    if not folder.exists():
        raise FileNotFoundError(f"Post folder not found: {folder}")
    files = [folder / name for name in ("post.gif", "preview.png", "post.txt", "first-comment.txt")]
    return {"local_folder": str(folder), "drive": upload_many(config, files, POSTS_FOLDER)}


def _latest_post_folder(config: Config) -> Path:
    candidates = [path for path in config.output_dir.iterdir() if (path / "post.gif").exists()]
    if not candidates:
        raise FileNotFoundError("No post.gif exists yet. Call POST /posts/create first.")
    return max(candidates, key=lambda path: (path / "post.gif").stat().st_mtime)


def main() -> None:
    config = Config()
    server = ThreadingHTTPServer(("127.0.0.1", config.api_port), Handler)
    print(f"API on http://127.0.0.1:{config.api_port}", flush=True)
    print("GET / lists every endpoint.", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

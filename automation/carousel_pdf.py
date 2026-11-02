"""Build the carousel HTML and, when Chrome is installed, the PDF you upload yourself."""

import shutil
import subprocess
from pathlib import Path

ACCENT = "#006BFF"
INK = "#101114"
PAPER = "#F6F4EF"


def build_slides(payload: dict) -> list[dict]:
    """Cover, stake, one idea per slide, recap, call to action. Cap the deck at 12."""
    slides: list[dict] = []
    cover = payload.get("cover") if isinstance(payload.get("cover"), dict) else {}
    slides.append(
        {
            "kind": "cover",
            "headline": str(cover.get("headline") or payload.get("title") or "One idea").strip(),
            "body": str(cover.get("promise") or "").strip(),
        }
    )
    stake = str(payload.get("stake") or "").strip()
    if stake:
        slides.append({"kind": "stake", "headline": "Why this matters", "body": stake})
    for item in payload.get("slides") or []:
        if not isinstance(item, dict):
            continue
        headline = str(item.get("headline") or "").strip()
        body = str(item.get("body") or "").strip()
        if headline or body:
            slides.append({"kind": "point", "headline": headline or "Next", "body": body})
    recap = payload.get("recap") or []
    if isinstance(recap, list) and recap:
        slides.append(
            {
                "kind": "recap",
                "headline": "Keep this",
                "body": "\n".join(f"- {str(line).strip()}" for line in recap if str(line).strip()),
            }
        )
    cta = str(payload.get("cta") or "").strip()
    if cta:
        slides.append({"kind": "cta", "headline": "Do this", "body": cta})
    # Under 8 slides is a text post. Over 12 and people stop swiping.
    return slides[:12]


def render_html(slides: list[dict], handle: str = "AIOrbit Lab") -> str:
    """One section per slide, 1080 by 1350, type large enough for a phone thumbnail."""
    total = len(slides)
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>",
        "@page { size: 1080px 1350px; margin: 0; }",
        "html, body { margin: 0; padding: 0; background: #111; }",
        "section {",
        "  width: 1080px; height: 1350px; box-sizing: border-box;",
        f"  background: {PAPER}; color: {INK};",
        "  padding: 96px 88px 120px; position: relative;",
        "  page-break-after: always; font-family: Arial, Helvetica, sans-serif;",
        "}",
        f"h1 {{ font-size: 84px; line-height: 1.05; margin: 0 0 36px; letter-spacing: -1px; }}",
        "p, li { font-size: 36px; line-height: 1.35; margin: 0 0 18px; }",
        "ul { margin: 0; padding-left: 40px; }",
        f".num {{ color: {ACCENT}; font-size: 28px; font-weight: 700; letter-spacing: 1px; }}",
        ".handle { position: absolute; left: 88px; bottom: 56px; font-size: 28px; opacity: 0.7; }",
        "</style></head><body>",
    ]
    for index, slide in enumerate(slides, start=1):
        body = slide["body"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        headline = slide["headline"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if slide["kind"] == "recap":
            items = "".join(f"<li>{line[2:]}</li>" for line in body.splitlines() if line.startswith("- "))
            body_html = f"<ul>{items}</ul>"
        else:
            body_html = "".join(f"<p>{line}</p>" for line in body.splitlines() if line.strip())
        parts.append(
            "<section>"
            f"<div class='num'>{index}/{total}</div>"
            f"<h1>{headline}</h1>"
            f"{body_html}"
            f"<div class='handle'>{handle}</div>"
            "</section>"
        )
    parts.append("</body></html>")
    return "".join(parts)


def write_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Print with Chrome when it is installed. The HTML remains either way."""
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    binary = chrome or (str(mac_chrome) if mac_chrome.exists() else "")
    if not binary:
        print("Chrome is not installed, so the PDF was not built. The HTML is ready.", flush=True)
        return False
    command = [
        binary,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not pdf_path.exists():
        detail = (completed.stderr or completed.stdout or "").strip()
        print(f"Chrome did not write the PDF. {detail}", flush=True)
        return False
    print(f"PDF: {pdf_path}", flush=True)
    return True

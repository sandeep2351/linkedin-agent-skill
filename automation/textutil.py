"""Small text helpers shared by the post runner and the other commands."""

import json
import re

from .bedrock import ask
from .config import Config

# Openers and closers the comment and post skills reject on sight.
BANNED_OPENERS = (
    "great post",
    "love this",
    "so true",
    "couldn't agree more",
    "could not agree more",
    "this resonates",
    "thoughts?",
    "agree?",
    "who else",
)
PERSONAL_CLAIM = re.compile(
    r"\$\d|\bclients?\b|\brevenue\b|\bsalary\b|\bI (?:made|earned|closed|fired)\b",
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}")


def extract_json(text: str) -> dict:
    """Pull the JSON object out of a reply that may include extra text."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("The model did not return JSON")
    return json.loads(text[start : end + 1])


def ask_json(config: Config, model_id: str, prompt: str, *, max_tokens: int) -> tuple[dict, str]:
    """Ask twice if the first reply is not JSON."""
    last_error = "The model did not return JSON"
    for _ in range(2):
        try:
            raw, used = ask(config, model_id, prompt, max_tokens=max_tokens)
            return extract_json(raw), used
        except (ValueError, json.JSONDecodeError, RuntimeError) as error:
            last_error = str(error)
    raise RuntimeError(last_error)


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def limit_hashtags(text: str) -> str:
    """Keep at most three hashtags, and put them on the last line."""
    tags = re.findall(r"#\w+", text)
    body = re.sub(r"#\w+", "", text)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    kept: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        kept.append(tag)
        if len(kept) == 3:
            break
    if kept:
        body = body + "\n\n" + " ".join(kept)
    return body.strip() + "\n"


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(text)


def personal_claims(text: str, allowed: str) -> list[str]:
    """Claims about money or clients that are not already in the voice or the source."""
    haystack = allowed.lower()
    found: list[str] = []
    for match in PERSONAL_CLAIM.finditer(text):
        token = match.group(0)
        if token.lower() not in haystack:
            found.append(token)
    return found


def quality_issues(text: str, *, min_chars: int = 700, max_chars: int = 1800) -> list[str]:
    """Problems a rewrite should fix. Structural tells are handled by the humanizer."""
    issues: list[str] = []
    body = text.strip()
    count = len(body)
    if count < min_chars:
        issues.append(f"too short ({count} characters, want at least {min_chars})")
    if count > max_chars:
        issues.append(f"too long ({count} characters, want at most {max_chars})")
    line = first_line(body)
    if len(line) > 140:
        issues.append(f"line 1 is {len(line)} characters. Keep it under 140 so the phone does not cut it.")
    lowered = body.lower()
    for opener in BANNED_OPENERS:
        if opener in lowered:
            issues.append(f"contains banned phrase: {opener}")
    if "—" in body or "–" in body:
        issues.append("still has a dash that should be a comma or a hyphen")
    return issues


def split_blocks(text: str) -> list[str]:
    """Split a paste on a line of three dashes, or on a blank line between blocks."""
    chunks = re.split(r"\n(?:---|-{3,})\n", text.strip())
    blocks = [chunk.strip() for chunk in chunks if chunk.strip()]
    return blocks or ([text.strip()] if text.strip() else [])

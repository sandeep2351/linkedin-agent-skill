"""Load paths and the local .env file for the LinkedIn runner."""

import os
from pathlib import Path

# Repo root is the parent of this package. Every path below hangs off it.
REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_DIR = REPO_ROOT / "automation"
ENV_PATH = AUTOMATION_DIR / ".env"
# The YouTube runner already stores the Bedrock key. Use it when this folder has none.
YOUTUBE_ENV = REPO_ROOT.parent / "youtube-agent-skill" / "automation" / ".env"
HOME_DIR = Path.home() / ".claude" / "linkedin"


# The YouTube file holds the same Bedrock key. Its voice path and upload flags stay there.
SHARED_FROM_YOUTUBE = {
    "AWS_BEARER_TOKEN_BEDROCK",
    "BEDROCK_REGION",
    "MODEL_SCRIPT",
    "MODEL_STORY",
    "MODEL_TITLE",
    "MODEL_LONGFORM",
}


def _apply_env_line(line: str, allowed: set[str] | None) -> None:
    """Set one KEY=VALUE line. `allowed` limits which keys a borrowed file may set."""
    if not line or line.startswith("#") or "=" not in line:
        return
    key, value = line.split("=", 1)
    key = key.strip()
    if allowed is not None and key not in allowed:
        return
    os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def load_env(path: Path, *, allowed: set[str] | None = None) -> None:
    """Read KEY=VALUE lines into the environment without overriding real env vars."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        # The Bedrock console shows `export KEY=value`. Drop the export word.
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        _apply_env_line(line, allowed)


def _flag(name: str, default: str = "no") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "yes", "true", "on"}


def _path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


class Config:
    def __init__(self) -> None:
        load_env(ENV_PATH)
        # A key already set in the shell or in this folder wins over the YouTube file.
        load_env(YOUTUBE_ENV, allowed=SHARED_FROM_YOUTUBE)
        self.bedrock_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        self.bedrock_region = os.environ.get("BEDROCK_REGION", "ap-southeast-2").strip()
        # One model per task. Override any of these in automation/.env.
        self.model_script = os.environ.get("MODEL_SCRIPT", "amazon.nova-lite-v1:0").strip()
        self.model_story = os.environ.get(
            "MODEL_STORY", "au.anthropic.claude-haiku-4-5-20251001-v1:0"
        ).strip()
        self.model_title = os.environ.get("MODEL_TITLE", "amazon.nova-micro-v1:0").strip()
        self.model_longform = os.environ.get(
            "MODEL_LONGFORM", "au.anthropic.claude-sonnet-4-6"
        ).strip()
        self.home_dir = HOME_DIR
        self.state_dir = AUTOMATION_DIR / "state"
        self.output_dir = AUTOMATION_DIR / "output"
        self.logs_dir = AUTOMATION_DIR / "logs"
        self.topics_path = AUTOMATION_DIR / "topics.json"
        self.hooks_path = REPO_ROOT / "skills" / "li-post" / "hooks.json"
        self.rubric_path = REPO_ROOT / "skills" / "li-profile" / "rubric.json"
        self.used_topics_path = self.state_dir / "used_topics.json"
        self.log_path = self.state_dir / "log.md"
        self.plan_path = self.state_dir / "plan.md"
        self.engage_path = AUTOMATION_DIR / "engage.txt"
        youtube_secrets = REPO_ROOT.parent / "youtube-agent-skill" / "automation" / "secrets"
        self.client_secret = _path("GOOGLE_CLIENT_SECRET", youtube_secrets / "client_secret.json")
        self.drive_token = _path("DRIVE_TOKEN", youtube_secrets / "drive_token.json")
        self.applications_dir = self.output_dir / "applications"
        self.api_port = int(os.environ.get("API_PORT", "8787"))
        # The home profile is the one the skills read. The repo file is the fallback.
        home_voice = self.home_dir / "voice.md"
        fallback_voice = AUTOMATION_DIR / "voice.md"
        self.voice_path = _path("VOICE_PATH", home_voice if home_voice.exists() else fallback_voice)

    def missing(self, *, need_model: bool) -> list[str]:
        """Return the human-readable gaps that block a model run."""
        gaps: list[str] = []
        if not self.voice_path.exists():
            gaps.append(f"Voice profile missing at {self.voice_path}")
        if need_model and not self.bedrock_token:
            gaps.append(
                "AWS_BEARER_TOKEN_BEDROCK is empty. Add it to automation/.env "
                "or to the YouTube automation/.env"
            )
        return gaps

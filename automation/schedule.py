"""Install or remove the Mac schedule that prepares one GIF post every two days.

The clock fires every morning. The runner skips a day when the last GIF is still fresh.
The schedule writes a file. It does not open LinkedIn.
"""

import plistlib
import subprocess
from pathlib import Path

from .config import REPO_ROOT

LABEL = "com.aiorbitlab.linkedin"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = REPO_ROOT / "automation" / "logs"


def _python() -> str:
    """Pillow lives in the local venv. The schedule has to use that interpreter."""
    venv_python = REPO_ROOT / "automation" / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return "python3"


def install() -> None:
    """Write a LaunchAgent and load it. Uses the Mac's local clock."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": LABEL,
        "ProgramArguments": [_python(), "-m", "automation.run", "--scheduled"],
        "WorkingDirectory": str(REPO_ROOT),
        # 08:15 every day. --scheduled publishes only when the previous GIF is 2 days old.
        "StartCalendarInterval": [
            {"Hour": 8, "Minute": 15},
        ],
        "StandardOutPath": str(LOG_DIR / "linkedin.log"),
        "StandardErrorPath": str(LOG_DIR / "linkedin.err"),
    }
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_bytes(plistlib.dumps(payload))
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
    subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
    print(f"Scheduled a GIF every 2 days at 08:15. Agent file: {PLIST_PATH}")
    print("Each run writes post.gif and post.txt. You upload them. LinkedIn is not opened.")


def remove() -> None:
    if PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
        PLIST_PATH.unlink()
    print("LinkedIn draft schedule removed.")

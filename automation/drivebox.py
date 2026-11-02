"""Create two Drive folders and upload files the API produced.

Posts go in one folder. Tailored resumes go in another.
The token is the Drive login already saved for this Google account.
Scope is drive.file, so the API only sees files it created.
"""

from pathlib import Path

from .config import Config

POSTS_FOLDER = "Sandeep LinkedIn Posts"
APPLICATIONS_FOLDER = "Sandeep Job Applications"
PROFILE_FOLDER = "Sandeep LinkedIn Profile"
SCOPE = ["https://www.googleapis.com/auth/drive.file"]


def _credentials(config: Config):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not config.drive_token.exists():
        raise FileNotFoundError(
            "Google Drive is not connected. Run the YouTube automation auth once, "
            "or place drive_token.json at the path in DRIVE_TOKEN."
        )
    creds = Credentials.from_authorized_user_file(str(config.drive_token), SCOPE)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        config.drive_token.write_text(creds.to_json(), encoding="utf-8")
    if not creds.valid:
        raise RuntimeError("Drive token is not valid. Sign in again with the YouTube automation --auth step.")
    return creds


def _service(config: Config):
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=_credentials(config))


def ensure_folder(config: Config, name: str) -> str:
    """Create the named folder once and remember its id in automation/state."""
    config.state_dir.mkdir(parents=True, exist_ok=True)
    stamp = config.state_dir / f"drive-{name.lower().replace(' ', '-')}.txt"
    if stamp.exists():
        folder_id = stamp.read_text(encoding="utf-8").strip()
        if folder_id:
            return folder_id
    created = (
        _service(config)
        .files()
        .create(
            body={"name": name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        )
        .execute()
    )
    stamp.write_text(created["id"], encoding="utf-8")
    return created["id"]


def upload_file(config: Config, path: Path, folder_name: str) -> dict:
    """Upload one file into the named folder. Returns id, name, and link."""
    from googleapiclient.http import MediaFileUpload

    folder_id = ensure_folder(config, folder_name)
    service = _service(config)
    media = MediaFileUpload(str(path), resumable=True)
    # Replace a file this app already uploaded with the same name, so a rebuilt resume does not stack a second copy.
    safe_name = path.name.replace("'", "\\'")
    existing = (
        service.files()
        .list(
            q=f"name = '{safe_name}' and '{folder_id}' in parents and trashed = false",
            fields="files(id, name)",
            pageSize=1,
        )
        .execute()
    )
    files = existing.get("files") or []
    if files:
        created = (
            service.files()
            .update(fileId=files[0]["id"], media_body=media, fields="id, name, webViewLink")
            .execute()
        )
    else:
        created = (
            service.files()
            .create(
                body={"name": path.name, "parents": [folder_id]},
                media_body=media,
                fields="id, name, webViewLink",
            )
            .execute()
        )
    return {
        "id": created.get("id", ""),
        "name": created.get("name", path.name),
        "webViewLink": created.get("webViewLink", ""),
        "folder": folder_name,
    }


def upload_many(config: Config, paths: list[Path], folder_name: str) -> list[dict]:
    uploaded = []
    for path in paths:
        if path.exists() and path.is_file():
            uploaded.append(upload_file(config, path, folder_name))
    return uploaded

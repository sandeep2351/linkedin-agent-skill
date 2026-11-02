"""Call Amazon Bedrock with the bearer token in AWS_BEARER_TOKEN_BEDROCK.

Every model goes through the same Converse endpoint. Only the model id changes.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from .config import Config

SYSTEM = (
    "You write LinkedIn drafts for AIOrbit Lab in the voice profile you are given. "
    "Reply with one JSON object and no markdown. "
    "Never invent the author's clients, employers, revenue, salary, or personal results. "
    "If a personal number is missing, write the token {{your number}}."
)


def _candidates(model_id: str, region: str) -> list[str]:
    """Base id first, then the cross-region profile Bedrock often requires."""
    options = [model_id]
    # The playground that works is Sydney, so Australia profiles are the first retry.
    if region.startswith("ap-southeast") and "claude-haiku" in model_id:
        options.append("au.anthropic.claude-haiku-4-5-20251001-v1:0")
    if region.startswith("ap-southeast") and "claude-sonnet" in model_id:
        options.append("au.anthropic.claude-sonnet-4-6")
        options.append("au.anthropic.claude-sonnet-4-5-20250929-v1:0")
    if model_id.startswith("amazon.nova") or model_id.startswith("meta."):
        options.append("us." + model_id)
    if "claude-sonnet" in model_id:
        options.extend(
            [
                "global.anthropic.claude-sonnet-4-6",
                "us.anthropic.claude-sonnet-4-6",
                "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            ]
        )
    if "claude-haiku" in model_id:
        options.append("global.anthropic.claude-haiku-4-5-20251001-v1:0")
        options.append("us.anthropic.claude-haiku-4-5-20251001-v1:0")
    unique: list[str] = []
    for option in options:
        if option not in unique:
            unique.append(option)
    return unique


def _converse(config: Config, model_id: str, prompt: str, max_tokens: int, system: str) -> str:
    """One Converse request. The model id is escaped because it contains a colon."""
    encoded = urllib.parse.quote(model_id, safe="")
    url = (
        f"https://bedrock-runtime.{config.bedrock_region}.amazonaws.com"
        f"/model/{encoded}/converse"
    )
    body = {
        "system": [{"text": system}],
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.6},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {config.bedrock_token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Bedrock {model_id} returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Bedrock {model_id} could not be reached: {error}") from error
    parts = payload.get("output", {}).get("message", {}).get("content", [])
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise RuntimeError(f"Bedrock {model_id} returned no text")
    return text


def ask(
    config: Config,
    model_id: str,
    prompt: str,
    *,
    max_tokens: int = 1200,
    system: str = SYSTEM,
) -> tuple[str, str]:
    """Return (reply text, model id that actually answered)."""
    last_error: Exception | None = None
    for candidate in _candidates(model_id, config.bedrock_region):
        try:
            return _converse(config, candidate, prompt, max_tokens, system), candidate
        except RuntimeError as error:
            last_error = error
            message = str(error).lower()
            # A wrong on-demand id can be retried as an inference profile. A bad key cannot.
            profile_problem = any(
                phrase in message
                for phrase in (
                    "inference profile",
                    "on-demand",
                    "model identifier",
                    "not found",
                    "validationexception",
                    "access denied",
                    "not subscribed",
                    "unsupported",
                )
            )
            if not profile_problem:
                raise
    raise RuntimeError(str(last_error))

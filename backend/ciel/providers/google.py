import os

from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import gAPI, gCIEL, gProv

API_KEY = gAPI
URL = gProv
MODEL = gCIEL
FILE = "google.py"
TIMEOUT_SECONDS = max(1.0, float(os.getenv("CIEL_RESPONSE_TIMEOUT_SECONDS", "60")))
MAX_RETRIES = max(0, int(os.getenv("CIEL_RESPONSE_MAX_RETRIES", "2")))


def _validate_configuration() -> None:
    missing = []
    if not API_KEY:
        missing.append("GEMINI_API")
    if not URL:
        missing.append("GEMINI_PROV")
    if not MODEL:
        missing.append("GOOGLE_CIEL_MODEL")
    if missing:
        raise RuntimeError(
            "Response provider configuration is missing: " + ", ".join(missing)
        )


def geminiComm(sysPrompt, usrPrompt, isStreaming, onToken=None):
    from openai import OpenAI

    _validate_configuration()
    log("debug", f"{FILE}: communication started")

    client = OpenAI(
        base_url=URL,
        api_key=API_KEY,
        timeout=TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )

    log("info", f"{FILE}: client configured for response provider")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": str(sysPrompt)},
                {"role": "user", "content": str(usrPrompt)},
            ],
            stream=bool(isStreaming),
        )
    except Exception as error:
        log("error", f"{FILE}: provider request failed: {error}")
        raise RuntimeError("Response-model communication failed") from error

    if isStreaming:
        full_response = ""
        for chunk in response:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if not content:
                continue
            full_response += content
            print(content, end="", flush=True)
            if onToken is not None:
                onToken(content)
        return full_response

    choices = getattr(response, "choices", None)
    if not choices:
        raise RuntimeError("Response model returned no choices")
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None) if message is not None else None
    if content is None:
        raise RuntimeError("Response model returned empty content")
    return str(content)

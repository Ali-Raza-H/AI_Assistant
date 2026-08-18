import time

from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import (
    groqApiKey,
    groqBaseUrl,
    groqMaxRetries,
    groqRetryBackoffSeconds,
    groqRouterModel,
    groqTimeoutSeconds,
)


FILE = "groqProv.py"
SCHEMA_NAME = "ciel_router_decision"
JSON_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-safeguard-20b",
}
RETIRED_MODELS = {
    "llama-3.3-70b-specdec": "openai/gpt-oss-20b or openai/gpt-oss-120b",
}
RETRYABLE_STATUS_CODES = {408, 409, 429, 498}
RETRYABLE_MARKERS = (
    "capacity_exceeded",
    "connection error",
    "rate limit",
    "rate_limit_exceeded",
    "service unavailable",
    "service_unavailable",
    "timed out",
    "timeout",
    "temporarily unavailable",
    "overloaded",
)


def _groqErrorText(error):
    values = [str(error)]
    for attribute in ("error", "message", "body"):
        value = getattr(error, attribute, None)
        if value is not None:
            values.append(str(value))
    return " ".join(values).lower()


def _groqStatusCode(error):
    statusCode = getattr(error, "status_code", None)
    if statusCode is None:
        response = getattr(error, "response", None)
        statusCode = getattr(response, "status_code", None)
    try:
        return int(statusCode) if statusCode is not None else None
    except (TypeError, ValueError):
        return None


def _isRetryableError(error):
    statusCode = _groqStatusCode(error)
    if statusCode in RETRYABLE_STATUS_CODES or (
        statusCode is not None and statusCode >= 500
    ):
        return True
    errorText = _groqErrorText(error)
    return any(marker in errorText for marker in RETRYABLE_MARKERS)


def _responseFormat(responseFormat, model=None):
    if responseFormat is None:
        return None

    if isinstance(responseFormat, dict):
        # Callers may supply an OpenAI/Groq response_format directly.
        if responseFormat.get("type") in {"json_schema", "json_object", "text"}:
            return responseFormat

        selectedModel = model or groqRouterModel
        if selectedModel in JSON_SCHEMA_MODELS:
            # Ollama accepts a raw JSON Schema. Supported Groq models require
            # that schema to be wrapped for the Chat Completions API.
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": SCHEMA_NAME,
                    "strict": False,
                    "schema": responseFormat,
                },
            }

        # Groq models without Structured Outputs still support JSON Object
        # Mode. The router's prompt, parser, and retry loop enforce the schema.
        return {"type": "json_object"}

    formatName = str(responseFormat).strip().lower()
    if formatName in {"json", "json_object"}:
        return {"type": "json_object"}
    if formatName == "text":
        return {"type": "text"}
    raise ValueError(f"Unsupported Groq response format: {responseFormat!r}")


def _chatWithGroqRecovery(
    client,
    chatArguments,
    maxRetries=None,
    retryBackoffSeconds=None,
):
    maxRetries = groqMaxRetries if maxRetries is None else max(0, maxRetries)
    retryBackoffSeconds = (
        groqRetryBackoffSeconds
        if retryBackoffSeconds is None
        else max(0.0, retryBackoffSeconds)
    )

    for attempt in range(maxRetries + 1):
        try:
            return client.chat.completions.create(**chatArguments)
        except Exception as error:
            shouldRetry = _isRetryableError(error) and attempt < maxRetries
            if not shouldRetry:
                raise RuntimeError(f"Groq request failed: {error}") from error

            delay = retryBackoffSeconds * (2**attempt)
            log(
                "warning",
                f"{FILE}: transient Groq error; retrying in {delay:g}s "
                f"({attempt + 1}/{maxRetries})",
            )
            if delay:
                time.sleep(delay)

    raise RuntimeError("Groq request failed without returning a response")


def _validateConfiguration():
    missing = []
    if not groqApiKey:
        missing.append("GROQ_API_KEY (or GROQ_API)")
    if not groqRouterModel:
        missing.append("GROQ_ROUTER_MODEL (or GROQ_MODEL)")
    if missing:
        raise RuntimeError("Groq router configuration is missing: " + ", ".join(missing))
    if groqRouterModel in RETIRED_MODELS:
        replacement = RETIRED_MODELS[groqRouterModel]
        raise RuntimeError(
            f"Groq router model {groqRouterModel!r} has been retired; "
            f"set GROQ_ROUTER_MODEL to {replacement}"
        )


def _responseContent(response):
    choices = getattr(response, "choices", None)
    if not choices:
        raise RuntimeError("Groq returned a response without any choices")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if content is None:
        refusal = getattr(message, "refusal", None)
        details = f": {refusal}" if refusal else ""
        raise RuntimeError(f"Groq returned an empty response{details}")
    return str(content)


def groqComm(sysMsg, usrMsg, isStreaming, responseFormat=None):
    _validateConfiguration()
    from openai import OpenAI

    log("debug", f"{FILE}: Groq provider started")

    # Disable the SDK's implicit retries because this adapter owns the retry
    # count and backoff, keeping router latency predictable.
    client = OpenAI(
        api_key=groqApiKey,
        base_url=groqBaseUrl,
        max_retries=0,
        timeout=groqTimeoutSeconds,
    )
    chatArguments = {
        "model": groqRouterModel,
        "messages": [
            {"role": "system", "content": str(sysMsg)},
            {"role": "user", "content": str(usrMsg)},
        ],
        "stream": bool(isStreaming),
    }

    formattedResponse = _responseFormat(responseFormat, model=groqRouterModel)
    if formattedResponse is not None:
        chatArguments["response_format"] = formattedResponse

    response = _chatWithGroqRecovery(client, chatArguments)
    log("debug", f"{FILE}: Groq request completed")

    if isStreaming:
        fullResponse = ""
        for chunk in response:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None)
            if content:
                content = str(content)
                print(content, end="", flush=True)
                fullResponse += content
        return fullResponse

    return _responseContent(response)

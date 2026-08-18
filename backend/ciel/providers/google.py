import os

from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import gAPI, gCIEL, gProv

API_KEY = gAPI
URL = gProv
MODEL = gCIEL
FILE = "googleProv.py"


def geminiComm(sysPrompt, usrPrompt, isStreaming, onToken=None):
    from openai import OpenAI


    log("debug", f"{FILE}: Gemini Communication function started")
    log("debug", f"{FILE}: Setting up client settings")

    client = OpenAI(base_url=URL, api_key=API_KEY)

    log("info", f"{FILE}: Client configured for provider {URL}")
    log("debug", f"{FILE}: Starting communication with gemini")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": str(sysPrompt)},
                {"role": "user", "content": str(usrPrompt)},
            ],
            stream=isStreaming,
        )
    except Exception as e:
        log("ERROR", f"{FILE}: ERROR ENCOUNTERED AFTER IN GEMINI COMMUNICATION: {e}")
        raise RuntimeError("Gemini communication failed") from e

    if isStreaming == True:
        log("debug", f"{FILE}: Streaming response path")

        fullResponse = ""

        for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                fullResponse += content
                print(content, end="", flush=True)
                if onToken is not None:
                    onToken(content)

        return fullResponse

    elif isStreaming == False:
        log("debug", f"{FILE}: Not streaming response path")
        return response.choices[0].message.content

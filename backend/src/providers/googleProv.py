import os

from openai import OpenAI
from src.tools.logger import log
from src.tools.settings import gAPI, gCIEL, gProv

API_KEY = gAPI
URL = gProv
MODEL = gCIEL
FILE = "googleProv.py"


def geminiComm(sysPrompt, usrPrompt, isStreaming):

    log("debug", f"{FILE}: Gemini Communication function started")
    log("debug", f"{FILE}: Setting up client settings")

    client = OpenAI(base_url=URL, api_key=API_KEY)

    log(
        "info",
        f"{FILE}: Client settings used -- provider - {URL} -- API KEY - {API_KEY}",
    )
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

    if isStreaming == True:
        log("debug", f"{FILE}: Streaming response path")

        fullResponse = ""

        for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                fullResponse += content
                print(content, end="", flush=True)

        return fullResponse

    elif isStreaming == False:
        log("debug", f"{FILE}: Not streaming response path")
        return response

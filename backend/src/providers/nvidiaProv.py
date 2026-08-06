import os
from src.tools.logger import log
from src.tools.settings import nvAPI, nvCIEL, nvProv

API_KEY = nvAPI
URL = nvProv
MODEL = nvCIEL
FILE = "nvidiaProv.py"


def nvidiaComm(sysPrompt, usrPrompt, isStreaming):
    from openai import OpenAI


    log("debug", f"{FILE}: nvidia Communication function started")
    log("debug", f"{FILE}: Setting up client settings")

    client = OpenAI(base_url=URL, api_key=API_KEY)

    log("info", f"{FILE}: Client settings used -- provider - {URL} -- API KEY - {API_KEY}")
    log("debug", f"{FILE}: Starting communication with nvidia")

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
        log("ERROR", f"{FILE}: ERROR ENCOUNTERED AFTER IN NVIDIA COMMUNICATION: {e}")

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

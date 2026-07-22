import os
from openai import OpenAI
from dotenv import load_dotenv
from src.tools.logger import log
from src.tools.vars import nvAPI, cielModel, provider, gAPI


API_KEY = gAPI
URL = provider
MODEL = cielModel
FILE = "llmCom.py"



def nvidiaComm(key, prov, model, sysPrompt, usrPrompt):
    log("debug", f"{FILE}: Nvidia Provider Function started")
    
    #Client settings
    client = OpenAI(
        base_url=prov,
        api_key = key
    )
    log("info", f"{FILE}: Client open using provider - {prov} with api: {key}")
    
    log("debug", f"{FILE}: Starting nvidia llm communication")
    response = client.chat.completions.create(
        model = model,
        messages=[
            {
                "role": "system",
                "content": str(sysPrompt)
            },
            {
                "role": "user",
                "content": str(usrPrompt)
            }
        ],
        stream=True
    )
    log("debug", f"{FILE}: Nvidia llm communication ended")
    
    fullResponse = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            fullResponse += content
            print(content, end='', flush=True)
    
    return fullResponse




def geminiComm(key, prov, model, sysPrompt, usrPrompt):
    log("debug", f"{FILE}: Gemini provider function started")
    
    #Clinet settings
    
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key = key
    )
    log("info", f"{FILE}: Client open using provider - {prov} with api: {key}")
    
    log("debug", f"{FILE}: Starting gemini llm communication")
    response = client.chat.completions.create(
        model = model,
        messages=[
            {
                "role": "system",
                "content": str(sysPrompt)
            },
            {
                "role": "user",
                "content": str(usrPrompt)
            }
        ],
        stream=True
    )
    
    fullResponse = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            fullResponse += content
            print(content, end='', flush=True)
    
    log("debug", f"{FILE}, Gemini communication finished")
    return fullResponse




#nvidiaComm(API_KEY, URL, MODEL, "You are a helpfull assistant called CIEL", "Hey how you doing?")

#geminiComm(API_KEY, URL, MODEL, "You are a helpfull assistant called CIEL", "Hey how you doing?")
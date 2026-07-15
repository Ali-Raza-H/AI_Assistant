import json

#PATH = "/home/aliraza/Devs/python/active/CIEL/backend/test/testSchema.json"
#with open(PATH, "r", encoding="UTF-8") as f:
#   tools = json.load(f)
    
#print(tools)

chatHistory = "/home/aliraza/Devs/python/active/CIEL/backend/test/testSchema1.json"



routerPrompt = """
    RESPOND ONLY IN JSON FORMAT
    JSON SCHEMA RESPONSE

    {
    "tool": "tool To be Used",
    "action": "action/response"
    }

    Example Response:
    {
    "tool": "runBash",
    "action": "start https://www.google.com"
    }
"""


def loadHistory():
    with open(chatHistory, 'r', encoding="UTF-8") as f:
        y = json.load(f)
        f.append(chatHistory)
        json.stringify(f)
    return f

#z = loadHistory()
#str(z)
#x = "this is random: ", z

#print(x)


x = {'tool': 'llmCom', 'action' : 'userMessage'}

if x ['tool'] == "llmCom":
    print(x['action'])


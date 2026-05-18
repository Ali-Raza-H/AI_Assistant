import json

with open('backend/test/testSchema.json', 'r') as file:
    tools = json.load(file)

print(tools)
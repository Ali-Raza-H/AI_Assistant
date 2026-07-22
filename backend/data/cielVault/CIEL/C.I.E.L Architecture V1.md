

# DATE: Tuesday 21 of July 2026


## Version 1 Architecture

![[CIEL Architecture 1|1500]]

This version of the CIEL Architecture works quite good but it has a multitude of issues:

1. The router doesn't reason as to if a command is to be used or not. We have to specify when running commands.
2. Router can only run one command at a time. We need support for multiple commands to be run.
3. This script only runs one which makes it horrible for Agentic Workflows.
4. This version doesn't have support for when errors are encountered when running the wrong commands.
5. The main LLM receives duplicate messages when using the `llmCom` tool. One with the router response and one with the users message.


## Version 1 File structure

```

📁 root
├── 📁 data
│   ├── 📁 cielVault
│   │   └── 📁 CIEL
│   │       ├── 📄 C.I.E.L Architecture.md
│   │       └── 📁 Excalidraw
│   │           └── 📄 CIEL Architecture 1.md
│   ├── 📁 database
│   ├── 📁 install
│   │   └── 📄 requirements.txt
│   └── 📁 logs
│       ├── 📄 debug.log
│       ├── 📄 error.log
│       └── 📄 info.log
├── 📁 docs
│   ├── 📁 CIELFeedback
│   │   └── 📄 cielFeedBack-22:50-July-18-Saturday.txt
│   └── 📁 reports
│       └── 📄 bugReport_18-05-26.txt
├── 📄 main.py
├── 📁 modules
│   ├── 📄 runBashCommands.py
│   └── 📄 toolManager.py
├── 📁 schemas
│   ├── 📄 chatHistory.json
│   ├── 📁 temp
│   │   └── 📄 commands.json
│   └── 📄 toolsSchema.json
├── 📁 src
│   ├── 📄 llmCom.py
│   └── 📁 tools
│       ├── 📄 chatHistoryTools.py
│       ├── 📄 jsonTools.py
│       ├── 📄 logger.py
│       └── 📄 vars.py
└── 📁 test
    ├── 📄 commandHandlign.py
    ├── 📄 loadJsonTest.py
    ├── 📄 loggingTesting.py
    ├── 📁 testDat
    │   ├── 📄 debug.log
    │   ├── 📄 error.log
    │   ├── 📄 info.log
    │   ├── 📄 testSchema1.json
    │   └── 📄 testSchema.json
    ├── 📄 testEnv.py
    ├── 📄 toolCalls.py
    └── 📄 toolDatFlow.py
```

This is the current file structure of CIEL. 

#### `Main.py:`

This is the file that's executed when running CIEL. This file contains the following functions:

1. `quitCommand`:  This function calls the `wipeChatHistory` function and exits CIEL
2. `router`: This function takes the `userInput` as a parameter. It contains an `if` statement that checks whether the input is `/quit` and if it is it calls the `quitCommand` function. 
   After that it uses `Ollama`'s python library to send the [[routerPrompt]] and the `userInput` to the `qwen2.5:1.5b:instruct` LLM. 
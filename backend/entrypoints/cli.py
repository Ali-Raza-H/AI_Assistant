from backend.ciel.core.controller import runController
from backend.ciel.core.router import clearRouterHistory
from backend.ciel.runtime.chat_history import wipeChatHistory
from backend.ciel.runtime.logging import log
from backend.ciel.services.lifeos_notifications import startLifeOSNotificationListener


log("info", "main.py: variables created")


def quitCommand():
    wipeChatHistory()
    clearRouterHistory()
    print("Goodbye")
    log("debug", "main.py: quit function executed")
    raise SystemExit


def llmComs(message):
    log("debug", "main.py: controller interaction started")
    return runController(message)


def main():
    try:
        from backend.entrypoints.web import startWebServer

        startWebServer()
        print("CIEL interface: http://127.0.0.1:8765")
    except ImportError as error:
        log("error", f"main.py: web interface unavailable: {error}")
        print("CIEL interface unavailable. Install backend requirements to enable it.")
    startLifeOSNotificationListener()
    while True:
        try:
            print("")
            userInput = input(">>   ")
            print("")
        except (EOFError, KeyboardInterrupt):
            quitCommand()

        if userInput == "/quit":
            quitCommand()

        try:
            llmComs(userInput)
        except Exception as error:
            # Loop history is deliberately retained so the next interaction
            # can inspect a request that failed before the router ended it.
            log("error", f"main.py: request failed: {error}")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()

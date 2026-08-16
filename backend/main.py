from src.controller import runController
from src.router import clearRouterHistory
from src.tools.chatHistoryTools import wipeChatHistory
from src.tools.lifeosNotifications import startLifeOSNotificationListener
from src.tools.logger import log


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
        from server import startWebServer

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

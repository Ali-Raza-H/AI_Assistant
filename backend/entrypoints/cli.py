from backend.ciel.core.controller import runController
from backend.ciel.runtime.logging import log
from backend.ciel.services.lifeos_notifications import startLifeOSNotificationListener


log("info", "cli.py: variables created")


def quitCommand():
    print("Goodbye")
    log("debug", "cli.py: clean shutdown requested")
    raise SystemExit


def llmComs(message):
    log("debug", "cli.py: controller interaction started")
    return runController(message)


def main():
    try:
        from backend.entrypoints.web import startWebServer

        startWebServer()
        print("CIEL interface: http://127.0.0.1:8765")
    except ImportError as error:
        log("error", f"cli.py: web interface unavailable: {error}")
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

        if not userInput.strip():
            continue

        try:
            llmComs(userInput)
        except Exception as error:
            log("error", f"cli.py: request failed: {error}")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()

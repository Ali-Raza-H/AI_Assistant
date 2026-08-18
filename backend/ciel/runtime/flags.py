from backend.ciel.runtime.logging import log

file = "flagManager.py"

# Class for flags declaration
class flags:

    isLooping = True
    doRemember = True

    @classmethod
    def setFlagState(cls, flag, state):
        log("debug", f"{file}: Using setFlagState function")
        log("info", f"{file}: Changing state of {flag} flag to {state}")

        if flag not in {"isLooping", "doRemember"}:
            raise ValueError(f"Unknown flag: {flag}")
        if type(state) is not bool:
            raise TypeError(f"Flag {flag} must be a boolean")

        setattr(cls, flag, state)
        log("debug", f"{file}: {flag} flag changed")

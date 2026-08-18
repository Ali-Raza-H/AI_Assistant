import logging
from logging.handlers import RotatingFileHandler

from backend.ciel.runtime.settings import DEBUG_LOG, ERROR_LOG, INFO_LOG

logForm = "%(asctime)s [%(levelname)s] %(message)s"
bakCount = 3
maxSize = 5 * 1024 * 1024


def log(logLevel, logMsg):
    logLevel = str(logLevel).upper()

    if logLevel == "DEBUG":
        logPath = DEBUG_LOG
    elif logLevel in {"INFO", "WARNING"}:
        logPath = INFO_LOG
    elif logLevel == "ERROR":
        logPath = ERROR_LOG
    else:
        raise ValueError(f"Unsupported log level: {logLevel}")

    logPath.parent.mkdir(parents=True, exist_ok=True)
    logVal = getattr(logging, logLevel)

    logger = logging.getLogger("customLogging")
    logger.setLevel(logVal)
    logger.propagate = False

    handler = RotatingFileHandler(logPath, maxBytes=maxSize, backupCount=bakCount)
    handler.setLevel(logVal)
    handler.setFormatter(logging.Formatter(logForm))
    logger.addHandler(handler)

    try:
        logger.log(logVal, logMsg)
    finally:
        logger.removeHandler(handler)
        handler.close()

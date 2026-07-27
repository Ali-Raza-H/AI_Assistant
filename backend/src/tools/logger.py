import logging
from logging.handlers import RotatingFileHandler

from src.tools.settings import DEBUG_LOG, ERROR_LOG, INFO_LOG

# Log settings
logForm = "%(asctime)s [%(levelname)s] %(message)s"
bakCount = 3
maxSize = 5 * 1024 * 1024


def log(logLevel, logMsg):

    logLevel = logLevel.upper()

    # Set log path depending on log level
    if logLevel == "DEBUG":
        logPath = DEBUG_LOG
    elif logLevel == "INFO":
        logPath = INFO_LOG
    elif logLevel == "ERROR":
        logPath = ERROR_LOG
    else:
        print(f"ERROR: log level {logLevel} not valid")
        return

    # Gets numerical values for logging
    logVal = getattr(logging, logLevel, logging.DEBUG)  # DEBUG is default backup

    # Starting the logger
    logger = logging.getLogger("customLogging")  # Logging instance
    logger.setLevel(logVal)  # Setting logging levels

    # Setting up file rotation and formatting
    handler = RotatingFileHandler(logPath, maxBytes=maxSize, backupCount=bakCount)
    handler.setFormatter(logging.Formatter(logForm))
    logger.addHandler(handler)

    try:
        # Logging using log level and input message
        logger.log(logVal, logMsg)

    finally:
        # removes handler for optimization
        logger.removeHandler(handler)
        handler.close()

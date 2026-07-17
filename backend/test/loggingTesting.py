import logging
from logging.handlers import RotatingFileHandler

x = 2

if x == None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers = [logging.FileHandler("backend/test/testDat/exampleApp.log", mode="a")]
    )
    output = "something else entierly"
    for i in range(500):
        x = str(i)
        output = output + " " + x
        logging.debug(output)



elif x == 1:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a handler that rolls over at 5 Megabytes, keeping 3 backup files
    handler = RotatingFileHandler("backend/test/testDat/Exampleapp.log", maxBytes=5 * 1024 * 1024, backupCount=2)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    
    for i in range(500):
        x = str(i)
        output = "Number " + x    
        logger.info(output)


INFO_LOG = "testDat/info.log"
DEBUG_LOG = "testDat/debug.log"
ERROR_LOG = "testDat/error.log" 

logForm = "%(asctime)s [%(levelname)s] %(message)s"
bakCount = 3
maxSize = 5 * 1024 * 1024



def log(logLevel, logMsg):
    # Convert string level to uppercase to prevent matching bugs
    logLevel = logLevel.upper()
    
    # 1. Map string to correct file path
    if logLevel == "DEBUG":
        logPath = DEBUG_LOG
    elif logLevel == "INFO":      # Fixed syntax (= to ==)
        logPath = INFO_LOG
    elif logLevel == "ERROR":     # Fixed syntax (= to ==)
        logPath = ERROR_LOG
    else:
        print(f"ERROR: log level '{logLevel}' not valid")
        return

    # 2. Map string to native logging numeric level constants
    numeric_level = getattr(logging, logLevel, logging.INFO)

    # 3. Instantiate the logger safely
    logger = logging.getLogger("custom_wrapper")
    logger.setLevel(numeric_level)
    
    # 4. Create, format, and attach the handler temporarily
    handler = RotatingFileHandler(logPath, maxBytes=maxSize, backupCount=bakCount)
    handler.setFormatter(logging.Formatter(logForm)) # Fixed: Wrap string in Formatter object
    logger.addHandler(handler)
    
    try:
        # 5. Dynamically log using the exact intended level (Fixed hardcoded .debug)
        logger.log(numeric_level, logMsg)
    finally:
        # 6. CRITICAL OPTIMIZATION: Detach and close the handler immediately 
        # This prevents duplicate lines on the next function run.
        logger.removeHandler(handler)
        handler.close()

# --- Verification Test Runs ---
if __name__ == "__main__":
    print("logging")
    log("debug", "This goes exclusively to debug.log")
    log("INFO", "This goes exclusively to info.log")
    log("ERROR", "This goes exclusively to error.log")

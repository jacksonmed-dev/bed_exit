import logging
import argparse


parser = argparse.ArgumentParser(description="Logger configuration")
parser.add_argument(
    "--log-level",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="DEBUG",
    help="Set the log level (default: DEBUG)",
)
args = parser.parse_args()
log_level = getattr(logging, args.log_level)

# Configure the logger
logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)
logger.setLevel(log_level)

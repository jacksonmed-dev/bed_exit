import argparse
import logging
import os
from enum import Enum
from logging.handlers import TimedRotatingFileHandler

log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Create an argument parser
parser = argparse.ArgumentParser(description="Logger configuration")
parser.add_argument(
    "--log-level",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="DEBUG",
    help="Set the log level (default: DEBUG)",
)
args = parser.parse_args()

# Configure the logger based on the log level argument
log_level = getattr(logging, args.log_level)

# Create a TimedRotatingFileHandler to split log files by day
logHandler = TimedRotatingFileHandler(
    "logs/logs.log",
    when="midnight",
    interval=1,
    backupCount=7
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)

# Create and configure the logger
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)

# Set the logger level
logger.setLevel(log_level)

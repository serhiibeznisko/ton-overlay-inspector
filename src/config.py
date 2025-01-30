import os
import logging.config
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(f'.env', raise_error_if_not_found=True))

# Database
DB_NAME = 'broadcast'
DB_URL = os.environ["DB_URL"]

# Other
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = -1002236792014

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s.%(msecs)03d: " "%(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "verbose_output": {
            "formatter": "default",
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "src": {
            "level": "INFO",
            "handlers": [
                "verbose_output",
            ],
        }
    },
}
logging.config.dictConfig(LOGGING_CONFIG)

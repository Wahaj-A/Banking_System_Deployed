import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


logger = logging.getLogger("banking_crm")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if this module is imported more than once
if not logger.handlers:

    # Vercel has a read-only filesystem.
    # Use console logging there so Vercel can collect the logs.
    if os.getenv("VERCEL"):
        handler = logging.StreamHandler()

    # Local development: keep writing logs to logs/app.log
    else:
        log_dir = Path(__file__).resolve().parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
import logging
import sqlite3
import os
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
DB_PATH = os.path.join(LOG_DIR, "posts.db")
LOG_FILE = os.path.join(LOG_DIR, "agent.log")

os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler with UTF-8 encoding for Windows compatibility
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.INFO)
        if hasattr(ch.stream, "reconfigure"):
            ch.stream.reconfigure(encoding="utf-8")

        # File handler
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS post_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            discord_message TEXT,
            fb_post_id TEXT,
            status TEXT,
            error TEXT
        )
    """)
    conn.commit()
    return conn


def log_post(discord_message: str, fb_post_id: str, status: str, error: str = None):
    """Write a post result to the SQLite log database."""
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO post_log (timestamp, discord_message, fb_post_id, status, error) VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), discord_message[:500], fb_post_id, status, error),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write to log DB: {e}")


def get_recent_posts(limit: int = 20) -> list:
    """Retrieve recent post log entries."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT timestamp, discord_message, fb_post_id, status, error FROM post_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows

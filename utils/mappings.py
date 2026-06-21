import json
import os
from logger.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "mappings.json")


def load_mappings(path: str = None) -> dict:
    path = path or DEFAULT_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except FileNotFoundError:
        logger.error(f"Mappings file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mappings file: {e}")
        raise

    _validate_mappings(mappings)
    return mappings


def _validate_mappings(mappings: dict):
    if not isinstance(mappings, dict):
        raise ValueError("Mappings file must contain a JSON object")

    for channel_id, cfg in mappings.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"Mapping for channel {channel_id} must be an object")
        if not cfg.get("page_id"):
            raise ValueError(f"Missing page_id for channel {channel_id}")
        if not cfg.get("page_token"):
            raise ValueError(f"Missing page_token for channel {channel_id}")

"""
Message handler for the Discord → Facebook pipeline.
"""

import config
from logger.logger import get_logger
from formatter.formatter import format_message
from facebook.publisher import publish
from utils.helpers import truncate, mark_last_post_time

logger = get_logger("handler")


async def handle_message(content: str, author: str, attachments: list, created_at, page_config: dict):
    """
    Pipeline:
    1. Format (simple or AI)
    2. Truncate to FB limits
    3. Publish to the mapped Facebook page
    """
    logger.info(f"Processing message from {author} at {created_at}")

    try:
        formatted = await format_message(content=content, author=author)
        formatted = truncate(formatted)

        result = await publish(
            message=formatted,
            image_urls=attachments,
            page_id=page_config["page_id"],
            page_token=page_config["page_token"],
        )
        mark_last_post_time()
        logger.info(f"Pipeline complete. FB Post ID: {result.get('id')}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

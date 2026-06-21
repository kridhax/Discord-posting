"""
Discord → Facebook Auto-Posting Agent
Entry point: python app.py
"""

import asyncio
import config
from logger.logger import get_logger
from formatter.formatter import format_message
from facebook.publisher import publish, check_token
from discord_listener.bot import start_bot
from utils.helpers import truncate, mark_last_post_time

logger = get_logger("app")


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


async def _check_all_tokens():
    for channel_id, mapping in config.CHANNEL_TO_PAGE.items():
        logger.info(f"Checking Facebook token for channel {channel_id} (page {mapping['page_id']})...")
        if not await check_token(mapping["page_id"], mapping["page_token"]):
            logger.error(f"Facebook token check failed for channel {channel_id}. Verify page token and page ID.")
            return False
    return True


def main():
    logger.info("=== Discord -> Facebook Agent Starting ===")

    try:
        config.validate()
    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        raise SystemExit(1)

    logger.info("Checking Facebook access tokens...")
    if not asyncio.run(_check_all_tokens()):
        raise SystemExit(1)
    logger.info("All Facebook tokens are valid.")

    logger.info(f"AI Formatter: {'ENABLED' if config.USE_AI_FORMATTER else 'DISABLED'}")
    logger.info(f"Rate limit: {config.RATE_LIMIT_SECONDS}s between posts")
    if not config.DISCORD_GUILD_ID:
        logger.info("No DISCORD_GUILD_ID set — will monitor ALL servers")
    else:
        logger.info(f"Monitoring server ID: {config.DISCORD_GUILD_ID}")
    logger.info(f"Mapped channels: {list(config.CHANNEL_TO_PAGE.keys())}")

    start_bot(on_valid_message=handle_message)


if __name__ == "__main__":
    main()


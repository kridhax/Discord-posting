"""
FastAPI wrapper for the Discord → Facebook agent.

This allows the Discord bot to run on Render's free Web Service tier.
It exposes a /health endpoint that Render can ping, keeping the service awake.

Run locally:
    uvicorn web_app:app --host 0.0.0.0 --port 8000

Or with the Dockerfile:
    docker build -t discord-fb-agent .
    docker run -p 8000:8000 --env-file .env discord-fb-agent
"""

import asyncio
import os
from contextlib import asynccontextmanager

import config
from fastapi import FastAPI
from discord_listener.bot import start_bot_async
from logger.logger import get_logger
from facebook.publisher import check_token
from handlers import handle_message

logger = get_logger("web_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the Discord bot in the background when the app starts."""
    logger.info("=== Discord -> Facebook Agent Starting ===")

    try:
        config.validate()
    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        raise

    logger.info("Checking Facebook access tokens...")
    for channel_id, mapping in config.CHANNEL_TO_PAGE.items():
        logger.info(f"Checking Facebook token for channel {channel_id} (page {mapping['page_id']})...")
        if not await check_token(mapping["page_id"], mapping["page_token"]):
            logger.error(f"Facebook token check failed for channel {channel_id}.")
            raise RuntimeError("Facebook token check failed")
    logger.info("All Facebook tokens are valid.")

    logger.info(f"AI Formatter: {'ENABLED' if config.USE_AI_FORMATTER else 'DISABLED'}")
    logger.info(f"Rate limit: {config.RATE_LIMIT_SECONDS}s between posts")
    if config.DISCORD_GUILD_ID:
        logger.info(f"Monitoring server ID: {config.DISCORD_GUILD_ID}")
    logger.info(f"Mapped channels: {list(config.CHANNEL_TO_PAGE.keys())}")

    # Start Discord bot in background task
    bot_task = asyncio.create_task(start_bot_async(on_valid_message=handle_message))

    yield

    # Shutdown
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Discord -> Facebook Agent",
        "mapped_channels": len(config.CHANNEL_TO_PAGE),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("web_app:app", host="0.0.0.0", port=port)

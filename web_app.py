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
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from discord_listener.bot import start_bot_async
from logger.logger import get_logger
from facebook.publisher import check_token
from handlers import handle_message
from token_refresh import (
    HTML_PAGE,
    exchange_user_token,
    fetch_page_token,
    render_result,
)

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


@app.get("/token", response_class=HTMLResponse)
async def token_form():
    return HTML_PAGE.format(result="")


@app.post("/token", response_class=HTMLResponse)
async def token_generate(
    app_id: str = Form(...),
    app_secret: str = Form(...),
    short_lived_token: str = Form(...),
    page_id: str = Form(...),
):
    try:
        long_lived_user_token = exchange_user_token(app_id, app_secret, short_lived_token)
        page_token = fetch_page_token(long_lived_user_token, page_id)
        result = render_result("", token=page_token)
    except Exception as e:
        result = render_result(f"Token generation failed: {e}", is_error=True)
    return HTML_PAGE.format(result=result)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("web_app:app", host="0.0.0.0", port=port)

import asyncio
import aiohttp
import json
import config
from logger.logger import get_logger, log_post

logger = get_logger(__name__)


def _feed_url(page_id: str) -> str:
    return f"{config.FACEBOOK_BASE_URL}/{page_id}/feed"


def _photos_url(page_id: str) -> str:
    return f"{config.FACEBOOK_BASE_URL}/{page_id}/photos"


async def publish(message: str, image_urls: list = None, page_id: str = None, page_token: str = None) -> dict:
    """
    Publish a message to a Facebook page feed.
    Retries up to MAX_RETRIES times on failure.
    Returns the Facebook post ID on success.
    """
    if not page_id or not page_token:
        raise ValueError("page_id and page_token are required")

    image_urls = image_urls or []
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            result = await _post_to_facebook(message, image_urls, page_id, page_token)
            post_id = result.get("id")
            logger.info(f"Facebook post published successfully. Post ID: {post_id}")
            log_post(discord_message=message, fb_post_id=post_id, status="SUCCESS")
            return result
        except FacebookTokenError as e:
            logger.error(f"Facebook token error: {e}")
            log_post(discord_message=message, fb_post_id=None, status="FAILED_TOKEN", error=str(e))
            raise
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{config.MAX_RETRIES} failed: {e}")
            if attempt < config.MAX_RETRIES:
                await asyncio.sleep(config.RETRY_DELAY_SECONDS)
            else:
                logger.error(f"All {config.MAX_RETRIES} attempts failed.")
                log_post(discord_message=message, fb_post_id=None, status="FAILED", error=str(e))
                raise


async def _post_to_facebook(message: str, image_urls: list, page_id: str, page_token: str) -> dict:
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if not image_urls:
            return await _post_text(session, message, page_id, page_token)
        if len(image_urls) == 1:
            return await _post_single_photo(session, message, image_urls[0], page_id, page_token)
        return await _post_multi_photo(session, message, image_urls, page_id, page_token)


async def _post_text(session: aiohttp.ClientSession, message: str, page_id: str, page_token: str) -> dict:
    payload = {
        "message": message,
        "access_token": page_token,
    }
    async with session.post(_feed_url(page_id), data=payload) as response:
        data = await response.json()
        _raise_for_facebook_status(response.status, data)
        return data


async def _post_single_photo(session: aiohttp.ClientSession, message: str, image_url: str, page_id: str, page_token: str) -> dict:
    payload = {
        "url": image_url,
        "message": message,
        "access_token": page_token,
    }
    async with session.post(_photos_url(page_id), data=payload) as response:
        data = await response.json()
        _raise_for_facebook_status(response.status, data)
        return data


async def _post_multi_photo(session: aiohttp.ClientSession, message: str, image_urls: list, page_id: str, page_token: str) -> dict:
    media_fbids = []
    for url in image_urls:
        payload = {
            "url": url,
            "published": "false",
            "access_token": page_token,
        }
        async with session.post(_photos_url(page_id), data=payload) as response:
            data = await response.json()
            _raise_for_facebook_status(response.status, data)
            media_fbids.append(data["id"])

    payload = {
        "message": message,
        "attached_media": json.dumps([{"media_fbid": fbid} for fbid in media_fbids]),
        "access_token": page_token,
    }
    async with session.post(_feed_url(page_id), data=payload) as response:
        data = await response.json()
        _raise_for_facebook_status(response.status, data)
        return data


def _raise_for_facebook_status(status: int, data: dict):
    if status == 200:
        return
    error = data.get("error", {})
    code = error.get("code")
    msg = error.get("message", "Unknown Facebook API error")
    if code in (190, 102):
        raise FacebookTokenError(msg)
    raise FacebookAPIError(f"[{status}] {msg}")


async def check_token(page_id: str, page_token: str) -> bool:
    """Verify the token can access the given Facebook page."""
    url = f"{config.FACEBOOK_BASE_URL}/{page_id}"
    params = {"access_token": page_token, "fields": "id"}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Token check request failed: {e}")
        return False


class FacebookAPIError(Exception):
    pass


class FacebookTokenError(FacebookAPIError):
    pass

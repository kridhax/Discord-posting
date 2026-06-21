import config
from logger.logger import get_logger

logger = get_logger(__name__)


async def format_message(content: str, author: str = "") -> str:
    """
    Format a Discord message for Facebook.
    If USE_AI_FORMATTER=true, uses OpenAI to rewrite the message.
    Otherwise, returns content as-is with optional author credit.
    """
    if config.USE_AI_FORMATTER:
        return await _ai_format(content)
    return _simple_format(content, author)


def _simple_format(content: str, author: str = "") -> str:
    """Pass-through — post exactly what was in Discord."""
    return content


async def _ai_format(content: str) -> str:
    """
    Use OpenAI to rewrite the Discord message into a polished Facebook post.
    """
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )

        prompt = (
            "You are a social media manager. Rewrite the following Discord message "
            "as a polished, engaging Facebook post. Keep it concise (under 300 words), "
            "use relevant emojis, and maintain a professional yet friendly tone. "
            "Return only the post text — no extra commentary.\n\n"
            f"Discord message:\n{content}"
        )

        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )

        formatted = response.choices[0].message.content.strip()
        logger.info("AI formatter produced output successfully.")
        return formatted

    except Exception as e:
        logger.error(f"AI formatting failed: {e} — falling back to original content.")
        return content

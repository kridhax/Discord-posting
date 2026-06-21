import discord
import config
from logger.logger import get_logger
from utils.helpers import is_rate_limited, is_duplicate

logger = get_logger(__name__)


class DiscordBot(discord.Client):
    def __init__(self, on_valid_message):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.on_valid_message = on_valid_message

    async def on_ready(self):
        logger.info(f"Discord bot logged in as {self.user} (ID: {self.user.id})")
        if config.DISCORD_GUILD_ID:
            logger.info(f"Monitoring server ID: {config.DISCORD_GUILD_ID}")
        logger.info(f"Monitoring {len(config.CHANNEL_TO_PAGE)} mapped channel(s)")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if config.DISCORD_GUILD_ID and message.guild.id != config.DISCORD_GUILD_ID:
            return

        mapping = config.CHANNEL_TO_PAGE.get(str(message.channel.id))
        if not mapping:
            return

        content = message.content.strip()
        attachments = [a.url for a in message.attachments]

        if not content and not attachments:
            return

        lower = content.lower()
        for word in config.BANNED_WORDS:
            if word.lower() in lower:
                logger.warning(f"Message blocked — contains banned word: '{word}'")
                return

        if is_rate_limited():
            logger.warning("Rate limit active — skipping message.")
            return

        if is_duplicate(content):
            logger.warning("Duplicate message detected — skipping.")
            return

        logger.info(f"Valid message from {message.author}: {content[:80]}...")

        await self.on_valid_message(
            content=content,
            author=str(message.author),
            attachments=attachments,
            created_at=message.created_at,
            page_config=mapping,
        )

    async def on_error(self, event, *args, **kwargs):
        logger.exception(f"Discord error in event '{event}'")


def start_bot(on_valid_message):
    bot = DiscordBot(on_valid_message=on_valid_message)
    bot.run(config.DISCORD_TOKEN)

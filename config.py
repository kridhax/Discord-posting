import os
from dotenv import load_dotenv
from utils import mappings as mappings_loader
from utils.storage import get_storage

load_dotenv()


def _int_env(name: str, default: int = 0) -> int:
    val = os.getenv(name)
    return int(val) if val else default


# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = _int_env("DISCORD_GUILD_ID")

# Facebook
FACEBOOK_API_VERSION = "v19.0"
FACEBOOK_BASE_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"

# AI Formatter (optional)
USE_AI_FORMATTER = os.getenv("USE_AI_FORMATTER", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Validation
BANNED_WORDS = [w.strip() for w in os.getenv("BANNED_WORDS", "").split(",") if w.strip()]
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "10"))

# Retry
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Channel → Facebook page mappings
MAPPINGS_FILE = os.getenv("MAPPINGS_FILE", "mappings.json")
CHANNEL_TO_PAGE = {}


def load_channel_mappings():
    global CHANNEL_TO_PAGE
    storage = get_storage(MAPPINGS_FILE)
    CHANNEL_TO_PAGE = storage.load()
    return CHANNEL_TO_PAGE


def validate():
    missing = []
    if not DISCORD_TOKEN:
        missing.append("DISCORD_TOKEN")
    if not DISCORD_GUILD_ID:
        missing.append("DISCORD_GUILD_ID")
    if USE_AI_FORMATTER and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY (required when USE_AI_FORMATTER=true)")
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    load_channel_mappings()
    if not CHANNEL_TO_PAGE:
        raise EnvironmentError(f"No channel mappings found in {MAPPINGS_FILE or 'configured storage'}")

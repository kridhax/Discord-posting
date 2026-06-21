# Agent Notes

## Project
Discord → Facebook Auto-Posting Agent
Listens to mapped Discord channels and forwards messages to the corresponding Facebook Pages.

## Setup
1. Copy `.env.example` to `.env` and fill in the values.
2. Edit `mappings.json` to map Discord channel IDs to Facebook page IDs and tokens.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`

## Discord Bot Setup
1. Go to https://discord.com/developers/applications
2. Create application → Bot tab → Add Bot
3. Enable **Message Content Intent** under Privileged Gateway Intents
4. Generate OAuth2 URL with scope `bot` and permissions:
   - Read Messages/View Channels
   - Read Message History
5. Open URL in browser and invite bot to server

## Facebook Token Setup
1. Go to https://developers.facebook.com/tools/explorer/
2. Select app `shoro ai`
3. Generate User Access Token with permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
4. Use the dropdown: **Get Page Access Token** → select page
5. Ensure "User or Page" dropdown shows the page name, not "User"
6. Copy token to `mappings.json` for the relevant channel
7. For public visibility, switch app from Development Mode to Live

## Channel → Page Mapping
Store mappings in `mappings.json`:

```json
{
  "123456789012345678": {
    "page_id": "111111111111",
    "page_token": "EAAB..."
  },
  "987654321098765432": {
    "page_id": "222222222222",
    "page_token": "EAAB..."
  }
}
```

To add a new channel/page pair, just add another entry to `mappings.json`. No code changes are needed.

## Common Issues

### Bot doesn't see Discord messages
- Verify bot is in the server
- Verify channel permissions: View Channel + Read Message History
- Verify Message Content Intent is enabled
- Check `DISCORD_GUILD_ID` value
- Check that the channel ID exists in `mappings.json`

### Facebook 403 error
- Token is a User token, not a Page token. Must select page in Graph API Explorer dropdown.
- Token missing `pages_manage_posts` or `pages_read_engagement` permissions.

### Posts don't appear publicly
- Facebook app is in Development Mode. Posts are visible only to app admins.
- Switch app to Live in Facebook Developer Console, or check posts in Meta Business Suite.

## Environment Variables
- `DISCORD_TOKEN` - required
- `DISCORD_GUILD_ID` - required
- `MAPPINGS_FILE` - optional, defaults to `mappings.json`
- `OPENAI_API_KEY` or `OPEN_ROUTER_API_KEY` - optional
- `USE_AI_FORMATTER` - optional, default false
- `BANNED_WORDS` - optional
- `RATE_LIMIT_SECONDS` - optional, default 10

## Files Modified During Setup
- `app.py` - entry point
- `config.py` - env loading, supports mappings file
- `discord_listener/bot.py` - Discord client
- `facebook/publisher.py` - Facebook posting with aiohttp
- `formatter/formatter.py` - AI formatting
- `utils/helpers.py` - rate limit and duplicate detection
- `utils/mappings.py` - channel → page mapping loader
- `logger/logger.py` - logging and SQLite post log
- `mappings.json` - channel → page mapping
- `requirements.txt` - dependencies

## Logs
- Runtime logs: `logs/agent.log`
- Post history: `logs/posts.db`

## Docker
```bash
docker-compose up -d
```
opencode -s ses_1205e2681ffeIUV0BtFpmDc9eW
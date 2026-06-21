# Discord → Facebook Auto-Posting Agent

Listens to a Discord channel and automatically cross-posts messages to a Facebook Page.

---

## Setup

### 1. Clone / Extract the project

```bash
cd discord-fb-agent
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Fill in the values (see Configuration below).

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python app.py
```

---

## Configuration

Edit `.env`:

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Your Discord bot token |
| `DISCORD_GUILD_ID` | ✅ | Server ID to listen to |
| `DISCORD_CHANNEL_ID` | Optional | Channel ID to listen to (defaults to all channels in the server) |
| `FACEBOOK_PAGE_ID` | ✅ | Your Facebook Page ID |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | ✅ | Long-lived Page Access Token |
| `OPENAI_API_KEY` | Optional | Only needed if `USE_AI_FORMATTER=true` |
| `OPEN_ROUTER_API_KEY` | Optional | Alternative to `OPENAI_API_KEY` for OpenRouter |
| `OPENAI_BASE_URL` | Optional | API base URL (e.g. `https://openrouter.ai/api/v1`) |
| `OPENAI_MODEL` | Optional | Model name (default: `gpt-4o-mini`) |
| `USE_AI_FORMATTER` | Optional | `true` to rewrite posts with GPT |
| `BANNED_WORDS` | Optional | Comma-separated words to block |
| `RATE_LIMIT_SECONDS` | Optional | Min seconds between posts (default: 10) |

---

## Getting Your Tokens

### Discord Bot Token
1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it
3. Go to **Bot** tab → click **Add Bot**
4. Under **Token**, click **Reset Token** and copy it
5. Under **Privileged Gateway Intents**, enable **Message Content Intent**
6. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Read Messages/View Channels`, `Read Message History`
7. Copy the generated URL, open it in browser, and add the bot to your server

### Discord Channel ID
1. In Discord, go to **User Settings → Advanced → Enable Developer Mode**
2. Right-click the target channel → **Copy Channel ID**

### Facebook Page Access Token
1. Go to https://developers.facebook.com
2. Create an App (type: **Business**)
3. Add **Facebook Login** and **Pages API** products
4. Go to **Graph API Explorer**
5. Select your app, click **Generate Access Token**
6. Add permissions: `pages_manage_posts`, `pages_read_engagement`
7. Click **Get Page Access Token** (select your page)
8. To get a **long-lived token** (recommended), use:
   ```
   GET https://graph.facebook.com/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={app_id}
     &client_secret={app_secret}
     &fb_exchange_token={short_lived_token}
   ```

### Facebook Page ID
- Visit your Facebook Page → **About** → scroll to bottom
- Or: `https://graph.facebook.com/me/accounts?access_token=YOUR_TOKEN`

---

## Docker (optional)

```bash
docker-compose up -d
```

Logs are persisted in the `./logs/` folder.

---

## Logs

- `logs/agent.log` — runtime logs
- `logs/posts.db` — SQLite database of all post attempts

To view recent posts:
```python
from logger.logger import get_recent_posts
for row in get_recent_posts():
    print(row)
```

# Discord → Facebook Agent Setup Guide

This guide explains how to set up and run the Discord → Facebook auto-posting agent, even if you have no coding experience.

## What You Need

- A Discord server where you are an admin.
- A Facebook account.
- Facebook Pages you want to post to.
- A Facebook app called **shoro ai** already created by the developer.

---

## Step 1: Create a Facebook Page

A Facebook Page is different from your personal Facebook profile.

1. Go to https://www.facebook.com/pages/create
2. Click **Business or Brand**.
3. Enter a **Page Name**.
4. Choose a **Category**.
5. Click **Create Page**.

Repeat this for every Facebook Page you want to connect to a Discord channel.

---

## Step 2: Find Your Facebook Page ID

1. Open your Facebook Page in a browser.
2. Look at the address bar.

**If the URL has numbers:**

```
https://www.facebook.com/123456789012345
```

The Page ID is `123456789012345`.

**If the URL has a name:**

```
https://www.facebook.com/MyPageName
```

Use a Page ID lookup tool like https://lookup-id.com/ and paste your Page URL to get the numeric Page ID.

---

## Step 3: Get a Short-Lived User Access Token

1. Go to https://developers.facebook.com/tools/explorer/
2. At the top, make sure the selected app is **shoro ai**.
3. Make sure the **User or Page** dropdown says **User** (not your Page).
4. Click **Generate User Access Token**.
5. A popup will ask for permissions. Check these boxes:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
6. Click **Generate**.
7. Copy the long token that appears. It will start with something like `EAAB...` or `EAAN...`.

This token is short-lived and expires in about **1 hour**.

---

## Step 4: Convert to a Long-Lived Page Token

The agent needs a token that lasts about **60 days**. Use the helper script to convert your short-lived token.

1. Make sure you are in the project folder in your terminal:

```bash
cd "C:\Users\BIT\OneDrive\Desktop\New folder\discord-fb-agent"
```

2. Run the token refresh script:

```bash
python refresh_facebook_tokens.py
```

3. When asked, paste your short-lived User token from Step 3.
4. Press Enter.
5. The script will update `mappings.json` automatically.

---

## Step 4 (Alternative): Use the Admin Web Panel

For an all-in-one interface to manage mappings **and** refresh tokens, use the Streamlit admin panel.

### Run locally

1. Install dependencies:

```bash
pip install streamlit requests
```

2. Run the admin panel:

```bash
streamlit run admin_panel.py
```

3. Your browser will open. The panel has three tabs:
   - **Refresh Tokens**: Enter App ID, App Secret, and short-lived User token to refresh all page tokens.
   - **Manage Mappings**: Add, edit, or delete channel → page mappings. Changes are saved directly to `mappings.json`.
   - **Download / Upload**: Download `mappings.json` or replace it by uploading a new one.

### Deploy to Streamlit Cloud

You can host this online so users can manage mappings without touching files.

1. Push this project to GitHub.
2. Go to https://share.streamlit.io and create a new app.
3. Select `admin_panel.py` as the main file.
4. Set an environment variable if your `mappings.json` is in a custom location:
   - `MAPPINGS_FILE` — absolute or relative path to `mappings.json`
5. Deploy.

**Important:**
- This panel handles secrets. Only share the URL with trusted users.
- Tokens are kept in browser sessions and are never logged or stored server-side.
- Because Streamlit Cloud containers restart, `mappings.json` may reset unless you use persistent storage. For free Streamlit Cloud hosting, use a cloud database or cloud storage instead. See below for options.

---

## Persistent Storage Options for Deployment

If you deploy the admin panel online, the local `mappings.json` file may not persist across restarts. Choose one of these options:

### Option A: Cloud Database (Recommended)

Store mappings in a database like Supabase, Firebase Firestore, or PostgreSQL. This keeps data safe and shared across all users.

Ask a developer to connect the admin panel to a database instead of reading/writing `mappings.json` directly.

### Option B: Cloud Storage

Upload and download `mappings.json` from AWS S3, Google Cloud Storage, or Dropbox. The admin panel can read and write the file from cloud storage on every change.

### Option C: Always Download After Changes

If using free Streamlit Cloud without persistence, always download the updated `mappings.json` after making changes, and re-upload it the next time you open the panel.

---

## Step 5: Create Discord Channels and Get Their IDs

1. Open your Discord server.
2. Create a new text channel for each Facebook Page you want to connect.
3. Right-click the channel name → **Copy Channel ID**.
   - If you don't see this option, enable **Developer Mode** in Discord:
     - User Settings → Advanced → Developer Mode → ON.

---

## Step 6: Update mappings.json (Local Mode)

Open the `mappings.json` file in any text editor.

It looks like this:

```json
{
  "DISCORD_CHANNEL_ID": {
    "page_id": "FACEBOOK_PAGE_ID",
    "page_token": "LONG_LIVED_PAGE_TOKEN"
  }
}
```

Replace the values:

- `DISCORD_CHANNEL_ID` — the Discord channel ID from Step 5.
- `FACEBOOK_PAGE_ID` — the Facebook Page ID from Step 2.
- `LONG_LIVED_PAGE_TOKEN` — the token generated by `refresh_facebook_tokens.py` in Step 4.

To add more channels, add more entries:

```json
{
  "CHANNEL_ID_1": {
    "page_id": "PAGE_ID_1",
    "page_token": "TOKEN_1"
  },
  "CHANNEL_ID_2": {
    "page_id": "PAGE_ID_2",
    "page_token": "TOKEN_2"
  }
}
```

---

## Step 6 (Alternative): Use the Admin Web Panel

For an all-in-one interface to manage mappings **and** refresh tokens, use the Streamlit admin panel.

### Run locally

1. Install dependencies:

```bash
pip install streamlit requests
```

2. Run the admin panel:

```bash
streamlit run admin_panel.py
```

3. Your browser will open. The panel has three tabs:
   - **Refresh Tokens**: Enter App ID, App Secret, and short-lived User token to refresh all page tokens.
   - **Manage Mappings**: Add, edit, or delete channel → page mappings. Changes are saved directly to `mappings.json`.
   - **Download / Upload**: Download `mappings.json` or replace it with an upload.

### Deploy with persistent storage (Supabase, free)

Free Streamlit Cloud does **not** persist local files. Use Supabase to store mappings online.

1. Go to https://supabase.com and create a free project.
2. In the SQL Editor, run this:

```sql
CREATE TABLE mappings (
  id TEXT PRIMARY KEY,
  data JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

3. Go to Project Settings → API.
4. Copy:
   - `URL` (e.g. `https://your-project.supabase.co`)
   - `anon public` key
5. In your deployment platform, set these environment variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

Optional:

```env
SUPABASE_TABLE=mappings
SUPABASE_ROW_ID=default
```

6. Deploy `admin_panel.py`.
7. Now mappings are saved in Supabase and persist across restarts.

**Security:** Use Row Level Security and only share the admin URL with trusted users.

---

## Step 7: Set Environment Variables

1. Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

2. Open `.env` in a text editor.
3. Fill in these values:

```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id
```

### How to get DISCORD_TOKEN

1. Go to https://discord.com/developers/applications
2. Create a new application.
3. Go to the **Bot** tab and click **Add Bot**.
4. Enable **Message Content Intent** under Privileged Gateway Intents.
5. Click **Reset Token** and copy the token.
6. Paste it into `.env`.

### How to get DISCORD_GUILD_ID

1. Open Discord in a browser.
2. Open your server.
3. Look at the URL:

```
https://discord.com/channels/123456789012345678/...
```

The first number is your Guild ID: `123456789012345678`.

Paste it into `.env`.

---

## Step 8: Install Dependencies

Run this in the terminal:

```bash
pip install -r requirements.txt
```

If you use the token refresh script, also run:

```bash
pip install requests
```

---

## Step 9: Run the Bot

Run:

```bash
python app.py
```

You should see messages like:

```
All Facebook tokens are valid.
Discord bot logged in as shoro ai#5273
Monitoring server ID: ...
Monitoring 1 mapped channel(s)
```

Now any message you send in a mapped Discord channel will be posted to the connected Facebook Page.

---

## Step 10: Keep the Bot Running

The bot stops when you close the terminal. To keep it running:

- On Windows, run it as a background service.
- Use a tool like PM2 or NSSM.
- Or leave the terminal window open.

---

## Refreshing Tokens

Facebook long-lived Page tokens expire after about **60 days**. To refresh them:

1. Repeat Step 3 to get a new short-lived User token.
2. Run `python refresh_facebook_tokens.py` again.
3. The script updates `mappings.json` with fresh long-lived tokens.
4. Restart the bot with `python app.py`.

---

## Troubleshooting

### "Facebook token check failed"

- The token is expired.
- The token is a User token, not a Page token.
- The Page ID in `mappings.json` is wrong.
- The Facebook app doesn't have the required permissions.

### "Bot doesn't see Discord messages"

- The bot is not in the server.
- The bot doesn't have permission to read the channel.
- Message Content Intent is not enabled.
- The channel ID is not in `mappings.json`.

### "Posts don't appear publicly"

- The Facebook app is in Development Mode. Only app admins can see posts.
- Switch the app to Live in the Facebook Developer Console.

---

## Important Notes

- Never share your tokens, App Secret, or `.env` file with anyone.
- Do not commit `mappings.json` or `.env` to GitHub.
- If you deploy the admin panel, protect it with authentication or share only with trusted users.
- Supabase `anon` key is safe to embed in the Streamlit app, but enable Row Level Security to control access.

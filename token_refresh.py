"""
Facebook Long-Lived Page Token Generator (backend)

Shared logic used by token_refresh_app.py (Streamlit) and the FastAPI web UI.
"""

import requests

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def exchange_user_token(app_id: str, app_secret: str, short_lived_token: str) -> str:
    url = f"{BASE_URL}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    if response.status_code != 200 or "access_token" not in data:
        error = data.get("error", {})
        raise RuntimeError(
            f"Failed to exchange user token: {error.get('message', data)}"
        )

    return data["access_token"]


def fetch_page_token(long_lived_user_token: str, page_id: str) -> str:
    url = f"{BASE_URL}/{page_id}"
    params = {
        "access_token": long_lived_user_token,
        "fields": "access_token",
    }
    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    if response.status_code != 200:
        error = data.get("error", {})
        raise RuntimeError(
            f"Failed to fetch page token: {error.get('message', data)}"
        )

    token = data.get("access_token")
    if not token:
        raise RuntimeError(
            "No page token returned. Make sure the user token has "
            "pages_manage_posts and pages_read_engagement permissions, "
            "and that you are an admin of the page."
        )

    return token


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Long-Lived Page Token Generator</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            color: #1a1a2e;
            margin: 0;
            padding: 2rem;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        h1 { margin-top: 0; font-size: 1.5rem; }
        label {
            display: block;
            margin: 1rem 0 0.4rem;
            font-weight: 600;
            font-size: 0.9rem;
        }
        input, textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 0.95rem;
            font-family: inherit;
        }
        textarea { min-height: 80px; resize: vertical; }
        button {
            margin-top: 1.5rem;
            width: 100%;
            padding: 0.85rem;
            background: #2563eb;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { background: #1d4ed8; }
        .error {
            margin-top: 1rem;
            padding: 0.75rem;
            background: #fee2e2;
            color: #991b1b;
            border-radius: 8px;
            white-space: pre-wrap;
        }
        .success {
            margin-top: 1rem;
            padding: 0.75rem;
            background: #d1fae5;
            color: #065f46;
            border-radius: 8px;
        }
        .token-box {
            margin-top: 0.75rem;
            width: 100%;
            padding: 0.75rem;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-family: monospace;
            word-break: break-all;
            min-height: 60px;
        }
        .help {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #eff6ff;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        .help ul { margin: 0.5rem 0 0; padding-left: 1.2rem; }
        .notice {
            margin-top: 1rem;
            font-size: 0.85rem;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Facebook Long-Lived Page Token Generator</h1>
        <div class="help">
            <strong>How to get these values:</strong>
            <ul>
                <li><strong>App ID & App Secret</strong>: Facebook Developer Console → your app → Settings → Basic.</li>
                <li><strong>Short-lived User Token</strong>: Graph API Explorer, set to <strong>User</strong>, grant
                    <code>pages_show_list</code>, <code>pages_read_engagement</code>, <code>pages_manage_posts</code>.</li>
                <li><strong>Page ID</strong>: Open your Facebook Page. The numeric ID is in the URL.</li>
            </ul>
        </div>
        <form method="post" action="/token">
            <label for="app_id">Facebook App ID</label>
            <input type="text" id="app_id" name="app_id" placeholder="1234567890" required>

            <label for="app_secret">Facebook App Secret</label>
            <input type="password" id="app_secret" name="app_secret" placeholder="Paste here" required>

            <label for="short_lived_token">Short-lived User Access Token</label>
            <textarea id="short_lived_token" name="short_lived_token" placeholder="EAAB... or EAAN..." required></textarea>

            <label for="page_id">Facebook Page ID</label>
            <input type="text" id="page_id" name="page_id" placeholder="111111111111" required>

            <button type="submit">Generate Long-Lived Page Token</button>
        </form>
        {result}
        <p class="notice">
            Tokens are processed in memory and never logged or stored.
            This token lasts about 60 days; save it in your mappings.json.
        </p>
    </div>
</body>
</html>
""".strip()


def render_result(message: str, is_error: bool = False, token: str = None) -> str:
    if token:
        return f"""
        <div class="success">
            <strong>Long-lived Page token generated successfully!</strong>
            <div class="token-box">{token}</div>
        </div>
        """
    css_class = "error" if is_error else "success"
    return f'<div class="{css_class}">{message}</div>'

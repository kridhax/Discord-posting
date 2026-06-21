"""
Facebook Long-Lived Page Token Refresher (CLI)

This script:
1. Prompts for App ID, App Secret, and a short-lived User token.
2. Exchanges the short-lived User token for a long-lived User token.
3. Fetches long-lived Page tokens using the page IDs in mappings.json.
4. Updates mappings.json with the new long-lived Page tokens.

Run: python refresh_facebook_tokens.py

For a web UI, see token_refresh_app.py.
"""

import json
import os
import sys
import requests

from logger.logger import get_logger

logger = get_logger("refresh_facebook_tokens")

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def load_mappings(path: str = "mappings.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mappings file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mappings(mappings: dict, path: str = "mappings.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)
        f.write("\n")


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

    logger.info("Short-lived User token exchanged for long-lived User token.")
    return data["access_token"]


def fetch_page_token(long_lived_user_token: str, page_id: str) -> str:
    """Fetch a long-lived Page token for a specific page ID."""
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
            f"Failed to fetch token for page {page_id}: {error.get('message', data)}"
        )

    token = data.get("access_token")
    if not token:
        raise RuntimeError(
            f"No access_token returned for page {page_id}. "
            "Make sure the user token has pages_manage_posts and pages_read_engagement permissions."
        )

    return token


def update_mappings(mappings: dict, long_lived_user_token: str) -> dict:
    updated = False
    for channel_id, cfg in mappings.items():
        page_id = cfg.get("page_id")
        if not page_id:
            logger.warning(f"Skipping channel {channel_id}: missing page_id")
            continue

        try:
            cfg["page_token"] = fetch_page_token(long_lived_user_token, page_id)
            logger.info(f"Updated token for channel {channel_id} (page {page_id}).")
            updated = True
        except Exception as e:
            logger.error(f"Could not update token for channel {channel_id} (page {page_id}): {e}")

    if not updated:
        raise RuntimeError("No mappings were updated. Check your page IDs and token permissions.")

    return mappings


def main():
    print("=== Facebook Long-Lived Page Token Refresher ===")
    print()

    app_id = input("Enter Facebook App ID: ").strip()
    app_secret = input("Enter Facebook App Secret: ").strip()
    short_lived_token = input("Enter short-lived User Access Token: ").strip()

    if not app_id or not app_secret or not short_lived_token:
        logger.error("App ID, App Secret, and User token are all required.")
        sys.exit(1)

    mappings_path = input("Enter mappings.json path (default: mappings.json): ").strip() or "mappings.json"

    try:
        mappings = load_mappings(mappings_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info("Exchanging short-lived User token for long-lived User token...")
    long_lived_user_token = exchange_user_token(app_id, app_secret, short_lived_token)

    logger.info("Fetching long-lived Page tokens from mappings.json page IDs...")
    updated_mappings = update_mappings(mappings, long_lived_user_token)
    save_mappings(updated_mappings, mappings_path)

    logger.info(f"mappings.json updated successfully: {mappings_path}")
    print()
    print("Done. You can now restart your bot with python app.py")


if __name__ == "__main__":
    main()

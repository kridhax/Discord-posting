"""
Streamlit Admin Panel for Discord → Facebook Agent

This app combines:
1. Facebook long-lived token refresh.
2. mappings.json management (view, add, edit, delete, download).
3. Persistent storage via local file or Supabase.

Run locally:
    streamlit run admin_panel.py

To use Supabase, set these environment variables:
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your-anon-or-service-key
    SUPABASE_TABLE=mappings          # optional, default: mappings
    SUPABASE_ROW_ID=default          # optional, default: default

Deploy to Streamlit Cloud:
    - Push this repo to GitHub.
    - Create app on https://share.streamlit.io with main file admin_panel.py.
    - Add the env vars above in Streamlit Cloud settings.
"""

import json
import os

import requests
import streamlit as st

from utils.storage import get_storage

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

st.set_page_config(
    page_title="Discord → Facebook Admin",
    page_icon="⚙️",
    layout="wide",
)


def get_storage_info() -> str:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        table = os.getenv("SUPABASE_TABLE", "mappings")
        row_id = os.getenv("SUPABASE_ROW_ID", "default")
        return f"Supabase table `{table}`, row `{row_id}`"
    return f"Local file `{os.getenv('MAPPINGS_FILE', 'mappings.json')}`"


storage = get_storage()


def load_mappings() -> dict:
    try:
        return storage.load()
    except Exception as e:
        st.error(f"Failed to load mappings: {e}")
        return {}


def save_mappings(mappings: dict):
    storage.save(mappings)


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
            f"Failed to fetch token for page {page_id}: {error.get('message', data)}"
        )

    token = data.get("access_token")
    if not token:
        raise RuntimeError(
            f"No access_token returned for page {page_id}. "
            "Make sure the user token has pages_manage_posts and pages_read_engagement permissions."
        )

    return token


def refresh_all_tokens(app_id: str, app_secret: str, short_lived_token: str, mappings: dict):
    long_lived_user_token = exchange_user_token(app_id, app_secret, short_lived_token)
    updated = {}
    errors = []

    for channel_id, cfg in mappings.items():
        page_id = cfg.get("page_id")
        if not page_id:
            errors.append(f"Channel {channel_id}: missing page_id")
            updated[channel_id] = cfg
            continue

        try:
            new_token = fetch_page_token(long_lived_user_token, page_id)
            updated[channel_id] = {"page_id": page_id, "page_token": new_token}
        except Exception as e:
            errors.append(f"Channel {channel_id} (page {page_id}): {e}")
            updated[channel_id] = cfg

    return updated, errors


def main():
    st.title("⚙️ Discord → Facebook Admin Panel")
    st.caption(f"Storage: {get_storage_info()}")

    tab1, tab2, tab3 = st.tabs(["🔑 Refresh Tokens", "🗺️ Manage Mappings", "⬇️ Download / Upload"])

    mappings = load_mappings()

    with tab1:
        st.header("Refresh Facebook Tokens")
        st.markdown(
            "Convert short-lived Facebook User tokens into long-lived Page tokens."
        )

        with st.expander("How to get these values"):
            st.markdown(
                """
                1. **App ID & App Secret**: Facebook Developer Console → your app → Settings → Basic.
                2. **Short-lived User Token**: Graph API Explorer, set to **User**, grant
                   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`.
                """
            )

        col1, col2 = st.columns(2)
        with col1:
            app_id = st.text_input("Facebook App ID", placeholder="1234567890")
        with col2:
            app_secret = st.text_input("Facebook App Secret", placeholder=" Paste here", type="password")

        short_lived_token = st.text_area(
            "Short-lived User Access Token",
            placeholder="EAAB... or EAAN...",
        )

        if st.button("🚀 Refresh Tokens", type="primary", use_container_width=True):
            if not app_id or not app_secret or not short_lived_token:
                st.error("Please fill in all three fields.")
            elif not mappings:
                st.error("No mappings found. Add mappings in the Manage Mappings tab first.")
            else:
                with st.spinner("Refreshing tokens..."):
                    try:
                        updated, errors = refresh_all_tokens(
                            app_id, app_secret, short_lived_token, mappings
                        )
                    except Exception as e:
                        st.error(f"Token refresh failed: {e}")
                        updated = mappings
                        errors = []

                if errors:
                    st.warning("Some tokens could not be refreshed:")
                    for err in errors:
                        st.write(f"- {err}")

                success_count = sum(
                    1
                    for ch, cfg in updated.items()
                    if cfg.get("page_token")
                    and cfg.get("page_token") != mappings.get(ch, {}).get("page_token")
                )

                if success_count > 0:
                    st.success(f"Refreshed {success_count} token(s) successfully.")
                    save_mappings(updated)
                    st.rerun()
                elif not errors:
                    st.info("No changes were made.")

    with tab2:
        st.header("Manage Channel → Page Mappings")

        st.subheader("Add / Edit Mapping")

        channel_ids = list(mappings.keys())
        selected_channel = st.selectbox(
            "Select channel to edit, or choose 'New channel'",
            options=["New channel"] + channel_ids,
        )

        if selected_channel == "New channel":
            edit_channel_id = st.text_input("Discord Channel ID", placeholder="123456789012345678")
            edit_page_id = st.text_input("Facebook Page ID", placeholder="111111111111")
            edit_page_token = st.text_input(
                "Facebook Page Token",
                placeholder="EAAB...",
                type="password",
            )
        else:
            cfg = mappings.get(selected_channel, {})
            edit_channel_id = st.text_input("Discord Channel ID", value=selected_channel)
            edit_page_id = st.text_input("Facebook Page ID", value=cfg.get("page_id", ""))
            edit_page_token = st.text_input(
                "Facebook Page Token",
                value=cfg.get("page_token", ""),
                type="password",
            )

        col_save, col_delete = st.columns(2)

        with col_save:
            if st.button("💾 Save Mapping", use_container_width=True):
                if not edit_channel_id or not edit_page_id or not edit_page_token:
                    st.error("Channel ID, Page ID, and Page Token are all required.")
                else:
                    if selected_channel != "New channel" and selected_channel != edit_channel_id:
                        del mappings[selected_channel]

                    mappings[edit_channel_id] = {
                        "page_id": edit_page_id,
                        "page_token": edit_page_token,
                    }
                    save_mappings(mappings)
                    st.success("Mapping saved.")
                    st.rerun()

        with col_delete:
            if selected_channel != "New channel" and st.button(
                "🗑️ Delete Mapping", use_container_width=True
            ):
                del mappings[selected_channel]
                save_mappings(mappings)
                st.success("Mapping deleted.")
                st.rerun()

        st.divider()
        st.subheader("Current Mappings")

        if mappings:
            for channel_id, cfg in mappings.items():
                token_preview = cfg.get("page_token", "")[:10] + "..."
                with st.expander(f"Channel {channel_id}"):
                    st.write(f"**Page ID:** {cfg.get('page_id')}")
                    st.write(f"**Token preview:** {token_preview}")
        else:
            st.info("No mappings yet. Add one above.")

    with tab3:
        st.header("Download / Upload mappings.json")

        col_down, col_up = st.columns(2)

        with col_down:
            st.download_button(
                label="⬇️ Download mappings.json",
                data=json.dumps(mappings, indent=2),
                file_name="mappings.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_up:
            uploaded = st.file_uploader("Upload mappings.json", type="json")
            if uploaded is not None:
                try:
                    new_mappings = json.loads(uploaded.read().decode("utf-8"))
                    if st.button("✅ Replace mappings.json", use_container_width=True):
                        save_mappings(new_mappings)
                        st.success("mappings.json replaced.")
                        st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")


if __name__ == "__main__":
    main()

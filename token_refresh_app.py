"""
Minimal Facebook Long-Lived Page Token Generator (Streamlit)

This Streamlit app takes 4 inputs and returns one long-lived Facebook Page token.

For a deployment that does not require Streamlit or Pillow, use the FastAPI web UI
included in web_app.py (routes /token and POST /token).

Inputs:
1. Facebook App ID
2. Facebook App Secret
3. Short-lived User Access Token
4. Facebook Page ID

Output:
- Long-lived Page Access Token

Run locally:
    streamlit run token_refresh_app.py

Deploy to Streamlit Cloud:
    - Push this repo to GitHub
    - Create app at https://share.streamlit.io
    - Select token_refresh_app.py as the main file

WARNING: This app handles secrets. Do not share the deployed URL publicly.
Tokens are processed in memory and never logged or stored.
"""

import streamlit as st

from token_refresh import exchange_user_token, fetch_page_token

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

st.set_page_config(
    page_title="Facebook Page Token Generator",
    page_icon="🔑",
    layout="centered",
)


def main():
    st.title("🔑 Facebook Long-Lived Page Token Generator")
    st.markdown("Enter 4 values below to generate a long-lived Facebook Page token.")

    with st.expander("How to get these values"):
        st.markdown(
            """
            1. **App ID & App Secret**: Facebook Developer Console → your app → Settings → Basic.
            2. **Short-lived User Token**: Graph API Explorer, set to **User**, grant
               `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`.
            3. **Page ID**: Open your Facebook Page. The numeric ID is in the URL,
               or use a Page ID lookup tool.
            """
        )

    app_id = st.text_input("Facebook App ID", placeholder="1234567890")
    app_secret = st.text_input("Facebook App Secret", placeholder=" Paste here", type="password")
    short_lived_token = st.text_area(
        "Short-lived User Access Token",
        placeholder="EAAB... or EAAN...",
    )
    page_id = st.text_input("Facebook Page ID", placeholder="111111111111")

    if st.button("🚀 Generate Long-Lived Page Token", type="primary", use_container_width=True):
        if not app_id or not app_secret or not short_lived_token or not page_id:
            st.error("Please fill in all 4 fields.")
            return

        with st.spinner("Generating token..."):
            try:
                long_lived_user_token = exchange_user_token(
                    app_id, app_secret, short_lived_token
                )
                page_token = fetch_page_token(long_lived_user_token, page_id)
            except Exception as e:
                st.error(f"Token generation failed: {e}")
                return

        st.success("Long-lived Page token generated successfully!")
        st.subheader("Your Page Token")
        st.code(page_token, language="text")
        st.button(
            "📋 Copy to clipboard",
            on_click=lambda: st.write("Use Ctrl+C / Cmd+C to copy the token above."),
            use_container_width=True,
        )
        st.info(
            "This token lasts about 60 days. Save it somewhere safe and paste it into your mappings.json."
        )


if __name__ == "__main__":
    main()

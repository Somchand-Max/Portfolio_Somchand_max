#!/usr/bin/env python3
"""Streamlit cloud deployment wrapper for Somchand Ratangwal's portfolio.

Integrates the static portfolio preview with the hardened Excel contact form
backend and an admin-gated `.xlsx` inbox viewer/downloader reusing `server.py`.
"""

from __future__ import annotations

import base64
import hmac
import mimetypes
import os
import re
import secrets
from pathlib import Path

import pandas as pd
import streamlit as st

from server import (
    BASE_DIR,
    EMAIL_MAX_LENGTH,
    EXCEL_PATH,
    LOCK_PATH,
    MESSAGE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SlidingWindowRateLimiter,
    ensure_excel_workbook,
    process_contact_submission,
)

ASSET_ATTR_RE = re.compile(r'(src|href)="(assets/[^"]+)"')
ASSET_JS_RE = re.compile(r"'(assets/[^']+)'")


@st.cache_resource
def get_streamlit_rate_limiter() -> SlidingWindowRateLimiter:
    """Keep a shared 3-messages-per-15-minutes rate limiter across reruns."""
    return SlidingWindowRateLimiter()


def _encode_asset_data_uri(rel_path: str, root: Path) -> str | None:
    """Resolve and base64-encode a local asset path under `root`, or return None."""
    candidate = (root / rel_path).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        return None
    mime, _ = mimetypes.guess_type(str(candidate))
    if not mime:
        return None
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _inline_local_asset(match: re.Match[str], root: Path) -> str:
    """Convert an HTML attribute `assets/...` reference to a base64 data URI."""
    attr, rel_path = match.group(1), match.group(2)
    data_uri = _encode_asset_data_uri(rel_path, root)
    return f'{attr}="{data_uri}"' if data_uri else match.group(0)


def _inline_js_asset(match: re.Match[str], root: Path) -> str:
    """Convert a JS single-quoted `'assets/...'` string literal to a base64 data URI."""
    data_uri = _encode_asset_data_uri(match.group(1), root)
    return f"'{data_uri}'" if data_uri else match.group(0)


@st.cache_data(show_spinner=False)
def build_standalone_portfolio_html(root_str: str = str(BASE_DIR)) -> str:
    """Bundle `index.html` with local CSS/JS/assets for sandboxed Streamlit iframe display."""
    root = Path(root_str)
    html_text = (root / "index.html").read_text(encoding="utf-8")
    css_text = (root / "css" / "styles.css").read_text(encoding="utf-8")
    theme_js = (root / "js" / "theme-init.js").read_text(encoding="utf-8").replace(
        "</script>", "<\\/script>"
    )
    main_js = ASSET_JS_RE.sub(
        lambda m: _inline_js_asset(m, root),
        (root / "js" / "script.js").read_text(encoding="utf-8"),
    ).replace("</script>", "<\\/script>")

    html_text = html_text.replace(
        '<script src="js/theme-init.js"></script>',
        f"<script>{theme_js}</script>",
    )
    html_text = html_text.replace(
        '<link rel="stylesheet" href="css/styles.css">',
        f"<style>{css_text}</style>",
    )
    html_text = html_text.replace(
        '<script src="js/script.js"></script>',
        f"<script>{main_js}</script>",
    )
    return ASSET_ATTR_RE.sub(lambda m: _inline_local_asset(m, root), html_text)


def _resolve_admin_key() -> str:
    """Load optional admin access key from Streamlit secrets or environment variables."""
    env_key = os.environ.get("PORTFOLIO_ADMIN_KEY", "").strip()
    if env_key:
        return env_key
    try:
        secret_key = str(st.secrets.get("PORTFOLIO_ADMIN_KEY", "")).strip()
        if secret_key:
            return secret_key
    except Exception:
        pass
    return ""


def _render_contact_tab(limiter: SlidingWindowRateLimiter) -> None:
    """Render the hardened contact form wired to `process_contact_submission`."""
    st.subheader("Send a Direct Message")
    st.caption(
        "Validated on the backend with length limits, XSS escaping, CSV/Excel formula neutralization, "
        "CSRF session binding, and a 3 messages / 15 min rate limit."
    )

    if "contact_csrf_nonce" not in st.session_state:
        st.session_state["contact_csrf_nonce"] = secrets.token_urlsafe(24)

    expected_nonce = st.session_state["contact_csrf_nonce"]

    with st.form("hardened_contact_form", clear_on_submit=True):
        sender_name = st.text_input(
            "Full Name",
            max_chars=NAME_MAX_LENGTH,
            placeholder="Your full name (max 80 chars)",
        )
        sender_email = st.text_input(
            "Email Address",
            max_chars=EMAIL_MAX_LENGTH,
            placeholder="you@example.com (max 120 chars)",
        )
        sender_message = st.text_area(
            "Message",
            max_chars=MESSAGE_MAX_LENGTH,
            height=140,
            placeholder="Write your message here (10 to 500 characters)...",
        )
        submitted = st.form_submit_button("Validate & Send Message", type="primary")

    if not submitted:
        return

    if not hmac.compare_digest(
        st.session_state.get("contact_csrf_nonce", ""), expected_nonce
    ):
        st.error("Security token validation failed. Please reload the page.")
        return

    client_key = f"streamlit-{expected_nonce[:12]}"
    allowed, retry_after = limiter.allow(client_key)
    if not allowed:
        st.error(
            f"Rate limit exceeded (max 3 messages per 15 minutes). "
            f"Please try again in {retry_after} seconds."
        )
        return

    status_code, response = process_contact_submission(
        {
            "name": sender_name,
            "email": sender_email,
            "message": sender_message,
            "website_url": "",
        },
        client_ip=client_key,
        excel_path=EXCEL_PATH,
        lock_path=LOCK_PATH,
    )

    if status_code == 200 and response.get("success"):
        st.success(
            "Message sent successfully! Your inquiry has been sanitized and logged to Excel."
        )
    else:
        st.error(response.get("error", "Unable to record your message."))


def _render_admin_tab() -> None:
    """Provide admin-key-gated Excel inbox preview and `.xlsx` download."""
    st.subheader("Protected Excel Contact Inbox (`data/contact_messages.xlsx`)")
    configured_key = _resolve_admin_key()
    if not configured_key:
        st.info(
            "Admin access key is not configured. Set `PORTFOLIO_ADMIN_KEY` in environment "
            "variables or `.streamlit/secrets.toml` to enable Excel log viewing and download."
        )
        return

    entered_key = st.text_input(
        "Admin Access Key",
        type="password",
        placeholder="Enter PORTFOLIO_ADMIN_KEY to unlock inbox",
    )
    if not entered_key:
        return

    if not hmac.compare_digest(entered_key, configured_key):
        st.error("Invalid admin access key.")
        return

    ensure_excel_workbook(EXCEL_PATH)
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    st.metric("Total Recorded Messages", len(df))
    st.dataframe(df, width="stretch", hide_index=True)

    excel_bytes = EXCEL_PATH.read_bytes()
    st.download_button(
        label="Download contact_messages.xlsx",
        data=excel_bytes,
        file_name="contact_messages.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def main() -> None:
    """Configure page metadata and render the Streamlit portfolio deployment."""
    st.set_page_config(
        page_title="Somchand Ratangwal | Cybersecurity & AI Portfolio",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    ensure_excel_workbook(EXCEL_PATH)
    limiter = get_streamlit_rate_limiter()

    tab_portfolio, tab_contact, tab_admin = st.tabs(
        ["Portfolio Website", "Contact Form (Excel Backend)", "Admin Excel Inbox"]
    )

    with tab_portfolio:
        embedded_html = build_standalone_portfolio_html(str(BASE_DIR))
        if hasattr(st, "iframe"):
            st.iframe(embedded_html, height=1100)
        else:
            import streamlit.components.v1 as components

            components.html(embedded_html, height=1100, scrolling=True)

    with tab_contact:
        _render_contact_tab(limiter)

    with tab_admin:
        _render_admin_tab()


if __name__ == "__main__":
    main()

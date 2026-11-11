#!/usr/bin/env python3
"""Streamlit cloud deployment wrapper for Somchand Ratangwal's portfolio.

Connects the portfolio showcase, direct native Excel contact backend, and a
restored brute-force-hardened Admin Authentication & Message Dashboard.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import mimetypes
import os
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from server import (
    BASE_DIR,
    EMAIL_MAX_LENGTH,
    EXCEL_PATH,
    IST_TIMEZONE,
    LOCK_PATH,
    MESSAGE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SlidingWindowRateLimiter,
    ensure_excel_workbook,
    process_contact_submission,
)

ASSET_ATTR_RE = re.compile(r'(src|href)="(assets/[^"]+)"')
ASSET_JS_RE = re.compile(r"'(assets/[^']+)'")
CONTACT_FORM_BLOCK_RE = re.compile(
    r"<!-- CONTACT_FORM_START -->.*?<!-- CONTACT_FORM_END -->", re.DOTALL
)

DEFAULT_ADMIN_EMAIL = "somchandratangwal7@gmail.com"
ADMIN_MAX_FAILED_ATTEMPTS = 5
ADMIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes

STREAMLIT_CONTACT_BRIDGE_HTML = """
<div class="card contact-form" id="streamlit-contact-callout">
  <h3>Send a Message Directly</h3>
  <p class="form-note">
    Running on Streamlit Cloud / App backend: use the interactive
    <strong>Direct Message Form immediately below this showcase</strong> (or open the
    <strong>Contact Form</strong> tab) to submit directly to the hardened Excel inbox.
  </p>
</div>
""".strip()


class AdminLoginRateLimiter:
    """Thread-safe brute-force lock for the Admin Portal (5 failures -> 15 min lock)."""

    def __init__(
        self,
        max_failures: int = ADMIN_MAX_FAILED_ATTEMPTS,
        lockout_seconds: int = ADMIN_LOCKOUT_SECONDS,
    ) -> None:
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def remaining_lockout_seconds(self, key: str = "admin") -> int:
        """Return remaining lockout seconds for `key`, clearing expired locks."""
        now = time.monotonic()
        with self._lock:
            until = self._locked_until.get(key, 0.0)
            if until > now:
                return max(1, int(until - now) + 1)
            if key in self._locked_until:
                self._locked_until.pop(key, None)
                self._failures.pop(key, None)
            return 0

    def record_failure(self, key: str = "admin") -> tuple[bool, int, int]:
        """Record a failed attempt; return `(locked, lock_seconds, attempts_left)`."""
        now = time.monotonic()
        with self._lock:
            until = self._locked_until.get(key, 0.0)
            if until > now:
                return True, max(1, int(until - now) + 1), 0

            count = self._failures.get(key, 0) + 1
            if count >= self.max_failures:
                self._failures[key] = 0
                self._locked_until[key] = now + self.lockout_seconds
                return True, self.lockout_seconds, 0

            self._failures[key] = count
            return False, 0, self.max_failures - count

    def reset(self, key: str = "admin") -> None:
        """Clear failed attempts and lockouts upon successful authentication."""
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)


@st.cache_resource
def get_streamlit_rate_limiter() -> SlidingWindowRateLimiter:
    """Keep a shared 3-messages-per-15-minutes contact rate limiter across reruns."""
    return SlidingWindowRateLimiter()


@st.cache_resource
def get_admin_login_limiter() -> AdminLoginRateLimiter:
    """Keep a shared brute-force lockout limiter across sessions and refreshes."""
    return AdminLoginRateLimiter()


def _get_config_secret(key: str, default: str = "") -> str:
    """Safely look up a configuration value in `st.secrets` then `os.environ`."""
    try:
        if key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val:
                return val
    except Exception:
        pass
    env_val = os.environ.get(key, "").strip()
    return env_val if env_val else default


def resolve_admin_credentials() -> tuple[str, str, str]:
    """Return `(admin_email, password_hash, password_plain)` from secrets/env."""
    admin_email = _get_config_secret("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip().lower()
    password_hash = _get_config_secret("ADMIN_PASSWORD_HASH")
    password_plain = _get_config_secret("ADMIN_PASSWORD") or _get_config_secret(
        "PORTFOLIO_ADMIN_KEY"
    )
    return admin_email, password_hash, password_plain


def hash_admin_password(password: str, iterations: int = 200_000) -> str:
    """Create a salted PBKDF2-HMAC-SHA256 hash suitable for `ADMIN_PASSWORD_HASH`."""
    salt_hex = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt_hex}${dk.hex()}"


def _sha256_digest(text: str) -> bytes:
    """Normalize arbitrary-length text to 32 bytes before constant-time comparison."""
    return hashlib.sha256(text.encode("utf-8")).digest()


def _verify_password_hash(entered_password: str, stored_hash: str) -> bool:
    """Verify `pbkdf2_sha256$<iter>$<salt>$<hex>` or `sha256:<hex>` hashes."""
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) != 4 or not parts[1].isdigit():
            return False
        iterations = int(parts[1])
        try:
            salt = bytes.fromhex(parts[2])
            expected_dk = bytes.fromhex(parts[3])
        except ValueError:
            return False
        computed_dk = hashlib.pbkdf2_hmac(
            "sha256", entered_password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(computed_dk, expected_dk)

    if stored_hash.startswith("sha256:"):
        expected_hex = stored_hash.split(":", 1)[1].strip().lower()
        computed_hex = hashlib.sha256(entered_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(computed_hex, expected_hex)

    return False


def verify_admin_credentials(
    entered_email: str,
    entered_password: str,
    *,
    configured_email: str,
    password_hash: str = "",
    password_plain: str = "",
) -> bool:
    """Authenticate admin email & password using constant-time digest checks."""
    if not configured_email or (not password_hash and not password_plain):
        return False

    normalized_email = entered_email.strip().lower()
    email_ok = hmac.compare_digest(
        _sha256_digest(normalized_email),
        _sha256_digest(configured_email.strip().lower()),
    )

    if password_hash:
        password_ok = _verify_password_hash(entered_password, password_hash)
    else:
        password_ok = hmac.compare_digest(
            _sha256_digest(entered_password),
            _sha256_digest(password_plain),
        )

    return bool(email_ok & password_ok)


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

    # Replace the static server.py fetch('/api/contact') form only inside the Streamlit bundle
    # so visitors submit directly via the native Streamlit form below without CORS/404 errors.
    html_text = CONTACT_FORM_BLOCK_RE.sub(STREAMLIT_CONTACT_BRIDGE_HTML, html_text)
    html_text = html_text.replace(
        '<a href="#home" class="back-top-link">Back to top &uarr;</a>',
        '<a href="?admin=true" target="_top" class="back-top-link">🔒 Admin Portal</a> '
        '<a href="#home" class="back-top-link">Back to top &uarr;</a>',
    )

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


def compute_message_stats(
    df: pd.DataFrame, *, now_utc: datetime | None = None
) -> dict[str, int]:
    """Calculate Total Inquiries, Today's Messages (IST), and Unique Senders."""
    if df.empty:
        return {"total": 0, "today": 0, "unique_senders": 0}

    ref_utc = now_utc or datetime.now(timezone.utc)
    today_ist = ref_utc.astimezone(IST_TIMEZONE).date()

    today_count = 0
    if "Timestamp (UTC/IST)" in df.columns:
        today_iso = today_ist.isoformat()
        for raw_ts in df["Timestamp (UTC/IST)"].dropna().astype(str):
            prefix = raw_ts.strip()[:19]
            try:
                parsed_utc = datetime.strptime(prefix, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if parsed_utc.astimezone(IST_TIMEZONE).date() == today_ist:
                    today_count += 1
            except ValueError:
                if raw_ts.startswith(today_iso):
                    today_count += 1

    unique_senders = 0
    if "Email Address" in df.columns:
        cleaned_emails = (
            df["Email Address"].dropna().astype(str).str.strip().str.lower()
        )
        unique_senders = int(cleaned_emails[cleaned_emails != ""].nunique())

    return {
        "total": int(len(df)),
        "today": today_count,
        "unique_senders": unique_senders,
    }


def _logout_admin() -> None:
    """Clear admin authentication state and return to the public portfolio view."""
    st.session_state.clear()
    try:
        if "admin" in st.query_params:
            del st.query_params["admin"]
    except Exception:
        pass
    st.rerun()


def _render_admin_login_form(
    limiter: AdminLoginRateLimiter, *, key_prefix: str
) -> None:
    """Render the brute-force-protected Admin login form."""
    configured_email, password_hash, password_plain = resolve_admin_credentials()
    if not password_hash and not password_plain:
        st.warning(
            "Admin Portal is configured in fail-closed mode because no password secret is set yet."
        )
        st.caption(
            "In Streamlit Community Cloud (**App Settings -> Secrets**), add:\n"
            '```toml\nADMIN_EMAIL = "somchandratangwal7@gmail.com"\n'
            'ADMIN_PASSWORD = "your-private-password"\n```'
        )
        return

    lock_seconds = limiter.remaining_lockout_seconds()
    if lock_seconds > 0:
        mins, secs = divmod(lock_seconds, 60)
        st.error(
            f"Too many failed login attempts. Admin Portal locked for {mins}m {secs}s."
        )
        return

    with st.form(f"{key_prefix}_admin_login_form", clear_on_submit=False):
        entered_email = st.text_input(
            "Admin Email",
            key=f"{key_prefix}_admin_email",
            value="",
            placeholder="somchandratangwal7@gmail.com",
        )
        entered_password = st.text_input(
            "Admin Password",
            key=f"{key_prefix}_admin_password",
            type="password",
            placeholder="Enter admin password",
        )
        submitted = st.form_submit_button("Login as Admin", type="primary")

    if not submitted:
        return

    lock_seconds = limiter.remaining_lockout_seconds()
    if lock_seconds > 0:
        mins, secs = divmod(lock_seconds, 60)
        st.error(
            f"Too many failed login attempts. Admin Portal locked for {mins}m {secs}s."
        )
        return

    if verify_admin_credentials(
        entered_email,
        entered_password,
        configured_email=configured_email,
        password_hash=password_hash,
        password_plain=password_plain,
    ):
        limiter.reset()
        st.session_state["is_admin"] = True
        st.session_state["admin_email_verified"] = configured_email
        st.rerun()
        return

    locked, wait_sec, attempts_left = limiter.record_failure()
    if locked:
        mins, secs = divmod(wait_sec, 60)
        st.error(
            f"Maximum failed attempts reached. Admin Portal locked for {mins}m {secs}s."
        )
    else:
        st.error(
            f"Invalid email or password ({attempts_left} attempt(s) remaining before 15-minute lock)."
        )


def _render_admin_dashboard() -> None:
    """Render authenticated Admin Management Dashboard for contact Excel logs."""
    header_col, logout_col = st.columns([5, 1])
    with header_col:
        st.title("Admin Management Dashboard")
        verified_email = st.session_state.get(
            "admin_email_verified", DEFAULT_ADMIN_EMAIL
        )
        st.caption(
            f"Signed in as `{verified_email}` • Hardened Excel inbox: `data/contact_messages.xlsx`"
        )
    with logout_col:
        if st.button("Log Out", key="dashboard_logout_btn", type="secondary"):
            _logout_admin()

    ensure_excel_workbook(EXCEL_PATH)
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    stats = compute_message_stats(df)

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Total Inquiries", stats["total"])
    metric_2.metric("Today's Messages", stats["today"])
    metric_3.metric("Unique Senders", stats["unique_senders"])

    action_col1, action_col2 = st.columns([3, 1])
    with action_col1:
        excel_bytes = EXCEL_PATH.read_bytes()
        st.download_button(
            label="📥 Download Messages Spreadsheet (.xlsx)",
            data=excel_bytes,
            file_name="contact_messages.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    with action_col2:
        if st.button("Refresh Messages", key="refresh_inbox_btn"):
            st.rerun()

    st.subheader("Live Contact Messages")
    if df.empty:
        st.info("No contact inquiries have been recorded yet.")
    else:
        preferred_cols = [
            col
            for col in (
                "Timestamp (UTC/IST)",
                "Sender Name",
                "Email Address",
                "Message",
                "Status",
                "IP_Hash",
            )
            if col in df.columns
        ]
        display_df = df[preferred_cols] if preferred_cols else df
        st.dataframe(display_df, width="stretch", hide_index=True)


def _render_contact_section(
    limiter: SlidingWindowRateLimiter, *, key_prefix: str
) -> None:
    """Render native Streamlit contact form saving directly to `data/contact_messages.xlsx`."""
    st.subheader("Send a Direct Message")
    st.caption(
        "Validated in Python with length limits, XSS escaping, CSV/Excel formula neutralization, "
        "CSRF session binding, and a 3 messages / 15 min rate limit — saved directly to Excel."
    )

    if "contact_csrf_nonce" not in st.session_state:
        st.session_state["contact_csrf_nonce"] = secrets.token_urlsafe(24)

    success_key = f"{key_prefix}_contact_success"
    if success_key in st.session_state:
        st.success(st.session_state.pop(success_key))

    ver_key = f"{key_prefix}_form_ver"
    form_ver = int(st.session_state.get(ver_key, 0))
    expected_nonce = st.session_state["contact_csrf_nonce"]

    with st.form(f"{key_prefix}_hardened_contact_form_{form_ver}", clear_on_submit=False):
        sender_name = st.text_input(
            "Full Name",
            key=f"{key_prefix}_name_{form_ver}",
            max_chars=NAME_MAX_LENGTH,
            placeholder="Your full name (max 80 chars)",
        )
        sender_email = st.text_input(
            "Email Address",
            key=f"{key_prefix}_email_{form_ver}",
            max_chars=EMAIL_MAX_LENGTH,
            placeholder="you@example.com (max 120 chars)",
        )
        sender_message = st.text_area(
            "Message",
            key=f"{key_prefix}_message_{form_ver}",
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
        st.session_state[success_key] = (
            "Message sent successfully! Som will get back to you shortly."
        )
        st.session_state[ver_key] = form_ver + 1
        st.rerun()
    else:
        st.error(response.get("error", "Unable to record your message."))


def _is_admin_query_requested() -> bool:
    """Check whether URL query parameter `?admin=true` was supplied."""
    try:
        raw = str(st.query_params.get("admin", "")).strip().lower()
        return raw in ("true", "1", "yes")
    except Exception:
        return False


def main() -> None:
    """Configure page metadata and render public portfolio + Admin Portal."""
    st.set_page_config(
        page_title="Somchand Ratangwal | Cybersecurity & AI Portfolio",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    ensure_excel_workbook(EXCEL_PATH)
    contact_limiter = get_streamlit_rate_limiter()
    login_limiter = get_admin_login_limiter()

    is_admin = bool(st.session_state.get("is_admin", False))
    admin_query = _is_admin_query_requested()

    with st.sidebar:
        with st.expander("🔒 Admin Portal", expanded=True):
            if is_admin:
                st.success(
                    f"Authenticated: {st.session_state.get('admin_email_verified', DEFAULT_ADMIN_EMAIL)}"
                )
                if st.button("Log Out", key="sidebar_logout_btn"):
                    _logout_admin()
            else:
                _render_admin_login_form(login_limiter, key_prefix="sidebar")

    if is_admin:
        _render_admin_dashboard()
        return

    if admin_query:
        st.subheader("🔒 Admin Portal Login")
        st.caption("Authorized portfolio administrator access only.")
        _render_admin_login_form(login_limiter, key_prefix="main")
        if st.button("← Return to Public Portfolio", key="back_to_portfolio_btn"):
            try:
                if "admin" in st.query_params:
                    del st.query_params["admin"]
            except Exception:
                pass
            st.rerun()
        return

    tab_portfolio, tab_contact, tab_admin = st.tabs(
        ["🌐 Portfolio Website", "✉️ Contact Form", "🔒 Admin Portal"]
    )

    with tab_portfolio:
        embedded_html = build_standalone_portfolio_html(str(BASE_DIR))
        if hasattr(st, "iframe"):
            st.iframe(embedded_html, height=1100)
        else:
            import streamlit.components.v1 as components

            components.html(embedded_html, height=1100, scrolling=True)

        st.divider()
        _render_contact_section(contact_limiter, key_prefix="portfolio")

    with tab_contact:
        _render_contact_section(contact_limiter, key_prefix="tab")

    with tab_admin:
        st.subheader("🔒 Admin Portal Login")
        st.caption("Sign in with administrator credentials to view & download contact submissions.")
        _render_admin_login_form(login_limiter, key_prefix="tab_admin")


if __name__ == "__main__":
    main()

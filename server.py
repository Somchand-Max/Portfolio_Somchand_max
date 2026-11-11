#!/usr/bin/env python3
"""Hardened local HTTP backend for Somchand Ratangwal's portfolio website.

Implements OWASP-aligned input validation, XSS escaping, spreadsheet formula
injection defense, HMAC CSRF tokens, origin/CORS enforcement, sliding-window IP
rate limiting, path traversal blocking, strict security headers, and atomic
`.xlsx` persistence in `data/contact_messages.xlsx` (chmod 600).
"""

from __future__ import annotations

import errno
import hashlib
import hmac
import html
import ipaddress
import json
import os
import posixpath
import re
import secrets
import socket
import tempfile
import threading
import time
import urllib.parse
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None  # type: ignore[assignment]


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "contact_messages.xlsx"
LOCK_PATH = DATA_DIR / ".contact_messages.lock"
SHEET_NAME = "Messages"

EXCEL_HEADERS = [
    "Timestamp (UTC/IST)",
    "Sender Name",
    "Email Address",
    "Message",
    "IP_Hash",
    "Status",
]

IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

MAX_BODY_BYTES = 10 * 1024  # 10 KB strict limit on POST bodies
NAME_MAX_LENGTH = 80
EMAIL_MAX_LENGTH = 120
MESSAGE_MIN_LENGTH = 10
MESSAGE_MAX_LENGTH = 500
ALLOWED_JSON_KEYS = frozenset({"name", "email", "message", "website_url"})

RATE_LIMIT_MAX_REQUESTS = 3
RATE_LIMIT_WINDOW_SECONDS = 15 * 60  # 15 minutes
CSRF_TOKEN_TTL_SECONDS = 2 * 60 * 60  # 2 hours

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)
CONTROL_CHARS_INLINE_RE = re.compile(r"[\x00-\x1f\x7f]")
CONTROL_CHARS_MESSAGE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

DEFAULT_ALLOWED_ORIGINS = frozenset(
    {
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://[::1]:8080",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    }
)

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

BLOCKED_TOP_LEVEL_NAMES = frozenset(
    {
        "data",
        "venv",
        ".venv",
        "__pycache__",
        ".git",
        ".github",
        "server.py",
        "app.py",
        "requirements.txt",
        "readme.md",
    }
)
ALLOWED_STATIC_EXTENSIONS = frozenset(
    {
        ".html",
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".pdf",
    }
)

_EXCEL_THREAD_LOCK = threading.Lock()
_DEFAULT_RUNTIME_SECRET = secrets.token_bytes(32)


def get_allowed_origins() -> frozenset[str]:
    """Build the strict CORS/Origin allowlist from env + safe local defaults."""
    env_raw = os.environ.get("ALLOWED_ORIGINS", "")
    origins = set(DEFAULT_ALLOWED_ORIGINS)
    for item in env_raw.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned and cleaned != "*":
            origins.add(cleaned)
    return frozenset(origins)


def _get_signing_secret() -> bytes:
    """Return process HMAC secret for CSRF tokens and anonymized IP hashing."""
    env_secret = os.environ.get("PORTFOLIO_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret.encode("utf-8")
    return _DEFAULT_RUNTIME_SECRET


def normalize_ip(raw_ip: str) -> str:
    """Normalize IPv4-mapped IPv6 addresses to a canonical IP string."""
    candidate = (raw_ip or "").strip() or "unknown"
    try:
        parsed = ipaddress.ip_address(candidate)
        if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped:
            return str(parsed.ipv4_mapped)
        return str(parsed)
    except ValueError:
        return "unknown"


def hash_ip_address(raw_ip: str, secret: bytes | None = None) -> str:
    """Compute a truncated keyed SHA-256 hash so raw client IPs are not stored."""
    key = secret if secret is not None else _get_signing_secret()
    canonical = normalize_ip(raw_ip)
    digest = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:16]


def generate_csrf_token(secret: bytes | None = None) -> str:
    """Issue an HMAC-SHA256 stateless CSRF token bound to a timestamp & nonce."""
    key = secret if secret is not None else _get_signing_secret()
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{timestamp}.{nonce}"
    sig = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_csrf_token(token: str, secret: bytes | None = None) -> bool:
    """Verify HMAC signature and expiry of an incoming X-CSRF-Token header."""
    if not token or not isinstance(token, str) or len(token) > 256:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    ts_str, nonce, provided_sig = parts
    if not ts_str.isdigit() or not nonce:
        return False
    try:
        issued_at = int(ts_str)
    except ValueError:
        return False
    now = int(time.time())
    if issued_at > now + 60 or (now - issued_at) > CSRF_TOKEN_TTL_SECONDS:
        return False

    key = secret if secret is not None else _get_signing_secret()
    payload = f"{ts_str}.{nonce}"
    expected_sig = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided_sig, expected_sig)


class SlidingWindowRateLimiter:
    """Thread-safe per-IP sliding-window limiter (default: 3 requests / 15 min)."""

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_ip: str) -> tuple[bool, int]:
        """Record an attempt and return `(allowed, retry_after_seconds)`."""
        key = normalize_ip(client_ip)
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(bucket[0] + self.window_seconds - now) + 1)
                return False, retry_after

            bucket.append(now)
            return True, 0


def sanitize_single_line_text(value: str) -> str:
    """Strip inline control characters and collapse runs of spaces/newlines."""
    cleaned = CONTROL_CHARS_INLINE_RE.sub(" ", value)
    return " ".join(cleaned.strip().split())


def sanitize_message_text(value: str) -> str:
    """Normalize line endings while stripping unsafe control characters."""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = CONTROL_CHARS_MESSAGE_RE.sub("", normalized)
    return cleaned.strip()


def escape_html_text(value: str) -> str:
    """Apply strict HTML escaping to neutralize reflected or stored XSS payloads."""
    return html.escape(value, quote=True)


def escape_spreadsheet_formula(value: str) -> str:
    """Neutralize CSV/Excel formula injection payloads with a leading apostrophe."""
    if not value:
        return ""
    stripped_leading = value.lstrip(" ")
    if value[0] in FORMULA_PREFIXES or (
        stripped_leading and stripped_leading[0] in FORMULA_PREFIXES
    ):
        return "'" + value
    return value


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    name: str = ""
    email: str = ""
    message: str = ""
    honeypot_triggered: bool = False
    error: str = ""


def validate_contact_payload(payload: Any) -> ValidationResult:
    """Strictly enforce JSON schema, allowed keys, lengths, and RFC email syntax."""
    if not isinstance(payload, dict):
        return ValidationResult(valid=False, error="Invalid JSON request object.")

    unexpected_keys = set(payload.keys()) - ALLOWED_JSON_KEYS
    if unexpected_keys:
        return ValidationResult(
            valid=False, error="Unexpected fields rejected by schema validation."
        )

    for key, val in payload.items():
        if not isinstance(val, str):
            return ValidationResult(
                valid=False, error=f"Field '{key}' must be a text string."
            )

    if payload.get("website_url", "").strip():
        return ValidationResult(valid=True, honeypot_triggered=True)

    raw_name = sanitize_single_line_text(payload.get("name", ""))
    raw_email = sanitize_single_line_text(payload.get("email", "")).lower()
    raw_message = sanitize_message_text(payload.get("message", ""))

    if not raw_name:
        return ValidationResult(valid=False, error="Please enter your full name.")
    if len(raw_name) > NAME_MAX_LENGTH:
        return ValidationResult(
            valid=False,
            error=f"Full name must not exceed {NAME_MAX_LENGTH} characters.",
        )

    if not raw_email or len(raw_email) > EMAIL_MAX_LENGTH or not EMAIL_REGEX.match(raw_email):
        return ValidationResult(
            valid=False,
            error=f"Please enter a valid email address (max {EMAIL_MAX_LENGTH} characters).",
        )

    if len(raw_message) < MESSAGE_MIN_LENGTH:
        return ValidationResult(
            valid=False,
            error=f"Message must be at least {MESSAGE_MIN_LENGTH} characters long.",
        )
    if len(raw_message) > MESSAGE_MAX_LENGTH:
        return ValidationResult(
            valid=False,
            error=f"Message must not exceed {MESSAGE_MAX_LENGTH} characters.",
        )

    return ValidationResult(
        valid=True,
        name=escape_spreadsheet_formula(escape_html_text(raw_name)),
        email=escape_spreadsheet_formula(escape_html_text(raw_email)),
        message=escape_spreadsheet_formula(escape_html_text(raw_message)),
    )


def _apply_strict_permissions(data_dir: Path, excel_path: Path, lock_path: Path | None = None) -> None:
    """Enforce owner-only permissions (`700` on dir, `600` on workbook & lock)."""
    os.chmod(data_dir, 0o700)
    if excel_path.exists():
        os.chmod(excel_path, 0o600)
    if lock_path and lock_path.exists():
        os.chmod(lock_path, 0o600)


def _create_styled_workbook(target_path: Path) -> Workbook:
    """Create a styled `.xlsx` workbook with the 6 locked security headers."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws.append(EXCEL_HEADERS)

    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="F8FAFC")
    header_alignment = Alignment(horizontal="left", vertical="center")

    for col_idx in range(1, len(EXCEL_HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 24
    column_widths = {"A": 32, "B": 26, "C": 32, "D": 64, "E": 20, "F": 14}
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    return wb


def _atomic_save_workbook(wb: Workbook, excel_path: Path) -> None:
    """Write workbook to an owner-only temp file and atomically replace target."""
    fd, tmp_name = tempfile.mkstemp(
        prefix=".tmp_contact_",
        suffix=".xlsx",
        dir=str(excel_path.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        os.chmod(tmp_path, 0o600)
        wb.save(tmp_path)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, excel_path)
        os.chmod(excel_path, 0o600)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def ensure_excel_workbook(excel_path: Path = EXCEL_PATH) -> None:
    """Ensure `data/` (700) and `contact_messages.xlsx` (600) exist with valid headers."""
    data_dir = excel_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(data_dir, 0o700)

    if excel_path.exists():
        _apply_strict_permissions(data_dir, excel_path)
        return

    wb = _create_styled_workbook(excel_path)
    _atomic_save_workbook(wb, excel_path)
    wb.close()


def format_dual_timestamp(dt_utc: datetime | None = None) -> str:
    """Format a dual UTC / IST timestamp string."""
    now_utc = dt_utc or datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST_TIMEZONE)
    return f"{now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC / {now_ist.strftime('%H:%M:%S')} IST"


def append_contact_message(
    *,
    name: str,
    email: str,
    message: str,
    ip_hash: str,
    status: str = "New",
    excel_path: Path = EXCEL_PATH,
    lock_path: Path | None = None,
) -> None:
    """Append one sanitized, formula-safe row to `contact_messages.xlsx` under locks."""
    resolved_lock = lock_path or (excel_path.parent / ".contact_messages.lock")
    ensure_excel_workbook(excel_path)

    with _EXCEL_THREAD_LOCK:
        lock_fd = os.open(resolved_lock, os.O_CREAT | os.O_RDWR, 0o600)
        os.chmod(resolved_lock, 0o600)
        try:
            if fcntl is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_EX)

            if excel_path.exists():
                wb = load_workbook(excel_path)
                ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active
            else:
                wb = _create_styled_workbook(excel_path)
                ws = wb.active

            row_idx = ws.max_row + 1
            ws.append(
                [
                    format_dual_timestamp(),
                    name,
                    email,
                    message,
                    ip_hash,
                    status,
                ]
            )
            for col_idx in range(1, len(EXCEL_HEADERS) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.alignment = Alignment(
                    horizontal="left",
                    vertical="top",
                    wrap_text=(col_idx == 4),
                )

            _atomic_save_workbook(wb, excel_path)
            wb.close()
        finally:
            if fcntl is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
            _apply_strict_permissions(excel_path.parent, excel_path, resolved_lock)


def process_contact_submission(
    payload: Any,
    client_ip: str = "unknown",
    *,
    excel_path: Path = EXCEL_PATH,
    lock_path: Path | None = None,
    secret: bytes | None = None,
) -> tuple[int, dict[str, Any]]:
    """Validate, neutralize XSS/formula injection, check honeypot, and persist."""
    result = validate_contact_payload(payload)
    if not result.valid:
        return HTTPStatus.BAD_REQUEST, {"success": False, "error": result.error}

    if result.honeypot_triggered:
        return HTTPStatus.OK, {
            "success": True,
            "message": "Thank you, your message has been recorded!",
        }

    ip_hash = hash_ip_address(client_ip, secret=secret)
    append_contact_message(
        name=result.name,
        email=result.email,
        message=result.message,
        ip_hash=ip_hash,
        status="New",
        excel_path=excel_path,
        lock_path=lock_path,
    )
    return HTTPStatus.OK, {
        "success": True,
        "message": "Thank you, your message has been recorded!",
    }


def resolve_safe_static_path(request_target: str, public_root: Path) -> Path | None:
    """Resolve URL path inside `public_root`, blocking traversal, dotfiles, and private paths."""
    parsed = urllib.parse.urlsplit(request_target)
    raw_path = parsed.path or "/"

    # Inspect both raw and multi-pass unquoted representations for traversal tokens.
    check_variants = {raw_path.lower()}
    decoded = raw_path
    for _ in range(3):
        decoded = urllib.parse.unquote(decoded)
        check_variants.add(decoded.lower())

    for variant in check_variants:
        if "\x00" in variant or "\\" in variant or ".." in variant or "%2e" in variant:
            return None

    normalized = posixpath.normpath(decoded)
    if normalized in ("/", "."):
        normalized = "/index.html"

    rel_str = normalized.lstrip("/")
    if not rel_str:
        rel_str = "index.html"

    segments = [seg for seg in rel_str.split("/") if seg]
    if not segments:
        return None

    if segments[0].lower() in BLOCKED_TOP_LEVEL_NAMES:
        return None

    for seg in segments:
        if seg.startswith(".") or seg in ("..", "."):
            return None

    root_resolved = public_root.resolve()
    candidate = (root_resolved / Path(*segments)).resolve()
    if not candidate.is_relative_to(root_resolved):
        return None
    if candidate.is_dir():
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    if candidate.suffix.lower() not in ALLOWED_STATIC_EXTENSIONS:
        return None
    return candidate


@dataclass
class ServerRuntimeConfig:
    base_dir: Path = BASE_DIR
    excel_path: Path = EXCEL_PATH
    lock_path: Path = LOCK_PATH
    allowed_origins: frozenset[str] = DEFAULT_ALLOWED_ORIGINS
    rate_limiter: SlidingWindowRateLimiter | None = None
    secret_key: bytes | None = None


class PortfolioRequestHandler(SimpleHTTPRequestHandler):
    """Security-hardened static file and JSON contact API handler."""

    server_version = "PortfolioServer"
    sys_version = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        server_obj = kwargs.get("server") or (args[2] if len(args) > 2 else None)
        config: ServerRuntimeConfig = getattr(
            server_obj,
            "runtime_config",
            ServerRuntimeConfig(allowed_origins=get_allowed_origins()),
        )
        self.runtime_config = config
        kwargs.setdefault("directory", str(config.base_dir))
        super().__init__(*args, **kwargs)

    def version_string(self) -> str:
        """Suppress Python/OS/BaseHTTP version fingerprinting in Server headers."""
        return "PortfolioServer"

    def log_message(self, format: str, *args: Any) -> None:
        """Emit concise non-sensitive access logs without request bodies or secrets."""
        client = normalize_ip(self.client_address[0] if self.client_address else "")
        try:
            line = format % args
        except Exception:
            line = str(format)
        print(f"[portfolio] {client} {line}", flush=True)

    def log_error(self, format: str, *args: Any) -> None:
        """Avoid leaking stack traces or filesystem details in server error logs."""
        self.log_message(format, *args)

    def _matched_allowed_origin(self) -> str | None:
        """Return matching Origin (or origin parsed from Referer) if strictly allowlisted."""
        origin = self.headers.get("Origin", "").strip().rstrip("/")
        if origin:
            if origin in self.runtime_config.allowed_origins:
                return origin
            return None

        referer = self.headers.get("Referer", "").strip()
        if referer:
            parsed = urllib.parse.urlsplit(referer)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                ref_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
                if ref_origin in self.runtime_config.allowed_origins:
                    return ref_origin
        return None

    def _emit_security_headers(self, *, is_api: bool = False) -> None:
        """Apply OWASP security response headers on every response."""
        self.send_header("Content-Security-Policy", CSP_POLICY)
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        self.send_header(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )

        origin_header = self.headers.get("Origin", "").strip().rstrip("/")
        if origin_header and origin_header in self.runtime_config.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin_header)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, X-CSRF-Token, X-Requested-With",
            )

        if is_api:
            self.send_header("Cache-Control", "no-store")

    def _send_json(
        self,
        status: int,
        payload: dict[str, Any],
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(int(status))
        self._emit_security_headers(is_api=True)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for hdr, val in extra_headers.items():
                self.send_header(hdr, val)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_plain_error(self, status: int, message: str) -> None:
        body = message.encode("utf-8")
        self.send_response(int(status))
        self._emit_security_headers(is_api=False)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        """Override default BaseHTTP error HTML so Server/Python details never leak."""
        try:
            short = HTTPStatus(code).phrase
        except ValueError:
            short = "Error"
        self._send_plain_error(code, short)

    def list_directory(self, path: str | os.PathLike[str]) -> None:  # type: ignore[override]
        """Disable all HTTP directory listings."""
        self._send_plain_error(HTTPStatus.FORBIDDEN, "Forbidden")
        return None

    def do_OPTIONS(self) -> None:
        """Enforce strict CORS preflight checks (never wildcard `*`)."""
        origin = self.headers.get("Origin", "").strip().rstrip("/")
        if origin and origin in self.runtime_config.allowed_origins:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._emit_security_headers(is_api=True)
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_json(
            HTTPStatus.FORBIDDEN,
            {"success": False, "error": "Origin not permitted."},
        )

    def do_GET(self) -> None:
        """Serve `/api/csrf-token` or safe static files locked inside public root."""
        try:
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path == "/api/csrf-token":
                origin_hdr = self.headers.get("Origin", "").strip().rstrip("/")
                if origin_hdr and origin_hdr not in self.runtime_config.allowed_origins:
                    self._send_json(
                        HTTPStatus.FORBIDDEN,
                        {"success": False, "error": "Origin not permitted."},
                    )
                    return
                secret = self.runtime_config.secret_key or _get_signing_secret()
                token = generate_csrf_token(secret=secret)
                self._send_json(HTTPStatus.OK, {"csrf_token": token})
                return

            if parsed.path.startswith("/api/"):
                self._send_json(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    {"success": False, "error": "Method not allowed."},
                )
                return

            self._serve_validated_static()
        except Exception:
            self._send_plain_error(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error"
            )

    def do_HEAD(self) -> None:
        """Support HEAD requests securely for static assets without exposing bodies."""
        self.do_GET()

    def _serve_validated_static(self) -> None:
        raw_path = urllib.parse.urlsplit(self.path).path or "/"

        # Differentiate blocked sensitive/traversal targets (403) vs benign missing assets (404).
        decoded_lower = urllib.parse.unquote(raw_path).lower()
        first_seg = next((s for s in decoded_lower.split("/") if s), "")
        if (
            ".." in raw_path.lower()
            or "%2e" in raw_path.lower()
            or ".." in decoded_lower
            or "\\" in decoded_lower
            or "\x00" in decoded_lower
            or any(seg.startswith(".") for seg in decoded_lower.split("/") if seg)
            or first_seg in BLOCKED_TOP_LEVEL_NAMES
        ):
            self._send_plain_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return

        safe_path = resolve_safe_static_path(self.path, self.runtime_config.base_dir)
        if safe_path is None:
            self._send_plain_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        ctype = self.guess_type(str(safe_path))
        data = safe_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._emit_security_headers(is_api=False)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if safe_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            self.send_header("Cache-Control", "public, max-age=3600")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_POST(self) -> None:
        """Handle hardened contact submissions on `/api/contact`."""
        try:
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != "/api/contact":
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"success": False, "error": "Endpoint not found."},
                )
                return

            if not self._matched_allowed_origin():
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"success": False, "error": "Cross-origin submission rejected."},
                )
                return

            if self.headers.get("X-Requested-With", "").strip() != "XMLHttpRequest":
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"success": False, "error": "Missing required security header."},
                )
                return

            secret = self.runtime_config.secret_key or _get_signing_secret()
            csrf_token = self.headers.get("X-CSRF-Token", "").strip()
            if not verify_csrf_token(csrf_token, secret=secret):
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {
                        "success": False,
                        "error": "Invalid or expired security token. Please refresh the page.",
                    },
                )
                return

            content_type = self.headers.get("Content-Type", "").lower()
            if not content_type.startswith("application/json"):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"success": False, "error": "Expected application/json payload."},
                )
                return

            raw_length = self.headers.get("Content-Length", "")
            try:
                content_length = int(raw_length)
            except ValueError:
                self._send_json(
                    HTTPStatus.LENGTH_REQUIRED,
                    {"success": False, "error": "Content-Length header is required."},
                )
                return

            if content_length <= 0:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"success": False, "error": "Empty request body."},
                )
                return

            if content_length > MAX_BODY_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {
                        "success": False,
                        "error": "Payload exceeds maximum allowed 10 KB limit.",
                    },
                )
                return

            raw_body = self.rfile.read(min(content_length, MAX_BODY_BYTES + 1))
            if len(raw_body) > MAX_BODY_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {
                        "success": False,
                        "error": "Payload exceeds maximum allowed 10 KB limit.",
                    },
                )
                return

            client_ip = self.client_address[0] if self.client_address else "unknown"
            limiter = self.runtime_config.rate_limiter
            if limiter is not None:
                allowed, retry_after = limiter.allow(client_ip)
                if not allowed:
                    self._send_json(
                        HTTPStatus.TOO_MANY_REQUESTS,
                        {
                            "success": False,
                            "error": "Too many messages sent from this IP. Please wait 15 minutes before trying again.",
                        },
                        extra_headers={"Retry-After": str(retry_after)},
                    )
                    return

            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"success": False, "error": "Malformed JSON payload."},
                )
                return

            status, response_body = process_contact_submission(
                payload,
                client_ip=client_ip,
                excel_path=self.runtime_config.excel_path,
                lock_path=self.runtime_config.lock_path,
                secret=secret,
            )
            self._send_json(status, response_body)
        except Exception:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "success": False,
                    "error": "Unable to process request right now.",
                },
            )


class DualStackServer(ThreadingHTTPServer):
    """Threaded HTTP server binding IPv6 dual-stack (IPv4 + IPv6) with IPv4 fallback."""

    address_family = socket.AF_INET6
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[PortfolioRequestHandler],
        *,
        runtime_config: ServerRuntimeConfig,
    ) -> None:
        self.runtime_config = runtime_config
        super().__init__(server_address, handler_class)

    def server_bind(self) -> None:
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except OSError:
            pass
        super().server_bind()


class IPv4Server(ThreadingHTTPServer):
    """Fallback IPv4 threaded HTTP server when dual-stack IPv6 is unavailable."""

    address_family = socket.AF_INET
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[PortfolioRequestHandler],
        *,
        runtime_config: ServerRuntimeConfig,
    ) -> None:
        self.runtime_config = runtime_config
        super().__init__(server_address, handler_class)


def create_server(
    port: int = 8080,
    *,
    base_dir: Path = BASE_DIR,
    excel_path: Path | None = None,
    lock_path: Path | None = None,
    allowed_origins: frozenset[str] | None = None,
    rate_limiter: SlidingWindowRateLimiter | None = None,
    secret_key: bytes | None = None,
) -> ThreadingHTTPServer:
    """Create and configure a hardened portfolio HTTP server instance."""
    resolved_base = base_dir.resolve()
    resolved_excel = (excel_path or (resolved_base / "data" / "contact_messages.xlsx")).resolve()
    resolved_lock = (lock_path or (resolved_excel.parent / ".contact_messages.lock")).resolve()
    ensure_excel_workbook(resolved_excel)

    origins = allowed_origins if allowed_origins is not None else get_allowed_origins()
    if port not in (8080, 0):
        origins = frozenset(
            set(origins)
            | {
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}",
                f"http://[::1]:{port}",
            }
        )

    config = ServerRuntimeConfig(
        base_dir=resolved_base,
        excel_path=resolved_excel,
        lock_path=resolved_lock,
        allowed_origins=origins,
        rate_limiter=rate_limiter or SlidingWindowRateLimiter(),
        secret_key=secret_key or _get_signing_secret(),
    )

    try:
        return DualStackServer(("::", port), PortfolioRequestHandler, runtime_config=config)
    except OSError as exc:
        if exc.errno in (errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT, errno.EADDRNOTAVAIL):
            return IPv4Server(("127.0.0.1", port), PortfolioRequestHandler, runtime_config=config)
        raise


def run_server(port: int = 8080) -> None:
    """Initialize hardened Excel storage and run the local portfolio backend."""
    server = create_server(port=port)
    actual_port = server.server_address[1]
    print(f"Serving hardened portfolio on http://localhost:{actual_port}", flush=True)
    print(f"Excel contact log: {server.runtime_config.excel_path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down hardened portfolio server...", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    listen_port = int(os.environ.get("PORT", "8080"))
    run_server(port=listen_port)

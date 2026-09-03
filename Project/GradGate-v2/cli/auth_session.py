from __future__ import annotations

import json
import mimetypes
import os
import threading
import uuid
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

try:
    from supabase import ClientOptions, create_client
except ImportError:
    ClientOptions = None
    create_client = None

CLI_ENV_PATH = Path(__file__).resolve().parent / ".env"
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(CLI_ENV_PATH)
load_dotenv(ROOT_ENV_PATH)

APP_DIR = Path(__file__).resolve().parent / ".gradgate"
SESSION_STORE = APP_DIR / "supabase_auth.json"
DEFAULT_REDIRECT_URL = "http://127.0.0.1:8765/auth/callback"
DEFAULT_API_URL = "http://127.0.0.1:8000"


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def get_api_url() -> str:
    return _env("GRADGATE_API_URL", "EXPO_PUBLIC_API_URL", "VITE_API_URL", default=DEFAULT_API_URL)


def _is_test_mode() -> bool:
    return _env("TEST_MODE", default="false").lower() == "true"


class FileStorage:
    """Minimal storage adapter for Supabase PKCE/session persistence."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, payload: dict[str, str]) -> None:
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def get_item(self, key: str) -> str | None:
        return self._read().get(key)

    def set_item(self, key: str, value: str) -> None:
        payload = self._read()
        payload[key] = value
        self._write(payload)

    def remove_item(self, key: str) -> None:
        payload = self._read()
        if key in payload:
            del payload[key]
            self._write(payload)


def create_auth_client():
    if create_client is None or ClientOptions is None:
        raise RuntimeError(
            "Supabase auth dependencies are not installed. Install the API dependencies for CLI cloud features."
        )

    url = _env("SUPABASE_URL", "EXPO_PUBLIC_SUPABASE_URL", "VITE_SUPABASE_URL")
    anon_key = _env(
        "SUPABASE_ANON_KEY",
        "EXPO_PUBLIC_SUPABASE_ANON_KEY",
        "VITE_SUPABASE_ANON_KEY",
    )
    if not url or not anon_key:
        raise RuntimeError(
            "Missing Supabase public auth config. Set SUPABASE_URL and SUPABASE_ANON_KEY "
            "in cli/.env before using CLI Google sign-in."
        )

    options = ClientOptions(
        flow_type="pkce",
        persist_session=True,
        storage=FileStorage(SESSION_STORE),
    )
    return create_client(url, anon_key, options=options)


def get_session():
    client = create_auth_client()
    session = client.auth.get_session()
    return client, session


def get_current_user_email() -> str | None:
    if _is_test_mode():
        return "local-test-user"
    client, session = get_session()
    if not session:
        return None
    user = client.auth.get_user(session.access_token)
    return user.user.email if user and user.user else None


@dataclass
class AuthCallbackResult:
    auth_code: str | None = None
    error: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        self.server.callback_result.auth_code = params.get("code", [None])[0]
        self.server.callback_result.error = params.get("error_description", [None])[0] or params.get(
            "error", [None]
        )[0]
        self.server.event.set()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            (
                "<html><body style='font-family:sans-serif;padding:2rem;'>"
                "<h2>GradGate sign-in complete</h2>"
                "<p>You can return to the terminal now.</p>"
                "</body></html>"
            ).encode("utf-8")
        )

    def log_message(self, _format: str, *_args: Any) -> None:
        return


class _CallbackServer(HTTPServer):
    def __init__(self, server_address, request_handler_class):
        super().__init__(server_address, request_handler_class)
        self.event = threading.Event()
        self.callback_result = AuthCallbackResult()


def _extract_code_from_url(callback_url: str) -> str:
    parsed = urlparse(callback_url.strip())
    params = parse_qs(parsed.query)
    code = params.get("code", [None])[0]
    if not code:
        raise RuntimeError("The callback URL did not include an OAuth code.")
    return code


def sign_in_with_google(console: Console, timeout_seconds: int = 180) -> str:
    client = create_auth_client()
    redirect_url = _env("GRADGATE_CLI_REDIRECT_URL", default=DEFAULT_REDIRECT_URL)
    parsed_redirect = urlparse(redirect_url)

    if parsed_redirect.scheme not in {"http", "https"} or not parsed_redirect.hostname:
        raise RuntimeError("GRADGATE_CLI_REDIRECT_URL must be an http(s) URL.")

    server = _CallbackServer((parsed_redirect.hostname, parsed_redirect.port or 80), _CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        response = client.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": redirect_url},
            }
        )

        console.print(
            Panel(
                "A browser window is opening for Google sign-in.\n"
                "If it does not open, use the URL below.\n\n"
                f"[cyan]{response.url}[/cyan]",
                title="Google Sign-In",
                border_style="cyan",
            )
        )
        webbrowser.open(response.url)

        if not server.event.wait(timeout_seconds):
            console.print("[yellow]The browser did not return automatically in time.[/]")
            callback_url = input("Paste the full callback URL here: ").strip()
            auth_code = _extract_code_from_url(callback_url)
        else:
            if server.callback_result.error:
                raise RuntimeError(server.callback_result.error)
            if not server.callback_result.auth_code:
                raise RuntimeError("No OAuth code was received from the browser callback.")
            auth_code = server.callback_result.auth_code

        auth_response = client.auth.exchange_code_for_session({"auth_code": auth_code})
        if not auth_response.session or not auth_response.user:
            raise RuntimeError("Supabase sign-in completed, but no session was returned.")
        return auth_response.user.email or auth_response.user.id
    finally:
        server.shutdown()
        server.server_close()


def sign_out() -> None:
    client, session = get_session()
    if session:
        client.auth.sign_out()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _access_token_or_raise(required_message: str) -> str:
    if _is_test_mode():
        return "test-token"

    try:
        _, session = get_session()
    except Exception as exc:
        raise RuntimeError(
            "Could not refresh the Supabase cloud session. "
            "Check internet/DNS and Supabase project status, run `python3 cli/gradgate.py --login`, "
            "or set TEST_MODE=true for local API-only OCR testing."
        ) from exc

    if not session:
        raise RuntimeError(required_message)
    return session.access_token


def _request_json(method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
    access_token = _access_token_or_raise("You are not signed in.")

    api_url = get_api_url().rstrip("/")
    url = f"{api_url}{endpoint}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = Request(url, headers=_auth_headers(access_token), data=data, method=method)
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("detail", str(exc))
        except Exception:
            detail = str(exc)
        raise RuntimeError(f"Cloud request failed: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach the GradGate API at {api_url}.") from exc


def _request_multipart(
    endpoint: str,
    file_path: str | Path,
    fields: dict[str, Any],
) -> Any:
    access_token = _access_token_or_raise(
        "PDF and image upload through the API requires Google sign-in first."
    )

    api_url = get_api_url().rstrip("/")
    url = f"{api_url}{endpoint}"
    path = Path(file_path)
    if not path.exists():
        raise RuntimeError(f"File not found: {path}")

    boundary = f"gradgate-{uuid.uuid4().hex}"
    body = bytearray()

    for key, value in fields.items():
        if value is None or value == "":
            continue
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    file_bytes = path.read_bytes()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        (
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    body.extend(file_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    request = Request(url, headers=headers, data=bytes(body), method="POST")
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("detail", str(exc))
        except Exception:
            detail = str(exc)
        raise RuntimeError(f"Cloud request failed: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach the GradGate API at {api_url}.") from exc


def fetch_history(scan_id: str | None = None) -> Any:
    endpoint = "/history"
    if scan_id:
        endpoint = f"{endpoint}/{scan_id}"
    return _request_json("GET", endpoint)


def save_local_audit(program: str, input_type: str, file_name: str | None, result: dict[str, Any]) -> Any:
    return _request_json(
        "POST",
        "/audit/log",
        {
            "program": program,
            "input_type": input_type,
            "file_name": file_name,
            "result": result,
        },
    )


def submit_scanned_audit(
    file_path: str | Path,
    program: str,
    *,
    waivers: str | None = None,
    level: str = "all",
    report: str = "normal",
    concentration: str | None = None,
    minor: str | None = None,
) -> Any:
    fields = {
        "program": program.upper(),
        "level": level,
        "report": report,
        "waivers": waivers or "",
        "concentration": concentration or "",
        "minor": minor or "",
    }
    return _request_multipart("/audit/image", file_path, fields)


def submit_reviewed_audit(
    *,
    program: str,
    input_type: str,
    file_name: str,
    extracted_csv: str,
    waivers: str | None = None,
    level: str = "all",
    report: str = "normal",
    concentration: str | None = None,
    minor: str | None = None,
    extraction_mode: str | None = None,
    warnings: list[str] | None = None,
) -> Any:
    payload = {
        "program": program.upper(),
        "input_type": input_type,
        "file_name": file_name,
        "extracted_csv": extracted_csv,
        "waivers": [item.strip().upper() for item in (waivers or "").split(",") if item.strip()],
        "level": level,
        "report": report,
        "concentration": concentration or None,
        "minor": minor or None,
        "extraction_mode": extraction_mode,
        "warnings": warnings or [],
    }
    return _request_json("POST", "/audit/review", payload)


def print_history_table(console: Console, scans: list[dict[str, Any]]) -> None:
    table = Table(title="Cloud Audit History", border_style="blue")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Scan ID", style="magenta")
    table.add_column("Created")
    table.add_column("Program")
    table.add_column("Input")
    table.add_column("File")

    for index, row in enumerate(scans, start=1):
        table.add_row(
            str(index),
            str(row["id"])[:8],
            str(row["created_at"]).replace("T", " ")[:19],
            row["program"],
            row["input_type"],
            row.get("file_name") or "-",
        )

    console.print(table)

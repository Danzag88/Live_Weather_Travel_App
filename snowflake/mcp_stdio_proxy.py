"""Stdio bridge from Cursor to the Snowflake-managed MCP server.

Reads SNOWFLAKE_PAT from the environment or from .secrets/snowflake_pat.
The token is never printed.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ACCOUNT_HOST = "QNKEIAF-UH49076.snowflakecomputing.com"
MCP_URL = (
    "https://QNKEIAF-UH49076.snowflakecomputing.com/api/v2/databases/"
    "SNOWFLAKE_LEARNING_DB/schemas/TEST_SNOWFLAKEDB/mcp-servers/TEST_MCP_SERVER"
)
ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / ".secrets" / "snowflake_pat"


def load_token() -> str:
    import os

    token = (os.environ.get("SNOWFLAKE_PAT") or "").strip()
    if not token and TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
    if not token:
        raise SystemExit("SNOWFLAKE_PAT is not set")
    return token


def read_message() -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        if b":" not in line:
            # Newline-delimited JSON, no framing headers.
            return json.loads(line.decode())
        name, value = line.decode().split(":", 1)
        headers[name.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    payload = sys.stdin.buffer.read(length)
    return json.loads(payload.decode())


def write_message(message: dict) -> None:
    payload = json.dumps(message).encode()
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode())
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def forward(token: str, message: dict) -> dict | None:
    if "id" not in message:
        return None
    request = urllib.request.Request(
        MCP_URL,
        data=json.dumps(message).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Host": ACCOUNT_HOST,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        return {
            "jsonrpc": "2.0",
            "id": message["id"],
            "error": {"code": error.code, "message": detail or error.reason},
        }
    if not raw.strip():
        return None
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        data_lines = [
            line[5:].strip()
            for line in raw.splitlines()
            if line.startswith("data:")
        ]
        raw = data_lines[-1] if data_lines else ""
    if not raw:
        return None
    return json.loads(raw)


def main() -> None:
    token = load_token()
    while True:
        message = read_message()
        if message is None:
            return
        reply = forward(token, message)
        if reply is not None:
            write_message(reply)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Check mietwohnen-eg.de/mietangebote for changes and notify via Telegram."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://mietwohnen-eg.de/mietangebote"
USER_AGENT = (
    "Mozilla/5.0 (compatible; PBG-Bot/1.0; "
    "+https://github.com/Stefan-Maximilian-Dietrich/PBG-Bot)"
)
TIMEOUT_SECONDS = 30
SELECTOR = "div.entry-content"
ERROR_THRESHOLD = 3

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"
SNAPSHOTS_DIR = REPO_ROOT / "snapshots"
LAST_HASH_FILE = STATE_DIR / "last_hash.txt"
ERROR_COUNT_FILE = STATE_DIR / "error_count.txt"
LOG_FILE = LOGS_DIR / "checks.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_page() -> tuple[int, str]:
    response = requests.get(
        URL,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.status_code, response.text


def extract_normalized(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(SELECTOR)
    if element is None:
        raise ValueError(f"Selector '{SELECTOR}' not found in HTML")
    text = element.get_text(separator="\n", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_state(path: Path, default: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return default


def write_state(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def append_log(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def save_snapshot(html: str, timestamp: str) -> str:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_ts = timestamp.replace(":", "-")
    path = SNAPSHOTS_DIR / f"{safe_ts}.html"
    path.write_text(html, encoding="utf-8")
    return str(path.relative_to(REPO_ROOT))


def send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(
            "WARN: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping notification",
            file=sys.stderr,
        )
        return False
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "disable_web_page_preview": False},
        timeout=15,
    )
    if not response.ok:
        print(
            f"ERROR: Telegram API returned {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    timestamp = now_iso()
    previous_hash = read_state(LAST_HASH_FILE, "")
    previous_errors = int(read_state(ERROR_COUNT_FILE, "0") or "0")

    try:
        http_status, html = fetch_page()
        content = extract_normalized(html)
        current_hash = hash_content(content)
    except Exception as exc:
        new_error_count = previous_errors + 1
        entry = {
            "timestamp": timestamp,
            "result": "error",
            "error": str(exc),
            "error_count": new_error_count,
        }
        append_log(entry)
        write_state(ERROR_COUNT_FILE, str(new_error_count))
        if new_error_count == ERROR_THRESHOLD:
            send_telegram(
                f"PBG-Bot: Fehler beim Checken — {ERROR_THRESHOLD}x in Folge.\n"
                f"Letzter Fehler: {exc}\n"
                f"Zeit: {timestamp}"
            )
        print(json.dumps(entry, ensure_ascii=False))
        return 0

    if previous_errors >= ERROR_THRESHOLD:
        send_telegram(
            f"PBG-Bot: läuft wieder normal (nach {previous_errors} Fehlern in Folge)."
        )

    if previous_hash == "":
        result = "initial"
    elif previous_hash == current_hash:
        result = "unchanged"
    else:
        result = "changed"

    entry = {
        "timestamp": timestamp,
        "result": result,
        "http_status": http_status,
        "hash": current_hash,
        "previous_hash": previous_hash or None,
    }

    if result == "changed":
        snapshot_rel = save_snapshot(html, timestamp)
        entry["snapshot"] = snapshot_rel
        send_telegram(
            f"PBG-Bot: ÄNDERUNG auf mietwohnen-eg.de/mietangebote erkannt!\n"
            f"Schau direkt: {URL}\n"
            f"Erkannt: {timestamp}\n"
            f"Snapshot im Repo: {snapshot_rel}"
        )

    if result in ("changed", "initial"):
        write_state(LAST_HASH_FILE, current_hash)

    if previous_errors > 0:
        write_state(ERROR_COUNT_FILE, "0")

    append_log(entry)
    print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Telegram-Benachrichtigungen (refactor von send_telegram + Listing-Formatierung)."""
from __future__ import annotations

import os
import sys

import requests


def send_telegram(message: str, disable_web_page_preview: bool = False) -> bool:
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
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": disable_web_page_preview,
        },
        timeout=15,
    )
    if not response.ok:
        print(
            f"ERROR: Telegram API returned {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        return False
    return True


def format_listing(listing: dict, source) -> str:
    def shown(value, suffix: str = "") -> str:
        return f"{value}{suffix}" if value not in (None, "") else "?"

    warm = listing.get("miete_warm")
    kalt = listing.get("miete_kalt")
    if warm not in (None, ""):
        miete = f"{warm} € warm"
    elif kalt not in (None, ""):
        miete = f"{kalt} € kalt"
    else:
        miete = "Miete ?"

    lines = [
        f"🏠 NEU bei {source.name} [{source.pillar}]",
        listing.get("titel") or "(ohne Titel)",
        f"{shown(listing.get('zimmer'))} Zi · {shown(listing.get('qm'), ' m²')} · {miete}",
    ]
    ort = " · ".join(p for p in (listing.get("stadt"), listing.get("stadtteil")) if p)
    if ort:
        lines.append(f"📍 {ort}")
    if listing.get("frei_ab"):
        lines.append(f"📅 frei ab {listing['frei_ab']}")

    flags = []
    if listing.get("braucht_wbs"):
        flags.append("WBS nötig")
    if listing.get("braucht_mitgliedschaft"):
        flags.append("Mitgliedschaft nötig")
    if flags:
        lines.append("⚠️ " + ", ".join(flags))

    lines.append(listing.get("url") or source.url)
    return "\n".join(lines)


def notify_new_listings(source, listings: list[dict]) -> int:
    sent = 0
    for listing in listings:
        if send_telegram(format_listing(listing, source)):
            sent += 1
    return sent

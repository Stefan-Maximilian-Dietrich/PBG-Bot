#!/usr/bin/env python3
"""Multi-Source Münchner Wohnungs-Monitor mit LLM-Extraktion + Telegram-Alerts.

Pro Lauf werden alle aktiven Quellen aus config/sources.yaml geprüft:
  fetch -> Hash-Vorfilter -> (bei Änderung) LLM-Extraktion -> Filter -> Dedup -> Telegram.

Ohne LLM_API_KEY fällt der Bot auf reine Hash-Änderungserkennung zurück
(Verhalten wie die ursprüngliche Single-Source-Version), damit er immer funktioniert.

Start (aus Repo-Root):  python -m bot.check
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bot.match import diff_new, filter_listings
from bot.notify import notify_new_listings, send_telegram
from bot.sources.base import Source, load_config
from bot.sources.http_source import content_text, fetch_detail_pages, fetch_source

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"
SNAPSHOTS_DIR = REPO_ROOT / "snapshots"
LOG_FILE = LOGS_DIR / "checks.jsonl"
ERROR_THRESHOLD = 3
# Drosselung gegen LLM-Rate-Limits (Gemini Free-Tier ~20 Requests/Minute): kurze Pause
# nach jedem LLM-Aufruf, damit ein Lauf mit vielen Quellen nicht ins Limit rennt.
LLM_CALL_DELAY_SECONDS = 5
# Hybrid-Fallback nur ausführen, wenn der bereinigte Text substanziell ist. Bei klar
# leeren Seiten ("keine Angebote", wenig Text) ist 0 korrekt -> kein teurer Zweit-Call.
FALLBACK_MIN_TEXT_CHARS = 500


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_state(path: Path, default: str = "") -> str:
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


def save_snapshot(html: str, timestamp: str, source_id: str) -> str:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_ts = timestamp.replace(":", "-")
    path = SNAPSHOTS_DIR / f"{source_id}_{safe_ts}.html"
    path.write_text(html, encoding="utf-8")
    return str(path.relative_to(REPO_ROOT))


def process_source(source: Source, criteria: dict, defaults, api_key: str | None) -> None:
    timestamp = now_iso()
    hash_file = STATE_DIR / f"{source.id}_hash.txt"
    error_file = STATE_DIR / f"{source.id}_error.txt"
    previous_hash = read_state(hash_file, "")
    previous_errors = int(read_state(error_file, "0") or "0")

    try:
        http_status, html = fetch_source(source, defaults)
        text = content_text(html, source.selector)
        current_hash = hash_content(text)
    except Exception as exc:  # noqa: BLE001 - jede Quelle isoliert behandeln
        new_error_count = previous_errors + 1
        entry = {
            "timestamp": timestamp,
            "source": source.id,
            "result": "error",
            "error": str(exc),
            "error_count": new_error_count,
        }
        append_log(entry)
        write_state(error_file, str(new_error_count))
        if new_error_count == ERROR_THRESHOLD:
            send_telegram(
                f"PBG-Bot: Fehler bei {source.name} — {ERROR_THRESHOLD}x in Folge.\n"
                f"Letzter Fehler: {exc}\nZeit: {timestamp}"
            )
        print(json.dumps(entry, ensure_ascii=False))
        return

    if previous_errors >= ERROR_THRESHOLD:
        send_telegram(
            f"PBG-Bot: {source.name} läuft wieder normal "
            f"(nach {previous_errors} Fehlern in Folge)."
        )

    if previous_hash == "":
        result = "initial"
    elif previous_hash == current_hash:
        result = "unchanged"
    else:
        result = "changed"

    entry = {
        "timestamp": timestamp,
        "source": source.id,
        "result": result,
        "http_status": http_status,
        "hash": current_hash,
        "previous_hash": previous_hash or None,
    }

    if result in ("changed", "initial"):
        extraction_ok = True
        if api_key:
            llm_text = text
            if source.detail_pages:
                details = fetch_detail_pages(html, source, defaults)
                if details:
                    llm_text = text + "\n\n--- DETAILSEITEN ---\n\n" + "\n\n".join(details)
            extraction_ok = _handle_with_llm(
                source, criteria, llm_text, html, timestamp, api_key, entry
            )
            time.sleep(LLM_CALL_DELAY_SECONDS)  # Rate-Limit-Schutz zwischen LLM-Aufrufen
        elif result == "changed":
            # Fallback ohne LLM: bei jeder Änderung melden (außer Erstlauf).
            entry["snapshot"] = save_snapshot(html, timestamp, source.id)
            send_telegram(
                f"PBG-Bot: ÄNDERUNG bei {source.name} erkannt!\n{source.url}\n"
                f"Erkannt: {timestamp}\n(LLM aus — kein LLM_API_KEY gesetzt)"
            )
        # Hash nur schreiben, wenn Extraktion ok war -> transiente LLM-Fehler
        # (z.B. Rate-Limit) werden im nächsten Lauf erneut versucht statt übersprungen.
        if extraction_ok:
            write_state(hash_file, current_hash)

    if previous_errors > 0:
        write_state(error_file, "0")

    append_log(entry)
    print(json.dumps(entry, ensure_ascii=False))


def _handle_with_llm(
    source: Source,
    criteria: dict,
    text: str,
    html: str,
    timestamp: str,
    api_key: str,
    entry: dict,
) -> bool:
    try:
        from bot.extract import extract_listings

        listings = extract_listings(text, source.name, api_key)
    except Exception as exc:  # noqa: BLE001 - Extraktionsfehler nicht fatal
        import re as _re

        msg = str(exc)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            mm = _re.search(r"limit:\s*(\d+).*?model:\s*([\w.\-]+)", msg, _re.DOTALL)
            entry["extract_error"] = (
                f"rate_limited (limit={mm.group(1)} model={mm.group(2)})"
                if mm
                else "rate_limited (429)"
            )
        else:
            entry["extract_error"] = msg[:200]
        return False

    # Hybrid-Fallback: liefert das günstige Standardmodell (z. B. flash-lite) nichts,
    # obwohl die Seite substanziellen Inhalt hat, einmal mit dem stärkeren Modell
    # nachfassen — fängt kryptische Listings (z. B. die knappen stadtimpuls-Tabellen).
    if not listings and len(text) > FALLBACK_MIN_TEXT_CHARS:
        fallback_model = os.environ.get("LLM_FALLBACK_MODEL") or "gemini-2.5-flash"
        try:
            fb = extract_listings(text, source.name, api_key, model=fallback_model)
            if fb:
                listings = fb
                entry["fallback_model"] = fallback_model
        except Exception as exc:  # noqa: BLE001 - Fallback nicht fatal
            # Ist der Fallback (nur) rate-limited, ist "0 Treffer" unsicher -> Hash NICHT
            # schreiben, damit der nächste Lauf es erneut versucht (selbstheilend, sobald
            # das Tagesquota wieder frei ist).
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                entry["fallback_error"] = "rate_limited"
                return False

    matched = filter_listings(listings, criteria)
    new, was_initial = diff_new(source.id, matched)
    entry["listings_total"] = len(listings)
    entry["listings_matched"] = len(matched)
    entry["new_matches"] = 0 if was_initial else len(new)

    if new and not was_initial:
        entry["snapshot"] = save_snapshot(html, timestamp, source.id)
        notify_new_listings(source, new)
    return True


def main() -> int:
    criteria, defaults, sources = load_config()
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "WARN: LLM_API_KEY not set — fallback to hash-only change detection",
            file=sys.stderr,
        )

    for source in sources:
        if not source.active:
            continue
        process_source(source, criteria, defaults, api_key)
    return 0


if __name__ == "__main__":
    sys.exit(main())

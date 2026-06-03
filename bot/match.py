"""Filter (Kriterien) + Dedup (gegen pro-Quelle gespeicherte gesehene Angebote)."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"


def _num(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def listing_key(listing: dict) -> str:
    """Stabiler Schlüssel zur Dedup. Bevorzugt die Detail-URL."""
    url = (listing.get("url") or "").strip()
    if url:
        return "url:" + url
    parts = [
        str(listing.get("titel") or "").strip().lower(),
        str(listing.get("zimmer") or ""),
        str(listing.get("qm") or ""),
        str(listing.get("stadtteil") or "").strip().lower(),
    ]
    return "sig:" + re.sub(r"\s+", " ", "|".join(parts))


def matches(listing: dict, criteria: dict) -> bool:
    """True, wenn das Angebot die Kriterien erfüllt.

    Bei UNBEKANNTEN Werten (null) wird zugunsten der Vollständigkeit eingeschlossen
    — lieber einmal zu viel melden als einen Treffer verpassen.
    """
    min_rooms = criteria.get("min_rooms")
    zimmer = _num(listing.get("zimmer"))
    if min_rooms is not None and zimmer is not None and zimmer < min_rooms:
        return False

    max_warm = criteria.get("max_warm_rent")
    if max_warm is not None:
        warm = _num(listing.get("miete_warm"))
        kalt = _num(listing.get("miete_kalt"))
        effective = warm if warm is not None else kalt
        if effective is not None and effective > max_warm:
            return False
    return True


def filter_listings(listings: list[dict], criteria: dict) -> list[dict]:
    return [l for l in listings if matches(l, criteria)]


def _seen_path(source_id: str) -> Path:
    return STATE_DIR / f"{source_id}_seen.json"


def _load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get("keys", []))
    except Exception:
        return set()


def diff_new(source_id: str, matched: list[dict]) -> tuple[list[dict], bool]:
    """Gibt (neue Angebote, war_erstlauf) zurück und aktualisiert den Seen-State.

    war_erstlauf=True beim allerersten Lauf einer Quelle -> Aufrufer soll NICHT
    benachrichtigen (sonst kämen alle Bestandsangebote auf einmal).
    """
    path = _seen_path(source_id)
    was_initial = not path.exists()
    seen = _load_seen(path)

    new: list[dict] = []
    current_keys: set[str] = set()
    for listing in matched:
        key = listing_key(listing)
        current_keys.add(key)
        if key not in seen:
            new.append(listing)

    seen |= current_keys
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"keys": sorted(seen)}, ensure_ascii=False), encoding="utf-8")
    return new, was_initial

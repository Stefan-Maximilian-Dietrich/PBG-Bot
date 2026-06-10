"""Filter (Kriterien) + Dedup (gegen pro-Quelle gespeicherte gesehene Angebote)."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"


def listing_key(listing: dict) -> str:
    """Stabiler Schlüssel zur Dedup. Bevorzugt die Detail-URL.

    Ohne URL: Ist die Größe (qm) bekannt, wird der Titel BEWUSST weggelassen
    (zimmer|qm|stadtteil) — das LLM vergibt für dieselbe Wohnung mal abweichende
    Titel ("2-Zimmer-Wohnung in Neuhausen" vs. "NHS 2 Zi"), was sonst Doppel-Alerts
    erzeugt. Fehlt qm (z. B. nur Titel/Tabellenzeile wie "Whg 0.5"), bleibt der Titel
    im Schlüssel, um mehrere ähnliche Wohnungen zu unterscheiden.
    """
    url = (listing.get("url") or "").strip()
    if url:
        return "url:" + url
    zimmer = str(listing.get("zimmer") or "")
    qm = str(listing.get("qm") or "")
    stadtteil = str(listing.get("stadtteil") or "").strip().lower()
    if qm:
        parts = [zimmer, qm, stadtteil]
    else:
        parts = [str(listing.get("titel") or "").strip().lower(), zimmer, stadtteil]
    return "sig:" + re.sub(r"\s+", " ", "|".join(parts))


def matches(listing: dict) -> bool:
    """High Recall: einziges Kriterium ist München — und nur als Negativ-Filter.

    Verworfen wird NUR, was klar außerhalb Münchens liegt (in_muenchen == False).
    Unbekannte Lage (null) und München/Umland (true) werden immer aufgenommen.
    Zimmerzahl und Miete filtern wir bewusst NICHT mehr — lieber eine Meldung zu viel
    als ein verpasstes Angebot (diese Wohnungen sind selten und wertvoll).
    """
    return listing.get("in_muenchen") is not False


def filter_listings(listings: list[dict], criteria: dict | None = None) -> list[dict]:
    # criteria bleibt für Aufrufer-Kompatibilität, wird aber nicht mehr genutzt:
    # High Recall -> nur der München-Negativfilter in matches().
    return [l for l in listings if matches(l)]


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
        # Sowohl gegen frühere Läufe (seen) als auch INNERHALB des Laufs (current_keys)
        # deduplizieren — manche Seiten listen dieselbe Wohnung mehrfach (z.B. Wix-Repeater).
        if key not in seen and key not in current_keys:
            new.append(listing)
        current_keys.add(key)

    seen |= current_keys
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"keys": sorted(seen)}, ensure_ascii=False), encoding="utf-8")
    return new, was_initial

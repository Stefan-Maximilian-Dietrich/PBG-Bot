"""Source-Konfiguration: lädt Quellen + Kriterien aus config/sources.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "bot" / "config" / "sources.yaml"


@dataclass
class Source:
    id: str
    name: str
    pillar: str
    url: str
    method: str = "http"
    selector: str | None = None
    active: bool = True
    # Wenn True: nach der Uebersicht auch die verlinkten Detailseiten holen und
    # ihren Text mit ans LLM geben (fuer Quellen, die in der Uebersicht nur Titel
    # zeigen, Details aber erst auf Unterseiten). Siehe fetch_detail_pages().
    detail_pages: bool = False


@dataclass
class Defaults:
    user_agent: str = (
        "Mozilla/5.0 (compatible; PBG-Bot/2.0; "
        "+https://github.com/Stefan-Maximilian-Dietrich/PBG-Bot)"
    )
    timeout_seconds: int = 30


def load_config(path: Path = CONFIG_PATH) -> tuple[dict, Defaults, list[Source]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    criteria = data.get("criteria") or {}

    d = data.get("defaults") or {}
    base = Defaults()
    defaults = Defaults(
        user_agent=d.get("user_agent") or base.user_agent,
        timeout_seconds=int(d.get("timeout_seconds") or base.timeout_seconds),
    )

    sources = [
        Source(
            id=s["id"],
            name=s.get("name", s["id"]),
            pillar=s.get("pillar", "genossenschaft"),
            url=s["url"],
            method=s.get("method", "http"),
            selector=s.get("selector"),
            active=bool(s.get("active", True)),
            detail_pages=bool(s.get("detail_pages", False)),
        )
        for s in (data.get("sources") or [])
    ]
    return criteria, defaults, sources

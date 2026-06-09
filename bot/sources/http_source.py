"""Generische HTTP-Quelle: holt eine Seite und extrahiert den relevanten Text."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.sources.base import Defaults, Source

# Begrenzt die an das LLM übergebene Textmenge (Token-/Kostenschutz).
MAX_CONTENT_CHARS = 24000
# Detailseiten-Crawl: max. Anzahl verlinkter Detailseiten und Gesamt-Textbudget dafür.
MAX_DETAIL_PAGES = 25
MAX_DETAIL_CHARS_PER_PAGE = 4000
MAX_DETAIL_CHARS_TOTAL = 20000


def _build_session() -> requests.Session:
    """HTTP-Session mit Retry für transiente Fehler.

    Wiederholt Connect-/Read-Timeouts, Verbindungsabbrüche und Server-5xx
    automatisch (GET ist idempotent und per Default retry-fähig), bevor ein
    Lauf als Fehler gilt. backoff_factor=1.0 -> ~0s / 2s / 4s zwischen Versuchen.
    HTTP 4xx (z. B. koogros intermittierende 415) bleibt absichtlich ein Fehler.
    """
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        raise_on_status=False,  # finalen Status durchreichen -> raise_for_status()
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_source(source: Source, defaults: Defaults) -> tuple[int, str]:
    with _build_session() as session:
        response = session.get(
            source.url,
            headers={
                "User-Agent": defaults.user_agent,
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            },
            timeout=defaults.timeout_seconds,
        )
    response.raise_for_status()
    return response.status_code, response.text


def content_text(html: str, selector: str | None = None, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """Sichtbaren Textinhalt extrahieren. Mit Selector den Container, sonst <body>.

    Boilerplate (script/style/noscript) wird entfernt; Whitespace normalisiert.
    Newlines bleiben erhalten, damit das LLM die Struktur (Angebotsblöcke) erkennt.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    element = soup.select_one(selector) if selector else None
    if element is None:
        element = soup.body or soup

    text = element.get_text(separator="\n", strip=True)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:max_chars]


def extract_detail_links(html: str, source: Source) -> list[str]:
    """Detail-Links aus der Übersicht ziehen: <a>-Links im (optionalen) Selector-Bereich,
    die unterhalb des Angebots-Pfads der Quelle liegen (also echte Unterseiten)."""
    soup = BeautifulSoup(html, "html.parser")
    container = (soup.select_one(source.selector) if source.selector else None) or soup.body or soup
    base_path = urlparse(source.url).path.rstrip("/")
    links: list[str] = []
    seen: set[str] = set()
    for a in container.find_all("a", href=True):
        full = urljoin(source.url, a["href"]).split("#")[0]
        path = urlparse(full).path.rstrip("/")
        if path.startswith(base_path + "/") and path != base_path and full not in seen:
            seen.add(full)
            links.append(full)
        if len(links) >= MAX_DETAIL_PAGES:
            break
    return links


def fetch_detail_pages(html: str, source: Source, defaults: Defaults) -> list[str]:
    """Text der verlinkten Detailseiten holen (für detail_pages-Quellen).

    Pro Seite und insgesamt budgetiert; einzelne fehlerhafte Detailseiten werden
    übersprungen (nicht fatal).
    """
    texts: list[str] = []
    total = 0
    with _build_session() as session:
        for url in extract_detail_links(html, source):
            try:
                resp = session.get(
                    url,
                    headers={
                        "User-Agent": defaults.user_agent,
                        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    },
                    timeout=defaults.timeout_seconds,
                )
                resp.raise_for_status()
            except Exception:  # noqa: BLE001 - einzelne Detailseite nicht fatal
                continue
            piece = content_text(resp.text, max_chars=MAX_DETAIL_CHARS_PER_PAGE)
            texts.append(piece)
            total += len(piece)
            if total >= MAX_DETAIL_CHARS_TOTAL:
                break
    return texts

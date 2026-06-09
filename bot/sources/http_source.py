"""Generische HTTP-Quelle: holt eine Seite und extrahiert den relevanten Text."""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.sources.base import Defaults, Source

# Begrenzt die an das LLM übergebene Textmenge (Token-/Kostenschutz).
MAX_CONTENT_CHARS = 24000


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


def content_text(html: str, selector: str | None = None) -> str:
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
    return text.strip()[:MAX_CONTENT_CHARS]

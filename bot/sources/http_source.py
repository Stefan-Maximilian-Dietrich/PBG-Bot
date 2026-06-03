"""Generische HTTP-Quelle: holt eine Seite und extrahiert den relevanten Text."""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from bot.sources.base import Defaults, Source

# Begrenzt die an das LLM übergebene Textmenge (Token-/Kostenschutz).
MAX_CONTENT_CHARS = 24000


def fetch_source(source: Source, defaults: Defaults) -> tuple[int, str]:
    response = requests.get(
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

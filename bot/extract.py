"""LLM-Extraktion: wandelt Seitentext in strukturierte Wohnungsangebote.

Anbieter-agnostisch über das OpenAI-kompatible Protokoll (openai-SDK mit base_url).
Standard ist Google Gemini Flash; per Env-Variablen frei austauschbar
(OpenAI, Groq, Mistral, OpenRouter, lokales Ollama ...). KEIN Anthropic.

  LLM_API_KEY   API-Key des gewählten Anbieters (Pflicht)
  LLM_BASE_URL  OpenAI-kompatibler Endpoint (Default: Gemini)
  LLM_MODEL     Modellname (Default: gemini-2.5-flash; auf manchen Accounts ist 2.0-flash Free-Tier-Limit 0)

Der openai-Import erfolgt lazy, damit das Modul auch ohne SDK/Key importierbar bleibt.

CLI-Test:  python -m bot.extract <snapshot.html> [css-selector]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Gemini spricht ein OpenAI-kompatibles API über diesen Endpoint.
DEFAULT_BASE_URL = os.environ.get("LLM_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = os.environ.get("LLM_MODEL") or "gemini-2.5-flash"

SYSTEM = (
    "Du extrahierst Miet-Wohnungsangebote aus dem Text einer deutschen Webseite "
    "(Wohnungsgenossenschaft, Immobilienportal oder städtisch). Ziel ist HOHER RECALL: "
    "Liste JEDE Wohnung, die als aktuelles Miet-/Vermietungsangebot erkennbar ist — AUCH "
    "wenn nur Adresse/Titel und Zimmerzahl angegeben sind und Miete oder Größe fehlen "
    "(dann diese Felder = null). Im Zweifel lieber aufnehmen als weglassen. "
    "Gib NUR DANN eine leere Liste zurück, wenn die Seite ausdrücklich sagt, dass es keine "
    "Angebote gibt (z. B. 'derzeit keine freien Wohnungen', 'alle Wohnungen vergeben', "
    "'keine Mietangebote vor'). KEINE Wohnungen sind: Navigations-/Menülinks, Stellplätze, "
    "Garagen, TG-Plätze, Gewerbeflächen, allgemeine Infotexte und bereits vergebene Wohnungen. "
    "Erfinde keine Werte; unbekannte Felder = null. Antworte ausschließlich mit JSON, ohne Erklärtext."
)

SCHEMA_HINT = (
    '{"listings": [\n'
    '  {"titel": "string",\n'
    '   "zimmer": Zahl oder null,\n'
    '   "qm": Zahl oder null,\n'
    '   "miete_warm": Zahl oder null,   // EUR, Punkt als Dezimaltrenner\n'
    '   "miete_kalt": Zahl oder null,\n'
    '   "stadt": "string oder null",   // z.B. Muenchen, Augsburg\n'
    '   "stadtteil": "string oder null",\n'
    '   "in_muenchen": true/false/null,   // true = Muenchen oder direktes Umland (Lkr. Muenchen); false = klar andere Stadt; null = unbekannt\n'
    '   "frei_ab": "string oder null",\n'
    '   "url": "string oder null",\n'
    '   "braucht_wbs": true/false/null,\n'
    '   "braucht_mitgliedschaft": true/false/null}\n'
    ']}'
)

PROMPT_TEMPLATE = (
    "Quelle: {source}\n\n"
    "Gib AUSSCHLIESSLICH ein JSON-Objekt exakt in dieser Form zurück:\n{schema}\n\n"
    "Wenn keine aktuell verfügbaren Angebote vorhanden sind: {{\"listings\": []}}.\n\n"
    "Seiteninhalt:\n\"\"\"\n{text}\n\"\"\""
)


def _to_num(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(".", "").replace(",", ".")
        m = re.search(r"-?\d+(\.\d+)?", s)
        return float(m.group()) if m else None
    return None


def _parse_json(content: str) -> dict:
    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    # Fallback: erstes {...}-Objekt aus evtl. umgebendem Text ziehen.
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _normalize(listing: dict) -> dict:
    return {
        "titel": str(listing.get("titel") or "").strip() or None,
        "zimmer": _to_num(listing.get("zimmer")),
        "qm": _to_num(listing.get("qm")),
        "miete_warm": _to_num(listing.get("miete_warm")),
        "miete_kalt": _to_num(listing.get("miete_kalt")),
        "stadt": (str(listing["stadt"]).strip() or None) if listing.get("stadt") else None,
        "stadtteil": (str(listing["stadtteil"]).strip() or None) if listing.get("stadtteil") else None,
        "in_muenchen": listing.get("in_muenchen") if isinstance(listing.get("in_muenchen"), bool) else None,
        "frei_ab": (str(listing["frei_ab"]).strip() or None) if listing.get("frei_ab") else None,
        "url": (str(listing["url"]).strip() or None) if listing.get("url") else None,
        "braucht_wbs": listing.get("braucht_wbs") if isinstance(listing.get("braucht_wbs"), bool) else None,
        "braucht_mitgliedschaft": listing.get("braucht_mitgliedschaft") if isinstance(listing.get("braucht_mitgliedschaft"), bool) else None,
    }


def _client(api_key: str | None, base_url: str | None):
    from openai import OpenAI

    api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY (bzw. GEMINI_API_KEY) ist nicht gesetzt")
    return OpenAI(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL)


def extract_listings(
    text: str,
    source_name: str,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> list[dict]:
    import openai

    client = _client(api_key, base_url)
    model = model or DEFAULT_MODEL
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": PROMPT_TEMPLATE.format(source=source_name, schema=SCHEMA_HINT, text=text)},
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=2048,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except openai.BadRequestError:
        # Anbieter/Modell unterstützt response_format nicht -> ohne erneut versuchen.
        response = client.chat.completions.create(
            model=model, temperature=0, max_tokens=2048, messages=messages
        )

    content = response.choices[0].message.content or "{}"
    data = _parse_json(content)
    listings = data.get("listings") if isinstance(data, dict) else None
    if not isinstance(listings, list):
        return []
    result = [_normalize(l) for l in listings if isinstance(l, dict)]
    return [l for l in result if l["titel"]]


def _main() -> int:
    from bot.sources.http_source import content_text

    if len(sys.argv) < 2:
        print("Usage: python -m bot.extract <snapshot.html> [css-selector]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    selector = sys.argv[2] if len(sys.argv) > 2 else None
    html = path.read_text(encoding="utf-8")
    text = content_text(html, selector)
    listings = extract_listings(text, path.stem)
    print(json.dumps(listings, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())

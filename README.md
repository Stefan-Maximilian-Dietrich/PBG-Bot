# PBG-Bot — Münchner Wohnungs-Suchsystem

Findet automatisch (LLM-gestützt) Mietwohnungen in München (Ziel: **2+ Zimmer, Warmmiete ≤ 1.500 €**)
und meldet neue Treffer per Telegram. Drei Standbeine:

1. **Genossenschaften** — öffentlich gelistete Angebotsseiten (dieser Bot).
2. **Freier Markt** — ImmoScout24/Immowelt/Kleinanzeigen/WG-Gesucht (geplant via [flathunter](https://github.com/flathunters/flathunter)).
3. **Städtisch/gefördert** — SOWON, München Modell, Münchner Wohnen (überwiegend administrativ; siehe unten).

## Wie es funktioniert

Pro Lauf (alle 5 Min. via GitHub Actions) für jede aktive Quelle:

```
fetch → Hash-Vorfilter → (bei Änderung) LLM-Extraktion → Filter → Dedup → Telegram
```

- **Hash-Vorfilter** spart LLM-Kosten: unveränderte Seiten lösen keinen LLM-Call aus.
- **LLM-Extraktion** (`bot/extract.py`, Google Gemini Flash; anbieter-agnostisch über das
  OpenAI-kompatible Protokoll) wandelt beliebige Angebotsseiten in strukturierte Listings —
  kein per-Seite-CSS-Selektor nötig.
- **Filter** (`bot/match.py`): ≥ Zimmer / ≤ Warmmiete; bei unbekannten Werten wird zugunsten
  der Vollständigkeit eingeschlossen.
- **Dedup**: pro Quelle in `state/<id>_seen.json`; nur **neue** Treffer benachrichtigen.
- Ohne `LLM_API_KEY` → Fallback auf reine Hash-Änderungserkennung.

## Setup

GitHub Actions Secrets (Repo → Settings → Secrets):

| Secret | Zweck |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Telegram-Bot |
| `TELEGRAM_CHAT_ID` | Ziel-Chat |
| `LLM_API_KEY` | LLM-Extraktion (sonst Hash-Fallback) — Default: **Google Gemini** (Key aus [Google AI Studio](https://aistudio.google.com/apikey)) |

Anbieter wechselbar **ohne Codeänderung** über optionale Repo-Variables (Settings → Variables):
`LLM_BASE_URL` (OpenAI-kompatibler Endpoint) und `LLM_MODEL`. Defaults im Code:
`https://generativelanguage.googleapis.com/v1beta/openai/` + `gemini-2.0-flash`. **Kein Anthropic.**

> Secrets via `gh secret set` ohne Trailing-Newline setzen (Pipe `--body -` verfälscht das Secret).

## Quelle hinzufügen

In `bot/config/sources.yaml` eintragen:

```yaml
  - id: meine-eg
    name: "Meine eG"
    pillar: genossenschaft
    url: https://example.de/freie-wohnungen
    selector: "div.content"   # optional; ohne Selector wird <body> genutzt
    active: true
```

## Lokal testen

```bash
.venv/bin/python -m pip install -r bot/requirements.txt
# Einzelne Seite extrahieren (braucht LLM_API_KEY; Default-Anbieter Gemini):
LLM_API_KEY=... .venv/bin/python -m bot.extract snapshots/<datei>.html "div.entry-content"
# Kompletter Lauf:
.venv/bin/python -m bot.check
```

Log-Viewer: `docs/` (liest `logs/checks.jsonl`).

## Roadmap

- **Stufe 1 (umgesetzt):** Multi-Source + LLM-Extraktion + gefilterter Telegram-Push.
- **Stufe 2:** E-Mail-Ingestion (Genossenschafts-/Mitbauzentrale-Newsletter), LLM-Bewerbungsentwürfe.
- **Stufe 3:** flathunter (freier Markt) produktiv, Auto-Versand von Bewerbungen (E-Mail zuerst),
  optional eingeloggter SOWON-Poller.

## Wichtig: Vergabemechanismus

Der Bot hilft dort, wo **öffentlich gelistet + offene Vergabe** gilt (z.B. wagnis eG, freier Markt).
Bei **Mitglieder-intern / Warteliste / Punktesystem** (Wogeno, Baugen. 1871, SOWON) ist der Hebel
nicht Monitoring, sondern **früh Mitglied werden / registrieren**:

- **SOWON-Registrierung** beim Amt für Wohnen und Migration stellen (~7 Monate Vorlauf).
- **München-Modell-Bescheid** beantragen (2-Pers.-Haushalt Einkommen ≤ ~43.100 €/Jahr).
- **Mitglied werden** bei offenen Genossenschaften + Newsletter abonnieren.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die PDF-Uebersicht 'Muenchner Wohnungsbaugenossenschaften'.

Alle Angaben recherchiert von den offiziellen Websites (Stand Juni 2026).
Ausfuehren:  .venv/bin/python docs/build_genossenschaften_pdf.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent / "Genossenschaften-Muenchen.pdf"

GREEN = colors.HexColor("#1a7f37")
ORANGE = colors.HexColor("#bf8700")
RED = colors.HexColor("#b42318")
HEAD = colors.HexColor("#11366b")
GREY = colors.HexColor("#444444")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=HEAD, fontSize=15, spaceBefore=14, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=HEAD, fontSize=11.5, spaceBefore=12, spaceAfter=2, keepWithNext=1)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.3, leading=12.6, alignment=TA_LEFT, spaceAfter=3)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8.2, leading=10.6, textColor=GREY)
STAT = ParagraphStyle("Stat", parent=BODY, fontSize=9.3, leading=12.6, spaceAfter=4)
TITLE = ParagraphStyle("Title", parent=styles["Title"], textColor=HEAD, fontSize=21, spaceAfter=4)
SUB = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10.5, textColor=GREY, spaceAfter=2)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.2, leading=10.4, spaceAfter=0)
CELLB = ParagraphStyle("CellB", parent=CELL, fontName="Helvetica-Bold")


def field(label, text):
    return Paragraph(f"<b>{label}:</b> {text}", BODY)


def coop(num, name, status, color, fields, sources):
    flow = [
        Paragraph(f"{num}. {name}", H2),
        Paragraph(f'<font color="{color.hexval()}"><b>Status:</b> {status}</font>', STAT),
    ]
    for lab, txt in fields:
        flow.append(field(lab, txt))
    flow.append(Spacer(1, 6))
    # Lange Eintraege duerfen umbrechen; Kopf + Status zusammenhalten.
    return [KeepTogether(flow[:3])] + flow[3:]


def howto(num, name, tag, color, steps, infos, unklar, quelle):
    flow = [
        Paragraph(f'{num}. {name} <font size="8" color="{color.hexval()}">[{tag}]</font>', H2),
        ListFlowable(
            [ListItem(Paragraph(s, BODY), leftIndent=4) for s in steps],
            bulletType="1", leftIndent=16,
        ),
    ]
    for lab, txt in infos:
        flow.append(field(lab, txt))
    if unklar:
        flow.append(Paragraph(f"<b>Unklar &ndash; bitte direkt erfragen:</b> {unklar}", BODY))
    flow.append(Paragraph(f"Beleg: {quelle}", SMALL))
    flow.append(Spacer(1, 8))
    return flow


story = []

# ---------- Titel ----------
story.append(Paragraph("M&uuml;nchner Wohnungsbaugenossenschaften", TITLE))
story.append(Paragraph("Wie es bei jeder Genossenschaft genau l&auml;uft &ndash; Mitgliedschaft, Anteile/Kosten, Wohnungsvergabe", SUB))
story.append(Paragraph("Stand: Juni 2026 &middot; Schwerpunkt: 2-Zimmer-Wohnungen bis 1.500 &euro; warm", SMALL))
story.append(Spacer(1, 8))

# ---------- Grundlagen ----------
story.append(Paragraph("So funktioniert eine Wohnungsgenossenschaft (Grundlagen)", H1))
basics = [
    "<b>Mitglied = Miteigentümer.</b> Man mietet nicht klassisch, sondern erwirbt ein dauerhaftes Nutzungsrecht. Voraussetzung für den Einzug ist fast immer die <b>Mitgliedschaft</b>.",
    "<b>Genossenschaftsanteile.</b> Mitglied wird man durch Zeichnung von Geschäftsanteilen (Eigenkapital). Üblich sind ein <b>Eintrittsgeld</b> (einmalig, oft 25–250 €) plus <b>Pflichtanteile</b>, meist gestaffelt nach Wohnungsgröße (in der Summe grob 700–3.500 €). Die Anteile bekommt man bei Austritt zurück &ndash; meist <b>unverzinst</b> und oft erst nach der nächsten Mitgliederversammlung.",
    "<b>Zwei Wege zur Wohnung.</b> (a) Auf eine konkret <b>ausgeschriebene freie Wohnung bewerben</b> (Mitgliedschaft entsteht dann mit der Zuteilung) &ndash; oder (b) auf eine <b>Warteliste/Vormerkliste</b> setzen lassen und auf ein Angebot warten.",
    "<b>Realität München.</b> Die Nachfrage ist extrem. Viele etablierte Genossenschaften haben <b>Aufnahmestopp</b> oder vergeben nur intern an Mitglieder bzw. deren Angehörige. Die besten Chancen für Neue: <b>offene/neuere Genossenschaften</b> und <b>schnelle</b> Bewerbung auf öffentlich ausgeschriebene Angebote (manche stehen nur wenige Tage online).",
    "<b>Förderung.</b> Viele Wohnungen sind gefördert: <b>EOF</b> (Sozialwohnung &ndash; WBS nötig), <b>München Modell</b> (mittlere Einkommen &ndash; Bescheid nötig) oder <b>KMB</b>. Dann gelten Einkommensgrenzen.",
]
story.append(ListFlowable([ListItem(Paragraph(b, BODY), leftIndent=10) for b in basics], bulletType="bullet", start="circle"))

# ---------- Schnelluebersicht ----------
story.append(Paragraph("Schnell&uuml;bersicht: Genossenschaften mit &ouml;ffentlicher Angebotsseite", H1))
rows = [[Paragraph("<b>Genossenschaft</b>", CELLB), Paragraph("<b>Neue Mitglieder?</b>", CELLB), Paragraph("<b>Vergabe &ndash; kurz</b>", CELLB)]]
overview = [
    ("wagnis eG", "Ja &ndash; offene Genossenschaft", "Infoabend + Mitgliedschaft; interne Ausschreibung, Belegungsausschuss, keine Warteliste"),
    ("Baugen. Hartmannshofen", "Ja &ndash; auch Nichtmitglieder", "Offene Bewerbung je Angebot (nur wenige Tage online), Mitglieder-Vorrang"),
    ("Progeno eG", "Nur mit Wohnungszusage", "Wohninteresse &rarr; Infoabend &rarr; Kennenlernen &rarr; Mitgliedschaft"),
    ("Verein f. Volkswohnungen", "Nur mit Wohnungszuschlag", "Keine Warteliste; freie Wohnungen auf der Homepage, offene Bewerbung"),
    ("Stadtimpuls eG", "Nur Einzug Projekt Neufreimann", "Aktuell freie 2-Zi (München Modell/KMB)!"),
    ("Postbaugen. (mietwohnen-eg)", "Nur bei Wohnungs&uuml;berlassung", "Objektbezogene Bewerbung per Fragebogen"),
    ("PostBG (Bundespost)", "Derzeit: Nichtmitglieder abwarten", "Bewerbung je Angebot + 3 Einkommensnachweise; Mitglieder-Vorrang"),
    ("ebm (Eisenbahner Hbf)", "Warteliste geschlossen", "Offene Online-Bewerbung je Angebot, keine Warteliste"),
    ("Baugen. 1898 (Verkehr)", "Externe-Warteliste zu; Bahn-Vorrang", "Bewerbung je Angebot; Anspruch nur Mitglieder/DB"),
    ("Verein f. Wohnungskultur", "Nur Mitglieder + enge Verwandte", "Nichtmitglieder können sich nicht bewerben"),
    ("Bauverein Haidhausen", "V.a. Angeh&ouml;rige v. Mitgliedern", "Online-Bewerbung je Angebot; 14 Sozialwhg. über SOWON"),
    ("IWG Isar", "Nein &ndash; derzeit keine Neuaufnahme", "Mitglieder-Vorrang (intern), dann Nicht-Mitglieder"),
    ("WBG 1951 (Flieger/Krieg)", "Nein &ndash; Vormerkliste geschlossen", "Vergabe nur an Vorgemerkte"),
    ("brf (Reichsbahnwerk)", "Nur Bahn-Personenkreis", "Vormerkliste, lange Wartezeiten"),
    ("Beamtenwohnungsverein", "Nein &ndash; Aufnahmestopp; nur &ouml;ff. Dienst", "Nur über Wohnungszuweisung"),
]
for n, m, v in overview:
    rows.append([Paragraph(n, CELL), Paragraph(m, CELL), Paragraph(v, CELL)])
tbl = Table(rows, colWidths=[4.6 * cm, 4.5 * cm, 7.1 * cm], repeatRows=1)
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HEAD),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(tbl)

# ---------- Schritt-für-Schritt-Anleitung ----------
story.append(Paragraph("So gehst du vor &ndash; Schritt f&uuml;r Schritt (die aussichtsreichen Genossenschaften)", H1))
story.append(Paragraph(
    "Konkrete Handlungsanleitung für die offenen (grün) und bedingt offenen (gelb) Genossenschaften. "
    "Alle Schritte und Beträge stammen von den offiziellen Websites (Stand Juni 2026); was dort nicht steht, "
    "ist als „Unklar“ markiert und sollte direkt erfragt werden &ndash; nichts ist geraten.", BODY))

A = []

A.append(howto(1, "Stadtimpuls eG", "grün &ndash; jetzt freie 2-Zi", GREEN, [
    "Freie Wohnungen im Projekt NORDIMPULS (Neufreimann) ansehen: stadtimpuls-genossenschaft.de/wohnungen.",
    "Zur nächsten Informationsveranstaltung anmelden (E-Mail an kontakt@stadtimpuls-genossenschaft.de).",
    "Satzung lesen; Mitgliedsantrag „nutzendes Mitglied“ (Download) ausfüllen und unterschreiben.",
    "Antrag per E-Mail (Betreff „Beitrittserklärung Stadtimpuls eG“) oder Post (Türkenstraße 60 UG, 80799 München) einreichen.",
    "Nach Aufnahme + Wohnungszuteilung wohnungsbezogene Pflichtanteile zeichnen, Vertrag, Einzug.",
], [
    ("Kosten", "2 Anteile à 500 € + 250 € Eintrittsgeld = 1.250 € (investierende Mitglieder 50 € Eintritt); bei Wohnung weitere Anteile je Größe/Förderung."),
    ("Einreichen", "kontakt@stadtimpuls-genossenschaft.de oder Türkenstraße 60 UG, 80799 München."),
    ("Aktuell", "Freie Wohnungen im Projekt NORDIMPULS Neufreimann (97 WE), Förderung EOF/München Modell/KMB."),
], "Konkrete Termine der Informationsveranstaltung (Website nennt keine); ob für die geförderten Wohnungen WBS bzw. München-Modell-Bescheid und welche Einkommensgrenze nötig ist.",
   "stadtimpuls-genossenschaft.de/wohnungen, /mitgliedwerden, /download"))

A.append(howto(2, "Kooperative Großstadt eG (KooGro)", "grün &ndash; offen, Projekt 2028", GREEN, [
    "Zu einem Infoabend (Zoom) anmelden: E-Mail an sign-in@koogro.de. Termine 2026: 12.03., 25.06., 29.10. (jeweils 19:00).",
    "Newsletter abonnieren (kooperative-grossstadt.de/newsletter/) &ndash; freie FREIMUNDO-Wohnungen werden „vor dem Sommer“ veröffentlicht.",
    "Beitrittserklärung (Download) ausfüllen; mit Originalunterschrift per Post (Friedenstraße 25, 81671 München) + zusätzlich als PDF an kontakt@koogro.de.",
    "Aufnahmebetrag zahlen (1.000 € Anteile + 200 € Eintrittsgeld).",
    "Als Mitglied auf eine FREIMUNDO-Wohnung bewerben (Vergabe nach Richtlinie; Mitgliedsdauer zählt &ndash; daher früh beitreten).",
], [
    ("Kosten", "2 Anteile à 500 € + 200 € Eintrittsgeld = 1.200 € (Anteile bei Austritt zurück)."),
    ("Einreichen", "Post: Friedenstraße 25, 81671 München + PDF an kontakt@koogro.de."),
    ("Aktuell", "Projekt FREIMUNDO Neufreimann, ~100 WE (EOF/München Modell/KMB), Bezug Anfang 2028; derzeit keine Bestandswohnungen frei."),
], "Konkrete Bewerbungsfrist für FREIMUNDO; welche Einkommensgrenzen/WBS je Förderweg gelten (Website beziffert sie nicht).",
   "kooperative-grossstadt.de/partizipation, /freimundo, /faq, /infoveranstaltung"))

A.append(howto(3, "wagnis eG", "grün &ndash; offen", GREEN, [
    "Pflicht-Infoabend „wagnis stellt sich vor“ besuchen (Anmeldung nötig). Nächster Termin: 17.06.2026, 18:00, wagnisART, Fritz-Winter-Str. 10.",
    "Beitrittserklärung ausfüllen + 1 Pflichtanteil (1.000 €) zeichnen → Mitglied (Intranet-Zugang).",
    "Auf eine freie Wohnung bewerben: Bewerbungsformular + Fragebogen/Motivationsschreiben per E-Mail an buero@wagnis.org.",
    "Vergabe durch den Belegungsausschuss („Bela“, keine Warteliste) → Vorstand. Bei Bezug weitere Pflichtanteile je Größe/Einkommen.",
], [
    ("Kosten", "1 Pflichtanteil 1.000 € + 150 € Verwaltungsgebühr; bei Wohnung weitere Pflichtanteile."),
    ("Einreichen", "buero@wagnis.org; Geschäftsstelle Petra-Kelly-Str. 29, 80797 München."),
    ("Aktuell", "In München derzeit keine freie Wohnung gelistet; freie Wohnungen nur im Projekt wagnisSHARE (Augsburg, WBS nötig)."),
], "Konkrete Einkommensgrenzen-Beträge je Förderweg; wann wieder Münchner Wohnungen frei werden.",
   "wagnis.org/genossenschaft/mitgliedschaft.html, /projekte/wohnungsvergabe.html, /aktuelles/freie-wohnungen.html, /aktuelles/veranstaltungen.html"))

A.append(howto(4, "Bürgerbauverein München eG (BbvM)", "grün &ndash; offen", GREEN, [
    "(Empfohlen) Infoabend besuchen &ndash; Termine über buergerbauverein-muenchen.de/kontakt/infoabend/ (derzeit keiner gelistet → für Benachrichtigung registrieren).",
    "Satzung lesen; Beitrittserklärung (Download) ausfüllen, unterschreiben, per Post einreichen.",
    "1.500 € überweisen (1.000 € Pflichtanteil + 500 € Eintrittsgeld) an IBAN DE51 6005 0101 0405 0264 21.",
    "Zulassung durch den Vorstand abwarten (Bestätigung per E-Mail, kann Wochen dauern).",
    "Als Mitglied per E-Mail über freie Wohnungen informiert werden; Mitgliedsdauer zählt bei der Vergabe → früh beitreten.",
], [
    ("Kosten", "1.000 € Pflichtanteil + 500 € Eintrittsgeld = 1.500 €; bei Wohnung wohnungsbezogene Pflichtanteile (je Fläche/Förderung)."),
    ("Einreichen", "Beitrittserklärung per Post; Kontakt post@buergerbauverein-muenchen.de."),
    ("Aktuell", "Prinz-Eugen-Park (87 WE) fertig/belegt; Eggarten-Projekt erst in Bildung. Derzeit keine freien Wohnungen."),
], "Nächster Infoabend-Termin (keiner gelistet); konkrete Wohnungszahl/Bezugstermin Eggarten; Einkommensgrenzen-Beträge.",
   "buergerbauverein-muenchen.de/faq, /hrf_faq/wie-werde-ich-mitglied, /kontakt/infoabend, /downloads"))

A.append(howto(5, "Baugenossenschaft Hartmannshofen eG", "grün &ndash; auch für Nichtmitglieder", GREEN, [
    "Wohnungsangebote auf bg-hartmannshofen.de/wohnungsangebote regelmäßig prüfen (Inserate stehen nur wenige Tage online).",
    "Bei passendem Angebot online über „Zur Wohnungsbewerbung“ bewerben (auch als Nichtmitglied möglich).",
    "Vorstand entscheidet (Mitglieder werden bevorzugt).",
    "Bei Zuteilung 9 Pflichtanteile zeichnen → Mitgliedschaft + Mietvertrag (keine Kaution/Provision).",
], [
    ("Kosten", "9 Pflichtanteile à 153,39 € = 1.380,51 € (bei Zuteilung); keine Kaution, keine Provision."),
    ("Einreichen", "ausschließlich online über die Wohnungsangebote-Seite; Geschäftsstelle Allacher Str. 98, 80997 München."),
    ("Aktuell", "Derzeit keine Angebote; keine Warteliste."),
], "Separates Eintrittsgeld; welche Nachweise (WBS/Einkommen) einzureichen sind (Website nennt sie nicht).",
   "bg-hartmannshofen.de/mitgliedschaft, /wohnungsangebote"))

A.append(howto(6, "Progeno Wohnungsgenossenschaft eG", "gelb &ndash; nur mit Wohnungszusage", ORANGE, [
    "Voraussetzungen prüfen und Wohninteresse über den Fragebogen anmelden (progeno.de/freie-wohnungen/). Aufnahme nur mit konkretem Wohninteresse/Zusage.",
    "An einer (Online-)Informationsveranstaltung teilnehmen.",
    "Kennenlern-Treffen: dort Bewerbungsunterlagen + Mitgliedschaftsinfos erhalten.",
    "Nach Zusage: Mitgliedschaft (1.000 € Anteil + 200 € Eintritt) + aktive Mitwirkung in der Bewohnergruppe.",
], [
    ("Kosten", "1.000 € Pflichtanteil + 200 € Eintrittsgeld; weitere Anteile je Förderung/Größe (per KfW-Programm 134 finanzierbar)."),
    ("Einreichen", "info@progeno.de; Ruth-Drexel-Str. 154, 81927 München."),
    ("Aktuell", "1 freie Wohnung (Neufreimann W.2.02, 1-Zi, KMB) &ndash; für 2 Personen zu klein; Freiham/Prinz-Eugen-Park vergeben."),
], "Nächster Infoabend für Neufreimann (derzeit keiner terminiert).",
   "progeno.de/genossenschaft/, /freie-wohnungen/, /fragebogen/"))

A.append(howto(7, "Verein für Volkswohnungen eG (VfV)", "gelb &ndash; nur mit Zuschlag", ORANGE, [
    "Freie Wohnungen auf vfv-muenchen.de/wohnungsangebote prüfen (keine Warteliste).",
    "In der jeweiligen Anzeige direkt online bewerben (Neukunden ohne Mitgliedsnummer).",
    "Vergabe nach den „Vergaberichtlinien“ (PDF unter /service/downloads); Einkommensnachweis erforderlich, bei geförderten Wohnungen WBS.",
    "Mit dem Zuschlag: Dauernutzungsvertrag + Mitgliedschaft + Geschäftsanteile (für Mitglieder keine Kaution/Provision).",
], [
    ("Kosten", "76,69 € Eintritt + Pflichtanteile (je 100 €), gestaffelt: bis 50 qm 700 €, bis 75 qm 1.700 €, bis 100 qm 2.800 €, über 100 qm 3.500 € (keine Ratenzahlung)."),
    ("Einreichen", "online über die Wohnungsanzeige; info@vfv-muenchen.de, Thalkirchner Str. 41, 80337 München."),
    ("Aktuell", "Derzeit keine Wohnungsangebote."),
], "Konkrete Einkommensgrenzen (außer den gesetzlichen beim WBS).",
   "vfv-muenchen.de/wohnungsangebote, /mitgliedschaft, /service/faqs, /service/downloads"))

A.append(howto(8, "Stadtbaustein eG", "gelb &ndash; frühe Phase", ORANGE, [
    "(Optional) Info-Veranstaltung &ndash; Termin per kontakt@stadtbaustein-muenchen.de erfragen.",
    "Mitgliedsantrag (Download) ausfüllen, unterschreiben, per Post einreichen.",
    "Vorstand bearbeitet Anträge einmal monatlich gebündelt → schriftliche Bestätigung.",
    "Mitgliedschaft sichert das Recht auf eine Wohnung in einem künftigen Projekt (Eggarten/Zschokkestr./Neufreimann, in Vorbereitung).",
], [
    ("Kosten", "2 Anteile à 500 € + 250 € Eintrittsgeld = 1.250 € (investierende Mitglieder 50 € Eintritt)."),
    ("Einreichen", "Post: c/o Sarah Mühlhaus, Pestalozzistr. 46 Rgb., 80469 München; Kontakt kontakt@stadtbaustein-muenchen.de."),
    ("Aktuell", "Keine konkreten Wohnungen/Termine veröffentlicht; Projekte in Vorbereitung."),
], "Download-Link des Mitgliedsantrags; Infotermine; Projekt-Zeitpläne/Wohnungszahlen; Einkommensgrenzen.",
   "stadtbaustein-muenchen.de/mitglied-werden, /kontakt; Mitbauzentrale-Projektbörse"))

A.append(howto(9, "Postbaugenossenschaft München u. Oberbayern eG (mietwohnen-eg)", "gelb &ndash; nur bei Wohnungsüberlassung", ORANGE, [
    "Mietangebote auf mietwohnen-eg.de/mietangebote prüfen (laufend aktualisiert).",
    "Auf eine Wohnung bewerben → Besichtigung.",
    "„Mietinteressenten-Fragebogen“ (Download unter /formulare-und-downloads) ausfüllen.",
    "Mitgliedschaft entsteht erst mit der Überlassung einer Wohnung.",
], [
    ("Kosten", "Auf der Website nicht angegeben &ndash; bei der Geschäftsstelle erfragen."),
    ("Einreichen", "Auf der Website nicht beschrieben; Kontakt Arnulfstr. 155, 80634 München, Tel. 089 13 06 71-30, post@bptm.de."),
    ("Aktuell", "Derzeit keine Wohnung gelistet."),
], "Genauer Bewerbungsweg (E-Mail/Post/persönlich); Anteils- und Eintrittskosten; ob Einkommensnachweis/WBS nötig.",
   "mietwohnen-eg.de/mietangebote, /formulare-und-downloads, /kontakt"))

A.append(howto(10, "PostBG München eG (Bundespostbeamte)", "gelb &ndash; derzeit eingeschränkt", ORANGE, [
    "Hinweis beachten: PostBG bittet Nichtmitglieder derzeit, von Wohnungsanfragen/-vormerkungen abzusehen (hohe Nachfrage).",
    "Wohnungsangebote unter /vermietungsangebote prüfen.",
    "„Bewerbungsbogen“ (Download) ausfüllen.",
    "Persönlich in der Geschäftsstelle abgeben &ndash; mit Ausweis + den 3 aktuellsten Einkommensnachweisen (Formulare auch per E-Mail möglich).",
    "Mitgliedschaft + Zahlung (in bar) vor Unterzeichnung des Nutzungsvertrags.",
], [
    ("Kosten", "100 € Eintritt + 2 Pflichtanteile à 250 € (= 500 €) + Zusatzanteile je Größe (à 250 €); bar vor Vertrag."),
    ("Einreichen", "persönlich: Canalettostr. 27, 80638 München; info@postbg-muenchen.de (Fr. Baumgärtel)."),
    ("Aktuell", "Derzeit keine Wohnung; Nichtmitglieder gebeten, von Anfragen abzusehen."),
], "Ob und ab wann Nichtmitglieder sich wieder bewerben können.",
   "postbg-muenchen.de/grundsaetzliches, /vermietungsangebote, /downloads-fuer-mietinteressenten"))

for e in A:
    story.extend(e)

# ---------- Detailteil ----------
story.append(Paragraph("Teil 1 &ndash; Im Detail: Genossenschaften mit &ouml;ffentlicher Wohnungsvergabe", H1))

D = []

D.append(coop(1, "wagnis eG", "Offen &ndash; nimmt neue Mitglieder auf, keine Warteliste", GREEN, [
    ("Neue Mitglieder", "Ja. „Die wagnis ist eine offene Genossenschaft, die neue Mitglieder aufnimmt und für die Wohnungsvergabe keine Warteliste führt.“"),
    ("Mitglied werden", "1) Infoveranstaltung besuchen (Pflicht). 2) Beitrittsformular ausfüllen + Pflichtanteil zeichnen. 3) Zugang zum Intranet, voll stimmberechtigtes Mitglied."),
    ("Anteile / Kosten", "Pflichtanteil bei Eintritt 1.000 € + einmalig 150 € Verwaltungspauschale. Bei Wohnungsbezug weitere Pflichtanteile (abhängig von Wohnungsgröße und Haushaltseinkommen). Rückzahlbar bei Kündigung. Freiwillige Anteile mit Dividende möglich."),
    ("Wohnungsvergabe", "Keine Warteliste. Frei werdende Wohnungen werden intern unter den Mitgliedern ausgeschrieben. Ein ehrenamtlicher Belegungsausschuss entscheidet (kein Punktesystem) nach Kriterien wie Identifikation mit dem Konzept, Quartiersbezug, sozialer Dringlichkeit und ausgewogener Hausgemeinschaft. Voraussetzung: Infoabend + Mitgliedschaft aller volljährigen Haushaltsmitglieder."),
    ("Voraussetzungen", "Mitgliedschaft + Infoabend. Je nach Förderung (EOF/München Modell/KMB) ggf. WBS/Einkommensgrenzen (Beträge auf Anfrage)."),
    ("Freie Wohnungen", "wagnis.org/aktuelles/freie-wohnungen.html (Bewerbung per Formular + Motivationsschreiben an buero@wagnis.org). Aktuell freie Wohnungen nur in Augsburg (Projekt wagnisSHARE, EOF-3, WBS nötig) &ndash; in München gerade keine. Pflicht-Infoabend laut Website z.B. 17.06.2026 (Termine rotieren)."),
], "wagnis.org/genossenschaft/mitgliedschaft.html; wagnis.org/projekte/wohnungsvergabe.html"))

D.append(coop(2, "Baugenossenschaft Hartmannshofen eG", "Offen &ndash; auch Nichtmitglieder d&uuml;rfen sich bewerben", GREEN, [
    ("Neue Mitglieder", "Ja, an eine Wohnungszuweisung gekoppelt: „Mitgliedschaft wird erst mit der Zuweisung einer Wohnung begründet.“ Bewerben dürfen sich Mitglieder und Nichtmitglieder."),
    ("Mitglied werden", "Online auf eine konkrete freie Wohnung bewerben; der Vorstand entscheidet; mit der Zuweisung entsteht die Mitgliedschaft."),
    ("Anteile / Kosten", "Bei Wohnungsbezug 9 Pflichtanteile laut Satzung; Anteilsbetrag aktuell auf Anfrage (bei der Geschäftsstelle erfragen, Tel. 089/14 99 050). Rückzahlung beim Austritt unverzinst."),
    ("Wohnungsvergabe", "Offene Bewerbung je Angebot, keine Warteliste („Eine Warteliste wird nicht mehr geführt.“). Angebote stehen „nur wenige Tage online“. Bei konkurrierenden Bewerbungen werden Mitglieder bevorzugt."),
    ("Voraussetzungen", "Keine Einkommensgrenzen/WBS/Berufsgruppen genannt (auf Anfrage)."),
    ("Freie Wohnungen", "bg-hartmannshofen.de/wohnungsangebote (aktuell keine Angebote; Inserate stehen oft nur wenige Tage online)"),
], "bg-hartmannshofen.de/mitgliedschaft; bg-hartmannshofen.de/wohnungsangebote"))

D.append(coop(3, "Progeno Wohnungsgenossenschaft eG", "Bedingt offen &ndash; Aufnahme nur mit konkretem Wohninteresse/Zusage", ORANGE, [
    ("Neue Mitglieder", "Eingeschränkt: „… derzeit ausschließlich Neumitglieder mit einem konkreten Wohninteresse und einer Wohnungszusage.“"),
    ("Mitglied werden", "1) Wohninteresse anmelden. 2) (Online-)Informationsveranstaltung. 3) Kennenlernveranstaltung (Bewerbungsunterlagen). 4) Nach Zusage: Mitgliedschaft + aktive Mitgestaltung. Kontakt: info@progeno.de."),
    ("Anteile / Kosten", "Pflichtanteil 1.000 € + einmalig 200 € Eintrittspauschale. Zusätzliche Wohnungspflichtanteile je nach Förderprogramm/Größe (im Factsheet); per KfW-Programm 134 finanzierbar. Rückzahlung der Wohnungspflichtanteile nach Neubelegung; keine Verzinsung."),
    ("Wohnungsvergabe", "Offene Anmeldung des Wohninteresses je Angebot, dann Info-/Kennenlernveranstaltungen. Warteliste/Mitglieder-Vorrang auf Anfrage."),
    ("Voraussetzungen", "Zielgruppe: Familien, Paare, Alleinstehende aus unterschiedlichen Einkommensgruppen; Bereitschaft zur aktiven Beteiligung. WBS/Einkommen je Wohnung (im Angebot ausgewiesen)."),
    ("Freie Wohnungen", "progeno.de/freie-wohnungen/ (aktuell 1 freie Wohnung: Neufreimann, freifinanziert, 1-Zi)"),
], "progeno.de/genossenschaft/; progeno.de/freie-wohnungen/"))

D.append(coop(4, "Verein f&uuml;r Volkswohnungen eG (VfV)", "Bedingt &ndash; Mitgliedschaft nur mit Wohnungszuschlag", ORANGE, [
    ("Neue Mitglieder", "Mitgliedschaft nur im Zuge eines Dauernutzungsvertrags: „… nur … wenn Sie den Zuschlag für eine von Ihnen beworbene Wohnung bekommen haben.“ Keine Vormerklisten."),
    ("Mitglied werden", "Über die Bewerbung auf eine ausgeschriebene Wohnung; mit dem Zuschlag Mitgliedschaft + Zeichnung der Anteile. Bestandsmieter ohne Mitgliedschaft können sich schriftlich bewerben (Vorstand entscheidet)."),
    ("Anteile / Kosten", "Geschäftsanteile gestaffelt (1 Anteil = 100 €): bis 50 qm = 700 €, bis 75 qm = 1.700 €, bis 100 qm = 2.800 €, über 100 qm = 3.500 €. Zzgl. einmalig 76,69 € Eintrittsgebühr. Keine Ratenzahlung. Rückzahlbar bei Mitgliedschaftsende. Dividende bis 4 % p.a."),
    ("Wohnungsvergabe", "Keine Warteliste: „… wir inserieren unsere freien Wohnungen auf unserer Homepage.“ Offene Bewerbung je Angebot (geringe Fluktuation)."),
    ("Voraussetzungen", "Einkommensnachweis erforderlich. Für geförderte Wohnungen WBS/B-Schein nötig. Konkrete Grenzen auf Anfrage."),
    ("Freie Wohnungen", "vfv-muenchen.de/wohnungsangebote (aktuell keine Angebote)"),
], "vfv-muenchen.de/mitgliedschaft; vfv-muenchen.de/service/faqs"))

D.append(coop(5, "Stadtimpuls eG", "Aktuell freie 2-Zi-Wohnungen im Projekt Neufreimann (M&uuml;nchen Modell/KMB)!", GREEN, [
    ("Neue Mitglieder", "Eingeschränkt: „Wir nehmen bis auf weiteres nur Mitglieder auf, die in unser Projekt im neuen Quartier Neufreimann ziehen werden.“"),
    ("Mitglied werden", "Voraussetzung: Wohnungszusage (Neufreimann) + Teilnahme an einer Infoveranstaltung. Dann Satzung anerkennen, Mitgliedsantrag ausfüllen und per E-Mail/Post (kontakt@stadtimpuls-genossenschaft.de)."),
    ("Anteile / Kosten", "2 Pflichtanteile à 500 € = 1.000 €. Eintrittsgeld 250 € (regulär) bzw. 100 € (investierendes Mitglied). Zusätzliche wohnungsbezogene Anteile nach qm/Förderform/Projektkosten. Alle Anteile bei Austritt rückzahlbar."),
    ("Wohnungsvergabe", "Über Informationsveranstaltungen („Melde dich bei Interesse an einer Wohnung bitte zur nächsten Informationsveranstaltung an.“). Warteliste/Punkte/Vorrang auf Anfrage."),
    ("Voraussetzungen", "Wohnungszusage im Projekt Neufreimann. Förderformen EOF, München Modell (MMG), KMB &ndash; Einkommensgrenzen auf Anfrage."),
    ("Freie Wohnungen", "stadtimpuls-genossenschaft.de/wohnungen &ndash; Projekt NORDIMPULS Neufreimann (97 WE), aktuell frei u.a. 4× 2-Zi (München Modell/KMB) + 1× 3-Zi (KMB). Freiham erst frühe Planung."),
], "stadtimpuls-genossenschaft.de/mitgliedwerden; .../wohnungen"))

D.append(coop(6, "Postbaugenossenschaft M&uuml;nchen u. Oberbayern eG (&bdquo;mietwohnen-eg&ldquo;)", "Bedingt &ndash; Mitgliedschaft nur bei Wohnungs&uuml;berlassung", ORANGE, [
    ("Neue Mitglieder", "„Eine Mitgliedschaft bei unserer Baugenossenschaft ist erst bei Überlassung einer unserer Wohnungen möglich.“ Keinen separaten Beitritt."),
    ("Mitglied werden", "Kein eigener Mitgliedsantrag. Weg über die Wohnungsbewerbung: nach Besichtigung „Mietinteressenten-Fragebogen“ ausfüllen. Mitgliedschaft entsteht mit der Überlassung."),
    ("Anteile / Kosten", "Auf Anfrage (Satzung 2024 ist verlinkt, aber keine Beträge auf den Seiten)."),
    ("Wohnungsvergabe", "Objektbezogene Bewerbung per Fragebogen. „Unser Angebot wird ständig aktualisiert.“"),
    ("Voraussetzungen", "Auf Anfrage."),
    ("Freie Wohnungen", "mietwohnen-eg.de/mietangebote"),
], "mietwohnen-eg.de/formulare-und-downloads; mietwohnen-eg.de/mietangebote"))

D.append(coop(7, "PostBG M&uuml;nchen eG (Baugen. der Bundespostbeamten)", "Bedingt &ndash; Nichtmitglieder sollen derzeit von Anfragen absehen", ORANGE, [
    ("Neue Mitglieder", "„… bitten wir Sie als Nichtmitglied … derzeit von Wohnungsanfragen und Wohnungsvormerkungen Abstand zu nehmen.“ Mitgliedschaft erst mit Wohnungsüberlassung."),
    ("Mitglied werden", "Bewerbung auf eine konkret ausgeschriebene Wohnung mit dem „Bewerbungsbogen“ inkl. drei aktueller Einkommensnachweise und Ausweisprüfung (persönliche Vorsprache)."),
    ("Anteile / Kosten", "Eintrittsgeld 100 € + 2 Pflichtanteile à 250 € (Mitgliedschaft). Zusätzliche Anteile nach Größe (bis 50 qm 1, bis 75 qm 2, bis 100 qm 3, über 100 qm 4 &ndash; je 250 €). Zahlung in bar vor Vertragsunterzeichnung. Rückzahlbarkeit nicht angegeben."),
    ("Wohnungsvergabe", "Objektbezogene Bewerbung je Angebot; Vorrang für Mitglieder. Warteliste/Punkte auf Anfrage."),
    ("Voraussetzungen", "Drei Einkommensnachweise. Konkrete Grenzen/WBS/Beruf auf Anfrage."),
    ("Freie Wohnungen", "postbg-muenchen.de/vermietungsangebote (aktuell keine Angebote)"),
], "postbg-muenchen.de/grundsaetzliches; .../vermietungsangebote"))

D.append(coop(8, "Eisenbahner-Baugenossenschaft M&uuml;nchen-Hbf eG (ebm)", "Eingeschr&auml;nkt &ndash; Warteliste geschlossen (Mitgliedschaft via Mietvertrag)", RED, [
    ("Neue Mitglieder", "„Eine Mitgliedschaft begründet sich nur in Verbindung mit einem Mietverhältnis.“ + „Wir haben unsere Warteliste geschlossen und können Bewerbungen derzeit leider nicht berücksichtigen.“"),
    ("Mitglied werden", "Online auf konkret ausgeschriebene Wohnungen bewerben; mit Abschluss des Mietvertrags automatisch Mitgliedschaft. Nur online (keine persönliche Unterlagenabgabe)."),
    ("Anteile / Kosten", "Auf Anfrage. (Größe: 2.714 Mitglieder, 2.566 Wohnungen, Stand 31.12.2024.)"),
    ("Wohnungsvergabe", "Offene Online-Bewerbung je Einzelangebot; „Es werden keine Wartelisten geführt.“ Mitglieder-Vorrang/Punkte nicht angegeben."),
    ("Voraussetzungen", "Trotz des Namens keine Zugangsbeschränkung auf bahnnahe Personen, ABER „Mitarbeiter der Bahn und deren Beteiligungsunternehmen werden bevorzugt.“ Einkommen/WBS nicht genannt."),
    ("Freie Wohnungen", "ebm-muenchen.de/mietangebote/ (aktuell keine Angebote)"),
], "ebm-muenchen.de/service/haeufige-fragen; ebm-muenchen.de/mietangebote/"))

D.append(coop(9, "Baugenossenschaft des Verkehrspersonals 1898 eG", "Eingeschr&auml;nkt &ndash; Warteliste f&uuml;r Externe geschlossen, Bahn-Vorrang", RED, [
    ("Neue Mitglieder", "„Die Warteliste für die Wohnungen in München ist bis auf weiteres für externe Bewerber geschlossen.“ 3-/4-Zimmer-Bewerbungen werden nicht mehr angenommen. Anspruch nur Mitglieder und DB-Konzern-Mitarbeiter."),
    ("Mitglied werden", "Mitgliedschaft erst mit Wohnungszuweisung; Selbstauskunftsformular + unbedingte Beitrittserklärung + Zulassung. Kein Rechtsanspruch."),
    ("Anteile / Kosten", "1 Geschäftsanteil = 300 €; Eintrittsgeld variabel (Beschluss Vorstand/Aufsichtsrat, max. 300 €). Pflichtanteile = gestaffelte Anzahl von 300-€-Anteilen: 1-Zi & 2-Zi bis 50 qm = 3 (900 €), 2-Zi über 50 qm & 3-Zi = 4 (1.200 €), 4&ndash;5-Zi = 5 (1.500 €). Rückzahlung verzögert. Bestand: 956 Wohnungen / ~1.200 Mitglieder."),
    ("Wohnungsvergabe", "Offene Bewerbung je Angebot über die Website; faktisch Warteliste (für Externe geschlossen). Vorrang Mitglieder + DB."),
    ("Voraussetzungen", "Priorität: Mitarbeiter der Deutschen Bahn / BEV und deren Tochterunternehmen sowie Renten-/Pensionsempfänger der ehem. Bundesbahn. Einkommen/WBS nicht angegeben."),
    ("Freie Wohnungen", "bg-1898.de/mietangebote (aktuell keine Angebote)"),
], "bg-1898.de/genossenschaft/mitgliedschaft; bg-1898.de/service/faq"))

D.append(coop(10, "Verein f&uuml;r Wohnungskultur eG (VfW)", "F&uuml;r Externe praktisch geschlossen &ndash; nur Mitglieder + enge Verwandte", RED, [
    ("Neue Mitglieder", "„Bewerbungen werden nur von Mitgliedern und engen Verwandten von Mitgliedern angenommen.“ Nichtmitglieder können sich NICHT um eine Wohnung bewerben. Reine Mitgliedschaft erst nach ca. 5 Jahren Mietverhältnis."),
    ("Mitglied werden", "Über ein bestehendes Mietverhältnis: laut FAQ mind. 5 Jahre Mieter, bevor man sich um die Mitgliedschaft bewerben kann. Kontakt: mittmann@vfw-muenchen.de."),
    ("Anteile / Kosten", "Auf Anfrage."),
    ("Wohnungsvergabe", "Nur an Mitglieder und nahe Angehörige. Größenrichtlinie nach Haushaltsgröße (z.B. 2 Pers. = 1,5&ndash;2,5 Zi.)."),
    ("Voraussetzungen", "Privathaftpflicht ist Pflicht. Einkommen/WBS auf Anfrage."),
    ("Freie Wohnungen", "vfw-muenchen.de/mietangebote/ (Beispiel zuletzt: 3-Zi. München-Blumenau, 68,6 qm, gesamt ca. 1.053 €/Monat). Vergaberichtlinie 12/2024 verlinkt."),
], "vfw-muenchen.de/faq/; vfw-muenchen.de/mietangebote/; Vergaberichtlinie 12/2024 (PDF)"))

D.append(coop(11, "Bauverein M&uuml;nchen Haidhausen eG", "Stark eingeschr&auml;nkt &ndash; v.a. Angeh&ouml;rige bestehender Mitglieder", RED, [
    ("Neue Mitglieder", "„Eine Mitgliedschaft auf Vorrat ist nicht möglich.“ Aktuell werden „vor allem Familienangehörige unserer Mitglieder berücksichtigt“; anderen Bewerbern „müssen wir leider eine Absage erteilen.“"),
    ("Mitglied werden", "Online auf eine konkret ausgeschriebene freie Wohnung bewerben (nur online). Mit der Wohnungsüberlassung entsteht die Mitgliedschaft."),
    ("Anteile / Kosten", "20&ndash;40 Geschäftsanteile à 60 € (= 1.200&ndash;2.400 €). Einmalige Aufnahmegebühr 120 €. Keine Kaution. Rückzahlung nicht beziffert."),
    ("Wohnungsvergabe", "Offene Online-Bewerbung je freiem Angebot; keine Wartelisten/Vormerkungen. Vergaberichtlinien (PDF). 14 EOF-Sozialwohnungen werden über sowon.muenchen.de vergeben. Mehrjährige Wartezeiten möglich."),
    ("Voraussetzungen", "Faktischer Vorrang für Angehörige bestehender Mitglieder. Sozialwohnungen über SOWON (WBS/Einkommen). Details auf Anfrage."),
    ("Freie Wohnungen", "bauverein-haidhausen.de/wohnungsangebote (zeigt 2&ndash;3-Zi. in Au-Haidhausen); Sozialwohnungen über sowon.muenchen.de"),
], "bauverein-haidhausen.de/mitgliedschaft; .../wohnungsangebote"))

D.append(coop(12, "IWG Isar Wohnungsbaugenossenschaft eG", "Eingeschr&auml;nkt &ndash; derzeit keine neuen Mitglieder; Mitglieder-Vorrang", RED, [
    ("Neue Mitglieder", "„Derzeit werden keine neuen Mitglieder aufgenommen.“"),
    ("Mitglied werden", "Nutzer einer Genossenschaftswohnung muss Mitglied sein. Bewerbung schriftlich mit dem Formular, das jedem Angebot beiliegt. Neuaufnahmen aktuell ausgesetzt."),
    ("Anteile / Kosten", "3 Geschäftsanteile à 255 € = 765 € + 50 € Eintrittsgeld. Geschäftsguthaben bei Austritt zurück (unverzinst). Bei Wohnungsnutzung weitere Pflichtanteile: 7 Anteile (40 qm) bis 32 Anteile (über 110 qm)."),
    ("Wohnungsvergabe", "Mitglieder-Vorrang: freie Wohnungen werden zuerst intern (Mitgliederbereich + Newsletter) angeboten. Kriterien: passende Bewohnerzahl, Dauer der Mitgliedschaft, Dringlichkeit, finanzielle Situation. Nicht-Mitglieder nur, falls keine Vergabe an ein Mitglied möglich."),
    ("Voraussetzungen", "Einkommen/WBS/Beruf auf Anfrage (finanzielle Situation ist nur eines von vier Kriterien)."),
    ("Freie Wohnungen", "iwg-muenchen.de/wohnungsangebote/ (öffentlich) + interner Mitgliederbereich"),
], "iwg-muenchen.de; Grundsaetze-PDF (Stand Nov. 2018)"))

D.append(coop(13, "WBG der Flieger- und Kriegsgesch&auml;digten in Bayern eG (1951)", "Eingeschr&auml;nkt &ndash; Vormerkliste derzeit geschlossen", RED, [
    ("Neue Mitglieder", "„Eine Neumitgliedschaft … ist erst bei Überlassung einer unserer Wohnungen möglich.“ + „Ab sofort sind Bewerbungen zur Aufnahme in unsere Vormerkliste leider nicht möglich.“"),
    ("Mitglied werden", "Mitgliedschaft entsteht mit der Wohnungsüberlassung; Wohnungen gehen „ausschließlich an vorgemerkte Interessenten“ &ndash; die Vormerkliste ist aktuell jedoch gesperrt."),
    ("Anteile / Kosten", "Eintrittsgeld 25 € + Grundanteil 310 € + Pflichtanteile à 310 € nach Größe (bis 49,99 qm 2, bis 69,99 qm 3, bis 89,99 qm 4, ab 90 qm 5). Kaution nach Zimmerzahl (1-Zi 665 €, 2-Zi 820 €, 3-Zi 1.025 €, über 3-Zi 1.400 €). Rückzahlbarkeit nicht angegeben."),
    ("Wohnungsvergabe", "Über die Vormerkliste; „Wohnungsvergaben erfolgen ausschließlich an vorgemerkte Interessenten.“"),
    ("Voraussetzungen", "Einkommen/WBS/Beruf auf Anfrage (der historische Name begründet keine aktuelle Zugangsbeschränkung laut Website)."),
    ("Freie Wohnungen", "wbg1951.de/wohnungsangebote (aktuell keine Angebote)"),
], "wbg1951.de/grundsaetzliches; wbg1951.de/wohnungsangebote"))

D.append(coop(14, "Baugenossenschaft Reichsbahnwerk Freimann eG (brf)", "Eingeschr&auml;nkt &ndash; nur Bahn-Personenkreis", RED, [
    ("Neue Mitglieder", "Mitgliedschaft nur mit Mietvertrag. „Zurzeit erfolgt eine Aufnahme in die Vormerkliste … nur für aktive Mitarbeiter, Rentner und Pensionisten der Deutschen Bahn und des Bundeseisenbahnvermögens.“"),
    ("Mitglied werden", "Wohnungsantrag per E-Mail (info@brf-muenchen.de) anfordern (Personengruppe angeben) &rarr; Berechtigungsprüfung &rarr; Aufnahme in Vormerkliste; Beitrittserklärung + Zulassung."),
    ("Anteile / Kosten", "3 Pflichtanteile à 500 €. Eintrittsgeld wird erhoben (Höhe variabel, Beschluss Vorstand/Aufsichtsrat). Rückzahlbarkeit nicht angegeben."),
    ("Wohnungsvergabe", "Vormerkliste/Warteliste mit langen Wartezeiten („Bei Wohnungen größer 60 qm … noch längeren Wartezeiten“). Mitgliedschaft ist Voraussetzung."),
    ("Voraussetzungen", "Bahnnahe Personen: brf ist „als betriebliche Sozialeinrichtung der Deutschen Bahn AG anerkannt“ (Personenkreis in Satzung §3). Einkommen/WBS nicht angegeben."),
    ("Freie Wohnungen", "brf-muenchen.de/mietangebote/ (Zugang über E-Mail-Antrag)"),
], "brf-muenchen.de/mietangebote/; brf-muenchen.de/faqs/; brf-muenchen.de/ueber-uns/"))

D.append(coop(15, "Beamtenwohnungsverein M&uuml;nchen eG (BWV)", "Geschlossen &ndash; Aufnahmestopp (Zielgruppe &ouml;ffentlicher Dienst)", RED, [
    ("Neue Mitglieder", "Nein: „Unser Bewerbungskontingent ist derzeit leider ausgeschöpft.“ „Aufnahmen … erfolgen ausschließlich im Zusammenhang mit der Zuweisung einer Wohnung beim bwv.“"),
    ("Mitglied werden", "Nur über eine Wohnungszuweisung; eigenständige Bewerbungen sollen derzeit unterbleiben. Detaillierter Ablauf auf Anfrage."),
    ("Anteile / Kosten", "Auf Anfrage."),
    ("Wohnungsvergabe", "Auf Anfrage. München-Modell-Wohnungen erfordern eine städtische Bescheinigung."),
    ("Voraussetzungen", "Zielgruppe laut Satzung §3 (überwiegend Beamte/Angestellte im öffentlichen Dienst); verlangt wird u.a. eine Arbeitgeberbestätigung über unbefristete Anstellung."),
    ("Freie Wohnungen", "bwv-muenchen.de/aktuelles/wohnungsangebote (aktuell keine Angebote)"),
], "bwv-muenchen.de/service/interessenten; bwv-muenchen.de/ueber-uns"))

for entry in D:
    story.extend(entry)

# ---------- Teil 2: Projekt-/Neubau-Genossenschaften ----------
story.append(Paragraph("Teil 2 &ndash; Projekt-/Neubau-Genossenschaften: oft der beste Weg für Neue", H1))
story.append(Paragraph(
    "Diese Genossenschaften bauen neu. Wer <b>jetzt Mitglied wird</b>, kann beim nächsten Projekt eine frische Wohnung bekommen &ndash; "
    "statt auf einen Auszug zu warten. Vorteil: die <b>Dauer der Mitgliedschaft</b> ist meist ein zentrales Vergabekriterium, die "
    "Einstiegskosten sind niedrig (ca. 1.000&ndash;1.500 €, bei Austritt rückzahlbar). Nachteil: der Bezug liegt oft <b>mittelfristig</b> "
    "(Neubaugebiete Freiham und Neufreimann/Bayernkaserne: Bezug überwiegend 2027/2028). Hinweis: <b>wagnis eG</b> und <b>Stadtimpuls eG</b> "
    "sind ebenfalls Projekt-Genossenschaften &ndash; ihre Details stehen bereits in Teil 1.", BODY))

PD = []

PD.append(coop(1, "Kooperative Großstadt eG (KooGro)", "Offen &ndash; frühe Mitgliedschaft = Vorteil; großes Projekt 2028", GREEN, [
    ("Neue Mitglieder", "Ja, jederzeit. „Wer also jetzt Mitglied wird, ist klar im Vorteil!“ (die Dauer der Mitgliedschaft ist vorrangiges Vergabekriterium)."),
    ("Mitglied werden / Kosten", "Infoabend besuchen &rarr; Satzung lesen &rarr; Beitrittserklärung (Original per Post + PDF an kontakt@koogro.de) &rarr; Beitrag zahlen. Pflicht: 2 Anteile à 500 € = 1.000 € + 200 € Eintrittsgeld. Freiwillige Anteile mit Dividende (aktuell 2,5 %). Investierende Mitglieder ohne Stimmrecht (Eintrittsgeld entfällt)."),
    ("Aktuelle &amp; geplante Projekte", "<b>FREIMUNDO &ndash; Neufreimann</b> (ehem. Bayernkaserne): ca. 100 Wohnungen, Förderung EOF + München Modell + KMB, <b>Bezug Anfang 2028</b> (Wohnungen werden „vor dem Sommer“ auf der Website veröffentlicht). metso'metso &ndash; Haidhausen (inklusiv, 14&ndash;16 Plätze, Fertigstellung 2026). Bereits bezogen: FREIHAMPTON &ndash; Freiham (45 WE, 2022), SAN RIEMO &ndash; Messestadt Riem (28 WE, 2020). Aktuell keine freien Bestandswohnungen."),
    ("Wie an eine Wohnung", "Erst Mitglied werden, dann Wohnungsbewerbung; eine Kommission vergibt nach Kriterien, Mitgliedsdauer vorrangig. Verfügbare Wohnungen werden auf der Website veröffentlicht (Newsletter empfohlen)."),
    ("Voraussetzungen", "Mitgliedschaft. Je Projekt verschiedene Förderformen (EOF/München Modell/KMB &rarr; WBS bzw. Bescheid/Einkommensgrenzen; teils frei finanziert). Konkrete Grenzen nur in den PDF-Richtlinien."),
    ("Jetzt Interesse bekunden", "Infoabende 2026 online/Zoom: 12.03., 25.06., 29.10. (19:00; Anmeldung sign-in@koogro.de; Zugangslink kommt 1&ndash;2 Tage vorher). Newsletter: kooperative-grossstadt.de/newsletter/; Beitritt: kontakt@koogro.de."),
], "kooperative-grossstadt.de/partizipation/, /freimundo/, /faq/, /category/aktuelles/"))

PD.append(coop(2, "Bürgerbauverein München eG (BbvM)", "Offen &ndash; sucht aktiv Mitglieder fürs neue Projekt", GREEN, [
    ("Neue Mitglieder", "Ja; für das neue Projekt ausdrücklich auch Nicht-Mitglieder angesprochen: „Werden Sie Mitglied im BbvM!“"),
    ("Mitglied werden / Kosten", "Infoabend (empfohlen) &rarr; Satzung lesen &rarr; Beitrittserklärung per Post + Zahlung „€ 1000,- sowie € 500,- Eintrittsgeld“ &rarr; Zulassung durch Vorstand. Beim Einzug zusätzlich wohnungsbezogene Pflichtanteile (flächen-/förderabhängig, je Wohnungsangebot ausgewiesen, unverzinst) + optional freiwillige Anteile (Dividende)."),
    ("Aktuelle &amp; geplante Projekte", "<b>Eggarten-Siedlung</b> (Norden): Gesamtquartier ca. 1.900 Wohnungen (~47 % Genossenschaften); davon ~900 WE über 8 GIMA-Unternehmen inkl. BbvM. Konkrete BbvM-Wohnungszahl, Förderung und Termin noch offen. Vorzeigeprojekt der Website bleibt der Prinz-Eugen-Park (Bogenhausen): 87 Wohnungen, frei finanziert &ndash; fertig/bezogen, derzeit nichts frei."),
    ("Wie an eine Wohnung", "„Wohnungen werden nur an Mitglieder vergeben. Die Dauer der Mitgliedschaft ist ein wichtiges Vergabekriterium.“ Mitglieder werden per E-Mail über freie Wohnungen informiert. Beim Eggarten-Projekt aktive Mitwirkung (Baugruppe)."),
    ("Voraussetzungen", "Meist EOF Stufe I; München Modell für mittlere Einkommen; KMB/frei finanziert ohne Einkommensgrenzen."),
    ("Jetzt Interesse bekunden", "Infoabend: buergerbauverein-muenchen.de/kontakt/infoabend/; Beitrittserklärung unter /downloads/."),
], "buergerbauverein-muenchen.de/faq/, /hrf_faq/wie-werde-ich-mitglied/, /eggarten/"))

PD.append(coop(3, "Stadtbaustein eG", "Offen &ndash; frühe Phase, Projekte noch in Vorbereitung", ORANGE, [
    ("Neue Mitglieder", "Ja. „Mitgliedsanträge werden derzeit einmal monatlich gebündelt bearbeitet.“"),
    ("Mitglied werden / Kosten", "Mitgliedsantrag (unterschrieben per Post) &rarr; Vorstand entscheidet &rarr; Bestätigung. 2 Pflichtanteile à 500 € = 1.000 € + 250 € Eintrittsgeld (investierende Mitglieder: 50 €)."),
    ("Aktuelle &amp; geplante Projekte", "Auf der Website keine konkreten Projekte. Laut Projektbörse der Mitbauzentrale „in Projektvorbereitung“, Standorte u. a. Eggartensiedlung, Zschokkestraße, Neufreimann; Förderformen EOF/frei finanziert/München Modell (Zeitplan offen). Eigene Projekt-Infos sind veraltet (Stand 2021); Standorte laut Mitbauzentrale."),
    ("Wie an eine Wohnung", "Mitgliedschaft gewährt „das Recht auf eine Wohnung in einem Wohnprojekt“. Detailliertes Bewerbungs-/Auswahlverfahren auf Anfrage."),
    ("Voraussetzungen", "Auf Anfrage (Förderformen würden WBS bzw. München-Modell-Bescheid voraussetzen)."),
    ("Jetzt Interesse bekunden", "Kontaktformular + Newsletter (ca. 2×/Jahr): stadtbaustein-muenchen.de/kontakt/; E-Mail kontakt@stadtbaustein-muenchen.de; Mitgliedsantrag: /mitglied-werden/."),
], "stadtbaustein-muenchen.de/mitglied-werden/, /kontakt/; Mitbauzentrale-Projektbörse"))

PD.append(coop(4, "Wogeno München eG", "Derzeit GESCHLOSSEN &ndash; Aufnahme nur in unregelmäßigen Fenstern", RED, [
    ("Neue Mitglieder", "Aktuell <b>geschlossen</b>: das Portal anmeldung.wogeno.de meldet „Im Moment nehmen wir keine neuen Mitglieder auf.“ Aufnahme erfolgt nur in unregelmäßigen Fenstern (früher z.B. Aktion „50 neue Mitglieder“). Eine ältere Meldung „Freiham auch für Nicht-Mitglieder“ ist von 2022 und überholt."),
    ("Mitglied werden / Kosten", "Über das Aufnahmefenster bzw. das Portal anmeldung.wogeno.de. Konkrete Anteilshöhe in dieser Recherche auf Anfrage."),
    ("Aktuelle &amp; geplante Projekte", "Freiham Haus „UTE“ ist ein fertiges Bestandsobjekt (83 Wohnungen, Bau 2020&ndash;2022), kein Planungsprojekt. Bestand insgesamt: selbstverwaltetes, soziales, ökologisches Wohnen; reguläre Wohnungen werden intern an Mitglieder vergeben."),
    ("Wie an eine Wohnung", "Regulär intern unter Mitgliedern (Intranet/E-Mail). Für Neue v. a. über die Aufnahmefenster und über Neubauprojekte (Freiham)."),
    ("Voraussetzungen", "Für geförderte/Freiham-Wohnungen ggf. WBS bzw. München-Modell-Bescheid (auf Anfrage)."),
    ("Jetzt Interesse bekunden", "anmeldung.wogeno.de (auf Öffnung eines Aufnahmefensters warten); Tel. 089/890 5718-30, info@wogeno.de."),
], "wogeno.de; Aufnahmeaktion/Freiham (Mitbauzentrale-/Freiham-Recherche)"))

PD.append(coop(5, "Das große kleine Haus eG", "Geschlossen &ndash; Aufnahmestopp (Projekt läuft)", RED, [
    ("Neue Mitglieder", "Nein: „Derzeit nimmt Das große kleine Haus eG … keine neuen Mitglieder mehr auf.“ Grund: über 70 Mitglieder, nur 1 Projekt (~30 Einheiten). Ausnahmen durch den Vorstand nur für geförderte (MMG)-/Gewerbe-Einheiten oder neue Projektgruppen."),
    ("Aktuelle &amp; geplante Projekte", "Kreativquartier (Heßstraße): ca. 30 Einheiten, davon 13 Wohnungen „München Modell Genossenschaft“ (MMG) + 16 im konzeptionellen Mietwohnungsbau (KMB); Erstbezug voraussichtlich um Oktober 2026 (Grundsteinlegung 2/2025, Richtfest 2/2026)."),
    ("Wie an eine Wohnung", "Primär über Mitgliedschaft; regulärer Quereinstieg nicht vorgesehen &ndash; nur über Vorstands-Ausnahmen (v. a. MMG-Wohnungen). Verfahren auf Anfrage."),
    ("Jetzt Interesse bekunden", "Nur per E-Mail info@dasgrossekleinehaus.de (kein offenes Formular)."),
], "dasgrossekleinehaus.de (Mitglied werden / Impressum); ru.muenchen.de (Richtfest 2026)"))

PD.append(coop(6, "wabe.zwo eG", "Derzeit geschlossen (frühe Phase)", RED, [
    ("Neue Mitglieder", "Nein: „Da wir leider aktuell keine neuen Mitglieder aufnehmen können, sind auch die Infoabende vorübergehend ausgesetzt.“"),
    ("Projektstand", "Auf der Website nicht beziffert; es läuft aktiv eine Grundstückssuche („Immobilien oder Bauland von privat gesucht“) &ndash; also frühe Planungsphase."),
    ("Jetzt Interesse bekunden", "Derzeit nur passiv über die Kontaktseite (wabezwo.de/kontakt). Empfehlung: über den Mitbauzentrale-Newsletter beobachten, wann die Aufnahme wieder öffnet."),
], "wabezwo.de"))

for e in PD:
    story.extend(e)

story.append(Paragraph("Zentrale Anlaufstelle: Mitbauzentrale München", H2))
story.append(ListFlowable([ListItem(Paragraph(x, BODY), leftIndent=10) for x in [
    "<b>Monats-Newsletter „freie Wohnungen in Gemeinschaftsprojekten“</b> &ndash; das wichtigste Frühwarnsystem (freie Wohnungen, Grundstücksausschreibungen, Veranstaltungen). Anmeldung: mitbauzentrale-muenchen.de/newsletter.html",
    "<b>Projektbörse</b> mit Statusfilter &ndash; „in Planung“/„in Projektvorbereitung“ zeigt, wo noch Plätze frei sein dürften: mitbauzentrale-muenchen.de/boersen/projektboerse.html",
    "<b>Kostenlose Beratung für Bürger:innen</b>: Di 10&ndash;14 Uhr, Mi 15&ndash;19 Uhr, Tel. (089) 579 389 50, info@mitbauzentrale-muenchen.de, Schwindstraße 1.",
    "Ergänzend: <b>Forum Baugemeinschaften München</b> (eigene Projektbörse offener Baugruppen) und der „Tag der offenen Wohnprojekte“ (laut Recherche ~4. Juli 2026).",
]], bulletType="bullet", start="circle"))

story.append(Paragraph("Weitere aktive Projekt-Genossenschaften &amp; Baugemeinschaften (Aktualität bitte direkt anfragen)", H2))
prows = [[Paragraph("<b>Gruppe</b>", CELLB), Paragraph("<b>Aufnahme/Status</b>", CELLB), Paragraph("<b>Quartier / Projekt</b>", CELLB)]]
padd = [
    ("Progeno eG", "Eigene „freie Wohnungen“-Seite; direkt anfragen (auch in Teil 1)", "Freiham; Neufreimann WA 11 West (~90 WE, ~2028); Prinz-Eugen-Park"),
    ("raumFAIR eG", "Teils freie geförderte Wohnungen; direkt anfragen (Sitz Regensburg)", "Freiham (München Modell Genossenschaften)"),
    ("WG München-West (WGMW)", "Bestand i.d.R. zu; Neubau projektbezogen anfragen", "Freiham (Konsortium WagnisWest)"),
    ("CoGeno eG", "„in Planung“ &ndash; Frühphase, meist offen; anfragen", "München (Projekt n. n.)"),
    ("Baugemeinschaft Freiham", "Sucht Mitstreitende", "Freiham (40&ndash;45 WE)"),
    ("Baugemeinschaft München", "Sucht Mitstreitende (v. a. Familien)", "Freiham (~30 WE)"),
    ("Gemeinsam Größer", "Offene Baugruppe; Status prüfen", "Prinz-Eugen-Park (~42 WE)"),
    ("Baugemeinschaft Riem", "Offene Baugruppe; Status prüfen", "Messestadt Riem"),
]
for a, b, c in padd:
    prows.append([Paragraph(a, CELL), Paragraph(b, CELL), Paragraph(c, CELL)])
ptbl = Table(prows, colWidths=[4.2 * cm, 6.0 * cm, 6.0 * cm], repeatRows=1)
ptbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HEAD),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(ptbl)
story.append(Paragraph("Hinweis: Baugemeinschaften sind keine Genossenschaften, funktionieren aber ähnlich (gemeinsam bauen). Schwerpunkt-Neubaugebiete sind Freiham (Westen) und Neufreimann/Bayernkaserne (Norden) &ndash; Bezug überwiegend 2027/2028.", SMALL))

# ---------- Teil 3: geschlossen / unbekannt ----------
story.append(Paragraph("Teil 3 &ndash; Geschlossene Genossenschaften und sonstige (ohne &ouml;ffentliche Info)", H1))

story.append(Paragraph("Geschlossen / nur f&uuml;r Mitglieder &ndash; f&uuml;r Neue derzeit kein Weg hinein", H2))
closed = [
    "<b>WOGENO München eG</b> (wogeno.de): Bestand nur an Mitglieder; Aufnahme nur in unregelmäßigen Fenstern (Portal anmeldung.wogeno.de derzeit geschlossen) &ndash; Status/Details siehe Teil 2.",
    "<b>Baugenossenschaft München von 1871 eG</b> (baugen1871.de): älteste WBG Deutschlands; keine Wartelisten/Registrierung; Angebote nur im Mitgliederbereich.",
    "<b>Wohnungsgenossenschaft München-West eG</b> (wg-mw.de): größte Münchner Genossenschaft (ca. 5.000 Mitglieder, über 3.300 Wohnungen); Angebote nur über das Login-Portal, keine öffentliche Liste.",
    "<b>Münchner Baugenossenschaft eG</b> (muenchner-baugenossenschaft.de): absoluter Aufnahmestopp; Anfragen „zwecklos“.",
    "<b>Baugenossenschaft München Süd eG</b> (bms-eg.de): „absoluter Aufnahmestopp“; Verweis auf andere Genossenschaften.",
    "<b>Baugenossenschaft München-Oberwiesenfeld eG</b> (bgmo.de): keine Angebote, keine neuen Mitglieder/Warteliste.",
    "<b>Baugenossenschaft Nord-West eG</b> (bgnw-muenchen.de): keine Angebote/Mitglieder auf absehbare Zeit.",
    "<b>Bauverein Giesing eG</b> (bvgiesing.de): derzeit keine Wohnungen, von Bewerbung absehen.",
    "<b>Gemeinnützige Wohnungsgenossenschaft München-Pasing eG</b> (wg-pasing.de): keine Angebote, niemand auf Warteliste.",
    "<b>Baugenossenschaft München-West des Eisenbahnpersonals eG</b> (ebg-muenchen-west.de): keine aktuellen Angebote, keine Wartelisten.",
    "<b>Frauen Wohnen eG</b> (frauenwohnen.de): nur Frauen; nimmt keine neuen Mitfrauen auf &ndash; Ausnahme: Frauen mit EOF-Registrierungsschein mit mind. 50 Punkten.",
]
story.append(ListFlowable([ListItem(Paragraph(c, BODY), leftIndent=10) for c in closed], bulletType="bullet", start="square"))

story.append(Paragraph("Status unbekannt / nur telefonisch (keine klare Online-Info)", H2))
unknown = [
    "<b>Heimstättenbaugenossenschaft Pasing eG</b> (hbgpasing.de): ca. 300 Wohnungen, gegr. 1918; „Wohnungsbewerbung“-Bereich vorhanden, Status auf Anfrage.",
    "<b>Eisenbahner-Baugenossenschaft München-Ost eG</b> (ebg-muenchen-ost.de) und <b>Eisenbahner-Baugenossenschaft Pasing eG</b> (ebgpasing.de): Bahn-Genossenschaften; Status auf Anfrage.",
    "<b>Baugenossenschaft der Verkehrsbeamten Obermenzing eG</b> (bg-obermenzing.de): Website im Aufbau.",
    "<b>GIMA München eG</b> (gima-muenchen.de): genossenschaftliche Immobilienagentur von 39 Wohnungsunternehmen &ndash; <b>kein eigener Wohnungsbestand</b>.",
    "<b>Ohne Website / nur telefonisch (Status unbekannt):</b> Bauverein „Neu-München“ eG, Gemeindebeamten eG, Gemeinnütziger Wohnungsverein München 1899, Münchener Kleinwohnungs-Baugenossenschaft eG, Münchener Wohnungsbeschaffung eG, Münchner Zentralbaugenossenschaft eG, Wohnungsbau-Genossenschaft München-Solln eG, Wohnungsbauverein München eG.",
]
story.append(ListFlowable([ListItem(Paragraph(u, BODY), leftIndent=10) for u in unknown], bulletType="bullet", start="square"))

# ---------- Schluss ----------
story.append(Spacer(1, 8))
story.append(Paragraph("Hinweis", H2))
story.append(Paragraph(
    "Erfasst sind rund 45 Münchner Wohnungsbaugenossenschaften. Aufnahme-Status, Beträge und Verfügbarkeiten ändern sich &ndash; vor einer Bewerbung bitte auf der jeweiligen Website prüfen. "
    "Realistisch offen für neue, nicht-bahnnahe Bewerber ohne bestehende Verbindung sind v.a. <b>wagnis eG</b> und <b>Baugenossenschaft Hartmannshofen</b>; "
    "mit etwas Geduld auch <b>Progeno</b> und <b>Verein für Volkswohnungen</b> (Mitgliedschaft jeweils über die Wohnungsbewerbung). "
    "Mittelfristig (Bezug 2027/2028) ist die Projekt-Route in Teil 2 besonders aussichtsreich &ndash; v.a. <b>Kooperative Großstadt</b> (Projekt FREIMUNDO) und <b>Bürgerbauverein</b> (Eggarten); dort zahlt sich frühe Mitgliedschaft aus. Kurzfristig lohnt aktuell <b>Stadtimpuls eG</b> (freie 2-Zimmer-Wohnungen im Projekt Neufreimann).",
    BODY))

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.5 * cm,
    title="Muenchner Wohnungsbaugenossenschaften - Uebersicht",
    author="Übersicht Wohnungsbaugenossenschaften München",
)
doc.build(story)
print("PDF geschrieben:", OUT)

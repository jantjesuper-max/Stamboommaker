"""Draait dossiers, tijdsbeeld-gebeurtenissen en verhalen uit als PDF.

  py scripts/pdf.py persoon jansen-jan-hendriks-1813
  py scripts/pdf.py verhaal 1814-de-schuitenmaker         # deel van de naam mag
  py scripts/pdf.py tijdsbeeld 1825-stormvloed --open     # meteen openen
  py scripts/pdf.py persoon --alle                        # elk dossier een eigen pdf
  py scripts/pdf.py persoon --alle --bundel               # een boekje met alles erin
  py scripts/pdf.py alles --bundel                        # personen + tijdsbeeld + verhalen
  py scripts/pdf.py lijst                                 # wat valt er uit te draaien?

De PDF's komen in pdf/ (bouwproduct, staat niet in git). De markdown-bestanden
blijven de bron; hier wordt niets aan gewijzigd.

Hoe het werkt: het markdown-bestand wordt naar print-HTML vertaald (eigen kleine
renderer, geen afhankelijkheden) en die HTML gaat door Edge of Chrome in
headless-stand naar PDF. Beide browsers staan op elke Windows-werkplek, dus er
valt niets te installeren. Paginanummers en de voettekst worden er daarna met
PyMuPDF op gestempeld; ontbreekt PyMuPDF, dan blijft de PDF verder gewoon goed.

Lukt het starten van een browser niet, dan blijft de HTML staan met de melding
dat je er zelf Ctrl+P -> "Opslaan als PDF" op kunt doen. Met --html sla je de
PDF-stap sowieso over.
"""

import argparse
import datetime
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instellingen

WORTEL = Path(__file__).resolve().parent.parent
PERSONEN = WORTEL / "personen"
TIJDSBEELD = WORTEL / "tijdsbeeld"
VERHALEN = WORTEL / "boek" / "verhalen"
UITVOER = WORTEL / "pdf"

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]

SOORTEN = {
    "persoon": {
        "map": PERSONEN,
        "uitmap": "personen",
        "etiket": "Persoonsdossier",
        "meervoud": "persoonsdossiers",
        "kop": ["geboren", "overleden", "beroep", "lijn", "generatie", "status",
                "vader", "moeder", "partner", "kinderen", "woonplaatsen"],
    },
    "tijdsbeeld": {
        "map": TIJDSBEELD,
        "uitmap": "tijdsbeeld",
        "etiket": "Tijdsbeeld",
        "meervoud": "gebeurtenissen",
        "kop": ["periode", "soort", "plaatsen", "personen", "status", "landing", "gevonden"],
    },
    "verhaal": {
        "map": VERHALEN,
        "uitmap": "verhalen",
        "etiket": "Verhaal",
        "meervoud": "verhalen",
        "kop": ["rubriek", "deel", "lijn", "periode", "personen", "sterkte",
                "score", "landing", "gevonden"],
    },
}
ALIASSEN = {
    "personen": "persoon", "dossier": "persoon", "dossiers": "persoon",
    "verhalen": "verhaal",
    "tijdsbeelden": "tijdsbeeld", "gebeurtenis": "tijdsbeeld", "gebeurtenissen": "tijdsbeeld",
}

ETIKETTEN = {
    "geboren": "Geboren", "overleden": "Overleden", "beroep": "Beroep", "lijn": "Lijn",
    "generatie": "Generatie", "status": "Status", "vader": "Vader", "moeder": "Moeder",
    "partner": "Partner", "kinderen": "Kinderen", "woonplaatsen": "Woonplaatsen",
    "periode": "Periode", "soort": "Soort", "plaatsen": "Plaatsen", "personen": "Personen",
    "landing": "Landing", "gevonden": "Gevonden", "rubriek": "Rubriek", "deel": "Deel",
    "sterkte": "Sterkte", "score": "Score", "gebeurtenis": "Gebeurtenis",
}

STATUSSEN = {"\u2713": "ok", "\u25d0": "half", "?": "vraag", "\u26a0": "waak"}
WIKILINK = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")


# ---------------------------------------------------------------------------
# Inlezen
# ---------------------------------------------------------------------------

def lees_frontmatter(tekst):
    """Het YAML-achtige blok tussen de eerste twee '---'-regels, plus de romp.

    Bewust dezelfde simpele parser als in website/server.py: sleutel: waarde, en
    lijstjes met '- "..."'. Geen PyYAML-afhankelijkheid.
    """
    if not tekst.startswith("---"):
        return {}, tekst
    einde = tekst.find("\n---", 3)
    if einde == -1:
        return {}, tekst
    kop, romp = tekst[3:einde], tekst[einde + 4:]
    data, lijstsleutel = {}, None
    for regel in kop.splitlines():
        if not regel.strip() or regel.strip().startswith("#"):
            continue
        m_lijst = re.match(r"^\s+-\s*(.+)$", regel)
        if m_lijst and lijstsleutel:
            data.setdefault(lijstsleutel, []).append(
                m_lijst.group(1).strip().strip('"').strip("'"))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", regel)
        if not m:
            continue
        sleutel, waarde = m.group(1), m.group(2).strip()
        if not waarde.startswith(('"', "'")) and " #" in waarde:
            waarde = waarde.split(" #", 1)[0].strip()
        waarde = waarde.strip().strip('"').strip("'")
        if waarde == "":
            lijstsleutel, data[sleutel] = sleutel, data.get(sleutel, [])
        else:
            lijstsleutel, data[sleutel] = None, waarde
    return data, romp.lstrip("\n")


def namenregister():
    """id -> leesbare naam, zodat [[wikilinks]] in de PDF een naam worden."""
    register = {}
    for pad in PERSONEN.glob("*.md"):
        if pad.stem.startswith("_"):
            continue
        kop, _ = lees_frontmatter(pad.read_text(encoding="utf-8"))
        naam = str(kop.get("naam") or "").strip()
        register[pad.stem] = naam or verfraai_id(pad.stem)
    return register


def verfraai_id(ident):
    """jansen-jan-hendriks-1813 -> Jansen Jan Hendriks 1813 (noodgreep)."""
    return " ".join(w.capitalize() for w in str(ident).split("-"))


# ---------------------------------------------------------------------------
# Afstammingslijn: hoe komen we bij deze persoon uit?
# ---------------------------------------------------------------------------

_STAMBOOM = None


def stamboomgegevens():
    """id -> {naam, geboren, overleden, beroep, generatie, vader, moeder} plus
    een omgekeerde index kind-van, zodat we van een voorouder terug naar Jan
    kunnen lopen.

    De dossiers vormen een kwartierstaat: elk dossier wijst met `vader:` en
    `moeder:` naar boven. Om te laten zien HOE we bij iemand uitkomen moeten we
    juist naar beneden, dus die pijlen worden hier omgedraaid.
    """
    global _STAMBOOM
    if _STAMBOOM is not None:
        return _STAMBOOM
    personen, kind_van = {}, {}
    for pad in PERSONEN.glob("*.md"):
        if pad.stem.startswith("_"):
            continue
        kop, _ = lees_frontmatter(pad.read_text(encoding="utf-8"))

        def link(sleutel):
            m = re.search(r"\[\[([a-z0-9-]+)\]\]", str(kop.get(sleutel) or ""))
            return m.group(1) if m else None

        vader, moeder = link("vader"), link("moeder")
        try:
            generatie = int(str(kop.get("generatie") or "").strip())
        except ValueError:
            generatie = None
        personen[pad.stem] = {
            "naam": str(kop.get("naam") or "").strip() or verfraai_id(pad.stem),
            "geboren": str(kop.get("geboren") or "").strip(),
            "overleden": str(kop.get("overleden") or "").strip(),
            "beroep": str(kop.get("beroep") or "").strip(),
            "generatie": generatie,
            "vader": vader,
            "moeder": moeder,
        }
        # omgekeerd: wie is het kind van deze ouder, en langs welke kant
        if vader:
            kind_van.setdefault(vader, (pad.stem, "vader"))
        if moeder:
            kind_van.setdefault(moeder, (pad.stem, "moeder"))
    _STAMBOOM = (personen, kind_van)
    return _STAMBOOM


def korte_naam(naam):
    """'Hil Joostes (in het doopboek Hill; ...)' -> 'Hil Joostes'.

    In de frontmatter staan bij veel voorouders naamvarianten tussen haakjes.
    Nuttig in het dossier, te lang voor een kaartje in de afstammingslijn.
    """
    return re.sub(r"\s*\(.*$", "", str(naam)).strip() or str(naam).strip()


def jaartallen(gegevens):
    """'1785 - 1831' uit de frontmatter, zonder de plaatsnamen erachter."""
    def jaar(waarde):
        if not waarde or waarde.lower().startswith("onbekend"):
            return ""
        voorvoegsel = "ca. " if re.search(r"\bca\.", waarde) else ""
        m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", waarde)
        return (voorvoegsel + m.group(1)) if m else ""

    geb, ovl = jaar(gegevens.get("geboren")), jaar(gegevens.get("overleden"))
    if geb and ovl:
        return "%s - %s" % (geb, ovl)
    if geb:
        return "geb. %s" % geb
    if ovl:
        return "overl. %s" % ovl
    return ""


def afstammingslijn(ident, maximum=16):
    """De keten van Jan naar deze persoon, als lijst van onder naar boven.

    Elk element: (id, gegevens, kant) waarbij `kant` zegt hoe je bij DEZE
    persoon komt vanaf de vorige: 'vader', 'moeder', of None voor het beginpunt.
    Geeft een lege lijst als de persoon niet in de kwartierstaat hangt.
    """
    personen, kind_van = stamboomgegevens()
    if ident not in personen:
        return []
    keten, gezien = [(ident, personen[ident], None)], {ident}
    huidig = ident
    while len(keten) < maximum:
        stap = kind_van.get(huidig)
        if not stap:
            break
        kind, kant = stap
        if kind in gezien or kind not in personen:
            break
        gezien.add(kind)
        # het kind komt vóór de ouder te staan, en draagt de kant waarlangs
        # je van het kind naar die ouder loopt
        keten.insert(0, (kind, personen[kind], None))
        keten[1] = (keten[1][0], keten[1][1], kant)
        huidig = kind
    return keten


# ---------------------------------------------------------------------------
# Markdown -> HTML (eigen renderer; dekt wat er in dit project gebruikt wordt)
# ---------------------------------------------------------------------------

def esc(tekst):
    return html.escape(str(tekst), quote=False)


# Een knipsel of scan in de tekst: ![bijschrift](pad). Het bijschrift mag één niveau rechte
# haken bevatten ("[...]" voor een weglating), net als in de website.
AFBEELDING = re.compile(r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]+)[^)]*\)")


def beeldbron(src, ctx):
    """Maakt van een markdown-beeldpad iets wat de headless browser kan openen.

    De HTML wordt als file:// geopend vanuit pdf/<soort>/, dus een relatief pad als
    `beeld/x.jpg` zou daar niets vinden. Het wordt opgelost ten opzichte van de map van
    het markdown-bestand (ctx["basismap"]) en als absoluut file://-pad meegegeven.
    Webadressen en paden die niet bestaan blijven zoals ze zijn.
    """
    if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
        return src
    basis = ctx.get("basismap")
    if basis is None:
        return src
    pad = (Path(basis) / urllib.parse.unquote(src)).resolve()
    return pad.as_uri() if pad.is_file() else src


def img_html(alt, src, ctx):
    return '<img src="%s" alt="%s">' % (html.escape(beeldbron(src, ctx)), html.escape(alt))


def inline(tekst, ctx):
    """Vet, cursief, code, links, wikilinks, voetnootverwijzingen, doorhalingen, beelden."""
    codes = []

    def bewaar_code(m):
        codes.append(m.group(1))
        return "\x00c%d\x00" % (len(codes) - 1)

    tekst = re.sub(r"`([^`]+)`", bewaar_code, tekst)
    # afbeeldingen vóór de links, anders wordt ![x](y) een uitroepteken met een link
    beelden = []

    def bewaar_beeld(m):
        beelden.append(img_html(m.group(1), m.group(2), ctx))
        return "\x00b%d\x00" % (len(beelden) - 1)

    tekst = AFBEELDING.sub(bewaar_beeld, tekst)
    tekst = esc(tekst)

    def wikilink(m):
        doel = m.group(1).strip()
        toon = (m.group(2) or "").strip() or ctx["namen"].get(doel) or verfraai_id(doel)
        return '<span class="wl">%s</span>' % esc(toon)

    tekst = WIKILINK.sub(wikilink, tekst)

    def noot(m):
        merk = m.group(1)
        if merk not in ctx["nootvolgorde"]:
            ctx["nootvolgorde"].append(merk)
        return '<sup class="noot">%d</sup>' % (ctx["nootvolgorde"].index(merk) + 1)

    tekst = re.sub(r"\[\^([^\]\s]+)\]", noot, tekst)
    tekst = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)",
                   lambda m: '<a href="%s">%s</a>' % (esc(m.group(2)), m.group(1)), tekst)
    tekst = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", tekst, flags=re.S)
    tekst = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>",
                   tekst, flags=re.S)
    tekst = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>",
                   tekst, flags=re.S)
    tekst = re.sub(r"~~(.+?)~~", r"<del>\1</del>", tekst, flags=re.S)
    tekst = re.sub(r"&lt;br\s*/?&gt;", "<br>", tekst)
    tekst = re.sub(r"\x00c(\d+)\x00",
                   lambda m: "<code>%s</code>" % esc(codes[int(m.group(1))]), tekst)
    tekst = re.sub(r"\x00b(\d+)\x00", lambda m: beelden[int(m.group(1))], tekst)
    return tekst


def statusbadge(cel):
    """Een cel die alleen een betrouwbaarheidscode bevat wordt een gekleurd merkje."""
    kaal = cel.strip()
    if kaal in STATUSSEN:
        return '<span class="st st-%s">%s</span>' % (STATUSSEN[kaal], esc(kaal))
    return None


def splits_rij(regel):
    regel = regel.strip()
    if regel.startswith("|"):
        regel = regel[1:]
    if regel.endswith("|"):
        regel = regel[:-1]
    return [c.strip() for c in regel.split("|")]


SCHEIDING = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
LIJSTREGEL = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
STREEP = re.compile(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$")


def markdown_naar_html(md, ctx):
    regels = md.replace("\r\n", "\n").split("\n")
    uit, i = [], 0
    while i < len(regels):
        regel = regels[i]
        kaal = regel.strip()

        if not kaal:
            i += 1
            continue

        # voetnootdefinitie: [^1]: tekst, eventueel met vervolgregels
        m = re.match(r"^\[\^([^\]\s]+)\]:\s*(.*)$", kaal)
        if m:
            merk, inhoud = m.group(1), [m.group(2)]
            i += 1
            while i < len(regels) and regels[i].strip() and \
                    not re.match(r"^\[\^[^\]\s]+\]:", regels[i].strip()):
                inhoud.append(regels[i].strip())
                i += 1
            ctx["noten"][merk] = " ".join(inhoud).strip()
            continue

        # tabel
        if kaal.startswith("|") and i + 1 < len(regels) and SCHEIDING.match(regels[i + 1]):
            kopcellen = splits_rij(regel)
            i += 2
            lichaam = []
            while i < len(regels) and regels[i].strip().startswith("|"):
                lichaam.append(splits_rij(regels[i]))
                i += 1
            uit.append("<table><thead><tr>" +
                       "".join("<th>%s</th>" % inline(c, ctx) for c in kopcellen) +
                       "</tr></thead><tbody>")
            for rij in lichaam:
                cellen = []
                for cel in rij:
                    badge = statusbadge(cel)
                    cellen.append('<td class="mid">%s</td>' % badge if badge
                                  else "<td>%s</td>" % inline(cel, ctx))
                uit.append("<tr>" + "".join(cellen) + "</tr>")
            uit.append("</tbody></table>")
            continue

        # kop
        m = re.match(r"^(#{1,6})\s+(.*)$", kaal)
        if m:
            n = len(m.group(1))
            uit.append("<h%d>%s</h%d>" % (n, inline(m.group(2), ctx), n))
            i += 1
            continue

        # losse afbeelding op een eigen regel: een figuur met het bijschrift eronder
        m = AFBEELDING.fullmatch(kaal)
        if m:
            uit.append('<figure class="beeld">%s<figcaption>%s</figcaption></figure>'
                       % (img_html(m.group(1), m.group(2), ctx), inline(m.group(1), ctx)))
            i += 1
            continue

        # streep
        if STREEP.match(kaal):
            uit.append("<hr>")
            i += 1
            continue

        # citaat
        if kaal.startswith(">"):
            blok = []
            while i < len(regels) and regels[i].strip().startswith(">"):
                blok.append(re.sub(r"^\s*>\s?", "", regels[i]))
                i += 1
            uit.append("<blockquote>" + markdown_naar_html("\n".join(blok), ctx) +
                       "</blockquote>")
            continue

        # lijst (met nesting op inspringing)
        if LIJSTREGEL.match(regel):
            i = lijst(regels, i, uit, ctx)
            continue

        # alinea
        blok = []
        while i < len(regels):
            r = regels[i]
            if not r.strip() or r.strip().startswith(("|", ">", "#")) or \
                    LIJSTREGEL.match(r) or STREEP.match(r.strip()) or \
                    re.match(r"^\[\^[^\]\s]+\]:", r.strip()):
                break
            blok.append(r.strip())
            i += 1
        if blok:
            uit.append("<p>%s</p>" % inline(" ".join(blok), ctx))
        else:
            i += 1  # veiligheidsklep: nooit blijven hangen op dezelfde regel
    return "\n".join(uit)


def lijst(regels, i, uit, ctx):
    """Bouwt een (genest) lijstje op; geeft de nieuwe regelpositie terug."""
    stapel = []  # (inspringing, tag)

    def sluit_tot(diepte):
        while len(stapel) > 1 and stapel[-1][0] > diepte:
            uit.append("</li></%s>" % stapel.pop()[1])

    while i < len(regels):
        regel = regels[i]
        if not regel.strip():
            volgende = regels[i + 1] if i + 1 < len(regels) else ""
            if not LIJSTREGEL.match(volgende):
                break
            i += 1
            continue
        m = LIJSTREGEL.match(regel)
        if not m:
            if stapel and regel.startswith(("  ", "\t")):  # vervolgregel van een punt
                uit.append(" " + inline(regel.strip(), ctx))
                i += 1
                continue
            break
        inspringing, merk, tekst = len(m.group(1)), m.group(2), m.group(3)
        tag = "ol" if merk[0].isdigit() else "ul"

        if not stapel or inspringing > stapel[-1][0]:
            stapel.append((inspringing, tag))
            uit.append("<%s>" % tag)
        else:
            sluit_tot(inspringing)
            uit.append("</li>")

        klasse = ""
        m_vink = re.match(r"^\[([ xX])\]\s*(.*)$", tekst)
        if m_vink:
            dicht = m_vink.group(1).lower() == "x"
            klasse = ' class="vink dicht"' if dicht else ' class="vink"'
            hokje = "\u2612" if dicht else "\u2610"
            tekst = '<span class="hokje">%s</span>%s' % (hokje, inline(m_vink.group(2), ctx))
        else:
            tekst = inline(tekst, ctx)
        uit.append("<li%s>%s" % (klasse, tekst))
        i += 1

    while stapel:
        uit.append("</li></%s>" % stapel.pop()[1])
    return i


# ---------------------------------------------------------------------------
# Document opbouwen
# ---------------------------------------------------------------------------

class Document:
    def __init__(self, soort, pad, namen):
        self.soort = soort
        self.pad = pad
        self.ident = pad.stem
        tekst = pad.read_text(encoding="utf-8")
        self.kop, romp = lees_frontmatter(tekst)
        self.ctx = {"namen": namen, "noten": {}, "nootvolgorde": [],
                    "basismap": pad.parent}  # relatieve beeldpaden lossen hiertegen op

        # de eerste H1 uit de romp is de mooiste titel; die komt in de kopregel
        m = re.search(r"^#\s+(.+)$", romp, re.M)
        if m:
            self.titel = m.group(1).strip()
            romp = romp[:m.start()] + romp[m.end():]
        else:
            self.titel = str(self.kop.get("titel") or self.kop.get("naam") or
                             verfraai_id(self.ident))
        self.ondertitel = ""
        if self.soort == "persoon":
            naam = str(self.kop.get("naam") or "").strip()
            if naam and naam not in self.titel:
                self.ondertitel = naam
        self.romp_html = markdown_naar_html(romp, self.ctx)

    def kopkaart(self):
        velden = []
        for sleutel in SOORTEN[self.soort]["kop"]:
            waarde = self.kop.get(sleutel)
            if not waarde:
                continue
            if isinstance(waarde, list):
                getoond = "<br>".join(inline(str(w), self.ctx) for w in waarde)
            else:
                getoond = statusbadge(str(waarde)) or inline(str(waarde), self.ctx)
            etiket = ETIKETTEN.get(sleutel, sleutel.capitalize())
            velden.append('<div class="veld"><dt>%s</dt><dd>%s</dd></div>'
                          % (esc(etiket), getoond))
        if not velden:
            return ""
        return '<dl class="kaart">' + "".join(velden) + "</dl>"

    def noten_html(self):
        if not self.ctx["nootvolgorde"]:
            return ""
        punten = []
        for merk in self.ctx["nootvolgorde"]:
            tekst = self.ctx["noten"].get(merk, "[noot ontbreekt in het bronbestand]")
            punten.append("<li>%s</li>" % inline(tekst, self.ctx))
        return ('<section class="noten"><h2>Noten</h2><ol>' + "".join(punten) +
                "</ol></section>")

    def lijn_html(self):
        """De afstammingslijn onder aan het dossier: hoe komen we bij deze mens uit?

        Alleen de hoofdpersonen van de lijn, geen partners en geen zijtakken —
        dat is precies wat een kwartierstaat is, en het houdt de voet leesbaar.
        """
        if self.soort != "persoon":
            return ""
        keten = afstammingslijn(self.ident)
        if len(keten) < 2:
            return ""
        rijen = []
        for stap, (ident, gegevens, kant) in enumerate(keten):
            hier = ident == self.ident
            if kant:
                # noem het kind erbij, anders moet de lezer terugtellen wiens
                # vader of moeder dit ook alweer is
                kind = korte_naam(keten[stap - 1][1].get("naam") or "").split(" ")[0]
                rijen.append('<div class="lijn-schakel"><span class="lijn-pijl"></span>'
                             '<span class="lijn-kant">%s van %s</span></div>'
                             % (esc(kant), esc(kind)))
            generatie = gegevens.get("generatie")
            merk = ("g%d" % generatie) if generatie is not None else "&mdash;"
            jaren = jaartallen(gegevens)
            beroep = gegevens.get("beroep") or ""
            if beroep.lower().startswith("onbekend"):
                beroep = ""
            if len(beroep) > 44:
                beroep = beroep[:41].rstrip(" ,;") + "…"
            regels = [x for x in (esc(jaren), esc(beroep)) if x]
            rijen.append(
                '<div class="lijn-kaart%s">'
                '<span class="lijn-gen">%s</span>'
                '<span class="lijn-naam">%s</span>'
                '<span class="lijn-bij">%s</span>'
                "</div>"
                % (" hier" if hier else "", merk,
                   esc(korte_naam(gegevens.get("naam") or verfraai_id(ident))),
                   " &middot; ".join(regels)))
        stappen = len(keten) - 1
        # de keten begint bij de diepste nakomeling die een dossier heeft — dat
        # hoeft Jan niet te zijn, dus noem gewoon wie het wél is
        onderschrift = (
            "Van %s naar %s: %s %s omhoog. Alleen de rechte lijn; "
            "partners, broers en zusters staan er niet in."
            % (esc(korte_naam(keten[0][1].get("naam") or verfraai_id(keten[0][0]))),
               esc(korte_naam(keten[-1][1].get("naam") or verfraai_id(self.ident))),
               stappen, "stap" if stappen == 1 else "stappen"))
        return ('<section class="afstamming"><h2>Hoe komen we hier uit?</h2>'
                '<div class="lijn">' + "".join(rijen) + "</div>"
                '<p class="lijn-onderschrift">' + onderschrift + "</p></section>")

    def html(self):
        stukken = ['<article class="doc" id="%s">' % esc(self.ident),
                   '<div class="etiket">%s</div>' % esc(SOORTEN[self.soort]["etiket"]),
                   "<h1>%s</h1>" % inline(self.titel, self.ctx)]
        if self.ondertitel:
            stukken.append('<p class="ondertitel">%s</p>' % inline(self.ondertitel, self.ctx))
        stukken.append(self.kopkaart())
        stukken.append(self.romp_html)
        stukken.append(self.noten_html())
        stukken.append(self.lijn_html())
        stukken.append('<p class="herkomst">Bron van deze uitdraai: <code>%s</code></p>'
                       % esc(self.pad.relative_to(WORTEL).as_posix()))
        stukken.append("</article>")
        return "\n".join(s for s in stukken if s)


# ---------------------------------------------------------------------------
# Opmaak
# ---------------------------------------------------------------------------

STIJL = """
@page { size: A4; margin: 20mm 17mm 20mm 17mm; }
:root {
  --inkt: #241f18; --inkt-zacht: #5f5646; --inkt-vaag: #8b8172;
  --groen: #2e5c46; --groen-donker: #1f4433; --groen-waas: #eef3ec;
  --rand: #d5cab3; --rand-zacht: #e6ddc8; --papier-zacht: #faf6ea;
  --ok: #2e7d32; --half: #b26a00; --vraag: #6f6f6f; --waak: #c62828;
  --serif: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
  --sans: "Segoe UI", system-ui, sans-serif;
  --mono: Consolas, "Cascadia Mono", "Courier New", monospace;
}
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--serif); font-size: 10.2pt; line-height: 1.5;
  color: var(--inkt); background: #fff;
}
.doc { break-before: page; }
.doc:first-of-type { break-before: auto; }

.etiket {
  font-family: var(--sans); font-size: 7.4pt; font-weight: 600;
  letter-spacing: .16em; text-transform: uppercase; color: var(--groen);
  border-bottom: 1.6pt solid var(--groen); padding-bottom: 3pt; margin-bottom: 9pt;
}
h1 {
  font-size: 19pt; line-height: 1.2; color: var(--groen-donker);
  margin: 0 0 2pt; font-weight: 600; break-after: avoid;
}
.ondertitel { margin: 0 0 2pt; color: var(--inkt-zacht); font-style: italic; font-size: 10.5pt; }
h2 {
  font-size: 12.4pt; color: var(--groen-donker); margin: 15pt 0 5pt;
  padding-bottom: 2pt; border-bottom: .6pt solid var(--rand-zacht); break-after: avoid;
}
h3 { font-size: 10.8pt; color: var(--groen-donker); margin: 11pt 0 3pt; break-after: avoid; }
h4, h5, h6 { font-size: 10.2pt; margin: 9pt 0 2pt; break-after: avoid; }
p { margin: 0 0 6pt; orphans: 2; widows: 2; text-align: justify; }
strong { font-weight: 600; }
del { color: var(--inkt-vaag); }
a { color: var(--groen); text-decoration: none; }
code { font-family: var(--mono); font-size: .85em; background: var(--papier-zacht);
       border: .4pt solid var(--rand-zacht); border-radius: 2pt; padding: 0 2pt; }
hr { border: 0; border-top: .6pt solid var(--rand); margin: 10pt 0; }
blockquote {
  margin: 6pt 0 6pt 6pt; padding: 3pt 0 3pt 8pt;
  border-left: 2pt solid var(--rand); color: var(--inkt-zacht); font-style: italic;
}

/* knipsels, scans en andere afbeeldingen in de tekst */
figure.beeld { margin: 8pt 0 10pt; break-inside: avoid; }
figure.beeld img, p img { display: block; max-width: 100%; height: auto;
  border: .5pt solid var(--rand-zacht); }
figure.beeld figcaption { font-family: var(--sans); font-size: 7.8pt; line-height: 1.35;
  color: var(--inkt-vaag); margin-top: 3pt; text-align: left; }

/* kopkaart met de frontmatter */
.kaart {
  margin: 9pt 0 12pt; padding: 8pt 10pt; background: var(--papier-zacht);
  border: .5pt solid var(--rand-zacht); border-left: 2.5pt solid var(--groen);
  border-radius: 2pt; display: grid; grid-template-columns: 1fr 1fr;
  gap: 3pt 16pt; break-inside: avoid;
}
.kaart .veld { display: grid; grid-template-columns: 23mm 1fr; gap: 5pt; align-items: baseline; }
.kaart dt {
  font-family: var(--sans); font-size: 7.2pt; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--inkt-vaag); padding-top: .8pt;
}
.kaart dd { margin: 0; font-size: 9.4pt; }

table {
  width: 100%; border-collapse: collapse; margin: 7pt 0 10pt;
  font-size: 8.6pt; line-height: 1.35;
}
thead { display: table-header-group; }
th {
  background: var(--groen-waas); color: var(--groen-donker); text-align: left;
  font-family: var(--sans); font-size: 7.4pt; font-weight: 600; letter-spacing: .05em;
  text-transform: uppercase; padding: 3.5pt 5pt; border: .5pt solid var(--rand-zacht);
}
td { padding: 3.5pt 5pt; border: .5pt solid var(--rand-zacht); vertical-align: top;
     overflow-wrap: break-word; }
td code { overflow-wrap: anywhere; }
td.mid { text-align: center; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) { background: #fcfaf3; }

ul, ol { margin: 0 0 7pt; padding-left: 14pt; }
li { margin-bottom: 2.5pt; }
li.vink { list-style: none; margin-left: -12pt; }
li.vink .hokje { display: inline-block; width: 11pt; color: var(--half); font-size: 10pt; }
li.vink.dicht .hokje { color: var(--ok); }
li.vink.dicht { color: var(--inkt-zacht); }

.wl { font-variant: small-caps; letter-spacing: .02em;
      border-bottom: .5pt dotted var(--rand); }
sup.noot { font-size: .7em; color: var(--groen); font-weight: 600; }
.noten { margin-top: 14pt; padding-top: 6pt; border-top: .6pt solid var(--rand-zacht);
         font-size: 8.6pt; color: var(--inkt-zacht); }
.noten h2 { font-size: 9.6pt; border: 0; margin: 0 0 4pt; }

.st { display: inline-block; min-width: 12pt; text-align: center; font-weight: 700;
      font-size: 9.5pt; }
.st-ok { color: var(--ok); } .st-half { color: var(--half); }
.st-vraag { color: var(--vraag); } .st-waak { color: var(--waak); }

/* afstammingslijn onder aan een persoonsdossier */
.afstamming { margin-top: 16pt; padding-top: 7pt;
              border-top: .6pt solid var(--rand-zacht);
              break-inside: avoid; }
.afstamming h2 { font-size: 9.6pt; border: 0; margin: 0 0 7pt; }
.lijn { display: flex; flex-direction: column; align-items: stretch; }
.lijn-kaart {
  display: flex; align-items: baseline; gap: 7pt;
  border: .6pt solid var(--rand); border-left: 2.4pt solid var(--rand);
  border-radius: 3pt; background: var(--papier-zacht);
  padding: 3.4pt 8pt; }
.lijn-kaart.hier {
  border-color: var(--groen); border-left-color: var(--groen);
  background: var(--groen-waas); }
.lijn-gen {
  flex: none; min-width: 17pt; text-align: center;
  font-family: var(--sans); font-size: 7.2pt; font-weight: 700;
  letter-spacing: .04em; color: var(--inkt-vaag); }
.lijn-kaart.hier .lijn-gen { color: var(--groen); }
.lijn-naam { font-size: 9.4pt; font-weight: 600; color: var(--inkt); }
.lijn-kaart.hier .lijn-naam { color: var(--groen-donker); }
.lijn-bij {
  margin-left: auto; text-align: right;
  font-family: var(--sans); font-size: 7.4pt; color: var(--inkt-zacht); }
/* het verbindingsstuk tussen twee kaarten: streepje plus het woord vader/moeder */
.lijn-schakel {
  display: flex; align-items: center; gap: 5pt;
  padding: 1.6pt 0 1.6pt 8.5pt; }
.lijn-pijl {
  display: inline-block; width: .6pt; height: 9pt;
  background: var(--rand); flex: none; }
.lijn-kant {
  font-family: var(--sans); font-size: 6.9pt; letter-spacing: .05em;
  text-transform: uppercase; color: var(--inkt-vaag); }
.lijn-onderschrift {
  margin: 7pt 0 0; font-size: 7.6pt; color: var(--inkt-vaag); }

.herkomst { margin-top: 12pt; padding-top: 4pt; border-top: .5pt dotted var(--rand);
            font-size: 7.6pt; color: var(--inkt-vaag); text-align: left; }
.herkomst code { background: none; border: 0; padding: 0; }

/* omslag en inhoudsopgave van een bundel */
.omslag { break-after: page; padding-top: 42mm; text-align: center; }
.omslag .merk { font-family: var(--sans); font-size: 8pt; letter-spacing: .3em;
                text-transform: uppercase; color: var(--groen); }
.omslag h1 { font-size: 30pt; margin: 10pt 0 4pt; border: 0; }
.omslag .onder { font-size: 12pt; color: var(--inkt-zacht); font-style: italic; }
.omslag .streep { width: 34mm; height: 1.6pt; background: var(--groen); margin: 16pt auto; }
.omslag .telling { font-family: var(--sans); font-size: 9pt; color: var(--inkt-zacht);
                   line-height: 1.9; }
.omslag .datum { margin-top: 26mm; font-family: var(--sans); font-size: 8pt;
                 color: var(--inkt-vaag); }
.inhoud h2 { font-size: 13pt; }
.inhoud ol { list-style: none; padding: 0; margin: 0; }
.inhoud li { display: flex; align-items: baseline; gap: 4pt; margin-bottom: 3.2pt;
             font-size: 9.6pt; break-inside: avoid; }
.inhoud .naam { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.inhoud .stip { flex: 1; border-bottom: .5pt dotted var(--rand); transform: translateY(-2pt); }
.inhoud .nr { font-family: var(--sans); font-size: 8.4pt; color: var(--inkt-zacht); }
.inhoud .groepkop { font-family: var(--sans); font-size: 7.6pt; font-weight: 600;
                    letter-spacing: .12em; text-transform: uppercase; color: var(--groen);
                    margin: 10pt 0 4pt; }
"""


def bouw_html(titel, lichaam):
    return ('<!doctype html>\n<html lang="nl"><head><meta charset="utf-8">'
            "<title>%s</title><style>%s</style></head><body>\n%s\n</body></html>\n"
            % (esc(titel), STIJL, lichaam))


# ---------------------------------------------------------------------------
# HTML -> PDF via een headless browser
# ---------------------------------------------------------------------------

BROWSERPADEN = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def zoek_browser():
    eigen = os.environ.get("STAMBOOM_BROWSER")
    if eigen and Path(eigen).exists():
        return eigen
    for pad in BROWSERPADEN:
        if Path(pad).exists():
            return pad
    for naam in ("msedge", "chrome", "chromium", "google-chrome"):
        gevonden = shutil.which(naam)
        if gevonden:
            return gevonden
    return None


def html_naar_pdf(browser, html_pad, pdf_pad, stil=False):
    """Drukt een HTML-bestand af naar PDF met Edge/Chrome in headless-stand."""
    pdf_pad.parent.mkdir(parents=True, exist_ok=True)
    if pdf_pad.exists():
        pdf_pad.unlink()
    with tempfile.TemporaryDirectory(prefix="stamboom-pdf-") as profiel:
        # eigen profielmap: anders geeft een al draaiende browser de opdracht door
        # aan het bestaande venster en wordt er niets afgedrukt
        basis = [
            "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--disable-sync", "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw", "--virtual-time-budget=8000",
            "--user-data-dir=" + profiel,
            "--print-to-pdf=" + str(pdf_pad), html_pad.as_uri(),
        ]
        for stand in ("--headless=new", "--headless"):
            try:
                klaar = subprocess.run([browser, stand] + basis, capture_output=True,
                                       text=True, timeout=180)
            except subprocess.TimeoutExpired:
                if not stil:
                    print("  browser reageerde niet binnen 3 minuten")
                return False
            if pdf_pad.exists() and pdf_pad.stat().st_size > 1000:
                return True
            if not stil and (klaar.stderr or "").strip():
                print("  browser (%s): %s" % (stand, klaar.stderr.strip().splitlines()[-1]))
    return False


def stempel(pdf_pad, voetlinks, sla_over=0):
    """Zet paginanummers en een voettekst op elke bladzijde (PyMuPDF)."""
    try:
        import fitz
    except ImportError:
        return False
    # het ingebouwde Times heeft een Latin-1-encoding: typografische tekens eerst plat
    veilig = (voetlinks.replace("\u2014", "-").replace("\u2013", "-")
              .replace("\u2019", "'").replace("\u2018", "'")
              .replace("\u201c", '"').replace("\u201d", '"'))
    veilig = "".join(c if ord(c) < 256 else "?" for c in veilig)
    if len(veilig) > 95:
        veilig = veilig[:92] + "..."
    grijs = (0.56, 0.53, 0.47)
    doc = fitz.open(pdf_pad)
    totaal = doc.page_count
    for nr in range(sla_over, totaal):
        blad = doc[nr]
        y = blad.rect.height - 30
        blad.draw_line(fitz.Point(48, y - 9), fitz.Point(blad.rect.width - 48, y - 9),
                       color=(0.84, 0.79, 0.70), width=0.4)
        blad.insert_text(fitz.Point(48, y), veilig, fontname="times-roman",
                         fontsize=7.2, color=grijs)
        rechts = "%d / %d" % (nr + 1, totaal)
        breedte = fitz.get_text_length(rechts, fontname="times-roman", fontsize=7.2)
        blad.insert_text(fitz.Point(blad.rect.width - 48 - breedte, y), rechts,
                         fontname="times-roman", fontsize=7.2, color=grijs)
    tijdelijk = Path(str(pdf_pad) + ".tmp")
    doc.save(tijdelijk, garbage=3, deflate=True)
    doc.close()
    tijdelijk.replace(pdf_pad)
    return True


def paginas(pdf_pad):
    try:
        import fitz
    except ImportError:
        return None
    with fitz.open(pdf_pad) as doc:
        return doc.page_count


# ---------------------------------------------------------------------------
# Documenten kiezen
# ---------------------------------------------------------------------------

def bestanden(soort):
    return sorted(p for p in SOORTEN[soort]["map"].glob("*.md")
                  if not p.stem.startswith("_"))


def kies(soort, zoekterm):
    """Exacte id, anders alles wat de zoekterm bevat (in id, naam of titel)."""
    kandidaten = bestanden(soort)
    for pad in kandidaten:
        if pad.stem == zoekterm:
            return [pad]
    term = zoekterm.lower()
    treffers = [p for p in kandidaten if term in p.stem.lower()]
    if not treffers:
        for pad in kandidaten:
            kop, _ = lees_frontmatter(pad.read_text(encoding="utf-8"))
            etiket = str(kop.get("naam") or kop.get("titel") or "").lower()
            if term in etiket:
                treffers.append(pad)
    return treffers


def sorteersleutel(doc):
    """Personen op generatie (dichtstbij eerst), de rest op bestandsnaam (= jaartal)."""
    volgorde = list(SOORTEN).index(doc.soort)
    if doc.soort == "persoon":
        try:
            generatie = int(str(doc.kop.get("generatie", "99")).strip())
        except ValueError:
            generatie = 99
        return (volgorde, generatie, str(doc.kop.get("naam") or doc.titel).lower())
    return (volgorde, 0, doc.ident)


# ---------------------------------------------------------------------------
# Voor de website: één document op verzoek, met cache
# ---------------------------------------------------------------------------

def maak_pdf(soort, ident, vernieuw=False):
    """Bouwt (of hergebruikt) de PDF voor één document en geeft het pad terug.

    De cache is simpel: bestaat pdf/<soort>/<id>.pdf en is die nieuwer dan het
    markdown-bestand, dan wordt die teruggegeven zonder de browser te starten.
    Gooit FileNotFoundError bij een onbekend id en RuntimeError als er geen
    browser is of het afdrukken mislukt.
    """
    soort = ALIASSEN.get(soort, soort)
    if soort not in SOORTEN:
        raise FileNotFoundError("onbekende soort: %s" % soort)
    if not re.fullmatch(r"[a-z0-9-]+", str(ident) or ""):
        raise FileNotFoundError(ident)
    bron = SOORTEN[soort]["map"] / (ident + ".md")
    if not bron.is_file():
        raise FileNotFoundError(ident)
    pdf_pad = UITVOER / SOORTEN[soort]["uitmap"] / (ident + ".pdf")
    # Ook een nieuwere versie van dit script maakt de cache ongeldig: anders blijft een
    # PDF die vóór een reparatie van de renderer is gemaakt gewoon terugkomen zolang het
    # markdown-bestand niet verandert.
    nieuwste_bron = max(bron.stat().st_mtime, Path(__file__).stat().st_mtime)
    if not vernieuw and pdf_pad.is_file() and pdf_pad.stat().st_mtime >= nieuwste_bron:
        return pdf_pad
    browser = zoek_browser()
    if browser is None:
        raise RuntimeError("geen Edge of Chrome gevonden om de PDF mee te maken")
    doc = Document(soort, bron, namenregister())
    pdf_pad.parent.mkdir(parents=True, exist_ok=True)
    html_pad = pdf_pad.with_suffix(".html")
    html_pad.write_text(bouw_html(doc.titel, doc.html()), encoding="utf-8")
    try:
        if not html_naar_pdf(browser, html_pad, pdf_pad, stil=True):
            raise RuntimeError("de browser kon geen PDF maken van %s" % ident)
        stempel(pdf_pad, "%s: %s" % (SOORTEN[soort]["etiket"], doc.titel))
    finally:
        html_pad.unlink(missing_ok=True)
    return pdf_pad


# ---------------------------------------------------------------------------
# Opdrachten
# ---------------------------------------------------------------------------

def vandaag_lang():
    d = datetime.date.today()
    return "%d %s %d" % (d.day, MAANDEN[d.month - 1], d.year)


def toon_pad(pad):
    try:
        return pad.relative_to(WORTEL).as_posix()
    except ValueError:
        return str(pad)


def uitdraai_los(docs, uitmap, browser, alleen_html, open_na):
    gemaakt = []
    for doc in docs:
        doelmap = uitmap / SOORTEN[doc.soort]["uitmap"]
        doelmap.mkdir(parents=True, exist_ok=True)
        html_pad = doelmap / (doc.ident + ".html")
        html_pad.write_text(bouw_html(doc.titel, doc.html()), encoding="utf-8")
        if alleen_html:
            print("  HTML  %s" % toon_pad(html_pad))
            gemaakt.append(html_pad)
            continue
        pdf_pad = doelmap / (doc.ident + ".pdf")
        if html_naar_pdf(browser, html_pad, pdf_pad):
            stempel(pdf_pad, "%s: %s" % (SOORTEN[doc.soort]["etiket"], doc.titel))
            html_pad.unlink(missing_ok=True)
            n = paginas(pdf_pad)
            print("  PDF   %s%s" % (toon_pad(pdf_pad), "  (%d blz.)" % n if n else ""))
            gemaakt.append(pdf_pad)
        else:
            print("  MISLUKT voor %s - de HTML blijft staan: %s" % (doc.ident, toon_pad(html_pad)))
            print("          open die en druk Ctrl+P -> Opslaan als PDF")
    if gemaakt and open_na:
        os.startfile(gemaakt[0])
    return gemaakt


def omslag_html(docs, bladnummers, titel, onder):
    per_soort = {}
    for doc in docs:
        per_soort.setdefault(doc.soort, []).append(doc)
    telling = " &middot; ".join("%d %s" % (len(v), SOORTEN[k]["meervoud"])
                               for k, v in per_soort.items())
    stukken = [
        '<section class="omslag">',
        '<div class="merk">%s</div>' % esc(instellingen.website_titel()),
        "<h1>%s</h1>" % esc(titel),
        '<div class="onder">%s</div>' % esc(onder),
        '<div class="streep"></div>',
        '<div class="telling">%s</div>' % telling,
        '<div class="datum">Uitgedraaid op %s</div>' % esc(vandaag_lang()),
        "</section>",
        '<section class="inhoud"><h2>Inhoud</h2>',
    ]
    huidige, punten = None, []
    for doc, blad in zip(docs, bladnummers):
        if doc.soort != huidige:
            if punten:
                stukken.append("<ol>" + "".join(punten) + "</ol>")
                punten = []
            huidige = doc.soort
            stukken.append('<div class="groepkop">%s</div>' % esc(SOORTEN[huidige]["etiket"]))
        punten.append('<li><span class="naam">%s</span><span class="stip"></span>'
                      '<span class="nr">%s</span></li>' % (esc(doc.titel), blad))
    if punten:
        stukken.append("<ol>" + "".join(punten) + "</ol>")
    stukken.append("</section>")
    return "\n".join(stukken)


def uitdraai_bundel(docs, uitmap, browser, naam, titel, onder, alleen_html, open_na):
    uitmap.mkdir(parents=True, exist_ok=True)

    if alleen_html:
        lichaam = (omslag_html(docs, [""] * len(docs), titel, onder) +
                   "\n".join(d.html() for d in docs))
        html_pad = uitmap / (naam + ".html")
        html_pad.write_text(bouw_html(titel, lichaam), encoding="utf-8")
        print("  HTML  %s" % toon_pad(html_pad))
        return html_pad

    try:
        import fitz
    except ImportError:
        print("  Bundelen heeft PyMuPDF nodig (py -m pip install pymupdf).")
        print("  Zonder dat: laat --bundel weg, of gebruik --html en druk zelf af.")
        return None

    werkmap = uitmap / ".werk"
    if werkmap.exists():
        shutil.rmtree(werkmap, ignore_errors=True)
    werkmap.mkdir(parents=True)

    print("  %d document(en) afdrukken..." % len(docs))
    delen = []
    for nr, doc in enumerate(docs, 1):
        h = werkmap / ("%03d.html" % nr)
        p = werkmap / ("%03d.pdf" % nr)
        h.write_text(bouw_html(doc.titel, doc.html()), encoding="utf-8")
        if not html_naar_pdf(browser, h, p):
            print("  MISLUKT voor %s - bundel afgebroken" % doc.ident)
            return None
        delen.append(p)
        if nr % 10 == 0 or nr == len(docs):
            print("    %d/%d" % (nr, len(docs)))

    lengtes = [paginas(p) for p in delen]

    # de inhoudsopgave twee keer bouwen: de bladnummers hangen af van hoe dik het
    # voorwerk zelf wordt, dus doorrekenen tot het klopt
    voorwerk, voorwerk_pdf = 1, None
    for _ in range(4):
        start, bladnummers = voorwerk + 1, []
        for lengte in lengtes:
            bladnummers.append(start)
            start += lengte
        h = werkmap / "000-omslag.html"
        p = werkmap / "000-omslag.pdf"
        h.write_text(bouw_html(titel, omslag_html(docs, bladnummers, titel, onder)),
                     encoding="utf-8")
        if not html_naar_pdf(browser, h, p):
            print("  MISLUKT bij de omslag - bundel afgebroken")
            return None
        voorwerk_pdf, gemeten = p, paginas(p)
        if gemeten == voorwerk:
            break
        voorwerk = gemeten

    bundel = uitmap / (naam + ".pdf")
    uit = fitz.open()
    with fitz.open(voorwerk_pdf) as vw:
        uit.insert_pdf(vw)
    inhoudsopgave, blad, huidige = [], voorwerk + 1, None
    for doc, deel, lengte in zip(docs, delen, lengtes):
        if doc.soort != huidige:
            huidige = doc.soort
            inhoudsopgave.append([1, SOORTEN[huidige]["etiket"], blad])
        inhoudsopgave.append([2, doc.titel, blad])
        with fitz.open(deel) as d:
            uit.insert_pdf(d)
        blad += lengte
    uit.set_toc(inhoudsopgave)
    uit.save(bundel, garbage=3, deflate=True)
    uit.close()
    stempel(bundel, titel, sla_over=1)
    shutil.rmtree(werkmap, ignore_errors=True)
    print("  PDF   %s  (%d blz., %d document(en), met bladwijzers)"
          % (toon_pad(bundel), paginas(bundel), len(docs)))
    if open_na:
        os.startfile(bundel)
    return bundel


def opdracht_lijst(argumenten):
    if argumenten.soort:
        soort = ALIASSEN.get(argumenten.soort, argumenten.soort)
        if soort not in SOORTEN:
            print("Onbekende soort: %s. Kies uit: %s" % (argumenten.soort, ", ".join(SOORTEN)))
            return 1
        soorten = [soort]
    else:
        soorten = list(SOORTEN)
    for soort in soorten:
        paden = bestanden(soort)
        print("\n%s (%d) - %s/" % (SOORTEN[soort]["etiket"], len(paden),
                                   toon_pad(SOORTEN[soort]["map"])))
        for pad in paden:
            kop, _ = lees_frontmatter(pad.read_text(encoding="utf-8"))
            etiket = str(kop.get("naam") or kop.get("titel") or "")
            print("  %-44s %-2s %s" % (pad.stem, str(kop.get("status") or ""), etiket[:58]))
    print()
    return 0


def opdracht_uitdraai(argumenten):
    alleen_html = argumenten.html
    browser = None if alleen_html else zoek_browser()
    if browser is None and not alleen_html:
        print("Geen Edge of Chrome gevonden. Ik maak alleen de HTML; open die en druk")
        print("Ctrl+P -> Opslaan als PDF. (Of zet STAMBOOM_BROWSER op het pad naar")
        print("msedge.exe of chrome.exe.)")
        alleen_html = True

    if argumenten.opdracht == "alles":
        soorten, term = list(SOORTEN), None
    else:
        soorten = [ALIASSEN.get(argumenten.opdracht, argumenten.opdracht)]
        term = argumenten.zoekterm

    namen = namenregister()
    docs = []
    for soort in soorten:
        if term:
            paden = kies(soort, term)
            if not paden:
                print("Niets gevonden voor '%s' in %s/." % (term, SOORTEN[soort]["map"].name))
                print("Overzicht: py scripts/pdf.py lijst %s" % soort)
                return 1
            if len(paden) > 1 and not argumenten.alle:
                print("'%s' past op %d bestanden:" % (term, len(paden)))
                for pad in paden:
                    print("  %s" % pad.stem)
                print("Maak het preciezer, of gebruik --alle om ze allemaal uit te draaien.")
                return 1
        else:
            paden = bestanden(soort)
        docs.extend(Document(soort, pad, namen) for pad in paden)

    if not docs:
        print("Niets uit te draaien.")
        return 1
    docs.sort(key=sorteersleutel)

    uitmap = Path(argumenten.map).resolve() if argumenten.map else UITVOER
    print("Uitvoer in %s/" % toon_pad(uitmap))

    if argumenten.bundel:
        if argumenten.opdracht == "alles":
            naam, titel = "stamboom-bundel", "Waar wij vandaan komen"
            onder = "Dossiers, tijdsbeeld en verhalen"
        else:
            soort = soorten[0]
            naam = SOORTEN[soort]["uitmap"] + "-bundel"
            titel = {"persoon": "De voorouders", "tijdsbeeld": "Tijdsbeeld",
                     "verhaal": "De verhalen"}[soort]
            onder = {"persoon": "Alle dossiers op een rij",
                     "tijdsbeeld": "Wat er in hun tijd gebeurde",
                     "verhaal": "Wat er tussen de aktes vandaan kwam"}[soort]
        gelukt = uitdraai_bundel(docs, uitmap, browser, naam, titel, onder,
                                 alleen_html, argumenten.open)
    else:
        gelukt = uitdraai_los(docs, uitmap, browser, alleen_html, argumenten.open)
    return 0 if gelukt else 1


def main():
    ontleder = argparse.ArgumentParser(
        prog="py scripts/pdf.py",
        description="Draait dossiers, tijdsbeeld en verhalen uit als PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Voorbeelden:\n"
               "  py scripts/pdf.py persoon jansen-jan-hendriks-1813 --open\n"
               "  py scripts/pdf.py verhaal 1814-de-schuitenmaker\n"
               "  py scripts/pdf.py persoon --alle --bundel\n"
               "  py scripts/pdf.py alles --bundel\n")
    onder = ontleder.add_subparsers(dest="opdracht", required=True)

    p_lijst = onder.add_parser("lijst", help="toont wat er uit te draaien valt")
    p_lijst.add_argument("soort", nargs="?", help="persoon | tijdsbeeld | verhaal")
    p_lijst.set_defaults(functie=opdracht_lijst)

    for naam in ["persoon", "tijdsbeeld", "verhaal", "alles"]:
        p = onder.add_parser(naam, help="draai %s uit als PDF" % naam)
        if naam != "alles":
            p.add_argument("zoekterm", nargs="?", help="id of een deel daarvan")
            p.add_argument("--alle", action="store_true", help="alles van deze soort")
        p.add_argument("--bundel", action="store_true",
                       help="een pdf met omslag, inhoudsopgave en bladwijzers")
        p.add_argument("--open", action="store_true", help="open het resultaat")
        p.add_argument("--html", action="store_true",
                       help="alleen de HTML maken (zelf Ctrl+P doen)")
        p.add_argument("--map", help="andere uitvoermap dan pdf/")
        p.set_defaults(functie=opdracht_uitdraai, alle=(naam == "alles"), zoekterm=None)

    argumenten = ontleder.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # anders struikelt cp1252 over ◐ en ✓
    except AttributeError:
        pass
    if argumenten.functie is opdracht_uitdraai and not argumenten.alle \
            and not argumenten.zoekterm:
        print("Geef een id op, of --alle. Overzicht: py scripts/pdf.py lijst %s"
              % argumenten.opdracht)
        return 1
    return argumenten.functie(argumenten)


if __name__ == "__main__":
    sys.exit(main())

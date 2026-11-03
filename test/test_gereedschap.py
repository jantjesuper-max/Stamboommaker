"""Controleert het gereedschap zelf: py test/test_gereedschap.py

`test/controleer.py` meet de inhoud van het onderzoek (lopen werklijst en dossiers
synchroon?). Dit bestand meet het gereedschap: doen de scripts wat ze beloven?

Draai dit na elke wijziging aan `scripts/`. Vind je een fout in een script, zet de
meting hier neer voordat je repareert — dan kan dezelfde fout niet terugkomen.
"""

import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORTEL / "scripts"))

import instellingen  # noqa: E402
import tijdsbeeld  # noqa: E402
from md_lezen import regels_buiten_uitleg  # noqa: E402

FOUTEN = []


def gelijk(gekregen, verwacht, wat):
    if gekregen != verwacht:
        FOUTEN.append(f"{wat}: kreeg {gekregen!r}, verwachtte {verwacht!r}")


def waar(uitkomst, wat):
    gelijk(bool(uitkomst), True, wat)


def onwaar(uitkomst, wat):
    gelijk(bool(uitkomst), False, wat)


# ---------------------------------------------------------------------------
# Plaatsvergelijking: de valkuil van de letterreeks
#
# Een kale `doel in plaats` koppelt provincies verkeerd omdat korte plaatsnamen
# in langere zitten. Dit is de hele klasse, niet alleen het geval dat het aan
# het licht bracht (»echt« in »Utrecht«).
# ---------------------------------------------------------------------------

def test_plaatsen():
    # Wél dezelfde plaats: de toevoeging staat achteraan
    for plaats, doel in [
        ("alphen aan den rijn", "alphen"),
        ("koudekerk aan den rijn", "koudekerk"),
        ("bergen op zoom", "bergen op zoom"),
        ("sint annaparochie", "sint annaparochie"),
        ("'s-hertogenbosch", "s-hertogenbosch"),
        ("Sint-Niklaas", "sint niklaas"),
        ("nieuw-amsterdam", "nieuw-amsterdam"),
        ("Utrecht", "utrecht"),
        ("Hoorn", "hoorn"),
    ]:
        waar(tijdsbeeld.plaats_past(plaats, doel), f"'{plaats}' hoort bij '{doel}'")

    # Niet dezelfde plaats: de letterreeks komt wel voor, de plaats niet
    for plaats, doel in [
        ("utrecht", "echt"),            # Echt ligt in Limburg
        ("wassenaar", "assen"),         # Assen ligt in Drenthe
        ("middelburg", "elburg"),       # Elburg ligt in Gelderland
        ("hoornaar", "hoorn"),          # Hoornaar ligt in Zuid-Holland
        ("nederweert", "ede"),          # Ede ligt in Gelderland
        ("rossum", "oss"),              # Oss ligt in Noord-Brabant
        ("nieuw-amsterdam", "amsterdam"),  # Drenthe, niet Noord-Holland
        ("aarle-rixtel", "arle"),       # Arle ligt in Oost-Friesland
        ("leerdam", "leer"),            # Leer ligt in Duitsland
        ("berkel en rodenrijs", "roden"),  # Roden ligt in Drenthe
        ("sneek", "eek"),               # te kort om iets te betekenen
    ]:
        onwaar(tijdsbeeld.plaats_past(plaats, doel),
               f"'{plaats}' hoort NIET bij '{doel}'")


def test_plaats_raakt():
    regios = {"limburg": ["echt", "weert"], "drenthe": ["assen", "emmen"]}
    gelijk(tijdsbeeld.plaats_raakt({"utrecht"}, ["limburg"], regios), None,
           "Utrecht raakt Limburg niet")
    gelijk(tijdsbeeld.plaats_raakt({"wassenaar"}, ["drenthe"], regios), None,
           "Wassenaar raakt Drenthe niet")
    gelijk(tijdsbeeld.plaats_raakt({"echt"}, ["limburg"], regios), "echt",
           "Echt raakt Limburg wel")
    gelijk(tijdsbeeld.plaats_raakt({"utrecht"}, ["landelijk"], regios), "landelijk",
           "landelijk raakt iedereen")


# ---------------------------------------------------------------------------
# De kalender moet parseerbaar blijven
# ---------------------------------------------------------------------------

def test_kalender():
    regios, gebeurtenissen, problemen = tijdsbeeld.lees_kalender()
    gelijk(problemen, [], "kalender zonder parseerfouten")
    waar(len(gebeurtenissen) > 0, "kalender bevat gebeurtenissen")
    waar(len(regios) > 0, "kalender bevat regio's")
    for g in gebeurtenissen:
        waar(g["gewicht"] in ("groot", "achtergrond"),
             f"gebeurtenis {g['id']}: gewicht '{g['gewicht']}' is groot of achtergrond")
        waar(g["van"] <= g["tot"], f"gebeurtenis {g['id']}: periode loopt vooruit")
    ids = [g["id"] for g in gebeurtenissen]
    gelijk(len(ids), len(set(ids)), "geen dubbele gebeurtenis-id's in de kalender")

    # Elk gebied moet een bestaande regio of 'landelijk' zijn, anders koppelt
    # een gebeurtenis stilzwijgend aan niemand.
    for g in gebeurtenissen:
        for gebied in g["gebied"]:
            waar(gebied == "landelijk" or gebied in regios or " " not in gebied,
                 f"gebeurtenis {g['id']}: gebied '{gebied}' is regio, plaats of landelijk")


# ---------------------------------------------------------------------------
# Instellingen: een verse kloon zonder stamboom.json mag niets laten omvallen
# ---------------------------------------------------------------------------

def test_instellingen():
    inst = instellingen.lees(opnieuw=True)
    for sleutel in ("eigenaar", "boek", "website", "lijnen"):
        waar(sleutel in inst, f"instellingen hebben sleutel '{sleutel}'")
    waar(instellingen.website_titel(), "website heeft altijd een titel")
    waar(instellingen.generatie_uitleg(), "generatie-uitleg is nooit leeg")
    gelijk(instellingen.waarde("bestaat.niet", "terugval"), "terugval",
           "onbekende sleutel geeft de terugval")


# ---------------------------------------------------------------------------
# Uitleg is geen gegeven
#
# Verschillende bestanden zijn tegelijk lijst en handleiding. Een voorbeeld in de
# uitleg mag nooit als echt gegeven gelezen worden — dat maakte een verse kloon
# van de repo twee keer "kapot" zonder dat de gebruiker iets had gedaan.
# ---------------------------------------------------------------------------

def test_uitleg_wordt_overgeslagen():
    import tempfile

    proef = """- echte-regel-een
<!-- - voorbeeld-in-commentaar -->
- echte-regel-twee
<!--
- voorbeeld-over
- meerdere-regels
-->
- echte-regel-drie
```
- voorbeeld-in-codeblok
```
- echte-regel-vier
"""
    with tempfile.TemporaryDirectory() as map_:
        pad = Path(map_) / "proef.md"
        pad.write_text(proef, encoding="utf-8")
        gelezen = [r.strip() for _, r in regels_buiten_uitleg(pad) if r.strip()]
    gelijk(gelezen,
           ["- echte-regel-een", "- echte-regel-twee",
            "- echte-regel-drie", "- echte-regel-vier"],
           "commentaar en codeblokken worden overgeslagen")

    # Een ontbrekend bestand mag niets laten omvallen
    gelijk(regels_buiten_uitleg(Path("bestaat-niet-xyz.md")), [],
           "ontbrekend bestand geeft een lege lijst")


def test_verse_kloon_is_schoon():
    """De meegeleverde bestanden mogen zelf geen problemen opleveren.

    De werklijst en _AFGEHANDELD.md bevatten voorbeelden in hun uitleg; als die
    als gegevens gelezen worden, meldt een verse kloon problemen over personen
    die niet bestaan.
    """
    werklijst = WORTEL / "onderzoek" / "werklijst-dossiers.md"
    if werklijst.exists():
        regels = [r for _, r in regels_buiten_uitleg(werklijst)]
        for r in regels:
            onwaar(r.strip().startswith("- [x]") or r.strip().startswith("- [ ]"),
                   f"werklijst bevat geen voorbeeldregel als gegeven: {r.strip()[:60]}")
    gelijk(tijdsbeeld.afgemeld(), {},
           "_AFGEHANDELD.md levert geen afmeldingen uit zijn uitleg")


# ---------------------------------------------------------------------------
# Broncode blijft tekst
#
# app.js gebruikte een letterlijke NUL-byte als scheidingsteken in de
# markdown-renderer. Git ziet een bestand met een NUL-byte als binair: geen
# diff, geen code review, en gereedschap dat er zomaar iets van kan maken. De
# JS-escape levert exact hetzelfde teken op, dus gebruik die. Deze test staat
# er omdat de byte al een keer is teruggekomen bij een herschreven app.js.
# ---------------------------------------------------------------------------

def test_broncode_is_tekst():
    tekstsoorten = {".py", ".js", ".css", ".html", ".json", ".md", ".cmd", ".sh"}
    # leaflet.js e.d. komen van buiten; die beheren we niet
    van_buiten = {"leaflet.js", "leaflet.css"}
    for pad in sorted(WORTEL.rglob("*")):
        if not pad.is_file() or pad.suffix.lower() not in tekstsoorten:
            continue
        if ".git" in pad.parts or "__pycache__" in pad.parts or pad.name in van_buiten:
            continue
        if b"\x00" in pad.read_bytes():
            FOUTEN.append(
                f"{pad.relative_to(WORTEL)}: bevat een letterlijke NUL-byte, waardoor git "
                f"het bestand als binair behandelt. Gebruik de JS-escape in plaats van het teken."
            )


# ---------------------------------------------------------------------------
# Kaart: een datum vóór een plaatsnaam mag die plaats niet verbergen
#
# Geboren-/overledenvelden zijn vrije tekst: "✓ 24-07-1837 Smilde", "◐ ged.
# 26-02-1727 Burum", "? vóór ca. 1745". De plaats moet eruit komen, de datum
# niet — en een pure datum is géén plaats. Elke regel hier is een keer de
# oorzaak geweest van een stip die ontbrak of een datum in de gebrekenlijst.
# ---------------------------------------------------------------------------

def test_plaats_uit_datumveld():
    import plaatsen

    for veld, verwacht in [
        ("✓ 24-07-1837 Smilde", ["Smilde"]),
        ("◐ ged. 26-02-1727 Burum", ["Burum"]),
        ("◐ ca. 1750-1758 Nieuwkerken-Waas", ["Nieuwkerken-Waas"]),
        ("✓ begr. 16-08-1768 Zegveld", ["Zegveld"]),
        ("waarschijnlijk 23-11-1808 te Koudekerk", ["Koudekerk"]),
        ("? vóór ca. 1745", []),
        ("04-08-1869", []),
        ("ca. 1650/1655 — het doopboek begint pas in 1676", []),
        ("na 1872, plaats onbekend", []),
        ("12-03-1900, Voorhout", ["Voorhout"]),   # 'voor' is hier geen datumwoord
        ("1901, Opmeer", ["Opmeer"]),            # 'op' evenmin
    ]:
        gelijk(plaatsen.veld_kandidaten(veld), verwacht, f"plaats uit '{veld}'")
    waar(plaatsen.is_gemeente("Lemsterland"), "Lemsterland is een gemeente")
    waar(plaatsen.is_gemeente("gem. Schoterland"), "'gem. ...' is altijd een gemeente")
    onwaar(plaatsen.is_gemeente("Oosterzee"), "Oosterzee is een dorp")


# ---------------------------------------------------------------------------
# Tijdsbeeld: "vóór JJJJ" is een bovengrens, geen sterfjaar
# ---------------------------------------------------------------------------

def test_voor_is_bovengrens():
    import tempfile

    with tempfile.TemporaryDirectory() as map_:
        pad = Path(map_) / "proef-1725ca.md"
        pad.write_text('---\nid: proef-1725ca\ngeboren: "? ca. 1725, plaats onbekend"\n'
                       'overleden: "? vóór 09-01-1834, plaats onbekend"\n---\n', encoding="utf-8")
        pers = tijdsbeeld.persoon_gegevens(pad)
    gelijk(pers["geb"], 1725, "geboortejaar gelezen")
    waar(pers["eind"] <= 1810, f"'vóór 1834' bij geboren 1725 eindigt op een mensenleven, niet op 1834 (kreeg {pers['eind']})")


# ---------------------------------------------------------------------------
# PDF: een knipsel wordt een figuur met bijschrift, met een pad dat de browser vindt
#
# De eigen markdown-renderer van pdf.py kende geen afbeeldingen: ![x](y) werd een
# uitroepteken met een link, en "Download als PDF" liet de knipsels weg. De HTML
# wordt als file:// geopend, dus een plaatje moet een absoluut file://-pad krijgen,
# opgelost ten opzichte van de map van het markdown-bestand.
# ---------------------------------------------------------------------------

def test_pdf_knipsels():
    import importlib.util
    import re
    import tempfile

    spec = importlib.util.spec_from_file_location("stamboom_pdf", WORTEL / "scripts" / "pdf.py")
    pdf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdf)

    with tempfile.TemporaryDirectory() as map_:
        basis = Path(map_)
        (basis / "beeld").mkdir()
        beeld = basis / "beeld" / "1893-04-05-knipsel.jpg"
        beeld.write_bytes(b"\xff\xd8\xff\xd9")
        ctx = {"namen": {}, "noten": {}, "nootvolgorde": [], "basismap": basis}

        html = pdf.markdown_naar_html("![Leeuwarder Courant, 5 april 1893: dankbetuiging [...] van de weduwe](beeld/1893-04-05-knipsel.jpg)", ctx)
        waar("<figure" in html, "los knipsel wordt een figuur")
        waar("<figcaption>Leeuwarder Courant, 5 april 1893: dankbetuiging [...] van de weduwe</figcaption>" in html,
             "bijschrift met [...] blijft heel")
        m = re.search(r'<img src="([^"]+)"', html)
        gelijk(m.group(1) if m else None, beeld.resolve().as_uri(), "beeldpad wordt een file://-URI")
        onwaar("!<a" in html, "geen uitroepteken met een link")

        html = pdf.markdown_naar_html("Zie ![kaart](https://example.org/kaart.png) hier.", ctx)
        waar('<img src="https://example.org/kaart.png"' in html, "webadres blijft staan")

        html = pdf.markdown_naar_html("Zie [Delpher](https://www.delpher.nl/).", ctx)
        waar('<a href="https://www.delpher.nl/">Delpher</a>' in html, "gewone link blijft een link")
        onwaar("<img" in html, "een link is geen beeld")


# ---------------------------------------------------------------------------
# Zoekscript: schrijfwijzen, de Begraven-alias en de archiefcodes
#
# Eén letter verschil is een andere zoekopdracht, en de API meldt niets bij een
# onbekende filterwaarde. Deze regels bewaken dat het script die valkuilen
# blijft afvangen. Alles offline: geen API-aanroep.
# ---------------------------------------------------------------------------

def test_zoek_openarch_offline():
    import zoek_openarch as z

    waar("Baukjen Wybes" in z._naamvarianten("Baukjen Wiebes"), "ie -> y: Wiebes geeft Wybes")
    waar("Lammert" in z._woordvarianten("Lambert"), "mb -> mm: Lambert geeft Lammert (assimilatie)")
    gelijk(z._klanksleutel("Barnevelt"), z._klanksleutel("Barneveld"), "t en d klinken hetzelfde")
    gelijk(z._klanksleutel("Bruinsma"), z._klanksleutel("Bruynsma"), "ui en uy klinken hetzelfde")
    onwaar("Baucjen Wybes" in z._naamvarianten("Baukjen Wiebes"), "nooit twee woorden tegelijk variëren")
    gelijk(z.BEGRAVEN_ALIAS.get("Begrafenis"), "Begraven", "Begrafenis wordt naar Begraven vertaald")
    waar("Begrafenis" in z.GEBEURTENISTYPEN and "Begraven" in z.GEBEURTENISTYPEN,
         "beide schrijfwijzen toegestaan")
    for code in ("frl", "dar", "hco", "wfa", "nha", "zar", "gld", "elo", "saa", "hua", "gra"):
        waar(code in z.ARCHIEFCODES, f"archiefcode {code} bekend")
    onwaar("dra" in z.ARCHIEFCODES, "'dra' is niet de Drentse code (dat is 'dar')")
    gelijk(z._fullsize("https://x-images.memorix.nl/abc/thumb/640x480/pad/scan.jp2"),
           "https://x-images.memorix.nl/abc/download/fullsize/pad/scan.jp2", "thumb -> fullsize")
    gelijk(z._iiif("https://x.memorix.io/resources/iiif/3/uuid/info.json"),
           "https://x.memorix.io/resources/iiif/3/uuid/full/max/0/default.jpg", "info.json -> volledig beeld")


def test_delpher_frase():
    import zoek_delpher as d

    waar(d.lijkt_frase("Jan de Vries Oudshoorn"), "losse woorden zonder AND zijn een frase (stille nul)")
    onwaar(d.lijkt_frase("Vries AND Oudshoorn"), "met AND is het geen frase")
    onwaar(d.lijkt_frase('"gouden bruiloft"'), "een bewuste frase tussen aanhalingstekens is in orde")
    onwaar(d.lijkt_frase("Oudshoorn"), "één woord is een ijkpunt, geen frase")


# ---------------------------------------------------------------------------
# Knipsels: elk beeld bestaat en heeft een bijschrift
# ---------------------------------------------------------------------------

def test_knipsel_controle():
    import importlib.util
    import tempfile

    spec = importlib.util.spec_from_file_location("stamboom_controleer", WORTEL / "test" / "controleer.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)

    with tempfile.TemporaryDirectory() as map_:
        wortel = Path(map_)
        (wortel / "personen").mkdir()
        (wortel / "boek" / "verhalen" / "beeld").mkdir(parents=True)
        (wortel / "boek" / "verhalen" / "beeld" / "1893-goed.jpg").write_bytes(b"\xff\xd8")
        (wortel / "boek" / "verhalen" / "beeld" / "1900-ongebruikt.jpg").write_bytes(b"\xff\xd8")
        (wortel / "boek" / "verhalen" / "1893-proef.md").write_text(
            "![Krant, 1893: bericht [...]](beeld/1893-goed.jpg)\n"
            "![](beeld/1893-goed.jpg)\n"
            "![Weg](beeld/bestaat-niet.jpg)\n"
            "![Web](https://example.org/x.png)\n", encoding="utf-8")
        (wortel / "personen" / "jansen-jan-1850.md").write_text(
            "![Akte, 1850: aangifte](../boek/verhalen/beeld/1893-goed.jpg)\n", encoding="utf-8")
        problemen, los = c.knipsel_problemen(wortel)
    gelijk(len(problemen), 2, f"één kapot pad en één leeg bijschrift: {problemen}")
    waar(any("bestaat-niet.jpg" in p for p in problemen), "kapot pad gemeld")
    waar(any("geen bijschrift" in p for p in problemen), "leeg bijschrift gemeld")
    gelijk(los, ["1900-ongebruikt.jpg"], "ongebruikt beeld wordt genoemd, gebruikt beeld niet")


def test_dubbele_werklijstregels():
    import importlib.util

    spec = importlib.util.spec_from_file_location("stamboom_controleer", WORTEL / "test" / "controleer.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)

    def item(nr, pid, gen, naam="Naam", af=False):
        return {"regelnr": nr, "af": af, "generatie": gen, "id": pid, "naam": naam,
                "regel": f"- [ ] g{gen} · {pid} — {naam}"}

    gelijk(c.dubbele_regels([item(1, "pieters-rinke-1730ca", 8), item(2, "pieters-rinke-1730ca", 8)]).__len__(), 1,
           "letterlijk dubbel id wordt gemeld")
    gelijk(len(c.dubbele_regels([item(1, "pieters-rinke", 8), item(2, "pieters-rinke-1730ca", 8)])), 1,
           "zelfde persoon met en zonder jaarstaart wordt gemeld")
    gelijk(c.dubbele_regels([item(1, "bijl-aldert-1894", 3), item(2, "bijl-aldert-1830", 6)]), [],
           "grootvader en kleinzoon met dezelfde naam zijn geen dubbel")
    gelijk(c.dubbele_regels([item(1, "pieters-rinke", 8, "Naam · overgeslagen: dubbele regel"),
                             item(2, "pieters-rinke-1730ca", 8)]), [],
           "een als overgeslagen gemarkeerde kopie telt niet mee")


# ---------------------------------------------------------------------------
# Alle scripts blijven geldige Python (ook die Pillow of PyMuPDF nodig hebben)
# ---------------------------------------------------------------------------

def test_scripts_parseerbaar():
    import ast

    for pad in sorted((WORTEL / "scripts").glob("*.py")) + sorted((WORTEL / "test").glob("*.py")):
        try:
            ast.parse(pad.read_text(encoding="utf-8"))
        except SyntaxError as fout:
            FOUTEN.append(f"{pad.relative_to(WORTEL)}: syntaxfout: {fout}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    for test in (test_plaatsen, test_plaats_raakt, test_kalender, test_instellingen,
                 test_uitleg_wordt_overgeslagen, test_verse_kloon_is_schoon,
                 test_broncode_is_tekst, test_plaats_uit_datumveld, test_voor_is_bovengrens,
                 test_pdf_knipsels, test_zoek_openarch_offline, test_delpher_frase,
                 test_knipsel_controle, test_dubbele_werklijstregels, test_scripts_parseerbaar):
        test()
    if FOUTEN:
        print(f"{len(FOUTEN)} fout(en):")
        for f in FOUTEN:
            print(f"  - {f}")
        return 1
    print("Gereedschap in orde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

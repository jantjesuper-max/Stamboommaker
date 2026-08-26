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


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    for test in (test_plaatsen, test_plaats_raakt, test_kalender, test_instellingen,
                 test_uitleg_wordt_overgeslagen, test_verse_kloon_is_schoon):
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

"""Leest stamboom.json — de enige plek waar dít project persoonlijk wordt.

Alle andere scripts zijn naamloos: ze werken met persoons-ID's, dossiers en
mappen, en weten niet wiens stamboom het is. Wat wél persoonlijk is (jouw naam,
je geboortejaar, de titel van je boek, de naam boven de website) staat in
`stamboom.json` in de projectmap, en komt hier binnen.

Gebruik:

    import instellingen
    inst = instellingen.lees()
    inst["boek"]["titel"]
    instellingen.waarde("eigenaar.naam")

Ontbreekt `stamboom.json`, dan werkt alles door op de standaardwaarden hieronder
en zegt `controleer.py` er iets over. Zo doet een verse kloon van de repo geen
gekke dingen voordat `py instellen.py` is gedraaid.
"""

import json
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
BESTAND = WORTEL / "stamboom.json"

# Standaardwaarden: zichtbaar neutraal, zodat je meteen ziet dat er nog niets is
# ingesteld in plaats van dat er iemand anders zijn naam in je uitdraai staat.
STANDAARD = {
    "eigenaar": {
        "naam": "",
        "geboortejaar": None,
        "geboorteplaats": "",
    },
    "boek": {
        "titel": "Waar wij vandaan komen",
        "ondertitel": "",
        "voor_wie": "",
    },
    "website": {
        "titel": "Mijn stamboom",
        "poort": 8123,
    },
    "lijnen": [],
}

_CACHE = None


def _samenvoegen(standaard, eigen):
    """Diep samenvoegen: wat in stamboom.json staat wint, de rest blijft standaard."""
    resultaat = dict(standaard)
    for sleutel, waarde in (eigen or {}).items():
        if isinstance(waarde, dict) and isinstance(resultaat.get(sleutel), dict):
            resultaat[sleutel] = _samenvoegen(resultaat[sleutel], waarde)
        else:
            resultaat[sleutel] = waarde
    return resultaat


def lees(opnieuw=False):
    """De instellingen als dict, altijd met alle sleutels gevuld."""
    global _CACHE
    if _CACHE is not None and not opnieuw:
        return _CACHE
    eigen = {}
    if BESTAND.exists():
        try:
            eigen = json.loads(BESTAND.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            eigen = {}  # stuk bestand mag geen script laten omvallen
    _CACHE = _samenvoegen(STANDAARD, eigen)
    return _CACHE


def waarde(pad, terugval=""):
    """Eén waarde via een puntpad: waarde("boek.titel")."""
    huidig = lees()
    for deel in pad.split("."):
        if not isinstance(huidig, dict) or deel not in huidig:
            return terugval
        huidig = huidig[deel]
    return terugval if huidig in (None, "") else huidig


def ingesteld():
    """Is `py instellen.py` al gedraaid? (Zonder naam is het project naamloos.)"""
    return BESTAND.exists() and bool(waarde("eigenaar.naam"))


def eigenaar_kort():
    """'Jans' -> voor koppen: de naam, of een neutrale terugval."""
    return waarde("eigenaar.naam") or "onbekend"


def boek_ondertitel():
    """Ondertitel van het boek; leidt hem zelf af als hij niet is ingevuld."""
    eigen = waarde("boek.ondertitel")
    if eigen:
        return eigen
    naam = waarde("eigenaar.naam")
    return f"De voorouders van {naam}" if naam else ""


def website_titel():
    """Naam boven de website; valt terug op de boektitel en dan op iets neutraals."""
    return waarde("website.titel") or waarde("boek.titel") or "Mijn stamboom"


def generatie_uitleg():
    """Tooltip bij het generatienummer: t.o.v. wie is generatie 0?"""
    naam = waarde("eigenaar.naam")
    jaar = waarde("eigenaar.geboortejaar", None)
    if naam and jaar:
        return f"t.o.v. {naam} ({jaar}) = 0"
    if naam:
        return f"t.o.v. {naam} = 0"
    return "t.o.v. jezelf = 0"


def schrijf(nieuw):
    """Instellingen wegschrijven (gebruikt door instellen.py)."""
    global _CACHE
    BESTAND.write_text(
        json.dumps(nieuw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _CACHE = None


if __name__ == "__main__":
    print(json.dumps(lees(), ensure_ascii=False, indent=2))

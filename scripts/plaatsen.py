"""Controleert of alle plaatsen uit de dossiers een coordinaat hebben.

Het Kaart-tabblad van de website tekent alleen plaatsen die in
website/static/plaatsen.json staan. Dit script legt alle plaatsnamen uit de
dossier-frontmatter (woonplaatsen, geboren, overleden) naast die gids en
meldt wat er ontbreekt, met de dossiers erbij.

Gebruik:  py scripts/plaatsen.py

Ontbreekt er een plaats, voeg die dan met de hand toe aan plaatsen.json --
niet blind laten geocoderen: Nederland zit vol naamgenoot-dorpen (Rottum
ligt in Friesland en Groningen, Echten in Friesland en Drenthe, Sloten in
Friesland en bij Amsterdam). Het dossier zelf zegt in welke streek je moet
zijn. Gemeentenamen (Lemsterland, Schoterland) krijgen geen coordinaat:
zoek het dorp, of laat het veld voor wat het is.

Sluit af met code 1 zodra een woonplaatsen-veld een onvindbare plaats
bevat, zodat het als controle in een ronde kan meedraaien.
"""

import importlib.util
import json
import os
import re
import sys

PROJECTMAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIDSPAD = os.path.join(PROJECTMAP, "website", "static", "plaatsen.json")

# dezelfde opschoningen als de kaart (website/static/app.js) hanteert
VOORVOEGSEL = re.compile(r"^(vermoedelijk|waarschijnlijk|mogelijk|te|in|onder(?:\s+de\s+stad)?)\s+", re.I)
GEM_ACHTERVOEGSEL = re.compile(r",\s*gem\..*$", re.I)
EO_ACHTERVOEGSEL = re.compile(r"\s+e\.o\.$", re.I)


def frontmatter_lezer():
    """De simpele frontmatter-parser van de webserver hergebruiken."""
    spec = importlib.util.spec_from_file_location(
        "stamboom_server", os.path.join(PROJECTMAP, "website", "server.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lees_frontmatter


def gids_laden():
    with open(GIDSPAD, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("plaatsen", {}), data.get("alias", {})


def vind_coord(naam, plaatsen, alias):
    """Zelfde zoekvolgorde als plaatsCoord() in app.js; geeft de sleutel of None."""
    for kandidaat in (naam,
                      GEM_ACHTERVOEGSEL.sub("", naam).strip(),
                      EO_ACHTERVOEGSEL.sub("", naam).strip()):
        if not kandidaat:
            continue
        kandidaat = alias.get(kandidaat, kandidaat)
        if kandidaat in plaatsen:
            return kandidaat
    return None


def woonplaats_naam(waarde):
    """'Eesterga (1843 - ca. 1865)' -> 'Eesterga'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", waarde).strip()


DATUMACHTIG = re.compile(r"^(\d|ca\.?\s*\d|(na|voor|vóór|tussen|rond|omstreeks)\b.*\d)", re.I)


def veld_kandidaten(waarde):
    """Mogelijke plaatsnamen uit een geboren-/overleden-veld, zoals de kaart ze leest."""
    zonder_haakjes = re.sub(r"\([^)]*\)", " ", waarde or "")
    kandidaten = []
    for deel in zonder_haakjes.split(","):
        deel = deel.strip()
        if not deel or re.search(r"onbekend", deel, re.I):
            continue
        # ook de tekst na " te " proberen: "waarschijnlijk 23-11-1808 te Koudekerk"
        for sub in (deel, re.split(r"\s+te\s+", deel, flags=re.I)[-1]):
            sub = VOORVOEGSEL.sub("", sub).strip()
            if not sub or DATUMACHTIG.match(sub) or len(sub) <= 2:
                continue
            if sub not in kandidaten:
                kandidaten.append(sub)
    return kandidaten


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    lees_frontmatter = frontmatter_lezer()
    plaatsen, alias = gids_laden()
    personenmap = os.path.join(PROJECTMAP, "personen")

    ontbreekt = {}     # plaatsnaam -> [dossier-id's]  (uit woonplaatsen: hard gebrek)
    beoordelen = {}    # veldtekst -> [dossier-id's]   (geboren/overleden zonder treffer)
    dossiers = 0

    for naam in sorted(os.listdir(personenmap)):
        if not naam.endswith(".md") or naam.startswith("_"):
            continue
        fm = lees_frontmatter(os.path.join(personenmap, naam))
        pid = fm.get("id") or naam[:-3]
        dossiers += 1

        woonplaatsen = fm.get("woonplaatsen") or []
        if isinstance(woonplaatsen, str):
            woonplaatsen = [woonplaatsen]
        for w in woonplaatsen:
            if not w or w == "[]":
                continue
            plaats = woonplaats_naam(w)
            if plaats and not vind_coord(plaats, plaatsen, alias):
                ontbreekt.setdefault(plaats, []).append(pid)

        for veld in ("geboren", "overleden"):
            waarde = fm.get(veld) or ""
            kandidaten = veld_kandidaten(waarde)
            if not kandidaten:
                continue
            if not any(vind_coord(k, plaatsen, alias) for k in kandidaten):
                beoordelen.setdefault(" / ".join(kandidaten), []).append(f"{pid} ({veld})")

    if ontbreekt:
        print("Plaatsen uit woonplaatsen-velden ZONDER coordinaat -- toevoegen aan")
        print("website/static/plaatsen.json (of een alias aanmaken):")
        for plaats, ids in sorted(ontbreekt.items()):
            print(f"  - {plaats}   (bij: {', '.join(sorted(set(ids)))})")
        print()
    if beoordelen:
        print("Geboren-/overledenvelden zonder herkenbare plaats (ter beoordeling;")
        print("vaak een gemeentenaam die je NIET moet toevoegen -- zoek dan het dorp):")
        for tekst, ids in sorted(beoordelen.items()):
            print(f"  - \"{tekst}\"   (bij: {', '.join(sorted(set(ids)))})")
        print()

    print(f"{dossiers} dossiers gelezen; gids bevat {len(plaatsen)} plaatsen en "
          f"{len(alias)} aliassen.")
    if not ontbreekt:
        print("Alle woonplaatsen uit de dossiers staan op de kaart.")
    sys.exit(1 if ontbreekt else 0)


if __name__ == "__main__":
    main()

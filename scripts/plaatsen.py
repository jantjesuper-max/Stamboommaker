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

Sluit af met code 1 zodra een woonplaatsen-, geboren- of overledenveld een
onvindbare plaatsnaam bevat, zodat het als controle in een ronde kan
meedraaien.

Let op de driedeling in geboren-/overledenvelden -- die zijn vrije tekst, dus
niet elke onherkenbare regel is een gebrek:

  1. een echte plaatsnaam zonder coordinaat  -> GEBREK, exit 1
  2. een gemeentenaam (Lemsterland)          -> bewust geen coordinaat
  3. alleen een datum of schatting           -> geen plaats, dus niets te doen

Vroeger gingen die drie op een hoop en kon geen ervan de exitcode raken.
Daardoor bleef een buitenlandse geboorteplaats (die alleen in `geboren:`
staat en nooit in `woonplaatsen:`) ongemerkt tussen de datumregels staan, en
ontbrak de verhuislijn van de enige immigrant in een stamboom op de kaart.
Buitenlandse plaatsen horen er dus net zo goed in als Nederlandse.
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


# de betrouwbaarheidscodes staan vaak vooraan in een geboren-/overledenveld
# ("◐ vóór ca. 1745"); zonder deze stap haalt zo'n regel de datumtest niet en
# komt een pure datum als vermeende plaatsnaam in de melding terecht
STATUSTEKEN = re.compile(r"^[✓◐?⚠\s]+")

# Een datum VOORAAN mag de plaatsnaam die erachter staat niet meeslepen. Velden als
#   geboren:   "◐ ca. 1750-1758 Nieuwkerken-Waas"
#   overleden: "✓ 24-07-1837 Smilde"
# leverden vroeger GEEN plaatsnaam op, omdat de hele kandidaat als "datumachtig" werd
# weggegooid, en het script sloot af met de geruststellende regel dat alles op de kaart
# stond. Sindsdien wordt de datum eraf gestript en telt wat er overblijft.
MAANDEN = ("januari|februari|maart|april|mei|juni|juli|augustus|september|"
           "oktober|november|december|jan|feb|mrt|apr|jun|jul|aug|sep|okt|nov|dec")
DATUMWOORD = re.compile(
    r"^(ca\.?|circa|omstreeks|rond|na|voor|vóór|tussen|en|of|te|in|op|"
    r"begraven|begr\.?|gedoopt|ged\.?|geb\.?|overl\.?|vermoedelijk|waarschijnlijk|mogelijk|"
    rf"{MAANDEN}|\d[\d\-/\.]*\??|#)(\s+|$)", re.I)
# een toelichting achter een gedachtestreepje is geen plaats:
#   "ca. 1650/1655 — het doopboek begint pas in 1676"
TOELICHTING = re.compile(r"\s+[—–]\s+.*$")


def zonder_datum(sub):
    """Haalt een datumaanduiding vooraan weg; geeft terug wat er als plaats overblijft.

    'ged. 26-02-1727 Burum' -> 'Burum'; '04-08-1869' -> '' (geen plaats);
    'Voorhout' blijft 'Voorhout', want DATUMWOORD eist na elk woord een spatie.
    """
    sub = TOELICHTING.sub("", sub).strip()
    vorige = None
    while sub != vorige:
        vorige = sub
        sub = DATUMWOORD.sub("", sub).strip()
    return sub


# Gemeenten, geen dorpen: die krijgen met opzet geen coordinaat, want de stip
# zou een dorp suggereren dat de akte niet noemt. Zoek het dorp, of laat het
# veld staan. Deze lijst is een begin; vul hem aan met de gemeenten en
# grietenijen uit jouw stamboom. Staat een gemeente hier niet bij, dan meldt het
# script haar als gebrek -- dat is bedoeld: iemand moet er een keer naar kijken.
# Een naam die met "gem." begint telt altijd als gemeente.
GEMEENTEN = {
    "lemsterland", "schoterland", "gaasterland", "doniawerstal", "haskerland",
    "wymbritseradeel", "hemelumer oldeferd", "utingeradeel", "aengwirden",
    "weststellingwerf", "ooststellingwerf", "opsterland", "smallingerland",
    "achtkarspelen", "kollumerland", "dantumadeel", "tietjerksteradeel",
    "rijnwoude", "alkemade", "jacobswoude", "nieuwer-amstel", "hulsterambacht",
}


def is_gemeente(naam):
    kaal = re.sub(r"^gem\.\s*", "", naam, flags=re.I).strip().lower()
    return kaal in GEMEENTEN or naam.lower().startswith("gem.")


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
            sub = STATUSTEKEN.sub("", sub)
            sub = VOORVOEGSEL.sub("", sub).strip()
            # ALTIJD uitkleden, en de uitkomst ONVOORWAARDELIJK overnemen, ook als zij
            # leeg is: een lege uitkomst betekent dat de hele tekst uit datumwoorden
            # bestond ("04-08-1869", "1646"), en zo'n regel is geen plaatsnaam.
            sub = zonder_datum(sub)
            if not sub or len(sub) <= 2:
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

    ontbreekt = {}       # plaatsnaam -> [dossier-id's]  (uit woonplaatsen: hard gebrek)
    ontbreekt_veld = {}  # plaatsnaam -> [dossier-id's]  (uit geboren/overleden: hard gebrek)
    gemeenten = {}       # gemeentenaam -> [dossier-id's] (bewust geen coordinaat)
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
                # Een gemeentenaam hoort ook hier bij "bewust geen coordinaat" en niet
                # bij de gebreken -- dezelfde regel voor alle drie de velden.
                doel = gemeenten if is_gemeente(plaats) else ontbreekt
                doel.setdefault(plaats, []).append(
                    f"{pid} (woonplaatsen)" if doel is gemeenten else pid)

        for veld in ("geboren", "overleden"):
            waarde = fm.get(veld) or ""
            kandidaten = veld_kandidaten(waarde)
            if not kandidaten:
                continue
            if any(vind_coord(k, plaatsen, alias) for k in kandidaten):
                continue
            # het veld noemt wel iets plaatsachtigs, maar de kaart vindt het niet:
            # gemeente (bewust) of een echte plaats die nog in de gids moet
            for k in kandidaten:
                doel = gemeenten if is_gemeente(k) else ontbreekt_veld
                doel.setdefault(k, []).append(f"{pid} ({veld})")

    if ontbreekt:
        print("Plaatsen uit woonplaatsen-velden ZONDER coordinaat -- toevoegen aan")
        print("website/static/plaatsen.json (of een alias aanmaken):")
        for plaats, ids in sorted(ontbreekt.items()):
            print(f"  - {plaats}   (bij: {', '.join(sorted(set(ids)))})")
        print()
    if ontbreekt_veld:
        print("Plaatsnamen uit geboren-/overledenvelden ZONDER coordinaat -- deze")
        print("horen bij een geboorte- of sterfplaats, dus zonder coordinaat mist de")
        print("kaart de eerste of laatste stip van dat leven (en de verhuislijn ernaar):")
        for plaats, ids in sorted(ontbreekt_veld.items()):
            print(f"  - {plaats}   (bij: {', '.join(sorted(set(ids)))})")
        print()
    if gemeenten:
        print("Gemeentenamen -- bewust GEEN coordinaat (een stip zou een dorp")
        print("suggereren dat de akte niet noemt). Zoek het dorp, of laat het staan:")
        for plaats, ids in sorted(gemeenten.items()):
            print(f"  - {plaats}   (bij: {', '.join(sorted(set(ids)))})")
        print()

    print(f"{dossiers} dossiers gelezen; gids bevat {len(plaatsen)} plaatsen en "
          f"{len(alias)} aliassen.")
    if not ontbreekt and not ontbreekt_veld:
        print("Alle plaatsnamen uit de dossiers staan op de kaart.")
    sys.exit(1 if (ontbreekt or ontbreekt_veld) else 0)


if __name__ == "__main__":
    main()

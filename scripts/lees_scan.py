"""Maak van een aktescan een klein bestand dat de AI kan inlezen.

Waarom dit script bestaat: een scan uit het archief is 3 tot 8 MB en 5000 pixels
breed. Wie die rechtstreeks inleest stuurt megabytes over de verbinding, en achter
een inspecterende proxy (op veel werkplekken) is dat een van de dingen die een
ECONNRESET uitlokt. Bovendien is zo'n beeld op ooghoogte tóch onleesbaar.

De werkwijze in twee stappen:

    py scripts/lees_scan.py overzicht <scan>              # waar staat de akte?
    py scripts/lees_scan.py strook <scan> <x> <y> <b> <h> # lees de regels

Het overzicht is grijswaarden op maximaal 1500 pixels: genoeg om te zien welke
bladzijde en welk aktenummer je hebt. De strook is een uitsnede op volle
resolutie, met autocontrast, opgeschaald tot een vaste breedte -- dat is wat je
nodig hebt om een naam of een datum écht te lezen.

Beide bestanden blijven gegarandeerd onder GRENS_KB (220 kB): het script meet na
en verlaagt zo nodig de kwaliteit, en pas als laatste redmiddel de breedte. Dat
is geen cosmetica maar de maatregel tegen ECONNRESET -- zie de opmerking bij die
constante.

Coördinaten geef je in het stelsel van de originele scan. Het overzicht print
de schaalfactor, zodat je van wat je op het overzicht ziet naar de echte
coördinaten kunt rekenen. Dezelfde coördinaten gebruik je daarna voor
scripts/knipsel.py, dat een uitsnede als knipsel voor een verhaal bewaart.
"""

import argparse
import os
import sys

from PIL import Image, ImageOps

# Grenzen die in de praktijk werken: leesbaar, en klein genoeg om niet op te vallen
# in het netwerkverkeer.
OVERZICHT_MAX = 1500
STROOK_BREEDTE = 2600
KWALITEIT = 72

# Harde bovengrens per uitvoerbestand. Eerder was de bestandsgrootte hier een gelukkig
# toeval: kwaliteit 72 op 2600 pixels gaf "meestal" 150 tot 200 kB, maar bij een
# dichtbeschreven strook of een grote uitsnede liep dat op. En juist een groot beeld is wat
# achter een inspecterende proxy een `Connection dropped (ECONNRESET)` uitlokt. Een script
# dat "meestal" klein blijft is dan niet goed genoeg: het faalt precies bij de moeilijk
# leesbare bladzijden, waar je de uitsnede het hardst nodig hebt.
#
# Daarom wordt elk bestand nagemeten en zo nodig opnieuw opgeslagen met lagere kwaliteit,
# en pas als laatste redmiddel smaller. Leesbaarheid gaat vóór scherpte: liever kwaliteit 45
# dan een uitsnede die niet aankomt.
GRENS_KB = 220
KWALITEIT_MIN = 40


def _uitvoerpad(naam):
    map_ = os.path.join(os.environ.get("TEMP", "."), "scanlees")
    os.makedirs(map_, exist_ok=True)
    return os.path.join(map_, naam)


def _bewaar_onder_grens(beeld, pad, grens_kb=GRENS_KB):
    """Sla op en blijf onder de grens; geeft (kB, kwaliteit, breedte) terug.

    Eerst de kwaliteit omlaag in stappen, en pas als dat niet genoeg is de breedte.
    Zo blijft de uitsnede leesbaar zolang het kan.
    """
    kwaliteit = KWALITEIT
    while True:
        beeld.save(pad, quality=kwaliteit, optimize=True)
        kb = os.path.getsize(pad) / 1024
        if kb <= grens_kb:
            return kb, kwaliteit, beeld.size[0]
        if kwaliteit > KWALITEIT_MIN:
            kwaliteit = max(KWALITEIT_MIN, kwaliteit - 12)
            continue
        if beeld.size[0] > 900:
            nieuw = int(beeld.size[0] * 0.8)
            beeld = beeld.resize((nieuw, max(1, round(beeld.size[1] * nieuw / beeld.size[0]))), Image.LANCZOS)
            kwaliteit = KWALITEIT
            continue
        return kb, kwaliteit, beeld.size[0]  # zo klein als het zinnig wordt


def overzicht(argumenten):
    Image.MAX_IMAGE_PIXELS = None  # krantenpagina's van 6000 x 9000 zijn geen bom maar een scan
    beeld = Image.open(argumenten.scan)
    breed, hoog = beeld.size
    klein = ImageOps.grayscale(beeld)
    klein.thumbnail((OVERZICHT_MAX, OVERZICHT_MAX), Image.LANCZOS)
    pad = _uitvoerpad(os.path.splitext(os.path.basename(argumenten.scan))[0] + "_overzicht.jpg")
    kb, kwaliteit, breedte_uit = _bewaar_onder_grens(klein, pad)
    factor = breed / breedte_uit
    print(f"origineel : {breed} x {hoog}")
    print(f"overzicht : {breedte_uit} x {klein.size[1]}  ({kb:.0f} kB, kwaliteit {kwaliteit})")
    print(f"schaal    : vermenigvuldig wat je op het overzicht meet met {factor:.2f}")
    if kb > GRENS_KB:
        print(f"LET OP    : boven de grens van {GRENS_KB} kB -- lees dit bestand liever in stroken")
    print(pad)


def strook(argumenten):
    Image.MAX_IMAGE_PIXELS = None
    beeld = ImageOps.grayscale(Image.open(argumenten.scan))
    x, y, breed, hoog = argumenten.x, argumenten.y, argumenten.breedte, argumenten.hoogte
    uitsnede = beeld.crop((x, y, x + breed, y + hoog))
    uitsnede = ImageOps.autocontrast(uitsnede, cutoff=argumenten.contrast)
    doelhoog = max(1, round(uitsnede.size[1] * STROOK_BREEDTE / uitsnede.size[0]))
    uitsnede = uitsnede.resize((STROOK_BREEDTE, doelhoog), Image.LANCZOS)
    naam = f"{os.path.splitext(os.path.basename(argumenten.scan))[0]}_{x}_{y}.jpg"
    pad = _uitvoerpad(naam)
    kb, kwaliteit, breedte_uit = _bewaar_onder_grens(uitsnede, pad)
    print(f"strook    : {breedte_uit} x {uitsnede.size[1]}  ({kb:.0f} kB, kwaliteit {kwaliteit})")
    if kwaliteit < KWALITEIT or breedte_uit < STROOK_BREEDTE:
        print(f"LET OP    : teruggeschaald om onder {GRENS_KB} kB te blijven. "
              "Is de tekst nu te vaag, neem dan een kleinere uitsnede in plaats van een lagere kwaliteit.")
    print(pad)


def main():
    ontleder = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    onder = ontleder.add_subparsers(dest="opdracht", required=True)

    o = onder.add_parser("overzicht", help="kleine grijswaardenversie van de hele scan")
    o.add_argument("scan")
    o.set_defaults(functie=overzicht)

    s = onder.add_parser("strook", help="uitsnede op volle resolutie, vergroot en met autocontrast")
    s.add_argument("scan")
    s.add_argument("x", type=int)
    s.add_argument("y", type=int)
    s.add_argument("breedte", type=int)
    s.add_argument("hoogte", type=int)
    s.add_argument("--contrast", type=int, default=1, help="autocontrast-cutoff in procenten (standaard 1)")
    s.set_defaults(functie=strook)

    argumenten = ontleder.parse_args()
    if not os.path.exists(argumenten.scan):
        sys.exit(f"bestaat niet: {argumenten.scan}")
    argumenten.functie(argumenten)


if __name__ == "__main__":
    main()

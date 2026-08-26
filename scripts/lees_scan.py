"""Maak van een aktescan een klein bestand dat de AI kan inlezen.

Waarom dit script bestaat: een scan uit het archief is 3 tot 8 MB en 5000 pixels
breed. Wie die rechtstreeks inleest stuurt megabytes over de verbinding, en achter
een inspecterende proxy (op veel werkplekken) is dat een van de dingen die een
ECONNRESET uitlokt. Bovendien is zo'n beeld op ooghoogte tóch onleesbaar.

De werkwijze in twee stappen:

    py scripts/lees_scan.py overzicht <scan>              # waar staat de akte?
    py scripts/lees_scan.py strook <scan> <x> <y> <b> <h> # lees de regels

Het overzicht is grijswaarden op maximaal 1500 pixels: genoeg om te zien welke
bladzijde en welk aktenummer je hebt, en meestal 100 tot 200 kB. De strook is
een uitsnede op volle resolutie, met autocontrast, opgeschaald tot een vaste
breedte -- dat is wat je nodig hebt om een naam of een datum écht te lezen.

Coördinaten geef je in het stelsel van de originele scan. Het overzicht print
de schaalfactor, zodat je van wat je op het overzicht ziet naar de echte
coördinaten kunt rekenen.
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


def _uitvoerpad(naam):
    map_ = os.path.join(os.environ.get("TEMP", "."), "scanlees")
    os.makedirs(map_, exist_ok=True)
    return os.path.join(map_, naam)


def overzicht(argumenten):
    beeld = Image.open(argumenten.scan)
    breed, hoog = beeld.size
    klein = ImageOps.grayscale(beeld)
    klein.thumbnail((OVERZICHT_MAX, OVERZICHT_MAX), Image.LANCZOS)
    pad = _uitvoerpad(os.path.splitext(os.path.basename(argumenten.scan))[0] + "_overzicht.jpg")
    klein.save(pad, quality=KWALITEIT, optimize=True)
    factor = breed / klein.size[0]
    print(f"origineel : {breed} x {hoog}")
    print(f"overzicht : {klein.size[0]} x {klein.size[1]}  ({os.path.getsize(pad) / 1024:.0f} kB)")
    print(f"schaal    : vermenigvuldig wat je op het overzicht meet met {factor:.2f}")
    print(pad)


def strook(argumenten):
    beeld = ImageOps.grayscale(Image.open(argumenten.scan))
    x, y, breed, hoog = argumenten.x, argumenten.y, argumenten.breedte, argumenten.hoogte
    uitsnede = beeld.crop((x, y, x + breed, y + hoog))
    uitsnede = ImageOps.autocontrast(uitsnede, cutoff=argumenten.contrast)
    doelhoog = max(1, round(uitsnede.size[1] * STROOK_BREEDTE / uitsnede.size[0]))
    uitsnede = uitsnede.resize((STROOK_BREEDTE, doelhoog), Image.LANCZOS)
    naam = f"{os.path.splitext(os.path.basename(argumenten.scan))[0]}_{x}_{y}.jpg"
    pad = _uitvoerpad(naam)
    uitsnede.save(pad, quality=KWALITEIT, optimize=True)
    print(f"strook    : {uitsnede.size[0]} x {uitsnede.size[1]}  ({os.path.getsize(pad) / 1024:.0f} kB)")
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

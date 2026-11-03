"""Knip een krantenbericht of een stuk akte uit een scan, voor opname in een verhaal of dossier.

Knipsels horen in de verhalen en in de levensloop van een dossier (zie CLAUDE.md,
"Knipsels: laat de lezer de bron zien"). Dit script snijdt de gevraagde rechthoek uit een
paginascan op VOLLE resolutie, maakt hem grijs met autocontrast, verkleint hem zo nodig tot
een leesbare breedte en schrijft hem naar boek/verhalen/beeld/.

Gebruik:
    py scripts/knipsel.py <scan> <x> <y> <breedte> <hoogte> <naam>
    py scripts/knipsel.py test/tijdelijk/krant/lc-1893-04-05-p3.png 410 2200 900 600 1893-04-05-leeuwarder-courant-dankbetuiging-weduwe

De coördinaten zijn die van de ORIGINELE scan: lees ze af op het overzicht van
scripts/lees_scan.py en vermenigvuldig met de schaalfactor die dat script print.
De naam krijgt .jpg erachter; gebruik JJJJ-MM-DD-bron-onderwerp, kleine letters, geen
accenten. Bij een akte: JJJJ-MM-DD-aktesoort-plaats-kern.

Waarom grijs en hooguit 1400 pixels breed: een krantenkolom is daar scherp leesbaar en het
bestand blijft rond de 100-300 kB, zodat de website en de PDF snel laden. Een foto of een
gekleurde kaart knip je met --kleur.

In het verhaal of dossier komt het knipsel vlak bij het citaat te staan:

    ![Leeuwarder Courant, 5 april 1893: dankbetuiging van de weduwe J. Berg](beeld/1893-04-05-...jpg)

Vanuit een dossier in personen/ is het pad ../boek/verhalen/beeld/<naam>.jpg. Het
onderschrift noemt bron en datum en de kern in de woorden van de bron. Het knipsel vervangt
de bronvermelding niet: de voetnoot of de regel **Bron:** blijft staan.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

R = Path(__file__).resolve().parents[1]
DOEL = R / "boek" / "verhalen" / "beeld"
MAX_BREED = 1400


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan")
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("breedte", type=int)
    ap.add_argument("hoogte", type=int)
    ap.add_argument("naam", help="bestandsnaam zonder extensie, bv. 1893-04-05-leeuwarder-courant-dankbetuiging")
    ap.add_argument("--kleur", action="store_true", help="kleur behouden (bij een gekleurde scan of foto)")
    ap.add_argument("--vergroot", type=float, default=1.0,
                    help="vergrotingsfactor (bv. 2) voor scans die alleen in lage resolutie bestaan")
    ap.add_argument("--overschrijf", action="store_true", help="een bestaand knipsel met deze naam vervangen")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    Image.MAX_IMAGE_PIXELS = None
    with Image.open(a.scan) as im:
        if a.x < 0 or a.y < 0 or a.x + a.breedte > im.width or a.y + a.hoogte > im.height:
            print(f"FOUT: de uitsnede valt buiten de scan ({im.width} x {im.height}); "
                  "reken de coördinaten na met de schaalfactor van lees_scan.py overzicht", file=sys.stderr)
            return 1
        vak = im.crop((a.x, a.y, a.x + a.breedte, a.y + a.hoogte))
        vak = vak.convert("RGB") if a.kleur else ImageOps.autocontrast(vak.convert("L"), cutoff=1)
        # Sommige krantenbanken leveren voor een deel van de jaargangen alleen een jpg van
        # ca. 1400 x 2048. Een kolom is dan zo'n 290 pixels breed; zonder vergroting is het
        # knipsel op de website te klein om te lezen.
        if a.vergroot != 1.0:
            vak = vak.resize((round(vak.width * a.vergroot), round(vak.height * a.vergroot)), Image.LANCZOS)
        if vak.width > MAX_BREED:
            vak = vak.resize((MAX_BREED, round(vak.height * MAX_BREED / vak.width)), Image.LANCZOS)
        DOEL.mkdir(parents=True, exist_ok=True)
        uit = DOEL / f"{a.naam}.jpg"
        if uit.exists() and not a.overschrijf:
            print(f"FOUT: {uit} bestaat al; kies een andere naam of gebruik --overschrijf", file=sys.stderr)
            return 1
        vak.save(uit, "JPEG", quality=82, optimize=True)
    kb = uit.stat().st_size // 1024
    print(f"knipsel: {uit.relative_to(R)}  ({vak.width} x {vak.height}, {kb} kB)")
    print(f"in een verhaal:  ![<bron, datum: de kern in de woorden van de bron>](beeld/{uit.name})")
    print(f"in een dossier:  ![<bron, datum: de kern in de woorden van de bron>](../boek/verhalen/beeld/{uit.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Zoek in Delpher (kranten) via de open SRU-API van de Koninklijke Bibliotheek.

Gebruik:
  py scripts/zoek_delpher.py zoek "Jansen AND Koudekerk"
  py scripts/zoek_delpher.py zoek "Jansen AND Koudekerk" --van 1925 --tot 1940
  py scripts/zoek_delpher.py zoek "Jansen AND Koudekerk" --krant Leidsch --plaats Leiden
  py scripts/zoek_delpher.py zoek "Jansen AND Koudekerk" --lees Jansen     # OCR-fragment per treffer
  py scripts/zoek_delpher.py toon ddd:010313885:mpeg21:a0043               # de OCR-tekst zelf

Waarom dit script bestaat. De website van Delpher is niet te doorzoeken met een
gewone HTTP-aanroep (JavaScript, en de zoekpagina geeft 403), waardoor Delpher in een
project gemakkelijk "niet bereikbaar" lijkt. De KB heeft er echter een open SRU-endpoint
bij zitten -- `jsru.kb.nl/sru/sru` -- dat geen sleutel vraagt en per treffer datum, krant,
pagina, kop en een resolver-URL geeft. Met `toon` komt daarna de **volledige OCR-tekst**
van het artikel binnen, en dat is precies wat een verhaal nodig heeft: een letterlijke
passage in plaats van een samenvatting.

Vier dingen om te weten voor je "niets gevonden" opschrijft:

* **Zet tussen élk woord een AND.** Losse woorden zonder AND worden als FRASE gezocht en
  geven stilzwijgend nul: `zoek "Jan de Vries Oudshoorn"` -> 0, `zoek "Vries AND
  Oudshoorn"` -> duizenden. Toets een onverwachte nul altijd eerst met een ijkpunt van
  één woord (`zoek "Oudshoorn"`) voordat je een muur opschrijft.
* **De API heeft geen werkend datumfilter.** `AND date="1931"` en
  `AND date within "..."` geven beide nul treffers -- niet omdat er niets is, maar
  omdat de index die vorm niet kent. Dit script haalt daarom eerst op en filtert
  **daarna zelf** op jaar, krant en plaats, en meldt onderaan hoeveel treffers het
  heeft doorzocht. Staat daar "N treffer(s) NIET doorzocht", dan is de zoekopdracht
  niet af: verhoog `--grens`.
* **De OCR is van oude kranten en zit vol fouten.** Zoek dus ook op spellingsvarianten
  en op de naam van de plaats erbij. Een naam die de OCR verminkt heeft, is met geen
  enkele zoekopdracht te vinden -- dat is een eigenschap van de bron, geen muur. Bij een
  landelijke bekendmaking (Staatscourant) staat hetzelfde bericht in tientallen kranten,
  elk met een eigen OCR: lees dan een andere krant, niet een andere zoekopdracht.
* **Delpher dekt alleen de KB-kranten.** Het plaatselijke nieuws staat vaak bij een
  regionale krantenbank: zie scripts/zoek_courant.py (Leiden, Alkmaar e.a.),
  zoek_dekrantvantoen.py (Leeuwarder Courant) en zoek_kbz.py (Krantenbank Zeeland).

Delpher is zelden bewijs voor een datum, maar vaak de enige bron voor het leven
eromheen: een gouden bruiloft, een ongeluk in de fabriek, een veiling, een
gemeentebericht. Neem een treffer op met krant, datum, pagina en de resolver-URL.

Een getal in de OCR is een lezing, geen feit: controleer het op de paginascan. De ALTO
van een pagina (`https://resolver.kb.nl/resolve?urn=<krant-id>:p002:alto`) geeft per woord
de positie (HPOS/VPOS) en de betrouwbaarheid (WC); de pagina zelf komt van `...:p002:image`
en is met scripts/lees_scan.py en scripts/knipsel.py te lezen en te knippen.
"""

import argparse
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

# Windows geeft een console met codepagina 1252, en oude krantenkoppen staan vol tekens die
# daar niet in passen: de ij-ligatuur, lange s, gedachtestreepjes. Zonder deze regel knapt
# het script halverwege de uitvoer af met een UnicodeEncodeError -- en dat lijkt op "geen
# treffers meer" terwijl er gewoon nog een bladzijde volgt.
for _stroom in (sys.stdout, sys.stderr):
    try:
        _stroom.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # oudere Python of omgeleide uitvoer
        pass

SRU = "https://jsru.kb.nl/sru/sru"
RESOLVER = "https://resolver.kb.nl/resolve?urn="

# Per aanroep haalt de API maximaal honderd records; dit is hoeveel er in totaal
# doorgebladerd wordt als het script zelf moet filteren. Zelfde afspraak als in
# zoek_openarch.py: liever een expliciete grens met melding dan stilzwijgend afknappen.
GRENS_STANDAARD = 400

NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ddd": "http://www.kb.nl/ddd",
}


def _haal(url):
    # Via curl: die gebruikt het certificaatarchief van het systeem, wat achter een
    # inspecterende proxy (werkplekken) vaak de enige werkende vertrouwensketen is.
    # De KB geeft bij te veel verzoeken HTTP 429 ("Too Many Requests"). Met --fail leek
    # dat op "de API antwoordde niet" en dus op een storing; het is gewoon een
    # snelheidslimiet, bijvoorbeeld als meerdere zoekers tegelijk draaien. Wacht en
    # probeer opnieuw, en zeg het eerlijk als het niet lukt.
    for poging in range(6):
        uitvoer = subprocess.run(
            ["curl", "-sL", "-w", "\n%{http_code}", url], capture_output=True, timeout=90
        )
        tekst = uitvoer.stdout.decode("utf-8", errors="replace")
        lichaam, _, code = tekst.rpartition("\n")
        if code == "200":
            return lichaam
        if code == "429":
            wacht = 15 * (poging + 1)
            print(f"(KB-API: HTTP 429, te veel verzoeken -- {wacht} s wachten)", file=sys.stderr)
            time.sleep(wacht)
            continue
        raise subprocess.CalledProcessError(22, ["curl", url], output=f"HTTP {code}")
    raise subprocess.CalledProcessError(22, ["curl", url], output="HTTP 429 na zes pogingen")


def _tekst(element, pad):
    gevonden = element.find(pad, NS)
    return (gevonden.text or "").strip() if gevonden is not None else ""


def _records(term, collectie, grens):
    """Blader door de SRU-resultaten. Geeft (lijst met records, totaal, doorzocht)."""
    records = []
    totaal = None
    start = 1
    while start <= grens:
        aantal = min(100, grens - start + 1)
        url = (
            f"{SRU}?operation=searchRetrieve&x-collection={collectie}"
            f"&recordSchema=ddd&maximumRecords={aantal}&startRecord={start}"
            f"&query={urllib.parse.quote(term)}"
        )
        boom = ET.fromstring(_haal(url))
        if totaal is None:
            gevonden = boom.find("srw:numberOfRecords", NS)
            totaal = int(gevonden.text) if gevonden is not None else 0
        blok = boom.findall(".//srw:record/srw:recordData", NS)
        if not blok:
            break
        records.extend(blok)
        start += len(blok)
        if len(records) >= totaal:
            break
    return records, totaal or 0, len(records)


def _ocr(sleutel):
    """Volledige OCR-tekst van een artikel als één string (of "" als het niet lukt)."""
    if not sleutel.endswith(":ocr"):
        sleutel = f"{sleutel}:ocr"
    try:
        boom = ET.fromstring(_haal(f"{RESOLVER}{urllib.parse.quote(sleutel)}"))
    except (subprocess.CalledProcessError, ET.ParseError):
        return ""
    return "\n".join((p.text or "").strip() for p in boom.iter("p"))


def _fragmenten(tekst, woord, breedte=220, maximum=2):
    """Stukjes tekst rond `woord` (hoofdletterongevoelig; een spatie in het woord mag in
    de OCR ook een regeleinde zijn)."""
    patroon = re.compile(r"\s+".join(map(re.escape, woord.split())), re.I)
    uit = []
    for m in patroon.finditer(tekst):
        a, b = max(0, m.start() - breedte), m.end() + breedte
        uit.append(" ".join(tekst[a:b].split()))
        if len(uit) >= maximum:
            break
    return uit


def _jaar(datum):
    treffer = re.match(r"(\d{4})", datum or "")
    return int(treffer.group(1)) if treffer else None


def lijkt_frase(term):
    """Losse woorden zonder AND/OR worden door de API als frase gezocht: stille nul."""
    woorden = term.split()
    return len(woorden) > 1 and not re.search(r"\b(AND|OR|NOT)\b", term) and '"' not in term


def waarschuw_frase(term):
    woorden = term.split()
    if lijkt_frase(term):
        print(
            f"WAARSCHUWING: '{term}' wordt als FRASE gezocht (de woorden moeten dan letterlijk "
            f"achter elkaar staan) en geeft dan gemakkelijk nul. Bedoelde je "
            f"'{' AND '.join(woorden)}'?"
        )


def zoek(args):
    waarschuw_frase(args.term)
    try:
        records, totaal, doorzocht = _records(args.term, args.collectie, args.grens)
    except subprocess.CalledProcessError as fout:
        print(f"De KB-API antwoordde niet: {fout}", file=sys.stderr)
        return 1

    print(f"{totaal} treffer(s) voor '{args.term}' in {args.collectie}")

    regels = []
    for record in records:
        datum = _tekst(record, "dc:date")
        jaar = _jaar(datum)
        krant = _tekst(record, "ddd:papertitle")
        plaats = _tekst(record, "ddd:spatialCreation")
        gebied = _tekst(record, "ddd:spatial")
        kop = _tekst(record, "dc:title")
        sleutel = _tekst(record, "ddd:metadataKey")
        bladzijde = _tekst(record, "ddd:page")

        if args.van and (jaar is None or jaar < args.van):
            continue
        if args.tot and (jaar is None or jaar > args.tot):
            continue
        if args.krant and args.krant.lower() not in krant.lower():
            continue
        if args.plaats and args.plaats.lower() not in f"{plaats} {gebied}".lower():
            continue

        regel = (
            f"- {datum[:10]:12s} {krant[:38]:38s} p.{bladzijde:3s} {kop[:52]}\n"
            f"    {sleutel}"
        )
        # --lees: de SRU-respons heeft geen snippets, dus zonder dit is een trefferlijst
        # een rij koppen als "Burgerlijke Stand." waar je niets aan ziet. Kost één
        # verzoek per getoonde treffer.
        if args.lees:
            frag = _fragmenten(_ocr(sleutel), args.lees)
            if frag:
                regel += "".join(f"\n      » {f}" for f in frag)
            else:
                regel += f"\n      ('{args.lees}' niet in de OCR)"
        regels.append(regel)

    for regel in regels:
        print(regel)

    if args.van or args.tot or args.krant or args.plaats:
        print(f"({len(regels)} na filteren, {doorzocht} treffer(s) doorzocht)")
    rest = totaal - doorzocht
    if rest > 0:
        print(f"⚠ {rest} treffer(s) NIET doorzocht -- verhoog --grens om verder te kijken.")
    return 0


def toon(args):
    if args.woord:
        for f in _fragmenten(_ocr(args.sleutel), args.woord, breedte=600, maximum=5):
            print(f"» {f}\n")
        print(f"Bron-URL: {RESOLVER}{args.sleutel.removesuffix(':ocr')}")
        return 0
    sleutel = args.sleutel
    if not sleutel.endswith(":ocr"):
        sleutel = f"{sleutel}:ocr"
    try:
        ruw = _haal(f"{RESOLVER}{urllib.parse.quote(sleutel)}")
    except subprocess.CalledProcessError as fout:
        print(f"Geen OCR-tekst op te halen voor {sleutel}: {fout}", file=sys.stderr)
        return 1

    try:
        boom = ET.fromstring(ruw)
    except ET.ParseError:
        print(ruw)
        return 0

    kop = boom.findtext("title") or ""
    if kop:
        print(f"# {kop.strip()}\n")
    for alinea in boom.iter("p"):
        if alinea.text:
            print(alinea.text.strip())
            print()
    basis = sleutel[: -len(":ocr")]
    print(f"Bron-URL: {RESOLVER}{basis}")
    return 0


def main():
    ontleder = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    onder = ontleder.add_subparsers(dest="opdracht", required=True)

    z = onder.add_parser("zoek", help="zoek in krantenartikelen")
    z.add_argument("term", help="zoekterm; zet AND tussen de woorden")
    z.add_argument("--van", type=int, help="alleen artikelen vanaf dit jaar")
    z.add_argument("--tot", type=int, help="alleen artikelen tot en met dit jaar")
    z.add_argument("--krant", help="deel van de krantennaam, bijv. Leidsch")
    z.add_argument("--plaats", help="plaats of gebied van uitgave, bijv. Leiden")
    z.add_argument("--collectie", default="DDD_artikel", help="DDD_artikel (standaard)")
    z.add_argument("--grens", type=int, default=GRENS_STANDAARD)
    z.add_argument("--lees", metavar="WOORD",
                   help="haal per treffer de OCR op en toon de tekst rond WOORD")
    z.set_defaults(functie=zoek)

    t = onder.add_parser("toon", help="haal de volledige OCR-tekst van een artikel op")
    t.add_argument("sleutel", help="bijv. ddd:010313885:mpeg21:a0043")
    t.add_argument("--woord", help="toon alleen de tekst rond dit woord")
    t.set_defaults(functie=toon)

    args = ontleder.parse_args()
    return args.functie(args)


if __name__ == "__main__":
    sys.exit(main())

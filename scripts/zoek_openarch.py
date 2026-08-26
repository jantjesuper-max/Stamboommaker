"""Zoek in Open Archieven (api.openarch.nl) — de brede ingang op Nederlandse aktes.

Gebruik:
  py scripts/zoek_openarch.py zoek "Jan Hendriks Jansen"            # zoeken op naam
  py scripts/zoek_openarch.py zoek "Jan Jansen" --type Geboorte --van 1860 --tot 1870
  py scripts/zoek_openarch.py toon frl:1102624b-...                 # detail + bron + scans

Geen API-key nodig. De detailweergave geeft de volledige bronvermelding
(instelling, collectie, boek/aktenummer, folio) en waar beschikbaar scan-URL's.
Let op: een treffer is pas bewijs na controle van datum, plaats en relaties —
naamgenoten zijn de grootste valkuil (zie CLAUDE.md).

GELDIGE WAARDEN VOOR --type (gebeurtenistype). Verzin hier niets: een niet-bestaande
waarde geeft stilzwijgend NUL treffers, en dat lijkt dan op een muur terwijl het een
filterfout is.

    Geboorte · Doop · Ondertrouw · Trouwen · Huwelijk · Overlijden · Begrafenis
    Registratie · Inschrijving · Notariële inschrijving

Voor voorouders van vóór 1811 zijn **Doop**, **Ondertrouw**, **Trouwen** en
**Begrafenis** de bruikbare typen; Geboorte/Huwelijk/Overlijden bestaan pas met de
burgerlijke stand. `Begrafenis` (DTB Begraven) is de enige ingang op een sterfgeval
vóór 1811 en wordt gemakkelijk vergeten.

Het bróntype (DTB Dopen, DTB Begraven, DTB Lidmaten, Bevolkingsregister, Stamboeken,
BS Huwelijk, ...) is iets anders dan het gebeurtenistype en zit niet in de API-filter.
Daarvoor is `--brontype`, dat na het ophalen filtert.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.parse

BASIS = "https://api.openarch.nl/1.1/records"

# Hoeveel treffers het script maximaal doorbladert als het zelf moet filteren. Een
# veelvoorkomende naam geeft duizenden treffers; ergens moet een grens liggen. Wordt die
# geraakt, dan zegt het script dat erbij — zodat "niets gevonden" nooit stilzwijgend afknapt.
PAGINEER_MAX = 600


def _haal(url):
    # Via curl.exe: die gebruikt het Windows-certificaatarchief, dat op deze
    # werklaptop (TLS-inspectie) wél de juiste vertrouwensketen heeft.
    uitvoer = subprocess.run(
        ["curl", "-s", "--fail", url], capture_output=True, timeout=60, check=True
    )
    return json.loads(uitvoer.stdout.decode("utf-8"))


# Waarden die de API daadwerkelijk als `eventtype` kent. Een typefout of een verzonnen
# waarde geeft nul treffers zonder foutmelding — vandaar de waarschuwing in zoek().
GEBEURTENISTYPEN = {
    "Geboorte",
    "Doop",
    "Ondertrouw",
    "Trouwen",
    "Huwelijk",
    "Overlijden",
    "Begrafenis",
    "Registratie",
    "Inschrijving",
    "Notariële inschrijving",
}


def _fullsize(uri):
    """Zet een Memorix-thumb-URL om naar de fullsize-variant.

    De API geeft alleen `thumb/<breedte>x<hoogte>/<pad>`, en dat is voor jp2-scans vaak
    een 404 — waardoor het lijkt of het document viewer-only is. De route
    `download/fullsize/<pad>` levert wél de volledige scan (als JPEG, ruim 2000 px breed,
    enkele MB's). Ontdekt bij een naamsaannemingsregister uit 1811 dat als "viewer-only"
    was afgeschreven en het niet bleek te zijn.
    """
    if not uri or "/thumb/" not in uri:
        return None
    voor, _, na = uri.partition("/thumb/")
    _, _, pad = na.partition("/")  # het formaat-segment (bijv. 640x480) eraf halen
    return f"{voor}/download/fullsize/{pad}" if pad else None


def _iiif(uri):
    """Zet een IIIF-scan-URI om naar de volledige afbeelding.

    Erfgoed Leiden (en enkele andere archieven) leveren hun scans via een IIIF-beeldserver.
    De API geeft dan geen thumb maar de *informatiebeschrijving* van de afbeelding:
    `.../iiif/3/<uuid>/info.json`. Die URL levert JSON en geen plaatje, dus wie hem
    downloadt houdt een paar honderd bytes metadata over en denkt dat de scan er niet is.
    De afbeelding zelf staat op `.../<uuid>/full/max/0/default.jpg` — het volledige blad,
    bij een doopboek ruim 3500 px breed en ongeveer 1,3 MB.

    Ontdekt bij een doopboek uit 1799 dat via de thumb-route onvindbaar leek en langs
    deze route in volledige resolutie binnenkwam (3541 x 2823 px).
    """
    if not uri or "/iiif/" not in uri:
        return None
    basis = uri.rsplit("/", 1)[0] if uri.endswith("/info.json") else uri.rstrip("/")
    return f"{basis}/full/max/0/default.jpg"


def _lijst(waarde):
    """Eén veld of een lijst van velden, altijd als lijst.

    De API geeft een veld dat één keer voorkomt als dict en hetzelfde veld bij twee
    voorkomens als lijst van dicts. Wie daar niet op rekent, leest bij precies die records
    waar het interessant wordt (twee opmerkingen, twee gebeurtenissen) niets uit.
    """
    if waarde in (None, "", []):
        return []
    return waarde if isinstance(waarde, list) else [waarde]


def _datum(d):
    """Datum uit een API-veld.

    De zoek-endpoint levert de sleutels in kleine letters (day/month/year), de
    show-endpoint met een hoofdletter (Day/Month/Year), en niet altijd met een
    voorloopnul. Wie maar een van de twee schrijfwijzen leest, denkt bij elke
    getoonde akte dat de datum ontbreekt.
    """
    if not isinstance(d, dict):
        return "?"

    def veld(naam):
        return d.get(naam) or d.get(naam.capitalize())

    jaar = veld("year")
    if not jaar:
        return "?"
    dag, maand = veld("day"), veld("month")
    dag = str(dag).zfill(2) if dag else "??"
    maand = str(maand).zfill(2) if maand else "??"
    return f"{dag}-{maand}-{jaar}"


def zoek(argumenten):
    parameters = {
        "name": argumenten.naam,
        "number_show": str(argumenten.aantal),
        "start": str(argumenten.start),
        "lang": "nl",
    }
    if argumenten.type:
        if argumenten.type not in GEBEURTENISTYPEN:
            print(
                f"WAARSCHUWING: '{argumenten.type}' is geen bekend gebeurtenistype. "
                f"De API geeft dan stilzwijgend nul treffers — dat is géén muur.\n"
                f"Geldig: {' · '.join(sorted(GEBEURTENISTYPEN))}\n"
                f"Bedoelde je een bróntype (DTB Lidmaten, Bevolkingsregister)? Gebruik --brontype."
            )
        parameters["eventtype"] = argumenten.type
    if argumenten.plaats:
        parameters["eventplace"] = argumenten.plaats
    if argumenten.archief:
        parameters["archive"] = argumenten.archief
    # --van/--tot en --brontype zitten niet in de API en worden hier gefilterd. Wie dan
    # één pagina ophaalt, filtert alleen die pagina en ziet een lege lijst waar de akte
    # gewoon op pagina drie stond. Dat is twee keer als "muur" opgeschreven terwijl het
    # gereedschap faalde, dus bij een eigen filter pagineert het script nu zelf door.
    zelf_filteren = bool(argumenten.van or argumenten.tot or argumenten.brontype)
    # Bij een zeldzame naam is 600 ruim; bij een veelvoorkomende naam (duizenden treffers)
    # verbergt die grens juist de treffers die je zoekt, en dan lijkt een onvoltooide
    # zoekopdracht een muur. --grens zet hem hoger voor die ene zoekopdracht.
    grens = argumenten.grens or PAGINEER_MAX
    gevonden = getoond = 0
    start, totaal = argumenten.start, None
    while True:
        parameters["start"] = str(start)
        data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(parameters)}")
        respons = data.get("response", {})
        if totaal is None:
            totaal = int(respons.get("number_found", 0) or 0)
            print(f"{totaal} treffers voor '{argumenten.naam}'")
        documenten = respons.get("docs", [])
        if not documenten:
            break
        for record in documenten:
            gevonden += 1
            datum = record.get("eventdate") or {}
            jaar = datum.get("year")
            if argumenten.van and (not jaar or int(jaar) < argumenten.van):
                continue
            if argumenten.tot and (not jaar or int(jaar) > argumenten.tot):
                continue
            if argumenten.brontype and argumenten.brontype.lower() not in str(
                record.get("sourcetype", "")
            ).lower():
                continue
            getoond += 1
            plaats = ", ".join(record.get("eventplace") or [])
            code = record.get("url", "").rsplit("/", 1)[-1]
            namen = "; ".join(
                f"{p.get('relationtype', '?')}: {p.get('name', '?')}"
                for p in record.get("persons", [])
            ) if record.get("persons") else ""
            print(f"- {record.get('eventtype'):<12} {_datum(datum):>10}  {plaats:<20} [{record.get('archive')}]  {code}")
            if namen:
                print(f"    {namen}")
        start += len(documenten)
        if not zelf_filteren or start >= min(totaal, grens):
            break
    if zelf_filteren:
        rest = max(0, totaal - gevonden)
        staart = f" · {rest} treffer(s) niet doorzocht (grens {grens}; verhoog met --grens)" if rest else ""
        print(f"({getoond} na filteren, {gevonden} treffers doorzocht{staart})")


def toon(argumenten):
    archief, _, identifier = argumenten.record.partition(":")
    url = f"{BASIS}/show.json?archive={archief}&identifier={identifier}&lang=nl"
    # De permalink hoort in elk onderzoekslog (zie CLAUDE.md, "Onderzoekslogs:
    # reproduceerbaar, met links"): dit is de URL waarmee een lezer het record
    # zelf kan nachecken. Zelfde opbouw als het url-veld dat search.json geeft.
    print(f"Permalink: https://www.openarchieven.nl/{archief}:{identifier}")
    data = _haal(url)
    records = data if isinstance(data, list) else [data]
    for record in records:
        persoon = record.get("Person") or {}
        personen = persoon if isinstance(persoon, list) else [persoon]
        # De rol (Overledene, Vader, Moeder, Bruid, Kind, ...) staat in RelationEP en is
        # het belangrijkste veld van een akte: zonder rol weet je niet WIE er centraal
        # staat. Gok nooit op de volgorde waarin de personen terugkomen.
        relaties = record.get("RelationEP") or {}
        relaties = relaties if isinstance(relaties, list) else [relaties]
        rol_van = {r.get("PersonKeyRef"): r.get("RelationType") for r in relaties}
        for p in personen:
            naam = p.get("PersonName", {})
            # PersonNamePatronym hoort ertussen. Vóór 1811 is het patroniem het énige wat
            # twee naamgenoten scheidt: "Sioerd Tijsses" is een andere man dan "Sjoerd
            # Jelles". Het veld werd eerder weggegooid, waardoor de ouders bij een doop van
            # 1785 als "Sjoert en Hil" verschenen en de akte onkoppelbaar leek.
            volledig = " ".join(
                x for x in (
                    naam.get("PersonNameFirstName"),
                    naam.get("PersonNamePatronym"),
                    naam.get("PersonNamePrefixLastName"),
                    naam.get("PersonNameLastName"),
                ) if x
            )
            rol = rol_van.get(p.get("@pid")) or "rol onbekend"
            extra = []
            leeftijd = (p.get("Age") or {}).get("PersonAgeLiteral")
            if leeftijd:
                extra.append(leeftijd)
            if p.get("BirthDate"):
                extra.append(f"geb. {_datum(p['BirthDate'])}")
            if p.get("Profession"):
                extra.append(str(p["Profession"]))
            achtervoegsel = f" ({', '.join(extra)})" if extra else ""
            print(f"  {rol:<12} {volledig}{achtervoegsel}")
        gebeurtenis = record.get("Event") or {}
        gebeurtenissen = gebeurtenis if isinstance(gebeurtenis, list) else [gebeurtenis]
        bron = record.get("Source") or {}
        for g in gebeurtenissen:
            # EventPlace ontbreekt vaak; de gemeente staat dan alleen in de bron.
            plaats = (g.get("EventPlace") or {}).get("Place") or (bron.get("SourcePlace") or {}).get("Place") or "?"
            print(f"Gebeurtenis: {g.get('EventType')} op {_datum(g.get('EventDate'))} te {plaats}")
            # EventRemark is bij bevolkingsregisters het KAARTNUMMER, en dat is het enige
            # waarmee je een gezinskaart bij het archief kunt opvragen. Zonder dit veld is
            # "hij staat in het bevolkingsregister van dat dorp" een mededeling zonder
            # vindplaats; mét dit veld is het "inv. 145.1.02-460, gezinskaart 916" en kun je
            # de kaart aanvragen. Zo werd een afstammingsvraag van een zoektocht een aanvraag.
            for opmerking in _lijst(g.get("EventRemark")):
                if opmerking.get("Value"):
                    # De sleutel heet in deze collectie "12 Kaart" of "92 Kaart"; het
                    # nummer ervoor is een veldnummer van de aanleverende instelling en
                    # zegt niets. Alleen het woord erachter is informatie.
                    label = re.sub(r"^\d+\s+", "", str(opmerking.get("@Key") or "opmerking"))
                    print(f"  {label}: {opmerking['Value']}")
        verwijzing = bron.get("SourceReference") or {}
        print("Bron:")
        print(f"  type: {bron.get('SourceType')}  plaats: {(bron.get('SourcePlace') or {}).get('Place')}")
        if verwijzing.get("Archive"):
            # Het archief-/toegangsnummer hoort in elke bronvermelding (zie CLAUDE.md) en
            # is bij bevolkingsregisters het deel waarmee je het register aanvraagt:
            # "145.1.02-460" is inventarisnummer 460 van toegang 145.1.02.
            print(f"  Archive: {verwijzing['Archive']}")
        for sleutel in ("InstitutionName", "Place", "Collection", "Book", "RegistryNumber", "DocumentNumber", "Folio"):
            if verwijzing.get(sleutel):
                print(f"  {sleutel}: {verwijzing[sleutel]}")
        # SourceIndexDate is de periode die het REGISTER dekt, niet de datum van een
        # gebeurtenis. Bij bevolkings- en gezinskaartenregisters is dat het antwoord op de
        # vraag die je werkelijk hebt: welke jaren van dit leven staan op deze kaart? De
        # gezinskaarten van één gemeente bleken zo 1920-1938 te dekken — precies het venster
        # waarin de voorouder in kwestie trouwde en haar kinderen kreeg.
        periode = bron.get("SourceIndexDate") or {}
        if periode.get("From") or periode.get("To"):
            print(f"  registerperiode: {periode.get('From', '?')} t/m {periode.get('To', '?')}")
        if bron.get("SourceDigitalOriginal"):
            print(f"  origineel: {bron['SourceDigitalOriginal']}")
        # SourceRemark bevat bij sommige collecties een volledig uitgewerkte samenvatting.
        # Bij "Friese militairen onder Napoleon" stond daar in één alinea dat Lammert
        # een voorouder plaatsvervanger was voor een boerenzoon uit het buurdorp, met zijn
        # ouders, zijn beroep, zijn woonplaats en de notarisakte erbij. Dat is soms meer
        # dan de akte zelf geeft, dus print het altijd. HTML eruit, want er zit soms
        # <b> en <a href> in.
        opmerkingen = bron.get("SourceRemark") or []
        opmerkingen = opmerkingen if isinstance(opmerkingen, list) else [opmerkingen]
        for opmerking in opmerkingen:
            sleutel = opmerking.get("@Key")
            if sleutel in (None, "Provenance"):   # herkomst van de XML-export, niet inhoudelijk
                continue
            tekst = re.sub(r"<[^>]+>", " ", str(opmerking.get("Value", "")))
            tekst = re.sub(r"\s+", " ", tekst).strip()
            if tekst and "voor suggesties scans" not in tekst:
                print(f"  {sleutel}: {tekst}")
        scans = (bron.get("SourceAvailableScans") or {}).get("Scan")
        if scans:
            scans = scans if isinstance(scans, list) else [scans]
            print(f"Scans ({len(scans)}):")
            for scan in scans:
                uri = scan.get("Uri") or ""
                print(f"  thumb:    {uri}")
                groot = _fullsize(uri) or _iiif(uri)
                if groot:
                    print(f"  FULLSIZE: {groot}")
        else:
            print("Scans: geen bij dit record — bronvermelding opnemen met [nog te downloaden]")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="opdracht", required=True)
    z = sub.add_parser("zoek")
    z.add_argument("naam")
    z.add_argument(
        "--type",
        help="gebeurtenistype; geldig: " + " · ".join(sorted(GEBEURTENISTYPEN)),
    )
    z.add_argument(
        "--brontype",
        help="filtert op bróntype na ophalen, bijv. 'DTB Begraven', 'DTB Lidmaten', "
        "'Bevolkingsregister', 'Stamboeken'",
    )
    z.add_argument("--plaats")
    z.add_argument("--archief", help="bijv. frl (AlleFriezen), dra (AlleDrenten), zar (Zeeuws Archief)")
    z.add_argument("--van", type=int, help="jaar vanaf")
    z.add_argument("--tot", type=int, help="jaar tot en met")
    z.add_argument("--aantal", type=int, default=30)
    z.add_argument("--start", type=int, default=0, help="paginering: sla de eerste N treffers over")
    z.add_argument("--grens", type=int, default=None,
                   help=f"hoeveel treffers het script bij --van/--tot/--brontype maximaal doorzoekt (standaard {PAGINEER_MAX}); verhoog dit als de uitvoer meldt dat er treffers niet doorzocht zijn")
    z.set_defaults(func=zoek)
    t = sub.add_parser("toon")
    t.add_argument("record", help="archief:identifier, bijv. frl:1102624b-...")
    t.set_defaults(func=toon)
    argumenten = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    argumenten.func(argumenten)


if __name__ == "__main__":
    main()

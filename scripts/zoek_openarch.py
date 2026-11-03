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
import time
import urllib.parse

BASIS = "https://api.openarch.nl/1.1/records"

# Hoeveel treffers het script maximaal doorbladert als het zelf moet filteren. Een naam als
# "Jan de Vries" geeft duizenden treffers; ergens moet een grens liggen. Wordt die geraakt,
# dan zegt het script dat erbij — zodat "niets gevonden" nooit stilzwijgend afknapt.
PAGINEER_MAX = 600


def _haal(url, pogingen=4):
    # Via curl.exe: die gebruikt het Windows-certificaatarchief, dat op deze
    # werklaptop (TLS-inspectie) wél de juiste vertrouwensketen heeft.
    #
    # Mét herhaalpoging, en dat is geen luxe: bij het doorpagineren van een brede
    # naam (een achternaam met bijna zevenduizend treffers) gaf de API op pagina vijf
    # één keer een fout, waarop de héle zoekopdracht met een traceback afbrak. Een
    # incidentele netwerkfout las daardoor als een muur. Vier pogingen met oplopende
    # wachttijd, en pas dan opgeven.
    laatste = None
    for poging in range(pogingen):
        try:
            uitvoer = subprocess.run(
                ["curl", "-s", "--fail", url], capture_output=True, timeout=60, check=True
            )
            return json.loads(uitvoer.stdout.decode("utf-8"))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as fout:
            laatste = fout
            if poging < pogingen - 1:
                time.sleep(2 * (poging + 1))
    raise laatste


# Waarden die de API daadwerkelijk als `eventtype` kent. Een typefout of een verzonnen
# waarde geeft nul treffers zonder foutmelding — vandaar de waarschuwing in zoek().
#
# ⚠ Gemeten op 27-08-2026, met `name=Jansen` als ijkpunt: negen van deze tien waarden geven
# tienduizenden treffers, en één gaf er NUL. Dat was **"Begrafenis"** — de waarde die tot dan
# toe in deze lijst én in CLAUDE.md stond als "de enige ingang op een sterfgeval vóór 1811".
# De API wil **"Begraven"**: `eventtype=Begrafenis` → 0, `eventtype=Begraven` → 53.198.
# Verwarrend genoeg is *Begrafenis* wél de waarde die de API in het veld `eventtype` van een
# record terúggeeft, dus wie de uitvoer naschrijft komt vanzelf op de dode waarde uit —
# dezelfde valkuil als bij "Memories van successie" hierboven.
#
# Dit is de derde keer in dit project dat een muur een gereedschapsprobleem bleek. Het gevolg
# was hier extra stil: `--type Begrafenis` gaf geen foutmelding en geen waarschuwing, want de
# waarde stond keurig in deze lijst. BEGRAVEN_ALIAS vertaalt hem daarom door, zodat oude
# commando's uit het logboek blijven werken en alsnog het juiste antwoord geven.
GEBEURTENISTYPEN = {
    "Geboorte",
    "Doop",
    "Ondertrouw",
    "Trouwen",
    "Huwelijk",
    "Overlijden",
    "Begraven",
    "Begrafenis",  # blijft toegestaan, wordt vertaald — zie BEGRAVEN_ALIAS
    "Registratie",
    "Inschrijving",
    "Notariële inschrijving",
}

# Waarden die de gebruiker mag intikken maar die de API anders wil zien.
BEGRAVEN_ALIAS = {"Begrafenis": "Begraven"}


# Archiefcodes die de API daadwerkelijk kent. Net als bij `eventtype` geeft een onbekende
# code **stilzwijgend nul treffers** — geen foutmelding, geen waarschuwing.
#
# ⚠ Gemeten op 28-08-2026 met `name=Jansen` als ijkpunt, en de helptekst van dit script zelf
# was fout: daar stond jarenlang `dra (AlleDrenten)`, en `--archief dra` geeft **0**. De
# Drentse code is **dar**, en die geeft er 46.298. Wie de helptekst volgde, mat dus voor élke
# Drentse zoekopdracht een lege provincie — en dat valt pas op bij een stamboom met een
# Drentse tak. Vierde keer dat een muur een gereedschapsprobleem bleek.
ARCHIEFCODES = {
    "frl": "AlleFriezen (Tresoar)",
    "dar": "Drents Archief",
    "hco": "Collectie Overijssel",
    "wfa": "Westfries Archief",
    "nha": "Noord-Hollands Archief",
    "zar": "Zeeuws Archief",
    "gld": "Gelders Archief",
    "eal": "Erfgoedcentrum Achterhoek en Liemers",
    "gaz": "Gemeentearchief Zaanstad",
    "swl": "Gemeentearchief Steenwijkerland",
    "elo": "Erfgoed Leiden en omstreken",
    # Aangevuld 18-10-2026, gemeten met name=Jansen: raa 7.558 · wat 1.686. Beide werden
    # als ONBEKEND gemeld terwijl zij werken. 'raa' levert de burgerlijke stand en het
    # bevolkingsregister van Den Helder, Texel en Alkmaar; 'wat' de DTB van
    # Edam en Volendam.
    "raa": "Regionaal Archief Alkmaar (Den Helder, Texel, Alkmaar e.o.)",
    "wat": "Waterlands Archief (Purmerend, Edam, Volendam)",
    # Aangevuld 29-08-2026. Deze acht codes werden door het script als ONBEKEND
    # gemeld, en de waarschuwing zei erbij dat een onbekende code stilzwijgend nul
    # geeft — terwijl zij alle acht gewoon werken. Gemeten met het ijkpunt
    # name=Jansen: prs 431 · dva 77 · saa 118.511 · hua 94.648 · gra 39.354 ·
    # ghn 20.575 · ohg 841 · abl 343. (Ter controle: 'uta' en 'nla' geven wél nul,
    # dus het waarschuwingsmechanisme zelf klopt — alleen de lijst was te kort.)
    "saa": "Stadsarchief Amsterdam",
    "hua": "Het Utrechts Archief",
    "gra": "AlleGroningers",
    "ghn": "Nationaal Archief (gahetNA)",
    "ohg": "Gemeentearchief Ommen-Hardenberg",
    "prs": "Particuliere prentjescollecties (bidprentjes)",
    "dva": "Oudheidkundige Kring De Vier Ambachten (Zeeuws-Vlaanderen)",
    # Gemeten 30-08-2026 bij een doop te Breda (1754): Bredase
    # DTB-records staan DUBBEL, bij het Stadsarchief Breda ('brd') en het BHIC
    # ('bhi'). Scans bij 'brd' via images.memorix.nl/brd/thumb/2000x2000/… —
    # het download/fullsize-endpoint geeft daar een 404 van de Pictura-server.
    "brd": "Stadsarchief Breda",
    "bhi": "Brabants Historisch Informatie Centrum (BHIC)",
    "wba": "West Brabants Archief (Bergen op Zoom e.o., o.a. Steenbergen)",
    "vls": "Gemeentearchief Vlissingen",
    "szu": "Regionaal archief Zutphen (huis-, burger-, zitplaats- en weeskamerregisters; geen DTB Dopen)",
    "rat": "Regionaal Archief Tilburg",
    # Toegevoegd 06-09-2026, gemeten met name=Jansen: rel geeft 5239 treffers.
    # ⓵ RHC Rijnstreek en Lopikerwaard dekt BODEGRAVEN, WOERDEN en Montfoort, en dat
    # is precies het gebied van een Rijnstreek-lijn. Het is een ander archief dan
    # 'elo' (Erfgoed Leiden), waarmee die tak tot deze datum werd doorzocht — het
    # doopregister van Bodegraven zit hier en niet daar. ⚠ Bodegraven heeft in deze
    # index wél 33.629 dopen en 22.812 begrafenissen maar GEEN DTB Trouwen; wie daar
    # een huwelijk zoekt, zoekt in een register dat niet bestaat.
    "rel": "RHC Rijnstreek en Lopikerwaard (Bodegraven, Woerden, Montfoort)",
    # Toegevoegd 15-10-2026 gemeten met
    # name=Jansen: ozw 83 treffers. Klein, maar het heeft het BEVOLKINGSREGISTER van
    # ZOETERWOUDE 1826-1939 met vestigings- en vertrekdatum, vorige woonplaats, adres
    # en kerkgenootschap per persoon — Erfgoed Leiden ('elo') heeft dat register niet.
    "ozw": "Stichting Oud Zoeterwoude (bevolkingsregister Zoeterwoude 1826-1939, overlijdens)",
    # Toegevoegd 16-10-2026 ijkpunt name=Jansen:
    # hvt 780. DTB en BS van MARKELO en Goor, bewerkt door Stichting Heemkunde Markelo,
    # met de BUURTSCHAP per inschrijving. ⚠ Het doopboek van Markelo is in deze index
    # leeg over 1733-1749 (losse jaren op Jan en Jenneken geven nul).
    "hvt": "Gemeente Hof van Twente (Markelo, Goor, Diepenheim)",
    # Toegevoegd 15-10-2026 ijkpunt name=Jansen: arg 671. DTB en BS van
    # Alphen, Koudekerk, Hazerswoude en Benthuizen. ⚠ Voor AARLANDERVEEN vrijwel leeg
    # (2 records op 'Jan') — een nul daar is dus geen meting.
    "arg": "Gemeentearchief Alphen aan den Rijn (Alphen, Koudekerk, Hazerswoude, Benthuizen)",
    # Toegevoegd 06-09-2026 gemeten met
    # name=Jansen: rar 27.015 · rad 23.908 · smh 5781 · ade 5666. Achtste keer dat
    # de lijst te kort was en het script ten onrechte waarschuwde.
    # ⓵ 'rar' is de belangrijkste van de vier: het Regionaal Archief Rivierenland
    # heeft de DTB en het BEVOLKINGSREGISTER van CULEMBORG (40.148 dopen, 205.396
    # bevolkingsregisterrecords), terwijl 'gld' daar alleen de burgerlijke stand
    # heeft. ⚠ En de BS van Culemborg begint pas met 1812: 1808 t/m 1811 geven nul.
    "rar": "Regionaal Archief Rivierenland (Tiel, Culemborg, Buren)",
    "rad": "Regionaal Archief Dordrecht",
    "smh": "Streekarchief Midden-Holland (Gouda e.o.)",
    "ade": "Archief Delft",
    "abl": "Rijksarchief België (Leuven)",
    # Nog drie Belgische vestigingen, gemeten 29-08-2026 met name=Jansen:
    # abt 40 · abg 39 · abb 4584. ⓵ 'abt' (Gent) dekt het WAASLAND — Beveren-Waas,
    # Kallo, Sint-Gillis-Waas — en is daarmee de enige ingang voor een
    # Waaslandse lijn over de grens. Het logboek van 27-08-2026 noemde die prefix al; het script
    # waarschuwde er toen nog voor als onbekende code.
    "abt": "Rijksarchief België (Gent) — Oost-Vlaanderen, incl. het Waasland",
    "abg": "Rijksarchief België (Bergen) — Henegouwen",
    "abb": "Rijksarchief België (Brussel)",
    # Toegevoegd 16-10-2026 gemeten met
    # name=Jansen: srt 68.900 · hga 21.977 · ran 20.239 · sch 4048 · rzh 3264 · svp 1392.
    # Negende keer dat de lijst te kort was. 'sch' gaf hier het gezin van een rijkscommies
    # dat in de zomer van 1846 drie kinderen verloor; 'hga' en 'srt' stonden al in de
    # zoekresultaten van tientallen rondes en werden toch als onbekend gemeld.
    "srt": "Stadsarchief Rotterdam",
    "hga": "Haags Gemeentearchief",
    "ran": "Regionaal Archief Nijmegen",
    "sch": "Gemeentearchief Schiedam",
    "rzh": "Nationaal Archief / Rijksarchief Zuid-Holland",
    "svp": "Streekarchief Voorne-Putten",
}


def waarschuw_archief(code):
    """Waarschuwt bij een archiefcode die de API niet kent (stille nul)."""
    if code and code not in ARCHIEFCODES:
        print(
            f"WAARSCHUWING: '{code}' staat niet in de lijst met bekende archiefcodes. "
            f"Een onbekende code geeft STILZWIJGEND nul treffers — dat is géén muur.\n"
            f"Bekend: {' · '.join(f'{k} ({v})' for k, v in sorted(ARCHIEFCODES.items()))}\n"
            f"⚠ Let op: Drenthe is 'dar' en niet 'dra' of 'dre'; Overijssel is 'hco'."
        )

# `sourcetype` is WÉL een echte API-filter — ontdekt 26-08-2026, en dat is de duurste
# ontdekking van die dag. Tot dan filterde --brontype pas ná het ophalen, waardoor elke
# brontype-zoekopdracht op een veelvoorkomende naam onafmaakbaar was: CLAUDE.md beschrijft
# hoe `zoek "<achternaam>" --brontype Naamsaanneming` op 600 van de 9526 treffers NUL gaf en pas
# met `--grens 9600` de zeven naamsaannemingen boven kreeg. Serverzijdig is datzelfde
# antwoord één verzoek: `name=<achternaam>&sourcetype=Naamsaanneming` geeft direct 7, compleet.
#
# ⚠ Twee valkuilen, allebei gemeten:
#   1. De filterwaarde is HOOFDLETTERGEVOELIG en moet exact zijn. 'Dopen' en 'DTB' geven
#      nul; alleen 'DTB Dopen' werkt.
#   2. De waarde die search.json in het veld `sourcetype` terúggeeft is niet altijd de
#      waarde waarop je kunt filteren. Teruggegeven "Memories van successie" (kleine s)
#      geeft 0 treffers; de filterwaarde is "Memories van Successie" (grote S) en geeft er
#      1408. Daarom wordt elke kandidaat hieronder eerst geteld en pas gebruikt als hij
#      treffers oplevert.
#
# Deze lijst is een startpunt, geen volledige woordenlijst — de API kent er tientallen.
# Wat er niet in staat wordt alsnog gevonden door ontdekking uit de treffers zelf
# (zie _brontypen_resolveren). Kom je een nieuwe tegen die ertoe doet: zet hem erbij.
BRONTYPEN = (
    "BS Geboorte",
    "BS Huwelijk",
    "BS Overlijden",
    "DTB Dopen",
    "DTB Trouwen",
    "DTB Begraven",
    "DTB Lidmaten",
    "Ondertrouwregister",
    "Registraties vóór 1811",
    "Bevolkingsregister",
    "Volkstelling",
    "Burgerboeken",
    "Naamsaanneming",
    "Notariële archieven",
    "Memories van Successie",
    "Quotisatie kohieren",
    "Kohieren hoofdelijke omslag",
    "Belastingregister",
    "Kadaster",
    "Stamboeken",
    "Militieregisters",
    "Gevangenisregister",
    "Rechterlijk register",
    "Schepenakten",
    "Schepenprotocollen",
    "Leenregister",
    "Dodenboek",
    "Bidprentjes&shy;verzameling",
    "Passagiersregisters",
    "Vreemdelingendossiers",
    "Instellingsregisters",
    "Personeels&shy;administratie",
    "Register van kiesgerechtigden",
)


def _fullsize(uri):
    """Zet een Memorix-thumb-URL om naar de fullsize-variant.

    De API geeft alleen `thumb/<breedte>x<hoogte>/<pad>`, en dat is voor jp2-scans vaak
    een 404 — waardoor het lijkt of het document viewer-only is. De route
    `download/fullsize/<pad>` levert wél de volledige scan (als JPEG, ruim 2000 px breed,
    enkele MB's). Ontdekt 25-08-2026 bij het naamsaannemingsregister van Noordwolde.
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

    Ontdekt 26-08-2026 bij het doopboek van Oude Wetering, waarmee een doop uit 1799 als eerste scan van een hele tak binnenkwam.
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


def _tel(parameters):
    """Hoeveel treffers geeft deze zoekopdracht? Eén verzoek, geen records."""
    krap = dict(parameters, number_show="1", start="0")
    data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(krap)}")
    return int((data.get("response") or {}).get("number_found", 0) or 0)


def _hoofdlettervarianten(waarde):
    """De schrijfwijzen waarin een sourcetype-waarde kan voorkomen, meest waarschijnlijk eerst.

    Nodig omdat de API teruggeeft in de ene schrijfwijze en filtert op de andere; zie de
    toelichting bij BRONTYPEN ("Memories van successie" tegenover "... Successie").
    """
    woorden = waarde.split(" ")
    return dict.fromkeys([
        waarde,
        waarde[:1].upper() + waarde[1:],
        " ".join(w[:1].upper() + w[1:] if w else w for w in woorden),
        (woorden[0] + " " + " ".join(w.lower() for w in woorden[1:])).strip(),
    ])


def _familienamen(plaats, van=1500, tot=1960):
    """De familienamen die in DEZE plaats en periode werkelijk in de registers staan.

    /stats/familynames.json geeft ze met hun aantal vermeldingen. Dat is de sterkste vorm
    van variantenonderzoek die er is: geen bedachte schrijfwijze maar de spelling die de
    klerken van dat dorp gebruikten. Zo komen ook vormen boven die geen enkele regel
    voorspelt — Bouma naast Bouwma naast Bouwsma, Tigchelaar naast Tichelaar.
    """
    parameters = {
        "eventplace": plaats,
        "eventyearstart": str(max(1500, van)),
        "eventyearend": str(min(1960, tot)),
        "number_show": "100",
        "lang": "nl",
    }
    try:
        data = _haal(f"https://api.openarch.nl/1.1/stats/familynames.json?{urllib.parse.urlencode(parameters)}")
    except Exception:
        return {}
    namen = {}
    for rij in data.get("rows") or []:
        cellen = rij.get("c") or []
        if len(cellen) >= 2 and cellen[0].get("v"):
            namen[str(cellen[0]["v"]).strip()] = int(cellen[1].get("v") or 0)
    return namen


def _ontdek_brontypen(parameters, monster=400):
    """Welke sourcetype-waarden komen in déze treffers voor?

    De woordenlijst BRONTYPEN dekt niet alles wat de API kent, dus wordt er ook gekeken
    naar wat de zoekopdracht zelf oplevert. Een monster van een paar honderd records is
    genoeg om de aanwezige soorten te zien; het is uitdrukkelijk geen telling.
    """
    gevonden = []
    p = dict(parameters)
    p.pop("sourcetype", None)
    # number_show is bij deze API gemaximeerd op 100 en wordt dáárbóven stilzwijgend
    # afgekapt: vraag je er 200, dan krijg je er 100 en geen foutmelding. Wie in stappen
    # van 200 pagineert slaat dus de helft over zonder het te merken.
    for start in range(0, monster, 100):
        p["number_show"], p["start"] = "100", str(start)
        try:
            data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(p)}")
        except Exception:
            break
        documenten = (data.get("response") or {}).get("docs") or []
        if not documenten:
            break
        for record in documenten:
            soort = record.get("sourcetype")
            if soort and soort not in gevonden:
                gevonden.append(soort)
        if len(documenten) < 200:
            break
    return gevonden


def _brontypen_resolveren(term, parameters):
    """Zet '--brontype Burger' om in de exacte, wérkende sourcetype-waarden.

    Geeft een lijst met (waarde, aantal). Leeg betekent: niet te resolveren, dan valt de
    aanroeper terug op het oude filter-na-ophalen. Elke kandidaat wordt geteld voordat hij
    wordt teruggegeven, want een waarde die de API teruggeeft is niet automatisch een
    waarde waarop de API filtert.
    """
    kleine = term.lower()
    kandidaten = [b for b in BRONTYPEN if kleine in b.lower()]
    for ontdekt in _ontdek_brontypen(parameters):
        if kleine in ontdekt.lower() and ontdekt not in kandidaten:
            kandidaten.append(ontdekt)
    werkend, gezien = [], set()
    for kandidaat in kandidaten:
        for variant in _hoofdlettervarianten(kandidaat):
            if variant in gezien:
                continue
            gezien.add(variant)
            try:
                aantal = _tel(dict(parameters, sourcetype=variant))
            except Exception:
                continue
            if aantal:
                werkend.append((variant, aantal))
                break
    return werkend


def _toon_regel(record):
    plaats = ", ".join(record.get("eventplace") or [])
    code = record.get("url", "").rsplit("/", 1)[-1]
    print(f"- {record.get('eventtype'):<12} {_datum(record.get('eventdate') or {}):>10}  {plaats:<20} [{record.get('archive')}]  {code}")
    # De zoekrespons is PERSOONSGERICHT: elk record is één persoonsvermelding, met de naam
    # zóals de index hem spelt in `personname` en de rol in `relationtype`. Beide velden
    # werden tot 27-08-2026 weggegooid, omdat deze functie zocht naar `persons` — en dat
    # veld bestaat alleen in de detailweergave (`toon`), niet in de zoekrespons.
    #
    # Dat heeft een muur van drie rondes gekost. De doop van **een voorouder, 01-10-1595 te
    # Enkhuizen** stond gewoon in de trefferlijst
    # van `zoek "Joost" --plaats Enkhuizen --brontype "DTB Dopen"`, tussen eenenvijftig
    # andere regels. Maar de regel toonde alleen datum, plaats en id, dus was er geen
    # enkele aanleiding om juist díe met `toon` te openen. In het dossier werd daarom
    # opgeschreven dat de Enkhuizer schakel "niet te vinden" was.
    #
    # Regel: wie op een vóórnaam of een patroniem zoekt, moet in de lijst kunnen zien
    # wélke naam er raakte en in welke rol. Dat is precies wat CLAUDE.md eist met "lees de
    # rollen, niet de volgorde" — en het kan niet als de lijst de rollen niet toont.
    naam, rol = record.get("personname"), record.get("relationtype")
    if naam:
        print(f"    {naam}" + (f"  ({rol})" if rol else ""))
    if record.get("persons"):
        print("    " + "; ".join(
            f"{p.get('relationtype', '?')}: {p.get('name', '?')}"
            for p in record["persons"]
        ))


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
        parameters["eventtype"] = BEGRAVEN_ALIAS.get(argumenten.type, argumenten.type)
    if argumenten.plaats:
        parameters["eventplace"] = argumenten.plaats
    if argumenten.archief:
        waarschuw_archief(argumenten.archief)
        parameters["archive"] = argumenten.archief

    # --van/--tot gaan sinds 27-08-2026 SERVERZIJDIG mee, als periode achter de naam
    # (`name=Joost 1593-1600`) — precies zoals `varianten` het al deed en zoals CLAUDE.md al
    # sinds 26-08-2026 bewéért. In `zoek` was het nooit gebouwd: daar werd ná het ophalen
    # gefilterd, met een grens van 600 treffers. Het verschil is geen nuance maar het
    # verschil tussen een meting en een verzinsel:
    #
    #   zoek "Jan" --plaats Enkhuizen --brontype "DTB Dopen" --van 1560 --tot 1592
    #     oud:  "(0 getoond, 600 doorzocht · 17278 treffer(s) niet doorzocht)"  → leest als nul
    #     nieuw: één verzoek, exact antwoord, en dat antwoord is écht nul
    #
    # Dat maakt het beginjaar van een register meetbaar in vier commando's in plaats van
    # in een halve middag pagineren, en het haalt een hele klasse valse muren weg.
    periode_serverzijdig = False
    if argumenten.van or argumenten.tot:
        met_periode = f"{argumenten.naam} {argumenten.van or 1500}-{argumenten.tot or 2000}"
        met = _tel(dict(parameters, name=met_periode))
        # Voorbehoud: geeft de periodevorm nul terwijl de naam alléén wél treffers geeft,
        # dan is de syntaxis hier om een of andere reden niet aangekomen (bijvoorbeeld een
        # naam die zelf al cijfers bevat). Dan liever terugvallen op het oude, begrensde
        # filter mét waarschuwing dan een stilzwijgende nul opschrijven.
        if met or not _tel(parameters):
            parameters["name"] = met_periode
            periode_serverzijdig = True
            print(f"periode {argumenten.van or 1500}-{argumenten.tot or 2000} serverzijdig → {met} treffer(s)")
        else:
            print(
                "⚠ De periode gaf serverzijdig nul terwijl de naam zonder periode wél "
                "treffers geeft; er wordt teruggevallen op filteren ná het ophalen. Die "
                "route is begrensd — let op de staartregel."
            )

    # --brontype gaat sinds 26-08-2026 serverzijdig als `sourcetype`, mits de term te
    # herleiden is tot een exacte waarde die de API kent. Dat is het verschil tussen een
    # afgekapte zoekopdracht en een complete: "achternaam + Naamsaanneming" ging van
    # "nul op 600 van de 9526" naar "zeven, klaar". Lukt herleiden niet, dan valt hij
    # terug op het oude filter-na-ophalen, mét een waarschuwing dat dat gebeurt.
    brontypen_serverzijdig = []
    if argumenten.brontype:
        brontypen_serverzijdig = _brontypen_resolveren(argumenten.brontype, parameters)
        if brontypen_serverzijdig:
            omschrijving = " · ".join(f"{w} ({n})" for w, n in brontypen_serverzijdig)
            print(f"brontype '{argumenten.brontype}' → {omschrijving}")
        else:
            print(
                f"⚠ '{argumenten.brontype}' is niet te herleiden tot een sourcetype die de API "
                "kent; er wordt teruggevallen op filteren ná het ophalen. Die route is "
                "begrensd — let op de staartregel."
            )

    if brontypen_serverzijdig:
        # Per herleide waarde één complete zoekopdracht: geen grens, geen post-filter.
        for waarde, _aantal in brontypen_serverzijdig:
            _zoek_een(dict(parameters, sourcetype=waarde), argumenten,
                      post_brontype=None, periode_serverzijdig=periode_serverzijdig)
        return
    _zoek_een(parameters, argumenten, post_brontype=argumenten.brontype,
              periode_serverzijdig=periode_serverzijdig)


def _zoek_een(parameters, argumenten, post_brontype, periode_serverzijdig=False):
    # Een niet-herleidbaar --brontype (en, vóór 27-08-2026, ook --van/--tot) zit niet in de
    # API en wordt hier gefilterd. Wie dan één pagina ophaalt, filtert alleen die pagina en
    # ziet een lege lijst waar de akte gewoon op pagina drie stond. Dat is twee keer als
    # "muur" opgeschreven terwijl het gereedschap faalde, dus bij een eigen filter
    # pagineert het script zelf door — tot `grens`, en het zégt dat als het niet af is.
    zelf_filteren = bool(post_brontype or
                         ((argumenten.van or argumenten.tot) and not periode_serverzijdig))
    # Bij een zeldzame naam is 600 ruim; bij een achternaam met duizenden treffers verbergt die
    # grens juist de treffers die je zoekt, en dan lijkt een onvoltooide zoekopdracht een muur.
    # --grens zet hem hoger voor die ene zoekopdracht.
    grens = argumenten.grens or PAGINEER_MAX
    gevonden = getoond = 0
    start, totaal = argumenten.start, None
    afgebroken = None
    while True:
        parameters["start"] = str(start)
        try:
            data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(parameters)}")
        except subprocess.CalledProcessError as fout:
            # Bij het diep doorbladeren van een naam met tienduizenden treffers kan de API
            # halverwege een HTTP-fout geven. Dat gebeurde eens bij
            # een brede zoekopdracht rond start=2850; dezelfde
            # zoekopdracht liep even later wél door tot 8010. Het is dus geen harde
            # dieptegrens maar een tijdelijke storing -- en zonder deze afhandeling stierf
            # het script met een stacktrace, wat op een muur lijkt terwijl het er geen is.
            # Belangrijk: de uitvoer moet dan zeggen dat de zoekopdracht NIET af is.
            afgebroken = start
            print(
                f"⚠ De API weigerde verder te pagineren vanaf treffer {start} ({fout}). "
                "De zoekopdracht is NIET af; beperk hem met --plaats, --van/--tot of een "
                "vollediger naam.",
                file=sys.stderr,
            )
            break
        respons = data.get("response", {})
        if totaal is None:
            totaal = int(respons.get("number_found", 0) or 0)
            etiket = parameters.get("sourcetype")
            print(f"{totaal} treffers voor '{argumenten.naam}'" + (f" [{etiket}]" if etiket else ""))
        documenten = respons.get("docs", [])
        if not documenten:
            break
        for record in documenten:
            gevonden += 1
            jaar = (record.get("eventdate") or {}).get("year")
            # Alleen nafilteren als de periode NIET serverzijdig is meegegaan. Anders zou
            # dit filter records wegwerken die de API terecht teruggaf maar waarvan het
            # jaartal in de index leeg is — en dat is stille afkapping, precies wat hier
            # niet mag.
            if not periode_serverzijdig:
                if argumenten.van and (not jaar or int(jaar) < argumenten.van):
                    continue
                if argumenten.tot and (not jaar or int(jaar) > argumenten.tot):
                    continue
            if post_brontype and post_brontype.lower() not in str(
                record.get("sourcetype", "")
            ).lower():
                continue
            getoond += 1
            _toon_regel(record)
        start += len(documenten)
        if not zelf_filteren or start >= min(totaal, grens):
            break

    # Altijd afsluiten met een telregel, óók zonder eigen filter. Zonder deze regel toonde
    # het script bij een plaatsgebonden zoekopdracht dertig van de 260 treffers en zweeg het
    # daarover: de kop zei 260, de lijst hield na dertig op, en niets zei dat er 230
    # ongezien bleven. Zo kan een gevonden akte er als een muur uitzien. CLAUDE.md eist
    # "geen stilzwijgende afkapping" — deze regel maakt dat waar.
    rest = max(0, (totaal or 0) - gevonden)
    staart = ""
    if rest and zelf_filteren:
        staart = f" · {rest} treffer(s) niet doorzocht (grens {grens}; verhoog met --grens)"
    elif rest:
        staart = (
            f" · ⚠ {rest} treffer(s) NIET GETOOND — dit is één pagina van {totaal}. "
            f"Verhoog --aantal, blader met --start, of versmal met --plaats/--type/--brontype"
        )
    if afgebroken is not None:
        staart += f" · ⚠ AFGEBROKEN door de API bij treffer {afgebroken}"
    print(f"({getoond} getoond, {gevonden} treffer(s) doorzocht{staart})")


# ── Schrijfwijzen van namen ────────────────────────────────────────────────────────────
#
# Vóór 1811 bestond er geen vaste spelling: de klerk schreef op wat hij hoorde, en dezelfde
# naam kreeg per akte een andere vorm. De index zoekt echter létterlijk, dus één afwijkende
# letter is het verschil tussen alles en niets. In dit project kostte dat drie rondes:
# Baukjen WIEBES heet in het trouwboek van 1784 Baukjen WYBES, en op "Wiebes" bleef het
# huwelijk van onze voorouders onvindbaar.
#
# De groepen hieronder zijn niet bedacht maar GEMETEN. `test/tijdelijk/letterwissels_-
# onderzoek.py` haalde via /stats/familynames.json de werkelijke familienamen op uit 33
# plaatsen van deze stamboom over 1600-1900 (6412 namen, 5252 vergelijkbaar), zocht paren
# die op één plek verschillen, en telde de wisselingen. De uitkomst, met het aantal
# gevonden paren en een voorbeeld:
#
#     · ↔ e   149  borman/boerman        · ↔ j    83  bruinsma/bruijnsma
#     · ↔ s   118  brouwer/brouwers      i ↔ y    63  bruinsma/bruynsma
#     · ↔ n    96  beekman/beekma        d ↔ t    58  barneveld/barnevelt
#     · ↔ o    64  boogaard/bogaard      · ↔ c    57  brinck/brink
#     · ↔ t    61  beinema/beintema      s ↔ z    50  broekhuisen/broekhuizen
#     · ↔ a    58  baaima/baima          · ↔ h    43  betting/bettingh
#     · ↔ z    33  barents/barentsz      c ↔ k    27  bakker/backer
#     e ↔ j    21  bijlsma/bielsma       · ↔ w    19  bouwman/bouman
#     · ↔ f    23  hofman/hoffman        aa ↔ oo  12  boonstra/baanstra
#     ei ↔ ij  12  heiningen/hijningen
#
# Wat NIET is overgenomen, hoe vaak het ook voorkwam: a↔e (bakker/bekker), a↔i
# (visser/vasser), l↔r (borman/bolman), n↔r, e↔o, l↔n en soortgelijke. Die tellen hoog
# omdat er nu eenmaal veel korte namen zijn die toevallig één letter schelen, niet omdat
# het spellingsvarianten zijn. Een regel is hier alleen opgenomen als het paar ook
# klánkgelijk is; anders levert hij ruis in plaats van treffers.
#
# Per groep zijn alle leden onderling uitwisselbaar. Ze worden op hele woorden toegepast,
# niet op de hele zoekterm, zodat "Baukjen Wiebes" varianten van Baukjen én van Wiebes
# oplevert en niet één onleesbare kruising.
# Elke groep is (leden, positie). `positie` is 'overal', 'begin' of 'eind' — zonder die
# beperking levert een groep als ("s","z") ook Wiebesch en Sytske op, en een d/t-regel
# maakt van Tijsses een Dijsses. De medeklinkerwisselingen zitten in de praktijk vrijwel
# altijd aan het begin of het einde van een woord; de klinkerwisselingen overal.
KLANKGROEPEN = (
    # klinkers en tweeklanken — verreweg de vruchtbaarste
    (("ij", "y", "ie", "i"), "overal"),      # Wiebes/Wybes/Wijbes · Bijlsma/Bielsma
    (("ei", "eij", "ey", "ij", "y"), "overal"),   # Heiningen/Hijningen · Reijer/Reyer
    (("ui", "uij", "uy"), "overal"),         # Bruinsma/Bruijnsma/Bruynsma · Huis/Huijs
    (("oe", "oo", "o"), "overal"),           # Borman/Boerman · Boogaard/Bogaard
    (("aa", "ae", "a"), "overal"),           # Adriaan/Adriaen · Baaima/Baima
    (("ee", "ae", "e"), "overal"),           # Beenen/Benen
    (("uu", "ue", "u"), "overal"),
    (("ou", "au", "ouw", "auw"), "overal"),  # Brouwer/Brauwer
    (("uw", "u"), "overal"),                 # Bouwman/Bouman · Bouwma/Bouma
    (("aa", "oo"), "overal"),                # Boonstra/Baanstra — Friese klinkerwisseling
    # medeklinkers, met een positie erbij
    (("k", "c", "ck"), "overal"),            # Kok/Cok · Bakker/Backer · Brink/Brinck
    (("s", "z"), "begin"),                   # Sytse/Zytse
    (("f", "v"), "begin"),                   # Feenstra/Veenstra
    (("ph", "f"), "overal"),
    (("s", "z"), "eind"),                    # Wiebes/Wiebez
    (("d", "t", "dt"), "eind"),              # Barnevelt/Barneveld · Sjoerd/Sjoert
    (("th", "t"), "begin"),                  # Theil/Teil
    (("g", "gh"), "eind"),                   # Brandenburg/Brandenburgh
    (("ch", "g"), "overal"),                 # Tigchelaar/Tichelaar
    (("x", "ks", "cks"), "overal"),          # Binxma/Binksma
    (("sch", "s", "sk"), "begin"),           # Schimmel/Skimmel
    (("sch", "s"), "eind-heen"),             # Bosch/Bos, maar niet Wiebes/Wiebesch
    # mb/mm — toegevoegd 29-08-2026, en het kostte een generatie. De b in "Lambert" wordt
    # voor de r geassimileerd tot een tweede m, en de klerken van Diever schrijven beide
    # vormen door elkaar. `varianten "Lambert"` gaf negen schrijfwijzen (Laambert, Lamberd,
    # Lammbert, Lamberrt ...) en Lammert zat er NIET bij, want dit is geen verdubbeling maar
    # een assimilatie. Gevolg: een complete zoekopdracht op "Lambert" te Diever gaf één
    # vader, en de doop van onze voorouder stond onder "Lammert Roelefs".
    # Zelfde paar: Rembert/Remmert, Humbert/Hummert, Lambrecht/Lammert.
    (("mb", "mm"), "overal"),
    # uitgangen van patroniemen en genitieven
    (("s", "sz", "se", "sen"), "eind"),      # Barents/Barentsz · Hendriks/Hendriksen
    (("g", "gh"), "eind"),                   # Betting/Bettingh
)

# Dubbele medeklinkers wisselen los van de groepen hierboven: Hofman/Hoffman,
# Bremer/Bremmer, Schimmel/Schimel. Nooit verdubbelen tot een drieklank.
DUBBELE = "bdfgklmnprst"


def _klanksleutel(naam):
    """Reduceert een naam tot hoe hij klínkt, zodat twee schrijfwijzen samenvallen.

    Geen Soundex: die is op het Engels gebouwd en gooit juist de klinkers weg, terwijl het
    in Nederlandse en Friese namen vaak precies de klinkers zijn die wisselen (ij/y/ie).
    Deze sleutel is op de gemeten wisselingen hierboven gebouwd en getoetst op paren
    waarvan dit project al weet dat ze samenhoren — zie test/tijdelijk/klanksleutel_test.py.
    """
    tekst = naam.lower().strip()
    for accent, plat in (("ë", "e"), ("ï", "i"), ("é", "e"), ("è", "e"), ("ö", "o"), ("ü", "u"), ("ÿ", "y")):
        tekst = tekst.replace(accent, plat)
    tekst = re.sub(r"[^a-z]", "", tekst)
    # volgorde is belangrijk: langste combinaties eerst, anders eet een korte regel ze op
    for oud, nieuw in (
        ("sch", "s"), ("ph", "f"), ("th", "t"), ("ch", "g"), ("gh", "g"),
        ("eij", "i"), ("uij", "u"), ("ouw", "ou"), ("auw", "ou"),
        ("ij", "i"), ("ei", "i"), ("ey", "i"), ("ie", "i"), ("y", "i"),
        ("ui", "u"), ("uy", "u"), ("uw", "u"),
        ("oe", "o"), ("oo", "o"), ("ae", "a"), ("aa", "a"), ("ee", "e"), ("uu", "u"),
        ("au", "ou"),
        ("ck", "k"), ("c", "k"), ("q", "k"), ("x", "ks"),
        ("z", "s"), ("v", "f"), ("d", "t"),
        ("mb", "m"),   # Lambert/Lammert — zie de mb/mm-groep hierboven. Zonder deze regel
                       # verschillen de sleutels (lambert tegen lamert) en gooit de vangrail
                       # de variant weg die hij net had bedacht.
    ):
        tekst = tekst.replace(oud, nieuw)
    tekst = re.sub(r"h", "", tekst)          # de h is in deze namen vrijwel altijd stom
    tekst = re.sub(r"(.)\1+", r"\1", tekst)  # dubbele letters tellen als één
    tekst = re.sub(r"(sen|se|s)$", "s", tekst)   # patroniem-uitgangen gelijktrekken
    return tekst


def _woordvarianten(woord, maximum=25):
    """Alle schrijfwijzen van één woord volgens de gemeten klankgroepen.

    De vangrail staat aan het eind: een kandidaat telt alleen mee als hij dezelfde
    klanksleutel heeft als het origineel. Daarmee is een variant per definitie een andere
    schríjfwijze van dezelfde naam en niet een andere naam, en glippen er geen vormen als
    Baukjeen of Skytske doorheen.
    """
    laag = woord.lower()
    sleutel = _klanksleutel(woord)
    uitkomst = [woord]
    hoofdletter = woord[:1].isupper()

    def voeg_toe(kandidaat):
        if not kandidaat or kandidaat == laag:
            return
        if re.search(r"(.)\1\1", kandidaat):      # nooit drie dezelfde letters op een rij
            return
        if _klanksleutel(kandidaat) != sleutel:   # een variant klinkt hetzelfde, anders is
            return                                # het een andere naam en geen schrijfwijze
        net = kandidaat.capitalize() if hoofdletter else kandidaat
        if net not in uitkomst:
            uitkomst.append(net)

    for leden, positie in KLANKGROEPEN:
        anker = positie.split("-")[0]
        bronnen = leden[:1] if positie.endswith("-heen") else leden
        for oud in bronnen:
            if not oud:
                continue
            if anker == "begin" and not laag.startswith(oud):
                continue
            if anker == "eind" and not laag.endswith(oud):
                continue
            if anker == "overal" and oud not in laag:
                continue
            for nieuw in leden:
                if nieuw == oud:
                    continue
                if anker == "begin":
                    voeg_toe(nieuw + laag[len(oud):])
                elif anker == "eind":
                    voeg_toe(laag[: len(laag) - len(oud)] + nieuw)
                else:
                    voeg_toe(laag.replace(oud, nieuw))
                    if laag.count(oud) > 1:
                        for m in re.finditer(re.escape(oud), laag):
                            voeg_toe(laag[: m.start()] + nieuw + laag[m.end():])
                if len(uitkomst) >= maximum:
                    return uitkomst
    # dubbele medeklinkers: bestaande verdubbeling weghalen, of één losse verdubbelen
    for letter in DUBBELE:
        if letter * 2 in laag:
            voeg_toe(laag.replace(letter * 2, letter))
        else:
            for m in re.finditer(re.escape(letter), laag):
                if 0 < m.start() < len(laag) - 1:
                    voeg_toe(laag[: m.start()] + letter * 2 + laag[m.start() + 1:])
        if len(uitkomst) >= maximum:
            break
    return uitkomst


def _naamvarianten(naam, maximum=60):
    """Schrijfwijzen van een hele zoekterm: per woord gevarieerd, één woord tegelijk.

    "Baukjen Wiebes" levert zo Baukjen Wybes en Baukjen Wijbes op, en niet de onbruikbare
    kruising Baucjen Wybes. Wie twee woorden tegelijk moet variëren, draait het commando
    op de uitkomst.
    """
    woorden = naam.split()
    uitkomst = [naam]
    for index, woord in enumerate(woorden):
        for variant in _woordvarianten(woord)[1:]:
            kandidaat = " ".join(woorden[:index] + [variant] + woorden[index + 1:])
            if kandidaat not in uitkomst:
                uitkomst.append(kandidaat)
            if len(uitkomst) >= maximum:
                return uitkomst
    return uitkomst


def varianten(argumenten):
    """Probeert dezelfde naam in alle gangbare schrijfwijzen.

    Dit is het commando dat de trouwinschrijving van 1784 drie rondes eerder had gevonden.
    "Baukjen Wiebes" geeft zeven treffers, geen ervan in Sloten; "Baukjen Wybes" geeft het
    huwelijk van onze voorouders. Eén letter, en de index zoekt letterlijk.
    """
    basis = {"lang": "nl"}
    if argumenten.plaats:
        basis["eventplace"] = argumenten.plaats
    if argumenten.archief:
        waarschuw_archief(argumenten.archief)
        basis["archive"] = argumenten.archief
    if argumenten.type:
        basis["eventtype"] = BEGRAVEN_ALIAS.get(argumenten.type, argumenten.type)
    if argumenten.brontype:
        herleid = _brontypen_resolveren(argumenten.brontype, dict(basis, name=argumenten.naam))
        if herleid:
            basis["sourcetype"] = herleid[0][0]
            print(f"brontype '{argumenten.brontype}' → {herleid[0][0]}")

    lijst = _naamvarianten(argumenten.naam)

    # De sterkste bron van varianten is niet een regel maar het register zelf. Staat er een
    # plaats bij, dan wordt de werkelijke namenlijst van dat dorp opgehaald en gekeken welke
    # daarvan hetzelfde klínken als de gezochte naam. Zo komen schrijfwijzen boven die geen
    # enkele regel voorspelt.
    uit_register = []
    if argumenten.plaats:
        doel = _klanksleutel(argumenten.naam.split()[-1])
        inventaris = _familienamen(argumenten.plaats, argumenten.van or 1500, argumenten.tot or 1960)
        for naam, aantal in inventaris.items():
            if _klanksleutel(naam) == doel and naam.lower() != argumenten.naam.split()[-1].lower():
                uit_register.append((naam, aantal))
        if inventaris:
            print(f"Namenlijst van {argumenten.plaats}: {len(inventaris)} familienamen in de registers.")
        if uit_register:
            print("Klinkt hetzelfde als de gezochte naam, en staat er écht:")
            for naam, aantal in sorted(uit_register, key=lambda x: -x[1]):
                print(f"  {aantal:6d}x  {naam}")
            woorden = argumenten.naam.split()
            for naam, _ in uit_register:
                kandidaat = " ".join(woorden[:-1] + [naam])
                if kandidaat not in lijst:
                    lijst.append(kandidaat)
        print()

    print(f"{len(lijst)} schrijfwijze(n) van '{argumenten.naam}':\n")
    raak = []
    for variant in lijst:
        naam_met_periode = variant
        if argumenten.van or argumenten.tot:
            # De API kent een jaar of periode ACHTER de naam; dat filtert serverzijdig.
            naam_met_periode = f"{variant} {argumenten.van or 1500}-{argumenten.tot or 1960}"
        try:
            aantal = _tel(dict(basis, name=naam_met_periode))
        except Exception as fout:
            print(f"  {'?':>6}  {variant}   (fout: {fout})")
            continue
        merk = "" if variant == argumenten.naam else "  ← andere schrijfwijze"
        print(f"  {aantal:6d}  {variant}{merk if aantal else ''}")
        if aantal:
            raak.append((naam_met_periode, aantal) if variant == argumenten.naam else (naam_met_periode, aantal))

    anders = [(v, n) for v, n in raak if v != argumenten.naam]
    if not anders:
        print("\nGeen enkele andere schrijfwijze geeft treffers. Dit negatief is dus "
              "gemeten over alle gangbare varianten en niet over één spelling.")
        return
    print(f"\n{len(anders)} andere schrijfwijze(n) geven treffers. Records:\n")
    for variant, aantal in anders:
        if aantal > argumenten.aantal:
            print(f"— {variant} ({aantal} treffers, eerste {argumenten.aantal}):")
        else:
            print(f"— {variant} ({aantal}):")
        data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(dict(basis, name=variant, number_show=str(argumenten.aantal), start='0'))}")
        for record in (data.get("response") or {}).get("docs") or []:
            _toon_regel(record)
        print()


def bronnen(argumenten):
    """Welke registers kent de index eigenlijk voor deze plaats?

    Dit is de vraag die je moet stellen vóór je "muur" opschrijft. Bij één stadje bleek zo dat
    de enige kerkelijke registers doop, trouw, begraven en lidmaten van de HERVORMDE
    gemeente zijn: er is geen doopsgezind of rooms register ontsloten. Dat maakt van
    "ik kan hun dopen niet vinden" een meting in plaats van een vermoeden, en het verandert
    de vervolgstap van "nog eens zoeken" in "naar de studiezaal".
    """
    basis = {"name": argumenten.naam, "lang": "nl"}
    if argumenten.plaats:
        basis["eventplace"] = argumenten.plaats
    if argumenten.archief:
        waarschuw_archief(argumenten.archief)
        basis["archive"] = argumenten.archief
    totaal = _tel(basis)
    kop = f"'{argumenten.naam}'"
    if argumenten.plaats:
        kop += f" te {argumenten.plaats}"
    print(f"{totaal} record(s) voor {kop}\n")

    kandidaten = list(BRONTYPEN)
    for ontdekt in _ontdek_brontypen(basis, monster=argumenten.monster):
        if ontdekt not in kandidaten:
            kandidaten.append(ontdekt)

    rijen, som = [], 0
    for kandidaat in kandidaten:
        for variant in _hoofdlettervarianten(kandidaat):
            try:
                aantal = _tel(dict(basis, sourcetype=variant))
            except Exception:
                continue
            if aantal:
                rijen.append((aantal, variant))
                som += aantal
                break
    for aantal, naam in sorted(rijen, reverse=True):
        print(f"{aantal:8d}  {naam}")

    rest = totaal - som
    print(f"\n{len(rijen)} brontype(n) gevonden, samen {som} van {totaal} records.")
    if rest > 0:
        # Eerlijk zijn over wat de meting níet dekt: de woordenlijst is niet volledig en
        # het monster ziet alleen wat er in de eerste paar honderd records zit.
        print(
            f"⚠ {rest} record(s) vallen buiten deze brontypen — er zijn dus soorten die "
            f"noch in BRONTYPEN staan noch in het monster van {argumenten.monster} records "
            f"voorkwamen. Verhoog --monster voor een completer beeld."
        )
    elif rest < 0:
        print("Let op: de som is hoger dan het totaal; een record kan onder twee soorten vallen.")


def dekking(argumenten):
    """Loopt de index voor deze plaats en dit register echt door, jaar voor jaar?

    Het derde soort muur uit CLAUDE.md is een index die ophoudt. Die meet je door een
    veelvoorkomende naam per jaar te tellen: de geboorte-index van Alphen aan den Rijn
    bleek zo met 1902 te eindigen, en het doopboek van Sloten bleek juist wél door te
    lopen — waarmee "de dopen ontbreken" van een registerprobleem een gezinseigenschap
    werd. Dit commando doet die telling in één keer.
    """
    parameters = {"name": argumenten.naam, "lang": "nl"}
    if argumenten.plaats:
        parameters["eventplace"] = argumenten.plaats
    if argumenten.archief:
        waarschuw_archief(argumenten.archief)
        parameters["archive"] = argumenten.archief
    # De periode gaat sinds 27-08-2026 serverzijdig mee in de zoekterm. Daarvóór haalde dit
    # commando álle records van die naam op (tot `grens`, standaard 600) en tekende het de
    # staafjes voor het gevraagde venster uit wat het tegenkwam. Bij een register met
    # 17.878 treffers leverde dat een histogram op dat er als een meting uitzag maar op 3%
    # van de records rustte: `dekking "Jan" --plaats Enkhuizen --brontype "DTB Dopen"
    # --van 1550 --tot 1620` gaf keurig nullen voor 1550-1592 — toevallig het juiste
    # antwoord, maar niet omdat het gemeten was. Nu dekt het venster zichzelf.
    if argumenten.van or argumenten.tot:
        parameters["name"] = f"{argumenten.naam} {argumenten.van or 1500}-{argumenten.tot or 2000}"
    if argumenten.type:
        parameters["eventtype"] = BEGRAVEN_ALIAS.get(argumenten.type, argumenten.type)
    if argumenten.brontype:
        herleid = _brontypen_resolveren(argumenten.brontype, parameters)
        if not herleid:
            print(f"⚠ '{argumenten.brontype}' is niet te herleiden tot een sourcetype; niet gefilterd.")
        elif len(herleid) > 1:
            print("⚠ Meerdere brontypen passen; kies er één voor een zuivere meting: "
                  + " · ".join(w for w, _ in herleid))
            return
        else:
            parameters["sourcetype"] = herleid[0][0]
            print(f"brontype '{argumenten.brontype}' → {herleid[0][0]} ({herleid[0][1]})")

    grens = argumenten.grens or PAGINEER_MAX
    per_jaar, zonder_jaar, gelezen, start = {}, 0, 0, 0
    totaal = None
    while True:
        parameters["number_show"], parameters["start"] = "100", str(start)   # 100 is het maximum
        data = _haal(f"{BASIS}/search.json?{urllib.parse.urlencode(parameters)}")
        respons = data.get("response", {})
        if totaal is None:
            totaal = int(respons.get("number_found", 0) or 0)
        documenten = respons.get("docs", [])
        if not documenten:
            break
        for record in documenten:
            gelezen += 1
            jaar = (record.get("eventdate") or {}).get("year")
            if jaar:
                per_jaar[int(jaar)] = per_jaar.get(int(jaar), 0) + 1
            else:
                zonder_jaar += 1
        start += len(documenten)
        if start >= min(totaal, grens):
            break

    van = argumenten.van or (min(per_jaar) if per_jaar else 0)
    tot = argumenten.tot or (max(per_jaar) if per_jaar else 0)
    print(f"\n{gelezen} van {totaal} record(s) gelezen; jaren {van} t/m {tot}\n")
    leeg = []
    for jaar in range(van, tot + 1):
        aantal = per_jaar.get(jaar, 0)
        if aantal:
            print(f"  {jaar}  {aantal:4d}  {'#' * min(aantal, 60)}")
        else:
            leeg.append(jaar)
            print(f"  {jaar}     0")
    if zonder_jaar:
        print(f"\n{zonder_jaar} record(s) zonder jaartal.")
    if leeg:
        print(f"\n{len(leeg)} jaar/jaren zonder enige treffer: {', '.join(str(j) for j in leeg)}")
        print("Een aaneengesloten staart van nullen aan het eind is meestal de "
              "openbaarheidstermijn of het einde van de index — geen muur maar een grens.")
    if totaal and gelezen < totaal:
        print(f"\n⚠ {totaal - gelezen} record(s) niet gelezen (grens {grens}); de meting is NIET af.")


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
            # ⚠ PersonName kan één dict zijn ÓF een lijst van dicts — precies zoals
            # EventRemark. Gemeten 28-08-2026: een overlijdensakte uit 1888
            # (dar:7e5f023c) heeft er twéé, en `toon` viel daarop
            # om met "AttributeError: 'list' object has no attribute 'get'". Een record
            # dat een tweede naamvorm draagt — juist het interessante geval, want dat is
            # waar een naamgenootverwarring of een aliasnaam zichtbaar wordt — was dus
            # onleesbaar. Alle naamvormen worden nu geprint, gescheiden door " / ".
            namen = naam if isinstance(naam, list) else [naam]
            # PersonNamePatronym hoort ertussen. Vóór 1811 is het patroniem het énige wat
            # twee naamgenoten scheidt: "Sioerd Tijsses" is een andere man dan "Sjoerd
            # Jelles". Het veld werd hier eerder weggegooid, waardoor de doop van een voorouder
            # (1785) als "Sjoert en Hil" verscheen en niet te koppelen leek.
            vormen = []
            for n in namen:
                if not isinstance(n, dict):
                    continue
                v = " ".join(
                    x for x in (
                        n.get("PersonNameFirstName"),
                        n.get("PersonNamePatronym"),
                        n.get("PersonNamePrefixLastName"),
                        n.get("PersonNameLastName"),
                    ) if x
                )
                if v and v not in vormen:
                    vormen.append(v)
            volledig = " / ".join(vormen)
            rol = rol_van.get(p.get("@pid")) or "rol onbekend"
            extra = []
            # De leeftijd staat bij de ene collectie als tekst (PersonAgeLiteral, "40"),
            # bij de andere uitgesplitst (PersonAgeYears/-Months/-Weeks/-Days). Alleen het
            # eerste werd geprint. Gemeten 17-10-2026: een huwelijk te
            # Dubbeldam, 1821 (rad:605a53c6), heeft alleen PersonAgeYears = 29 — en juist
            # die leeftijd weerlegde dat de bruidegom (geb. 1791) al in 1800 overleden zou zijn.
            leeftijdveld = p.get("Age") or {}
            leeftijd = leeftijdveld.get("PersonAgeLiteral")
            if not leeftijd:
                delen = [f"{leeftijdveld[k]} {eenheid}" for k, eenheid in (
                    ("PersonAgeYears", "jaar"), ("PersonAgeMonths", "mnd"),
                    ("PersonAgeWeeks", "wkn"), ("PersonAgeDays", "dgn")) if leeftijdveld.get(k)]
                leeftijd = " ".join(delen)
            if leeftijd:
                extra.append(leeftijd)
            if p.get("BirthDate"):
                extra.append(f"geb. {_datum(p['BirthDate'])}")
            # BirthPlace is bij BS-huwelijken de geboorteplaats van bruid en bruidegom,
            # en die kan het enige spoor naar een herkomst zijn. Bij een huwelijk te
            # Avereest (1840, hco:EFDD5CB8-…) stond hier
            # "Deldersen, Ambt (Nassau)" — de enige Nederlandse indexvermelding van zijn
            # Duitse geboorteplaats — en toon liet het veld weg (ontdekt 29-08-2026).
            geboorteplaats = (p.get("BirthPlace") or {}).get("Place")
            if geboorteplaats:
                extra.append(f"geboren te {geboorteplaats}")
            if p.get("Profession"):
                extra.append(str(p["Profession"]))
            # Residence is de woonplaats van deze pérsoon, en die kan een andere zijn dan
            # de plaats van de gebeurtenis. In een huwelijksakte van 1813 woonden
            # bruid en bruidegom in een ander dorp dan haar ouders; zonder dit veld leest
            # zo'n akte alsof iedereen in de stad woonde.
            woonplaats = (p.get("Residence") or {}).get("Place")
            if woonplaats:
                extra.append(f"wonende te {woonplaats}")
            achtervoegsel = f" ({', '.join(extra)})" if extra else ""
            print(f"  {rol:<12} {volledig}{achtervoegsel}")
            # PersonRemark is bij sommige collecties het énige inhoudelijke veld. In een
            # burgerboek staat er per naam "Inwoner sinds mei 1755.", "Komt voor
            # op lijst van burgers." of "Ingeschreven als inwoner." — dat is het verschil
            # tussen een naam op een lijst en een man die zich in een genoemde maand in de
            # stad vestigde, en het is soms de enige aanwijzing dat een familie van buiten
            # de stad kwam. In BS-aktes zit hier soms "plaats_overlijden" van een al gestorven ouder.
            for opmerking in _lijst(p.get("PersonRemark")):
                if opmerking.get("Value"):
                    label = re.sub(r"^\d+\s+", "", str(opmerking.get("@Key") or "opmerking"))
                    print(f"       {label}: {opmerking['Value']}")
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
            # vindplaats; mét dit veld is het "inv. 145.1.02-460, gezinskaart 916". Zo wordt
            # een gezinskaart aanwijsbaar, en een afstammingsvraag een concrete aanvraag.
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
        # Bij "Friese militairen onder Napoleon" stond daar in één alinea dat een voorouder
        # plaatsvervanger was voor een boerenzoon uit het buurdorp, met zijn
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
                # Het Stadsarchief Amsterdam ('saa') vult 'Uri' niet en zet de thumb in
                # 'UriViewer'/'UriPreview'. Zonder deze terugval printte `toon` vijf lege
                # thumb-regels en leek een notarieel testament scanloos (16-10-2026).
                uri = scan.get("Uri") or scan.get("UriViewer") or scan.get("UriPreview") or ""
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
    z.add_argument("--archief", help="frl (AlleFriezen), dar (Drents Archief), hco (Collectie Overijssel), zar (Zeeuws Archief) — LET OP: Drenthe is dar, niet dra")
    z.add_argument("--van", type=int, help="jaar vanaf")
    z.add_argument("--tot", type=int, help="jaar tot en met")
    z.add_argument("--aantal", type=int, default=30)
    z.add_argument("--start", type=int, default=0, help="paginering: sla de eerste N treffers over")
    z.add_argument("--grens", type=int, default=None,
                   help=f"hoeveel treffers het script bij --van/--tot/--brontype maximaal doorzoekt (standaard {PAGINEER_MAX}); verhoog dit als de uitvoer meldt dat er treffers niet doorzocht zijn")
    z.set_defaults(func=zoek)

    v = sub.add_parser("varianten", help="dezelfde naam in alle gangbare schrijfwijzen (ie/y/ij, t/d, k/c)")
    v.add_argument("naam")
    v.add_argument("--plaats")
    v.add_argument("--type", help="gebeurtenistype; geldig: " + " · ".join(sorted(GEBEURTENISTYPEN)))
    v.add_argument("--brontype")
    v.add_argument("--archief")
    v.add_argument("--van", type=int, help="jaar vanaf (gaat serverzijdig mee in de zoekterm)")
    v.add_argument("--tot", type=int, help="jaar tot en met")
    v.add_argument("--aantal", type=int, default=10, help="records per rakende schrijfwijze")
    v.set_defaults(func=varianten)

    b = sub.add_parser("bronnen", help="welke registers kent de index voor een plaats?")
    b.add_argument("plaats", nargs="?", help="plaatsnaam; laat weg om alleen op naam te kijken")
    b.add_argument("--naam", default="*", help="beperk tot een naam; standaard * (alles)")
    b.add_argument("--archief", help="bijv. frl (AlleFriezen)")
    b.add_argument("--monster", type=int, default=400,
                   help="hoeveel records worden bekeken om onbekende brontypen te ontdekken")
    b.set_defaults(func=bronnen)

    d = sub.add_parser("dekking", help="telt per jaar; laat zien of een index doorloopt of ophoudt")
    d.add_argument("naam", help="een véélvoorkomende naam uit de streek geeft de scherpste meting")
    d.add_argument("--plaats")
    d.add_argument("--type", help="gebeurtenistype; geldig: " + " · ".join(sorted(GEBEURTENISTYPEN)))
    d.add_argument("--brontype", help="bróntype, bijv. 'DTB Dopen' — nu serverzijdig")
    d.add_argument("--archief")
    d.add_argument("--van", type=int, help="eerste jaar van de grafiek")
    d.add_argument("--tot", type=int, help="laatste jaar van de grafiek")
    d.add_argument("--grens", type=int, default=None,
                   help=f"maximaal aantal records dat wordt geteld (standaard {PAGINEER_MAX})")
    d.set_defaults(func=dekking)

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

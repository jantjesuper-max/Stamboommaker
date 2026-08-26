"""Zet dit project klaar voor jouw stamboom.

    py instellen.py                 vraagt wat het nodig heeft en maakt de bestanden
    py instellen.py --toon          laat zien wat er nu staat, verandert niets
    py instellen.py --overschrijf   maakt de startbestanden opnieuw (let op: weg is weg)

Wat het doet:
  1. `stamboom.json` schrijven — de enige plek waar dit project persoonlijk wordt
     (jouw naam, je geboortejaar, de titel van je boek, de naam boven de website).
  2. `stamboom/overzicht.md` aanmaken met jou bovenaan de kwartierstaat.
  3. `onderzoek/werklijst-dossiers.md` aanmaken met een sectie per familielijn.

Bestaande bestanden blijven staan tenzij je `--overschrijf` meegeeft. Dit script
raakt nooit dossiers, documenten of het boek aan.

Daarna is het werk aan Claude Code: zeg `/opstarten` om je stamboom in te vullen
met wat je al weet, en daarna `/doorwerk` om het archiefwerk te laten doen.

Niet-interactief (voor een script of een test):
    py instellen.py --naam "Marie Bakker" --jaar 1988 --plaats Utrecht \\
        --lijnen "Bakker,De Wit" --stil
"""

import argparse
import datetime
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent
sys.path.insert(0, str(WORTEL / "scripts"))
import instellingen  # noqa: E402

OVERZICHT = WORTEL / "stamboom" / "overzicht.md"
WERKLIJST = WORTEL / "onderzoek" / "werklijst-dossiers.md"

# De repo levert overzicht en werklijst als plaatshouder mee, zodat je op GitHub
# ziet hoe ze eruitzien. Zo'n plaatshouder mag overschreven worden; een bestand
# waar al onderzoek in staat niet — daar is `--overschrijf` voor.
PLAATSHOUDER = "<!-- stamboommaker:plaatshouder -->"


# ---------------------------------------------------------------------------
# Vragen stellen
# ---------------------------------------------------------------------------

def vraag(tekst, standaard="", verplicht=False):
    """Eén vraag met een standaardantwoord tussen blokhaken."""
    achtervoegsel = f" [{standaard}]" if standaard else ""
    while True:
        antwoord = input(f"{tekst}{achtervoegsel}: ").strip()
        if not antwoord and standaard:
            return standaard
        if antwoord:
            return antwoord
        if not verplicht:
            return ""
        print("  Dit heb ik echt nodig.")


def vraag_jaar(tekst, standaard=None):
    nu = datetime.date.today().year
    while True:
        antwoord = vraag(tekst, str(standaard) if standaard else "")
        if not antwoord:
            return None
        try:
            jaar = int(antwoord)
        except ValueError:
            print("  Een jaartal graag, bijvoorbeeld 1990.")
            continue
        if not 1900 <= jaar <= nu:
            print(f"  Tussen 1900 en {nu} graag.")
            continue
        return jaar


def achternaam_uit(naam):
    """'Marie de Wit' -> 'de Wit' (alles na de eerste voornaam)."""
    delen = naam.split()
    return " ".join(delen[1:]) if len(delen) > 1 else naam


# ---------------------------------------------------------------------------
# Bestanden schrijven
# ---------------------------------------------------------------------------

def kop_overzicht(inst):
    naam = inst["eigenaar"]["naam"]
    jaar = inst["eigenaar"]["geboortejaar"]
    plaats = inst["eigenaar"]["geboorteplaats"]
    maand = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
             "augustus", "september", "oktober", "november", "december"]
    vandaag = datetime.date.today()
    stand = f"{maand[vandaag.month - 1]} {vandaag.year}"
    regel_jij = " — ".join(x for x in (str(jaar) if jaar else "", plaats) if x)
    lijnen = inst["lijnen"] or ["Vaderskant", "Moederskant"]

    takken = []
    for nr, lijn in enumerate(lijnen):
        laatste = nr == len(lijnen) - 1
        takken.append(
            "│\n"
            "├══════════════════════════════════════════════════════════════\n"
            f"│ {lijn.upper()}\n"
            "├══════════════════════════════════════════════════════════════\n"
            "│\n"
            # └ alleen bij de laatste lijn; anders volgt er nog een tak onder
            f"{'└' if laatste else '├'}── (nog niemand — vul aan met /opstarten "
            "of met de hand)\n"
        )

    return f"""# Stamboom {naam} — stand van onderzoek, {stand}

> Dit is de leesbare samenvatting. De persoonsdossiers in `personen/` zijn de waarheid;
> werk dit overzicht bij na elke dossierwijziging.
>
> Legenda: ✓ bewezen · ◐ waarschijnlijk · ? hypothese · ⚠ verwarringsgevaar

```
{naam.upper()}
{regel_jij}
{"".join(takken)}```

## Zo vul je dit aan

Elke voorouder krijgt een regel met naam, geboorte- en sterfdatum met plaats, het beroep
als dat bekend is, en een statusteken. De boom loopt van jong (bovenaan) naar oud
(onderaan): onder elke persoon staan zijn of haar ouders, verder ingesprongen.

Alleen **directe voorouders** staan hier — vaders en moeders, generatie na generatie.
Broers, zussen, ooms en tantes horen er niet in; zie `boek/zijtakken.md` voor waarom en
voor wat je dan wél met zo'n vondst doet.

De snelste weg: zeg **`/opstarten`** tegen Claude Code en vertel wat je van je familie
weet. De skill vult dit overzicht, de werklijst en de eerste dossiers in één keer.
"""


def kop_werklijst(inst):
    naam = inst["eigenaar"]["naam"]
    jaar = inst["eigenaar"]["geboortejaar"]
    jij = f"{naam} ({jaar})" if jaar else naam
    lijnen = inst["lijnen"] or ["Vaderskant", "Moederskant"]
    secties = "\n\n".join(
        f"## {lijn}\n\n<!-- regels toevoegen: - [ ] gN · persoon-id — Naam (jaren) status -->"
        for lijn in lijnen
    )

    return f"""# Werklijst dossiers — de afstreeplijst

Elke voorouder uit `stamboom/overzicht.md` staat hier één keer. Dit is de werkvoorraad van
de doorwerk-skill. De **volgorde** bepaalt `py test/controleer.py`: na elk afgerond dossier
zijn de óuders van die persoon aan de beurt (omhoog, diepste generatie eerst), bij een
muurvaste lijn gaat de route opzij naar de diepste open tak, en de lijstvolgorde hieronder
is alleen de terugval. Bovenaan een lijn probeert de skill de ontbrekende ouders te
vínden — gevonden voorouders komen er hier als nieuwe regels bij, dus deze lijst groeit.

**Regelformat:** `- [ ] gN · persoon-id — Naam (jaren) status`
`gN` = generatie t.o.v. {jij} = g0. Status: ✓ bewezen · ◐ waarschijnlijk · ? hypothese · ⚠ naamgenoot-gevaar.
Markeringen achter een regel: `· muur DD-MM-JJJJ` (lijn-top, ouders niet gevonden — zie
logboek) en `· overgeslagen: <reden>` (route slaat deze over; periodiek herzien).

**Afvinken mag pas als:** dossier bestaat volgens `personen/_TEMPLATE.md`, vader/moeder/partner
als wikilinks ingevuld, minstens één archiefbron gezocht (gevonden óf `[niets gevonden]`),
het onderzoekslog in het dossier is bijgewerkt, en elke open vraag is gesloten.

Voortgang: **0 / 0** afgevinkt. (Bijwerken met `py test/controleer.py --fix`.)

---

{secties}
"""


def is_plaatshouder(pad):
    try:
        return PLAATSHOUDER in pad.read_text(encoding="utf-8")
    except OSError:
        return False


def schrijf(pad, inhoud, overschrijven, gedaan):
    if pad.exists() and not overschrijven and not is_plaatshouder(pad):
        print(f"  overgeslagen (bestaat al): {pad.relative_to(WORTEL)}")
        return
    pad.parent.mkdir(parents=True, exist_ok=True)
    pad.write_text(inhoud, encoding="utf-8")
    gedaan.append(pad.relative_to(WORTEL))


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Zet dit stamboomproject klaar.")
    p.add_argument("--naam")
    p.add_argument("--jaar", type=int)
    p.add_argument("--plaats", default="")
    p.add_argument("--boektitel")
    p.add_argument("--websitetitel")
    p.add_argument("--lijnen", help='komma-gescheiden, bijv. "Bakker,De Wit"')
    p.add_argument("--stil", action="store_true", help="niets vragen, alleen de vlaggen gebruiken")
    p.add_argument("--overschrijf", action="store_true", help="bestaande startbestanden vervangen")
    p.add_argument("--toon", action="store_true", help="alleen tonen wat er nu staat")
    a = p.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    huidig = instellingen.lees()

    if a.toon:
        print(f"Instellingen ({instellingen.BESTAND.name}"
              f"{'' if instellingen.BESTAND.exists() else ' — bestaat nog niet'}):")
        print(f"  naam          {huidig['eigenaar']['naam'] or '(leeg)'}")
        print(f"  geboortejaar  {huidig['eigenaar']['geboortejaar'] or '(leeg)'}")
        print(f"  geboorteplaats{'':1}{huidig['eigenaar']['geboorteplaats'] or '(leeg)'}")
        print(f"  boektitel     {huidig['boek']['titel']}")
        print(f"  ondertitel    {instellingen.boek_ondertitel() or '(leeg)'}")
        print(f"  websitetitel  {instellingen.website_titel()}")
        print(f"  poort         {huidig['website']['poort']}")
        print(f"  lijnen        {', '.join(huidig['lijnen']) or '(geen)'}")
        return 0

    if a.stil and not a.naam and not huidig["eigenaar"]["naam"]:
        print("FOUT: met --stil heb ik minstens --naam nodig.")
        return 1

    if not a.stil:
        print("Stamboommaker — dit project klaarzetten voor jouw stamboom.")
        print("Enter zonder iets te typen neemt de waarde tussen [blokhaken].\n")

    naam = a.naam or (huidig["eigenaar"]["naam"] if a.stil else None)
    if naam is None:
        naam = vraag("Jouw volledige naam", huidig["eigenaar"]["naam"], verplicht=True)

    jaar = a.jaar or (huidig["eigenaar"]["geboortejaar"] if a.stil else None)
    if jaar is None:
        jaar = vraag_jaar("Jouw geboortejaar", huidig["eigenaar"]["geboortejaar"])

    plaats = a.plaats or (huidig["eigenaar"]["geboorteplaats"] if a.stil else None)
    if plaats is None:
        plaats = vraag("Jouw geboorteplaats", huidig["eigenaar"]["geboorteplaats"])

    boektitel = a.boektitel or (huidig["boek"]["titel"] if a.stil else None)
    if boektitel is None:
        boektitel = vraag("Werktitel van het boek", huidig["boek"]["titel"] or "Waar wij vandaan komen")

    standaard_web = huidig["website"]["titel"]
    if standaard_web in ("", "Mijn stamboom"):
        standaard_web = f"Stamboom {achternaam_uit(naam)}"
    websitetitel = a.websitetitel or (standaard_web if a.stil else None)
    if websitetitel is None:
        websitetitel = vraag("Naam boven de website", standaard_web)

    if a.lijnen is not None:
        lijnen = [x.strip() for x in a.lijnen.split(",") if x.strip()]
    elif a.stil:
        lijnen = huidig["lijnen"]
    else:
        standaard_lijnen = ", ".join(huidig["lijnen"]) or achternaam_uit(naam)
        print("\nFamilielijnen: de achternamen waar je stamboom in uiteenvalt.")
        print("Begin met de achternaam van je vader en de meisjesnaam van je moeder;")
        print("verder terug komen er zelf lijnen bij.")
        rauw = vraag("Familielijnen (komma's ertussen)", standaard_lijnen)
        lijnen = [x.strip() for x in rauw.split(",") if x.strip()]

    nieuw = {
        "eigenaar": {"naam": naam, "geboortejaar": jaar, "geboorteplaats": plaats},
        "boek": {
            "titel": boektitel,
            "ondertitel": f"De voorouders van {naam}",
            "voor_wie": huidig["boek"].get("voor_wie", ""),
        },
        "website": {"titel": websitetitel, "poort": huidig["website"]["poort"]},
        "lijnen": lijnen,
    }
    instellingen.schrijf(nieuw)
    print(f"\nGeschreven: {instellingen.BESTAND.relative_to(WORTEL)}")

    gedaan = []
    schrijf(OVERZICHT, kop_overzicht(nieuw), a.overschrijf, gedaan)
    schrijf(WERKLIJST, kop_werklijst(nieuw), a.overschrijf, gedaan)
    for pad in gedaan:
        print(f"Geschreven: {pad}")

    print("\nKlaar. Hierna:")
    print("  1. Open deze map in Claude Code en zeg  /opstarten")
    print("     — dan vraagt hij wat je van je familie weet en vult de stamboom.")
    print("  2. Daarna  /doorwerk  voor het archiefwerk, voorouder na voorouder.")
    print("  3. Bekijken:  py website/server.py   (of dubbelklik website/start-website.cmd)")
    print("  4. Meten:     py test/controleer.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

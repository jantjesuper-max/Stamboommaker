"""Koppelt geschiedenis — rampen, oorlogen, epidemieën — aan de personen in de stamboom.

  py scripts/tijdsbeeld.py kandidaten <persoon-id>   wat raakte dít leven?
  py scripts/tijdsbeeld.py kandidaten --alle          alle dossiers langs de kalender
  py scripts/tijdsbeeld.py zoek <term>                bestaat er al iets over deze gebeurtenis?
  py scripts/tijdsbeeld.py controleer                 kalender + gebeurtenisbestanden nakijken
  py scripts/tijdsbeeld.py index                      bouwt tijdsbeeld/_INDEX.md

De kalender (tijdsbeeld/_KALENDER.md) noemt per gebeurtenis periode, gebied en zoekingang.
Dit script legt daar de leefjaren en woonplaatsen uit elk dossier naast en noemt
kandidaten. Een kandidaat is een zoekopdracht, geen feit: onderzoeken, dan koppelen
(bestand in tijdsbeeld/, sjabloon _TEMPLATE.md) of afmelden (regel in _AFGEHANDELD.md).

Eén gebeurtenis = één bestand. Vóór je een nieuw bestand maakt: eerst `zoek` draaien
(of _INDEX.md nalopen) — bestaat de gebeurtenis al, dan voeg je de persoon aan dát
bestand toe. `controleer` weigert twee bestanden met dezelfde gebeurtenis-id.

Gewicht: alleen `groot`-gebeurtenissen zijn verplicht werk (elke ronde onderzoeken,
dan koppelen of afmelden). `achtergrond` is tijdskleuring: geen koppeling en geen
afmelding nodig, alleen koppelen bij een concreet spoor.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_lezen import regels_buiten_uitleg

WORTEL = Path(__file__).resolve().parent.parent
MAP = WORTEL / "tijdsbeeld"
KALENDER = MAP / "_KALENDER.md"
AFGEHANDELD = MAP / "_AFGEHANDELD.md"
INDEX = MAP / "_INDEX.md"
PERSONEN = WORTEL / "personen"
WERKLIJST = WORTEL / "onderzoek" / "werklijst-dossiers.md"

SOORTEN = {
    "ramp",
    "oorlog",
    "epidemie",
    "veepest",
    "honger",
    "economie",
    "wet",
    "weer",
    "plaatselijk",
}
GEWICHTEN = {"groot", "achtergrond"}
STATUSSEN = {"✓", "◐", "?", "⚠"}
VELDEN = ["titel", "gebeurtenis", "periode", "soort", "status", "landing", "gevonden"]
JAAR = re.compile(r"(\d{4})")
PERIODE = re.compile(r"^(\d{4})(?:\s*[-–]\s*(\d{4}))?$")
AFGEHANDELD_REGEL = re.compile(
    r"^- ([a-z0-9-]+) · ([a-z0-9-]+) · (\d{2}-\d{2}-\d{4}) · (.+)$"
)
WIKILINK = re.compile(r"\[\[([a-z0-9-]+)\]\]")


def lees_frontmatter(pad):
    tekst = pad.read_text(encoding="utf-8")
    if not tekst.startswith("---"):
        return None, tekst
    einde = tekst.find("\n---", 3)
    if einde == -1:
        return None, tekst
    kop, romp = tekst[3:einde], tekst[einde + 4 :]
    data, huidige_lijst = {}, None
    for regel in kop.splitlines():
        if not regel.strip():
            continue
        if regel.lstrip().startswith("- ") and huidige_lijst:
            data[huidige_lijst].append(regel.lstrip()[2:].strip().strip('"'))
            continue
        m = re.match(r"^(\w+):\s*(.*)$", regel)
        if not m:
            continue
        sleutel, waarde = m.group(1), m.group(2).split("#")[0].strip().strip('"')
        if waarde == "":
            data[sleutel], huidige_lijst = [], sleutel
        else:
            data[sleutel], huidige_lijst = waarde, None
    return data, romp.strip()


def lees_kalender():
    """Leest de regio- en gebeurtenissentabel uit _KALENDER.md."""
    regios, gebeurtenissen, problemen = {}, [], []
    sectie = None
    for nr, regel in enumerate(KALENDER.read_text(encoding="utf-8").splitlines(), 1):
        if regel.startswith("## "):
            kop = regel[3:].lower()
            sectie = "regio" if "regio" in kop else "gebeurtenis" if "gebeurtenis" in kop else None
            continue
        if not (sectie and regel.strip().startswith("|")):
            continue
        cellen = [c.strip() for c in regel.strip().strip("|").split("|")]
        if not cellen or set(cellen[0]) <= {"-", " ", ":"}:
            continue  # scheidingsregel van de tabel
        if sectie == "regio":
            if cellen[0].lower() == "regio":
                continue
            if len(cellen) >= 2:
                regios[cellen[0].lower()] = [
                    p.strip().lower() for p in cellen[1].split(",") if p.strip()
                ]
        else:
            if cellen[0].lower() == "id":
                continue
            if len(cellen) < 7:
                problemen.append(f"regel {nr}: {len(cellen)} kolommen, 7 verwacht (Id, Periode, Gebeurtenis, Soort, Gewicht, Gebied, Zoekingang)")
                continue
            m = PERIODE.match(cellen[1])
            if not m:
                problemen.append(
                    f"regel {nr} ({cellen[0]}): periode '{cellen[1]}' is geen JJJJ of JJJJ-JJJJ"
                )
                continue
            gebeurtenissen.append(
                {
                    "id": cellen[0],
                    "van": int(m.group(1)),
                    "tot": int(m.group(2) or m.group(1)),
                    "omschrijving": cellen[2],
                    "soort": cellen[3],
                    "gewicht": cellen[4],
                    "gebied": [g.strip().lower() for g in cellen[5].split(",") if g.strip()],
                    "zoekingang": cellen[6],
                }
            )
    return regios, gebeurtenissen, problemen


def _plaatsen_uit(waarde):
    """'08-09-1808, Sneek' -> ['sneek']; 'na 1872, plaats onbekend' -> []."""
    plaatsen = []
    if not isinstance(waarde, str) or "," not in waarde:
        return plaatsen
    for deel in re.split(r"[,/]", waarde.split(",", 1)[1]):
        p = re.sub(r"\(.*?\)", "", deel).strip().lower()
        if p and "onbekend" not in p and "?" not in p and not JAAR.search(p):
            plaatsen.append(p)
    return plaatsen


def persoon_gegevens(pad):
    kop, _ = lees_frontmatter(pad)
    kop = kop or {}
    geboren = str(kop.get("geboren", "") or "")
    overleden = str(kop.get("overleden", "") or "")
    m = JAAR.search(geboren)
    geb = int(m.group(1)) if m else None
    m = JAAR.search(overleden)
    if m:
        eind = int(m.group(1))
        onzeker = bool(re.search(r"\bna\b", overleden.lower()))
        if onzeker:
            eind += 15  # "na JJJJ": ruim nemen, kandidaten zijn maar aanwijzingen
    elif geb:
        eind, onzeker = geb + 85, True
    else:
        eind, onzeker = None, True
    plaatsen = set(_plaatsen_uit(geboren) + _plaatsen_uit(overleden))
    woonplaatsen = kop.get("woonplaatsen") or []
    if isinstance(woonplaatsen, str):
        woonplaatsen = [woonplaatsen]
    for w in woonplaatsen:
        p = re.sub(r"\(.*?\)", "", str(w)).strip().lower()
        if p:
            plaatsen.add(p)
    naam = kop.get("naam") or pad.stem
    return {
        "id": pad.stem,
        "naam": str(naam),
        "geb": geb,
        "eind": eind,
        "onzeker": onzeker,
        "plaatsen": plaatsen,
    }


def _woorden(naam):
    """'Alphen aan den Rijn' -> ('alphen','aan','den','rijn'); scheidt ook op - en '."""
    return tuple(w for w in re.split(r"[^a-z0-9]+", str(naam).lower()) if w)


def plaats_past(plaats, doel):
    """Is `plaats` dezelfde plaats als `doel`?

    Vergelijkt op héle woorden en niet op letterreeksen. Een kale
    `doel in plaats` matcht namelijk veel te veel: »echt« (Limburg) zit in
    »Utrecht«, »assen« in »Wassenaar«, »elburg« in »Middelburg« en »hoorn« in
    »Hoornaar« — vier provincies verkeerd gekoppeld door vier letterreeksen.

    De regel: gelijk, of de kortere naam is het **begin** van de langere. Dat
    klopt met hoe Nederlandse plaatsnamen zijn opgebouwd, want de toevoeging
    staat achteraan (»Alphen aan den Rijn«, »Koudekerk aan den Rijn«, »Bergen op
    Zoom«). Een toevoeging vóóraan maakt juist een ándere plaats, en die mag dus
    niet matchen: »Nieuw-Amsterdam« in Drenthe is niet Amsterdam.
    """
    a, b = _woorden(plaats), _woorden(doel)
    if not a or not b:
        return False
    kort, lang = (a, b) if len(a) <= len(b) else (b, a)
    if len(kort) == 1 and len(kort[0]) < 4:
        return False  # te kort om iets te betekenen
    return lang[: len(kort)] == kort


def plaats_raakt(plaatsen, gebied, regios):
    """Geeft de geraakte woonplaats terug, 'landelijk', of None."""
    if "landelijk" in gebied:
        return "landelijk"
    doelen = set()
    for g in gebied:
        doelen.update(regios.get(g, []))
        doelen.add(g)
    for p in sorted(plaatsen):
        for d in doelen:
            if plaats_past(p, d):
                return p
    return None


def gebeurtenis_bestanden():
    bestanden = []
    for pad in sorted(MAP.glob("*.md")):
        if pad.name.startswith("_"):
            continue
        kop, romp = lees_frontmatter(pad)
        bestanden.append({"pad": pad, "kop": kop or {}, "romp": romp})
    return bestanden


def personen_van(kop):
    return WIKILINK.findall("\n".join(kop.get("personen") or []))


def koppelingen(bestanden):
    paren = {}
    for b in bestanden:
        gid = str(b["kop"].get("gebeurtenis", b["pad"].stem))
        for p in personen_van(b["kop"]):
            paren[(p, gid)] = b["pad"].name
    return paren


def per_gebeurtenis(bestanden):
    """gebeurtenis-id -> bestandsna(a)m(en); meer dan één is een duplicaat."""
    mapping = {}
    for b in bestanden:
        gid = str(b["kop"].get("gebeurtenis", b["pad"].stem))
        mapping.setdefault(gid, []).append(b["pad"].name)
    return mapping


def afgemeld():
    paren = {}
    for _, regel in regels_buiten_uitleg(AFGEHANDELD):
        m = AFGEHANDELD_REGEL.match(regel)
        if m:
            paren[(m.group(1), m.group(2))] = m.group(4)
    return paren


def kandidaten(argumenten):
    regios, gebeurtenissen, problemen = lees_kalender()
    for p in problemen:
        print(f"KALENDER: {p}")
    bestanden = gebeurtenis_bestanden()
    gekoppeld = koppelingen(bestanden)
    bestaand = per_gebeurtenis(bestanden)
    gemeld = afgemeld()
    if argumenten.alle:
        paden = sorted(p for p in PERSONEN.glob("*.md") if not p.stem.startswith("_"))
    else:
        if not argumenten.persoon:
            print("FOUT: geef een persoon-id of --alle")
            return 1
        pad = PERSONEN / f"{argumenten.persoon}.md"
        if not pad.exists():
            print(f"FOUT: personen/{argumenten.persoon}.md bestaat niet")
            return 1
        paden = [pad]

    totaal_open = 0
    for pad in paden:
        pers = persoon_gegevens(pad)
        if not pers["geb"]:
            print(
                f"== {pers['id']} — geen geboortejaar in de frontmatter; "
                "kandidaten niet te bepalen ==\n"
            )
            continue
        eind = f"±{pers['eind']}" if pers["onzeker"] else str(pers["eind"])
        plaatsen = ", ".join(sorted(pers["plaatsen"])) or "geen (alleen landelijke kandidaten)"
        groot_, achter_, dicht = [], [], []
        for g in gebeurtenissen:
            if g["tot"] < pers["geb"] or g["van"] > pers["eind"]:
                continue
            raak = plaats_raakt(pers["plaatsen"], g["gebied"], regios)
            if not raak:
                continue
            paar = (pers["id"], g["id"])
            if paar in gekoppeld:
                dicht.append(f"al gekoppeld: {g['id']} → tijdsbeeld/{gekoppeld[paar]}")
                continue
            if paar in gemeld:
                dicht.append(f"afgemeld: {g['id']} — {gemeld[paar]}")
                continue
            periode = str(g["van"]) if g["van"] == g["tot"] else f"{g['van']}-{g['tot']}"
            if g["gewicht"] != "groot":
                achter_.append(f"  ~ [{g['soort']}] {g['id']} · {periode} · {g['omschrijving']}")
                continue
            leeftijd = g["van"] - pers["geb"]
            if leeftijd < 0:
                wanneer = "geboren middenin deze periode"
            elif leeftijd == 0:
                wanneer = "geboren in dit jaar"
            else:
                wanneer = f"{leeftijd} jaar bij aanvang"
            regel = (
                f"  [{g['soort']}] {g['id']} · {periode} · {g['omschrijving']}\n"
                f"     raakvlak: {raak} · {wanneer} · zoek: {g['zoekingang']}"
            )
            if raak == "landelijk":
                regel += "\n     landelijk: alleen koppelen met een plaatselijk of persoonlijk spoor"
            if g["id"] in bestaand:
                regel += (
                    f"\n     let op, bestaat al: tijdsbeeld/{bestaand[g['id']][0]} — "
                    "voeg deze persoon dáár toe, géén nieuw bestand"
                )
            groot_.append(regel)
        totaal_open += len(groot_)
        print(f"== {pers['id']} · {pers['naam']} ({pers['geb']}–{eind}) · plaatsen: {plaatsen} ==")
        print("\n".join(groot_) if groot_ else "  geen open groot-kandidaten")
        if achter_:
            print("  achtergrond (tijdskleuring — niet koppelen of afmelden, tenzij een concreet spoor opduikt):")
            print("\n".join(achter_))
        for d in dicht:
            print(f"  · {d}")
        print()

    if totaal_open:
        print(
            f"{totaal_open} open groot-kandida(a)t(en) — verplicht werk voor de ronde: "
            "elk echt onderzoeken via de zoekingang, dan koppelen of beargumenteerd "
            "afmelden (regel in tijdsbeeld/_AFGEHANDELD.md). Koppelen: éérst "
            "`py scripts/tijdsbeeld.py zoek <term>` — bestaat de gebeurtenis al, vul dát "
            "bestand aan; anders een nieuw bestand naar _TEMPLATE.md."
        )
    else:
        print("Geen open groot-kandidaten.")
    return 0


def zoek(argumenten):
    """Doorzoekt kalender én gebeurtenisbestanden — draaien vóór je een nieuw bestand maakt."""
    term = argumenten.term.lower()
    _, gebeurtenissen, _ = lees_kalender()
    treffers = 0
    for g in gebeurtenissen:
        doorzoekbaar = " ".join(
            [g["id"], g["omschrijving"], g["soort"], " ".join(g["gebied"]), g["zoekingang"]]
        ).lower()
        if term in doorzoekbaar:
            periode = str(g["van"]) if g["van"] == g["tot"] else f"{g['van']}-{g['tot']}"
            print(f"kalender   [{g['gewicht']}] {g['id']} · {periode} · {g['omschrijving']}")
            treffers += 1
    for b in gebeurtenis_bestanden():
        doorzoekbaar = (b["pad"].read_text(encoding="utf-8")).lower()
        if term in doorzoekbaar:
            kop = b["kop"]
            print(
                f"bestand    tijdsbeeld/{b['pad'].name} · {kop.get('periode', '?')} · "
                f"{kop.get('titel', '?')} · personen: "
                f"{', '.join(personen_van(kop)) or '—'}"
            )
            treffers += 1
    if treffers:
        print(
            f"\n{treffers} treffer(s). Staat de gebeurtenis er al als bestand: vul dát aan "
            "(persoon in de frontmatter + Raakvlak-regel). Staat hij alleen in de kalender: "
            "nieuw bestand met precies die gebeurtenis-id. Staat hij nergens: nieuw bestand "
            "met een eigen slug én een regel in de kalender."
        )
    else:
        print(
            "Geen treffers in kalender of bestanden — een nieuw bestand (en zo mogelijk "
            "een kalenderregel) is hier op zijn plaats."
        )
    return 0


def controleer(_argumenten):
    problemen = []
    regios, gebeurtenissen, kalender_problemen = lees_kalender()
    problemen += [f"_KALENDER.md: {p}" for p in kalender_problemen]
    ids = [g["id"] for g in gebeurtenissen]
    for dubbel in sorted({i for i in ids if ids.count(i) > 1}):
        problemen.append(f"_KALENDER.md: id '{dubbel}' komt meer dan één keer voor")
    for g in gebeurtenissen:
        if g["soort"] not in SOORTEN:
            problemen.append(
                f"_KALENDER.md ({g['id']}): soort '{g['soort']}' bestaat niet "
                f"({', '.join(sorted(SOORTEN))})"
            )
        if g["gewicht"] not in GEWICHTEN:
            problemen.append(
                f"_KALENDER.md ({g['id']}): gewicht '{g['gewicht']}' moet groot of achtergrond zijn"
            )

    bekend = {p.stem for p in PERSONEN.glob("*.md") if not p.stem.startswith("_")}
    if WERKLIJST.exists():
        bekend |= set(re.findall(r"· ([a-z0-9-]+) —", WERKLIJST.read_text(encoding="utf-8")))

    bestanden = gebeurtenis_bestanden()
    for gid, namen in per_gebeurtenis(bestanden).items():
        if len(namen) > 1:
            problemen.append(
                f"duplicaat: {', '.join(namen)} hebben allemaal gebeurtenis-id '{gid}' — "
                "één gebeurtenis hoort in één bestand; voeg ze samen"
            )
    for b in bestanden:
        naam = b["pad"].name
        kop = b["kop"]
        if not kop:
            problemen.append(f"{naam}: geen frontmatter")
            continue
        for veld in VELDEN:
            if not kop.get(veld):
                problemen.append(f"{naam}: veld '{veld}' ontbreekt of is leeg")
        if kop.get("soort") and str(kop["soort"]) not in SOORTEN:
            problemen.append(
                f"{naam}: soort '{kop['soort']}' bestaat niet ({', '.join(SOORTEN)})"
            )
        if kop.get("status") and str(kop["status"]) not in STATUSSEN:
            problemen.append(f"{naam}: status '{kop['status']}' moet ✓/◐/?/⚠ zijn")
        personen = personen_van(kop)
        if not personen:
            problemen.append(f"{naam}: geen personen gekoppeld")
        for p in personen:
            if p not in bekend:
                problemen.append(f"{naam}: [[{p}]] staat niet in de werklijst of personen/")
        if "**Bron" not in b["romp"]:
            problemen.append(f"{naam}: geen regel met **Bronnen:** — zonder bron geen koppeling")

    gemeld = afgemeld()
    for persoon, gid in gemeld:
        if persoon not in bekend:
            problemen.append(f"_AFGEHANDELD.md: persoon '{persoon}' onbekend")
        if gid not in set(ids):
            problemen.append(f"_AFGEHANDELD.md: gebeurtenis '{gid}' staat niet in de kalender")
    if AFGEHANDELD.exists():
        for nr, regel in regels_buiten_uitleg(AFGEHANDELD):
            if regel.startswith("- ") and not AFGEHANDELD_REGEL.match(regel):
                problemen.append(
                    f"_AFGEHANDELD.md regel {nr}: volgt het format "
                    "'- persoon-id · gebeurtenis-id · DD-MM-JJJJ · reden' niet"
                )

    print(
        f"Kalender: {len(gebeurtenissen)} gebeurtenissen, {len(regios)} regio's · "
        f"gebeurtenisbestanden: {len(bestanden)} · afgemeld: {len(gemeld)}"
    )
    if problemen:
        print(f"\n{len(problemen)} probleem(en):")
        for p in problemen:
            print(f"  - {p}")
        return 1
    print("Geen problemen gevonden.")
    return 0


def index(_argumenten):
    bestanden = [b for b in gebeurtenis_bestanden() if b["kop"]]
    bestanden.sort(key=lambda b: str(b["kop"].get("periode", "")))
    vandaag = datetime.date.today().strftime("%d-%m-%Y")
    regels = [
        "# Tijdsbeeld-index",
        "",
        "_Gebouwd bestand — niet met de hand bewerken. Bouwen met `py scripts/tijdsbeeld.py index`._",
        "",
        f"{len(bestanden)} gebeurtenis(sen) gekoppeld aan personen, bijgewerkt op {vandaag}.",
        "",
        "**Eerst hier (of met `py scripts/tijdsbeeld.py zoek <term>`) kijken vóór je een",
        "nieuw gebeurtenisbestand maakt** — bestaat de gebeurtenis al, dan voeg je de",
        "persoon aan dat bestand toe.",
        "",
        "| Soort | Id | Gebeurtenis | Periode | Plaatsen | Personen | Status | Landing |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for b in bestanden:
        kop = b["kop"]
        soort = str(kop.get("soort", "?"))
        gid = str(kop.get("gebeurtenis", b["pad"].stem))
        titel = f"[{kop.get('titel', b['pad'].name)}]({b['pad'].name})"
        plaatsen = kop.get("plaatsen") or []
        if isinstance(plaatsen, str):
            plaatsen = [plaatsen]
        personen = ", ".join(f"`{p}`" for p in personen_van(kop)) or "—"
        landing = str(kop.get("landing", "?"))
        landing = "**onverwerkt**" if landing == "onverwerkt" else landing
        regels.append(
            f"| {soort} | `{gid}` | {titel} | {kop.get('periode', '?')} "
            f"| {', '.join(plaatsen) or '—'} | {personen} "
            f"| {kop.get('status', '?')} | {landing} |"
        )
    regels.append("")
    INDEX.write_text("\n".join(regels) + "\n", encoding="utf-8")
    print(f"Gebouwd: {INDEX.relative_to(WORTEL)} ({len(bestanden)} gebeurtenissen)")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="opdracht", required=True)
    p = sub.add_parser("kandidaten")
    p.add_argument("persoon", nargs="?", help="persoon-id (bestandsnaam in personen/)")
    p.add_argument("--alle", action="store_true", help="alle dossiers langslopen")
    p.set_defaults(func=kandidaten)
    z = sub.add_parser("zoek")
    z.add_argument("term", help="zoekterm (plaats, jaar, gebeurtenis, persoon-id)")
    z.set_defaults(func=zoek)
    sub.add_parser("controleer").set_defaults(func=controleer)
    sub.add_parser("index").set_defaults(func=index)
    argumenten = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    return argumenten.func(argumenten)


if __name__ == "__main__":
    sys.exit(main())

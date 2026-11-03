"""Controleert of werklijst, dossiers en overzicht synchroon lopen.

Draaien met:  py test/controleer.py        (vanuit de projectmap)
              py test/controleer.py --fix   (werkt het voortgangscijfer bij)

Meet zeven dingen:
  0. Niemand staat twee keer op de werklijst, ook niet onder twee id's.
  1. Elk afgevinkt item heeft een dossier in personen/.
  2. Elk dossier in personen/ staat in de werklijst.
  3. Elk dossier is compleet genoeg om afgevinkt te mogen zijn (met Levensloop).
  4. Wikilinks in dossiers verwijzen naar ID's die in de werklijst bestaan, en een
     ouder die in de kerngegevens bij naam wordt genoemd heeft ook een
     `vader:`/`moeder:`-wikilink — en daarmee een werklijstregel.
  5. Documentmappen horen bij werklijst-ID's en elk bestand heeft een beschrijving.
  6. Elk knipsel (![bijschrift](pad)) in een dossier, verhaal of hoofdstuk wijst naar
     een bestand dat bestaat, en heeft een bijschrift.
"""

import re
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
WERKLIJST = WORTEL / "onderzoek" / "werklijst-dossiers.md"
PERSONEN = WORTEL / "personen"

REGEL = re.compile(r"^- \[([ x])\] (g\d+) . ([a-z0-9-]+) — (.+)$")
WIKILINK = re.compile(r"\[\[([a-z0-9-]+)\]\]")
OUDER = re.compile(r'^(vader|moeder): "\[\[([a-z0-9-]+)\]\]"', re.M)
OPEN_VRAAG = re.compile(r"^- \[ \] ", re.M)

# Tijdsbeeld: open groot-kandidaten (stap 6 van de doorwerk-skill) tellen als
# openstaand werk, net als open vragen — anders wordt die stap overgeslagen.
sys.path.insert(0, str(WORTEL / "scripts"))
from md_lezen import regels_buiten_uitleg

try:
    import tijdsbeeld as _tb
except Exception:
    _tb = None


def tijdsbeeld_stand():
    """persoon-id -> aantal open groot-kandidaten (niet gekoppeld, niet afgemeld)."""
    if _tb is None:
        return {}
    try:
        regios, gebeurtenissen, _ = _tb.lees_kalender()
        gekoppeld = _tb.koppelingen(_tb.gebeurtenis_bestanden())
        gemeld = _tb.afgemeld()
    except Exception:
        return {}
    stand = {}
    for pad in PERSONEN.glob("*.md"):
        if pad.stem.startswith("_"):
            continue
        pers = _tb.persoon_gegevens(pad)
        if not pers["geb"]:
            continue
        n = 0
        for g in gebeurtenissen:
            if g["gewicht"] != "groot":
                continue
            if g["tot"] < pers["geb"] or g["van"] > pers["eind"]:
                continue
            if not _tb.plaats_raakt(pers["plaatsen"], g["gebied"], regios):
                continue
            if (pers["id"], g["id"]) in gekoppeld or (pers["id"], g["id"]) in gemeld:
                continue
            n += 1
        if n:
            stand[pad.stem] = n
    return stand


def open_vragen(pad):
    """Aantal nog niet gesloten vragen in de sectie '## Open vragen' van een dossier.

    Een vraag mag pas dicht (`- [x]`) als er een antwoord is óf een expliciete sluiting
    ('niet gevonden in X'). Zolang er open vragen staan, is de persoon niet af."""
    if not pad.exists():
        return 0
    tekst = pad.read_text(encoding="utf-8")
    begin = tekst.find("## Open vragen")
    if begin == -1:
        return 0
    volgende = tekst.find("\n## ", begin + 1)
    sectie = tekst[begin : volgende if volgende != -1 else len(tekst)]
    return len(OPEN_VRAAG.findall(sectie))

# Kopjes die een dossier moet hebben om als afgevinkt te gelden. De Levensloop staat
# erbij: dat is het verhalende deel en volgens het sjabloon de grondstof voor het boek.
# In een ander project viel dat kopje ongemerkt weg zodra er thematische kopjes voor in
# de plaats kwamen, en na een maand misten 129 van de 452 dossiers het.
VEREISTE_KOPJES = ["## Kerngegevens", "## Levensloop", "## Documenten", "## Onderzoekslog"]

# Een knipsel of scan in de tekst: ![bijschrift](pad). Het bijschrift mag één niveau
# rechte haken bevatten ("[...]" voor een weglating), net als in de website en de PDF.
AFBEELDING = re.compile(r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]+)[^)]*\)")


def lees_werklijst():
    # regels_buiten_uitleg laat codeblokken en HTML-commentaar weg: de werklijst
    # legt bovenaan het regelformat uit met voorbeelden erbij, en die voorbeelden
    # zijn geen voorouders.
    items = []
    for nr, regel in regels_buiten_uitleg(WERKLIJST):
        m = REGEL.match(regel)
        if m:
            items.append(
                {
                    "regelnr": nr,
                    "af": m.group(1) == "x",
                    "generatie": int(m.group(2)[1:]),
                    "id": m.group(3),
                    "naam": m.group(4),
                    "regel": regel,
                }
            )
    return items


def kern_id(pid):
    """'rinke-pieters-1730ca' -> 'rinke-pieters': het id zonder jaarstaart."""
    return re.sub(r"-\d{3,4}(ca)?$", "", pid)


def dubbele_regels(items):
    """Dezelfde persoon twee keer op de werklijst — letterlijk, of onder twee id's.

    per_id is een dict, dus bij een dubbel ID wint stilzwijgend de LAATSTE regel en
    verdwijnt de eerste uit elke telling en uit de route; het voortgangscijfer telt de
    persoon bovendien dubbel. Het gemenere geval is een id mét en zonder jaarstaart
    (`rinke-pieters` naast `rinke-pieters-1730ca`), allebei dezelfde generatie: de route
    stuurt dan naar de kale kopie van iemand die al lang is afgerond. De eis "dezelfde
    generatie" is nodig, want grootvader en kleinzoon dragen geregeld dezelfde naam.
    Een regel met '· overgeslagen:' telt niet mee: dat is de manier om een kopie
    onschadelijk te maken.
    """
    problemen = []
    gezien = {}
    for i in items:
        gezien.setdefault(i["id"], []).append(i["regelnr"])
    for pid, regels in sorted(gezien.items()):
        if len(regels) > 1:
            problemen.append(
                f"'{pid}' staat {len(regels)}x op de werklijst (regels "
                + ", ".join(str(r) for r in regels)
                + ") — houd één regel over en voeg de vondsten samen"
            )
    kernen = {}
    for i in items:
        if "overgeslagen:" in i["naam"]:
            continue
        kernen.setdefault((kern_id(i["id"]), i["generatie"]), []).append(i)
    for (kern, gen), groep in sorted(kernen.items(), key=lambda x: str(x[0])):
        ids = sorted({i["id"] for i in groep})
        if len(ids) < 2:
            continue
        problemen.append(
            f"g{gen} · '{kern}' staat onder {len(ids)} verschillende id's op de werklijst ("
            + ", ".join(f"regel {i['regelnr']}={i['id']}" for i in groep)
            + ") — dezelfde persoon in dezelfde generatie; houd één id over en zet achter "
            "de andere '· overgeslagen: dubbele regel, zie <id>'"
        )
    return problemen


def ouders_zonder_wikilink(items):
    """Ouder wél bij naam in de kerngegevens, maar geen wikilink in de frontmatter.

    Dit is het gat waar voorouders in vallen: een vader staat als "Vader | Jan Jansen"
    in de kerngegevens van zijn kind, maar zonder `vader:`-wikilink en dus zonder
    werklijstregel. De route stuurt er dan nooit iemand heen. Een gevonden ouder krijgt
    altijd drie dingen: een werklijstregel, een wikilink en een node in het overzicht.
    """
    LEEG = ("onbekend", "niet gevonden", "niet in de akte", "niet bekend", "geen", "—", "-")
    problemen = []
    for i in items:
        pad = PERSONEN / f"{i['id']}.md"
        if not (i["af"] and pad.exists()):
            continue
        tekst = pad.read_text(encoding="utf-8")
        deel = tekst.split("---")
        fm, body = (deel[1], "---".join(deel[2:])) if len(deel) > 2 else ("", tekst)
        for rol in ("vader", "moeder"):
            # let op: `\s*` zou de nieuwe regel meenemen en dan lijkt een leeg veld gevuld
            m = re.search(rf"^{rol}:[^\S\n]*(.*)$", fm, re.M)
            if m and m.group(1).strip().strip('"'):
                continue  # veld is gevuld; controle 4 kijkt of het doel bestaat
            rij = re.search(rf"^\|\s*{rol}\s*\|([^|]*)\|", body, re.M | re.I)
            if not rij:
                continue
            inhoud = re.sub(r"[*⚠]", "", rij.group(1)).strip()
            if not inhoud or inhoud.lower().startswith(LEEG):
                continue
            problemen.append(
                f"personen/{i['id']}.md: veld '{rol}:' is leeg terwijl de kerngegevens "
                f"'{inhoud[:60]}' noemen — geen werklijstregel voor die voorouder?"
            )
    return problemen


def knipsel_problemen(wortel=WORTEL):
    """Elk knipsel wijst naar een bestand dat bestaat en heeft een bijschrift.

    Een knipsel is een bewering ("zo staat het in de krant"), dus een kapotte link of
    een leeg bijschrift is net zo'n gebrek als een feit zonder bron. Het pad wordt
    opgelost ten opzichte van het markdown-bestand, precies zoals de website en de PDF
    dat doen. Webadressen worden niet gecontroleerd.
    """
    problemen = []
    mappen = [wortel / "personen", wortel / "boek" / "verhalen", wortel / "boek" / "hoofdstukken",
              wortel / "tijdsbeeld"]
    gebruikt = set()
    for map_ in mappen:
        if not map_.is_dir():
            continue
        for pad in sorted(map_.glob("*.md")):
            if pad.name.startswith("_"):
                continue
            rel = pad.relative_to(wortel).as_posix()
            for m in AFBEELDING.finditer(pad.read_text(encoding="utf-8")):
                bijschrift, src = m.group(1).strip(), m.group(2)
                if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
                    continue
                doel = (pad.parent / src).resolve()
                try:
                    gebruikt.add(doel.relative_to(wortel.resolve()).as_posix())
                except ValueError:
                    pass
                if not doel.is_file():
                    problemen.append(f"{rel}: knipsel '{src}' bestaat niet (gezocht als {doel})")
                if not bijschrift:
                    problemen.append(f"{rel}: knipsel '{src}' heeft geen bijschrift — noem bron en datum")
    beeldmap = wortel / "boek" / "verhalen" / "beeld"
    los = []
    if beeldmap.is_dir():
        for b in sorted(beeldmap.iterdir()):
            if b.is_file() and b.name != ".gitkeep":
                if b.relative_to(wortel).as_posix() not in gebruikt:
                    los.append(b.name)
    return problemen, los


def bepaal_volgende(items, per_id, tb_stand):
    """De onderzoeksroute.

    0. **Afmaken vóór doorgaan.** Heeft een al afgevinkt dossier nog open vragen of
       onbehandelde tijdsbeeld-groot-kandidaten, dan is dát het werk: eerst sluiten
       (antwoord, koppeling of beargumenteerde afmelding), pas daarna een nieuwe
       voorouder beginnen.
    1. Omhoog: ouders van afgeronde dossiers, diepste generatie eerst, vader vóór moeder.
    2. Opzij: is er niets omhoog, dan de eerste onafgevinkte regel van de lijst."""
    onaf = []
    for i in items:
        if not i["af"]:
            continue
        vragen = open_vragen(PERSONEN / f"{i['id']}.md")
        tb = tb_stand.get(i["id"], 0)
        if vragen or tb:
            onaf.append((i, vragen, tb))
    if onaf:
        onaf.sort(key=lambda x: -x[0]["generatie"])
        kandidaat, vragen, tb = onaf[0]
        delen = []
        if vragen:
            delen.append(f"{vragen} open vraag/vragen")
        if tb:
            delen.append(f"{tb} tijdsbeeld-groot-kandida(a)t(en)")
        return kandidaat, "afmaken: nog " + " en ".join(delen) + " te sluiten"

    front = []
    gezien = set()
    for i in items:
        if not i["af"] or "overgeslagen:" in i["naam"]:
            continue
        pad = PERSONEN / f"{i['id']}.md"
        if not pad.exists():
            continue
        for rol, ouder in OUDER.findall(pad.read_text(encoding="utf-8")):
            kandidaat = per_id.get(ouder)
            if (
                kandidaat
                and not kandidaat["af"]
                and "overgeslagen:" not in kandidaat["naam"]
                and ouder not in gezien
            ):
                gezien.add(ouder)
                front.append((kandidaat, rol, i["id"]))
    if front:
        front.sort(key=lambda f: -f[0]["generatie"])  # stabiel: diepste eerst
        kandidaat, rol, kind = front[0]
        return kandidaat, f"omhoog: {rol} van {kind}"
    fallback = next(
        (i for i in items if not i["af"] and "overgeslagen:" not in i["naam"]), None
    )
    return fallback, "nieuwe lijn (geen open ouders meer bij afgeronde dossiers)"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows-console kan anders niet ✓/◐ printen
    except AttributeError:
        pass
    if not WERKLIJST.exists():
        print(f"FOUT: werklijst niet gevonden op {WERKLIJST}")
        return 1

    items = lees_werklijst()
    per_id = {i["id"]: i for i in items}
    dossiers = {p.stem for p in PERSONEN.glob("*.md") if not p.stem.startswith("_")}
    problemen = []

    # 0. dezelfde persoon twee keer op de werklijst
    problemen.extend(dubbele_regels(items))

    # 1. afgevinkt zonder dossier
    for i in items:
        if i["af"] and i["id"] not in dossiers:
            problemen.append(
                f"regel {i['regelnr']}: '{i['id']}' is afgevinkt maar personen/{i['id']}.md bestaat niet"
            )

    # 2. dossier zonder werklijst-regel
    for d in sorted(dossiers - set(per_id)):
        problemen.append(f"personen/{d}.md staat niet in de werklijst")

    # 3. afgevinkte dossiers op volledigheid
    for i in items:
        pad = PERSONEN / f"{i['id']}.md"
        if not (i["af"] and pad.exists()):
            continue
        tekst = pad.read_text(encoding="utf-8")
        for kopje in VEREISTE_KOPJES:
            if kopje not in tekst:
                problemen.append(f"personen/{i['id']}.md: kopje '{kopje}' ontbreekt")
        if "id: achternaam-voornamen-geboortejaar" in tekst:
            problemen.append(f"personen/{i['id']}.md: sjabloon-ID nog niet vervangen")

    # 4. wikilinks naar onbekende ID's
    for pad in sorted(PERSONEN.glob("*.md")):
        if pad.stem.startswith("_"):
            continue
        for doel in sorted(set(WIKILINK.findall(pad.read_text(encoding="utf-8")))):
            if doel not in per_id:
                problemen.append(
                    f"personen/{pad.stem}.md verwijst naar [[{doel}]], dat niet in de werklijst staat"
                )

    # 4b. ouder wél bij naam in de kerngegevens, maar geen wikilink in de frontmatter
    problemen.extend(ouders_zonder_wikilink(items))

    # 5. documenten: mappen horen bij werklijst-ID's, elk bestand heeft een beschrijving
    documenten = WORTEL / "documenten"
    # Een akte kan meer dan één scan hebben (een spread over twee bladzijden). Die heten
    # dan ..._2.jpg, ..._3.jpg; één beschrijvingsbestand op de basisnaam dekt ze allemaal.
    naamgeving = re.compile(
        r"^\d{4}-\d{2}-\d{2}_[a-z]+_[a-z0-9-]+(_\d+)?\.(jpg|jpeg|png|pdf)$"
    )
    vervolgscan = re.compile(r"_\d+$")
    for map_ in sorted(documenten.iterdir()):
        if not map_.is_dir() or map_.name == "inbox":
            continue
        if map_.name not in per_id:
            problemen.append(f"documenten/{map_.name}/ hoort bij geen enkel werklijst-ID")
        for bestand in sorted(map_.iterdir()):
            if bestand.suffix == ".md" or bestand.name == ".gitkeep":
                continue
            if not naamgeving.match(bestand.name):
                problemen.append(
                    f"documenten/{map_.name}/{bestand.name}: naam volgt de conventie "
                    "JJJJ-MM-DD_type_persoon-id.ext niet"
                )
            # Voor een vervolgscan (_2, _3) volstaat het beschrijvingsbestand van de eerste.
            basis = vervolgscan.sub("", bestand.stem)
            if not (map_ / f"{basis}.md").exists():
                problemen.append(
                    f"documenten/{map_.name}/{bestand.name}: beschrijvingsbestand "
                    f"({basis}.md) ontbreekt"
                )
    inbox = [b for b in (documenten / "inbox").glob("*") if b.name != ".gitkeep"]
    if inbox:
        print(f"Let op: {len(inbox)} bestand(en) in documenten/inbox/ wachten op verwerking.")

    # 6. knipsels: elk beeld bestaat en heeft een bijschrift
    knipsels, losse_beelden = knipsel_problemen()
    problemen.extend(knipsels)
    if losse_beelden:
        print(f"Let op: {len(losse_beelden)} knipsel(s) in boek/verhalen/beeld/ worden nergens "
              f"gebruikt: {', '.join(losse_beelden[:6])}{' …' if len(losse_beelden) > 6 else ''}")

    af = sum(1 for i in items if i["af"])
    totaal = len(items)
    print(f"Werklijst: {af} / {totaal} afgevinkt · dossiers aanwezig: {len(dossiers)}")

    # 6. afgevinkte dossiers met nog open vragen of tijdsbeeld-kandidaten: nog niet echt af
    tb_stand = tijdsbeeld_stand()
    nog_open = []
    for i in items:
        if not i["af"]:
            continue
        vragen = open_vragen(PERSONEN / f"{i['id']}.md")
        tb = tb_stand.get(i["id"], 0)
        if vragen or tb:
            nog_open.append((i["id"], vragen, tb))
    if nog_open:
        print(
            f"Nog te sluiten in {len(nog_open)} afgevinkt(e) dossier(s): "
            f"{sum(v for _, v, _ in nog_open)} open vraag/vragen en "
            f"{sum(t for _, _, t in nog_open)} tijdsbeeld-groot-kandida(a)t(en):"
        )
        for pid, v, t in sorted(nog_open, key=lambda x: -(x[1] + x[2])):
            delen = ([f"{v} vraag/vragen"] if v else []) + ([f"{t} tijdsbeeld"] if t else [])
            print(f"  - {pid}: " + ", ".join(delen))

    volgende, route = bepaal_volgende(items, per_id, tb_stand)
    if volgende:
        print(
            f"Volgende aan de beurt ({route}): "
            f"{volgende['id']} — {volgende['naam']} (g{volgende['generatie']})"
        )
    else:
        print("Werklijst is leeg — alle dossiers zijn gemaakt.")
    overgeslagen = sum(1 for i in items if not i["af"] and "overgeslagen:" in i["naam"])
    if overgeslagen:
        print(f"Let op: {overgeslagen} regel(s) gemarkeerd als overgeslagen — periodiek opnieuw bekijken.")

    if "--fix" in sys.argv:
        tekst = WERKLIJST.read_text(encoding="utf-8")
        nieuw = re.sub(
            r"Voortgang: \*\*\d+ / \d+\*\* afgevinkt\.",
            f"Voortgang: **{af} / {totaal}** afgevinkt.",
            tekst,
            count=1,
        )
        if nieuw != tekst:
            WERKLIJST.write_text(nieuw, encoding="utf-8")
            print("Voortgangscijfer in de werklijst bijgewerkt.")

    if problemen:
        print(f"\n{len(problemen)} probleem(en):")
        for p in problemen:
            print(f"  - {p}")
        return 1

    print("Geen problemen gevonden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

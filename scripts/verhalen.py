"""Beheert de verhalenverzameling: index bouwen, controleren, doorzoeken.

  py scripts/verhalen.py index                 bouwt boek/verhalen-index.md
  py scripts/verhalen.py lijst --deel 1        wat ligt er voor deel 1?
  py scripts/verhalen.py lijst --onverwerkt    wat wacht nog op een hoofdstuk?
  py scripts/verhalen.py lijst --lijn Bakker   alles van één familielijn
  py scripts/verhalen.py lijst --rubriek raadsel
  py scripts/verhalen.py controleer            frontmatter en bronnen nakijken

Eén bestand per verhaal in boek/verhalen/, met frontmatter volgens _TEMPLATE.md. Zo blijft
de verzameling doorzoekbaar als er honderden verhalen liggen, en kan het schrijven van een
hoofdstuk beginnen met "geef me alles voor deel 3".
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
VERHALEN = WORTEL / "boek" / "verhalen"
INDEX = WORTEL / "boek" / "verhalen-index.md"

VELDEN = ["titel", "rubriek", "deel", "lijn", "periode", "sterkte", "score", "landing", "gevonden"]
RUBRIEKEN = {
    "verlies",
    "migratie",
    "werk",
    "krant",
    "raadsel",
    "namen",
    "bureaucratie",
    "verband",
    "geloof",
    "geld",
    "tijdsbeeld",
}
STERKTES = {"sterk", "mager", "vermoeden"}


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


def alle_verhalen():
    verhalen = []
    for pad in sorted(VERHALEN.glob("*.md")):
        if pad.stem.startswith("_"):
            continue
        kop, romp = lees_frontmatter(pad)
        if kop is None:
            verhalen.append({"bestand": pad, "kapot": "geen frontmatter"})
            continue
        kop["bestand"] = pad
        kop["romp"] = romp
        verhalen.append(kop)
    return verhalen


def _sorteersleutel(v):
    try:
        deel = int(str(v.get("deel", 99)))
    except ValueError:
        deel = 99
    return (deel, str(v.get("periode", "")), str(v.get("titel", "")))


def index(_argumenten):
    verhalen = [v for v in alle_verhalen() if not v.get("kapot")]
    verhalen.sort(key=_sorteersleutel)
    vandaag = datetime.date.today().strftime("%d-%m-%Y")
    regels = [
        "# Verhalen-index",
        "",
        "_Gebouwd bestand — niet met de hand bewerken. Bouwen met `py scripts/verhalen.py index`._",
        "",
        f"{len(verhalen)} verhalen in `boek/verhalen/`, bijgewerkt op {vandaag}.",
        "",
    ]

    onverwerkt = [v for v in verhalen if str(v.get("landing", "")) == "onverwerkt"]
    vermoedens = [v for v in verhalen if str(v.get("sterkte", "")) == "vermoeden"]
    regels += [
        f"- **{len(onverwerkt)}** wachten nog op een hoofdstuk",
        f"- **{len(vermoedens)}** rusten nog op een vermoeden en hebben bewijs nodig",
        "",
        "---",
        "",
    ]

    per_deel = {}
    for v in verhalen:
        per_deel.setdefault(str(v.get("deel", "0")), []).append(v)

    for deel in sorted(per_deel, key=lambda d: int(d) if d.isdigit() else 99):
        groep = per_deel[deel]
        kop = f"## Deel {deel}" if deel != "0" else "## Nog geen deel"
        lijnen = sorted({str(v.get("lijn", "?")) for v in groep})
        regels += [f"{kop} — {', '.join(lijnen)}", ""]
        regels += ["| Rubriek | Verhaal | Periode | Sterkte | Landing |", "|---|---|---|---|---|"]
        for v in groep:
            rubriek = str(v.get("rubriek", "?"))
            naam = v["bestand"].name
            titel = f"[{v.get('titel', naam)}](verhalen/{naam})"
            landing = str(v.get("landing", "?"))
            landing = "**onverwerkt**" if landing == "onverwerkt" else landing
            regels.append(
                f"| {rubriek} | {titel} | {v.get('periode', '?')} | {v.get('sterkte', '?')} | {landing} |"
            )
        regels.append("")

    INDEX.write_text("\n".join(regels) + "\n", encoding="utf-8")
    print(f"Gebouwd: {INDEX.relative_to(WORTEL)} ({len(verhalen)} verhalen)")
    return 0


def lijst(argumenten):
    verhalen = [v for v in alle_verhalen() if not v.get("kapot")]
    if argumenten.deel:
        verhalen = [v for v in verhalen if str(v.get("deel")) == str(argumenten.deel)]
    if argumenten.lijn:
        verhalen = [v for v in verhalen if argumenten.lijn.lower() in str(v.get("lijn", "")).lower()]
    if argumenten.rubriek:
        verhalen = [v for v in verhalen if str(v.get("rubriek")) == argumenten.rubriek]
    if argumenten.onverwerkt:
        verhalen = [v for v in verhalen if str(v.get("landing", "")) == "onverwerkt"]
    if argumenten.persoon:
        verhalen = [
            v for v in verhalen
            if any(argumenten.persoon in p for p in (v.get("personen") or []))
        ]
    verhalen.sort(key=_sorteersleutel)
    if not verhalen:
        print("Geen verhalen die aan de filters voldoen.")
        return 0
    for v in verhalen:
        print(
            f"[{v.get('rubriek', '?')}] deel {v.get('deel', '?')} · {v.get('periode', '?')} · "
            f"{v.get('sterkte', '?')} · {v.get('landing', '?')}\n"
            f"   {v.get('titel', '?')}  [{v['bestand'].name}]"
        )
    print(f"\n{len(verhalen)} verhaal(en).")
    return 0


def heeft_citaat(romp):
    """Staat de bron zelf ergens aan het woord? (citaatblok met '>' — zie stijlgids)"""
    return any(regel.startswith(">") for regel in romp.splitlines())


def controleer(_argumenten):
    problemen = []
    zonder_citaat = []
    verhalen = alle_verhalen()
    for v in verhalen:
        naam = v["bestand"].name
        if v.get("kapot"):
            problemen.append(f"{naam}: {v['kapot']}")
            continue
        # Geen fout, wel een aandachtspunt: een verhaal dat op aktes rust en nergens een
        # letterlijke regel uit die aktes laat zien, leest als samenvatting in plaats van
        # als document. Zie boek/stijlgids.md, "Citeer de bron letterlijk".
        if str(v.get("sterkte", "")) == "sterk" and not heeft_citaat(v.get("romp", "")):
            zonder_citaat.append(naam)
        for veld in VELDEN:
            if not v.get(veld):
                problemen.append(f"{naam}: veld '{veld}' ontbreekt of is leeg")
        if v.get("rubriek") and str(v["rubriek"]) not in RUBRIEKEN:
            problemen.append(
                f"{naam}: rubriek '{v['rubriek']}' bestaat niet ({', '.join(RUBRIEKEN)})"
            )
        if v.get("sterkte") and str(v["sterkte"]) not in STERKTES:
            problemen.append(f"{naam}: sterkte '{v['sterkte']}' moet sterk/mager/vermoeden zijn")
        if v.get("score"):
            try:
                score = int(str(v["score"]))
                if not 1 <= score <= 20:
                    raise ValueError
            except ValueError:
                problemen.append(f"{naam}: score '{v['score']}' moet een geheel getal van 1 t/m 20 zijn")
        if not v.get("personen"):
            problemen.append(f"{naam}: geen personen gekoppeld")
        if "**Bron:**" not in v.get("romp", ""):
            problemen.append(f"{naam}: geen regel met **Bron:** — zonder bron geen verhaal")
    print(f"{len(verhalen)} verhalen gecontroleerd.")
    if zonder_citaat:
        print(
            f"\n{len(zonder_citaat)} verhaal(en) met sterkte 'sterk' zonder citaat uit de bron."
        )
        print("  Ligt er een letterlijke passage, zet hem erin (boek/stijlgids.md,")
        print('  "Citeer de bron letterlijk"); zoek met grep -rn "Citaatwaardig" documenten/.')
        for naam in zonder_citaat:
            print(f"  - {naam}")
    if problemen:
        print(f"\n{len(problemen)} probleem(en):")
        for p in problemen:
            print(f"  - {p}")
        return 1
    print("\nGeen problemen gevonden.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="opdracht", required=True)
    sub.add_parser("index").set_defaults(func=index)
    p = sub.add_parser("lijst")
    p.add_argument("--deel")
    p.add_argument("--lijn")
    p.add_argument("--rubriek")
    p.add_argument("--persoon", help="deel van een persoon-id")
    p.add_argument("--onverwerkt", action="store_true")
    p.set_defaults(func=lijst)
    sub.add_parser("controleer").set_defaults(func=controleer)
    argumenten = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    return argumenten.func(argumenten)


if __name__ == "__main__":
    sys.exit(main())

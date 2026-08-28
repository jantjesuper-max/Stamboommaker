"""Bouwt het werkmanuscript uit de hoofdstukken.

  py scripts/bouw_boek.py

Plakt de hoofdstukken uit boek/hoofdstukken/ (op nummer) aaneen tot
boek/manuscript.md. Voetnootnummers worden per hoofdstuk uniek gemaakt zodat ze
niet botsen, en wikilinks worden platgeslagen naar leesbare tekst: een alias
([[id|alias]]) wint, anders de naam uit het persoonsdossier ([[jansen-jan-1808]]
wordt "Jan Jansen"), en pas als beide ontbreken blijft het id staan.
Is pandoc geïnstalleerd, dan wordt er ook een boek/manuscript.docx gemaakt (Word).
Het manuscript is een bouwproduct en staat niet in git — de hoofdstukken zijn de bron.
"""

import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instellingen

WORTEL = Path(__file__).resolve().parent.parent
HOOFDSTUKKEN = WORTEL / "boek" / "hoofdstukken"
PERSONEN = WORTEL / "personen"
MANUSCRIPT = WORTEL / "boek" / "manuscript.md"


def dossier_namen():
    """persoon-id -> naam uit de frontmatter, voor het platslaan van wikilinks.

    In het manuscript hoort de naam te staan, niet het bestands-id — de lezer
    van het boek kent de id's niet."""
    namen = {}
    for pad in PERSONEN.glob("*.md"):
        if pad.name.startswith("_"):
            continue
        kop = pad.read_text(encoding="utf-8")[:600]
        m = re.search(r"^naam:\s*(.+)$", kop, re.M)
        if m:
            namen[pad.stem] = m.group(1).strip().strip('"')
    return namen


def main():
    paden = sorted(p for p in HOOFDSTUKKEN.glob("*.md") if not p.name.startswith("_"))
    if not paden:
        print("Geen hoofdstukken gevonden in boek/hoofdstukken/.")
        return 1

    namen = dossier_namen()

    def plat(m):
        # [[id|alias]] -> alias; [[persoon-id]] -> naam uit het dossier; anders het id.
        # Vóór deze functie bleef "id|alias" letterlijk in het manuscript staan.
        doel, _, alias = m.group(1).partition("|")
        doel = doel.strip()
        return (alias.strip() or namen.get(doel) or doel)

    delen = []
    for pad in paden:
        tekst = pad.read_text(encoding="utf-8").strip()
        nummer = pad.stem.split("-")[0]
        # voetnoten uniek per hoofdstuk, anders botsen [^1] uit hoofdstuk 1 en 2
        tekst = re.sub(r"\[\^(\w+)\]", rf"[^h{nummer}-\1]", tekst)
        # wikilinks platslaan naar leesbare tekst (alias > dossiernaam > id)
        tekst = re.sub(r"\[\[([^\]]+)\]\]", plat, tekst)
        delen.append(tekst)

    vandaag = datetime.date.today().strftime("%d-%m-%Y")
    # Titel en ondertitel komen uit stamboom.json; verder weet dit script niet
    # wiens boek het bouwt.
    titel = instellingen.waarde("boek.titel", "Waar wij vandaan komen")
    ondertitel = instellingen.boek_ondertitel()
    titelblad = (
        f"# {titel}\n\n"
        + (f"*{ondertitel}*\n\n" if ondertitel else "")
        + f"_Werkmanuscript, gebouwd op {vandaag} uit {len(paden)} hoofdstuk(ken)._\n\n"
        + "_Statussen en open vragen: zie boek/opzet.md. Dit bestand niet met de hand\n"
        + "bewerken — wijzig de hoofdstukken en bouw opnieuw._"
    )
    MANUSCRIPT.write_text("\n\n---\n\n".join([titelblad] + delen) + "\n", encoding="utf-8")
    print(f"Gebouwd: {MANUSCRIPT.relative_to(WORTEL)} ({len(paden)} hoofdstukken)")

    if shutil.which("pandoc"):
        docx = MANUSCRIPT.with_suffix(".docx")
        subprocess.run(
            ["pandoc", str(MANUSCRIPT), "-o", str(docx), "--from", "markdown", "--toc"],
            check=True,
        )
        print(f"Gebouwd: {docx.relative_to(WORTEL)} (Word)")
    else:
        print("pandoc niet gevonden — geen Word-export. Installeren: winget install pandoc")
    return 0


if __name__ == "__main__":
    sys.exit(main())

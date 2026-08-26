"""Bouwt het werkmanuscript uit de hoofdstukken.

  py scripts/bouw_boek.py

Plakt de hoofdstukken uit boek/hoofdstukken/ (op nummer) aaneen tot
boek/manuscript.md. Voetnootnummers worden per hoofdstuk uniek gemaakt zodat ze
niet botsen, en wikilinks worden platgeslagen naar leesbare tekst. Is pandoc
geïnstalleerd, dan wordt er ook een boek/manuscript.docx gemaakt (Word).
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
MANUSCRIPT = WORTEL / "boek" / "manuscript.md"


def main():
    paden = sorted(p for p in HOOFDSTUKKEN.glob("*.md") if not p.name.startswith("_"))
    if not paden:
        print("Geen hoofdstukken gevonden in boek/hoofdstukken/.")
        return 1

    delen = []
    for pad in paden:
        tekst = pad.read_text(encoding="utf-8").strip()
        nummer = pad.stem.split("-")[0]
        # voetnoten uniek per hoofdstuk, anders botsen [^1] uit hoofdstuk 1 en 2
        tekst = re.sub(r"\[\^(\w+)\]", rf"[^h{nummer}-\1]", tekst)
        # wikilinks platslaan naar leesbare tekst
        tekst = re.sub(r"\[\[([^\]]+)\]\]", r"\1", tekst)
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

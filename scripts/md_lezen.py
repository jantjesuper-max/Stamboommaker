"""Markdown-regels lezen zonder de uitleg als gegeven mee te nemen.

Verschillende bestanden in dit project zijn tegelijk **lijst** en **handleiding**:
`onderzoek/werklijst-dossiers.md` legt het regelformat uit en bevat dan de regels
zelf, `tijdsbeeld/_AFGEHANDELD.md` doet hetzelfde. Zet iemand daar een voorbeeld
in — en dat is precies wat een sjabloon hoort te doen — dan leest een regel-voor-
regel parser dat voorbeeld als een echt gegeven.

Dat is hier twee keer misgegaan, in twee verschillende scripts, met dezelfde vorm:
een verse kloon van de repo meldde problemen over personen die niet bestonden,
terwijl de gebruiker nog niets had gedaan. Vandaar één plek voor de oplossing.

Overgeslagen wordt:
  - alles tussen ```-hekjes (codeblokken)
  - alles tussen <!-- en --> (HTML-commentaar, ook over meerdere regels)

Gebruik:
    from md_lezen import regels_buiten_uitleg
    for nr, regel in regels_buiten_uitleg(pad):
        ...
"""


def regels_buiten_uitleg(pad):
    """[(regelnummer, regel), ...] zonder codeblokken en HTML-commentaar.

    Regelnummers blijven die van het échte bestand, zodat een foutmelding naar de
    juiste regel wijst.
    """
    try:
        tekst = pad.read_text(encoding="utf-8")
    except OSError:
        return []
    regels = []
    in_codeblok = False
    in_commentaar = False
    for nr, regel in enumerate(tekst.splitlines(), 1):
        kaal = regel.strip()

        if in_commentaar:
            if "-->" in regel:
                in_commentaar = False
                # tekst ná de afsluiting op dezelfde regel telt weer mee
                rest = regel.split("-->", 1)[1]
                if rest.strip() and not in_codeblok:
                    regels.append((nr, rest))
            continue

        if kaal.startswith("```"):
            in_codeblok = not in_codeblok
            continue

        if in_codeblok:
            continue

        if "<!--" in regel:
            voor = regel.split("<!--", 1)[0]
            na = regel.split("<!--", 1)[1]
            if "-->" in na:
                # commentaar begint en eindigt op deze regel
                rest = voor + na.split("-->", 1)[1]
                if rest.strip():
                    regels.append((nr, rest))
            else:
                in_commentaar = True
                if voor.strip():
                    regels.append((nr, voor))
            continue

        regels.append((nr, regel))
    return regels

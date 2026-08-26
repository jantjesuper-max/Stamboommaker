# Stamboommaker

**Een stamboom die zichzelf uitzoekt — en er een boek van maakt.**

Dit is geen stamboomprogramma waarin je zelf namen intikt. Het is een werkomgeving voor
[Claude Code](https://claude.com/claude-code): je vertelt één keer wat je van je familie weet,
en daarna doet de AI het onderzoek. Voorouder na voorouder zoekt hij de Nederlandse archieven
af, downloadt de aktes, transcribeert ze, legt vast wat hij *niet* vond, koppelt de rampen en
oorlogen die dat leven raakten, en schrijft er uiteindelijk hoofdstukken over.

Alles blijft op je eigen computer. Je hebt Python en Claude Code nodig, en verder niets: geen
account, geen abonnement op een genealogiesite, geen database.

---

## Wat je krijgt

| | |
|---|---|
| **Persoonsdossiers** | Eén markdown-bestand per voorouder: kerngegevens met bron en betrouwbaarheidscode, levensloop, documenten, open vragen, onderzoekslog |
| **Archiefzoeker** | `zoek_openarch.py` — de hele index van [Open Archieven](https://www.openarchieven.nl) vanaf de opdrachtregel, zonder API-key. Print rollen, patroniemen, opmerkingenvelden en de scan-URL's waar de website ze verstopt |
| **Scans binnenhalen en lezen** | Volledige resolutie ophalen waar de viewer alleen thumbnails geeft, en uitsnedes met contrast maken zodat een 18e-eeuwse hand werkelijk te lezen is |
| **Tijdsbeeld** | Een kalender van 41 Nederlandse rampen, oorlogen, epidemieën en crises van 1636 tot 1974, die het script naast de leefjaren en woonplaatsen van elke voorouder legt |
| **Verhalenverzameling** | Elke bijzondere vondst als apart bestand met bron en een score, doorzoekbaar — zodat niets verdwijnt tussen het vinden en het schrijven |
| **Het boek** | Stijlgids, boekopzet en hoofdstukken met voetnoten; `bouw_boek.py` plakt er een manuscript van (met pandoc ook Word) |
| **Website** | Een lokale site met een sleepbare kwartierstaat, alle dossiers, het tijdsbeeld, de verhalen en een verkenner die scans naast hun transcriptie zet. Ook op je telefoon, via wifi |
| **PDF-uitdraai** | Elk dossier, verhaal of hoofdstuk als nette A4 met kopkaart en paginanummers — of alles samen als boekje met omslag en inhoudsopgave |
| **Controlescript** | Meet of werklijst en dossiers synchroon lopen, en rekent uit wie er aan de beurt is |

En het belangrijkste: **de skill `/doorwerk`**, die dat allemaal aan elkaar knoopt en uren of
nachten achter elkaar door blijft werken.

---

## Beginnen

Je hebt nodig:

- **Python 3.10 of hoger** ([python.org](https://www.python.org/downloads/) — op Windows het
  vinkje "Add Python to PATH" aanzetten)
- **[Claude Code](https://claude.com/claude-code)** met een Claude-abonnement
- Optioneel: `py -m pip install pillow` voor het inzoomen op scans, en
  [pandoc](https://pandoc.org) voor de Word-export

Dan:

```
git clone https://github.com/jantjesuper-max/Stamboommaker.git mijn-stamboom
cd mijn-stamboom
py instellen.py
```

`instellen.py` vraagt je naam, je geboortejaar en de achternamen van je familielijnen, en zet
de startbestanden klaar. (Op macOS/Linux: `python3` in plaats van `py`.)

Open die map daarna in Claude Code en zeg:

```
/opstarten
```

Dan volgt het gesprek waarin je vertelt wat je weet: je ouders, je grootouders, je
overgrootouders, en welke papieren er in huis liggen. Claude bouwt daaruit de stamboom, de
werklijst en de eerste dossiers.

En dan het echte werk:

```
/doorwerk
```

Vanaf dat moment gaat het van jou af. De skill pakt de voorouder die volgens de route aan de
beurt is, zoekt het open web af naar sporen, gaat met die sporen naar de registers, downloadt
en transcribeert wat er is, legt vast wat er *niet* is, onderzoekt welke geschiedenis dat leven
raakte, schrijft de bijzondere vondsten op, vinkt af, commit, en begint aan de volgende. Zonder
tussenvraag, tot de lijst leeg is of je hem onderbreekt.

Kijken hoe het gaat:

```
py test/controleer.py        Hoeveel dossiers staan er, en wie is er nu aan de beurt?
py test/test_gereedschap.py  Doen de scripts nog wat ze beloven?
py website/server.py         De website op http://localhost:8123
```

---

## Hoe het denkt

Dit project is gebouwd op een handvol regels die het verschil maken tussen een stamboom waar je
iets aan hebt en een lijst namen die misschien klopt.

**Verzin nooit een feit.** Elke datum, plaats, naam en relatie heeft een bron, of is expliciet
gemarkeerd als hypothese. Vier codes: `✓` bewezen (akte gezien) · `◐` waarschijnlijk · `?`
hypothese · `⚠` naamgenoot-gevaar. Een status verhogen mag alleen met een bronvermelding erbij.
Een dossier met drie regels en een eerlijk `[niets gevonden]` is meer waard dan een verzonnen
datum.

**Archieven boven wiki's.** Genealogieonline, Geni en Geneanet zijn aanwijzingen, geen bronnen —
en ze hebben vaker dan je denkt twee naamgenoten samengesmolten. Eerst breed sporen jagen op het
open web, dan smal bewijzen in de registers.

**Leg vast wat je niet vond.** Elke zoekactie zonder resultaat gaat in het logboek, met het
volledige commando erbij. Dat commando *ís* de reproductie van "niets gevonden". Zonder die
negatieve resultaten doet de volgende sessie hetzelfde werk opnieuw — en dat gebeurt, want
sessies vergeten en de werklijst niet.

**Verdenk eerst je gereedschap, dan het archief.** "Niet gevonden" is meestal geen muur maar een
verkeerde ingang: een veld dat het script weggooit, een spelling die de index niet kent, een
zoekopdracht die op pagina één ophield. Elke les die dat opleverde staat in `CLAUDE.md`, en er
staan er veel — de naam van de moeder in plaats van de vader, het dorp in plaats van de gemeente,
`--brontype` in plaats van `--type`, de leeftijd in plaats van de rol. Een verbetering aan het
script is net zoveel waard als een gevonden akte.

**Alleen directe voorouders.** Vaders en moeders, generatie na generatie — een kwartierstaat.
Broers, zussen, ooms en tantes komen nergens in de stamboom; twaalf generaties terug zijn dat
duizenden mensen en dan heb je een telefoonboek in plaats van een boek. Zegt een vondst over een
zijtak iets over jóuw voorouder, dan is het een verhaal; zegt het niets, dan één regel in het
log.

**Het gaat om mensen, niet om datums.** Een geboorteakte geeft een dag. Het bevolkingsregister
geeft een huis, het notarieel archief een schuld, het militieregister een lichaam, het
gevangenisregister een signalement, en de krant een ongeluk. Die bronnen worden hier
systematisch afgelopen, want zonder hen levert een dossier geen boek op.

**Geen emoji's, en Nederlands.** In dossiers, scripts, commits en het boek.

Alles staat uitgeschreven in **[CLAUDE.md](CLAUDE.md)** — dat is het bestand dat Claude Code bij
elke sessie leest, en het is met opzet uitvoerig: de kennis moet in de repo zitten, niet in het
geheugen van één gesprek.

---

## Hoe de map in elkaar zit

```
├── stamboom.json           jouw naam, boektitel, familielijnen (niet in git)
├── instellen.py            zet het project klaar
├── CLAUDE.md               de werkinstructies: conventies, regels, archieflessen
├── .claude/skills/
│   ├── opstarten/          het openingsgesprek: van leeg naar werkende stamboom
│   └── doorwerk/           de motor: voorouder na voorouder afwerken
├── personen/               één dossier per voorouder (_TEMPLATE.md)
├── documenten/
│   ├── inbox/              eigen scans hier neerzetten → "verwerk de inbox"
│   └── <persoon-id>/       aktes met transcriptie en bronvermelding ernaast
├── stamboom/overzicht.md   de leesbare kwartierstaat
├── onderzoek/
│   ├── werklijst-dossiers.md  de afstreeplijst; hier zit de voortgang
│   ├── open-vragen.md         werkvoorraad, familievragen bovenaan
│   ├── bronnengids.md         welke archieven per streek
│   └── logboek.md             wat is wanneer geraadpleegd (ook: niets gevonden)
├── tijdsbeeld/
│   ├── _KALENDER.md        41 gebeurtenissen 1636-1974, met gebied en zoekingang
│   └── <jaar>-<slug>.md    één gebeurtenis, gekoppeld aan personen
├── boek/
│   ├── stijlgids.md        de stem van het boek — lees dit vóór je schrijft
│   ├── opzet.md            delen, rode draden, hoofdstukkentabel
│   ├── zijtakken.md        wat wél en niet in de stamboom komt
│   ├── verhalen/           losse vondsten met bron en score
│   └── hoofdstukken/       het boek zelf, met voetnoten
├── scripts/                het gereedschap (alleen standaardbibliotheek)
├── website/                de lokale site
└── test/
    ├── controleer.py       meet de voortgang en de route
    └── test_gereedschap.py controleert de scripts zelf
```

---

## Vragen die je waarschijnlijk hebt

**Werkt dit ook buiten Nederland?** De structuur en de skills wel, en de scripts voor het boek,
de website en de PDF's ook. De archiefzoeker is gebouwd op Open Archieven, dus die is Nederlands
(met wat Belgisch materiaal erin). De bronnengids noemt Belgische en Duitse ingangen; voor andere
landen zul je die zelf moeten aanvullen — en dat is precies wat `onderzoek/bronnengids.md` je
vraagt te doen.

**Hoe lang duurt het?** Een ronde per voorouder duurt in de praktijk vijf tot twintig minuten,
afhankelijk van hoeveel er te vinden is. Honderd voorouders is dus geen middag maar een aantal
lange sessies. Doordat de voortgang in de werklijst en in git staat en niet in het gesprek, kost
een afgebroken sessie niets: de volgende rekent de route opnieuw uit en gaat verder.

**Wat als er niets te vinden is?** Dan wordt dat opgeschreven, met wat er is nagekeken en welke
ingang nog open staat. Dat is het nuttigste soort resultaat dat er is, want het voorkomt dat het
werk over een maand opnieuw gedaan wordt.

**Kost het geld?** De archieven en scripts niet. Claude Code heeft een abonnement nodig, en een
lange doorwerksessie verbruikt daar behoorlijk van.

**Mag ik mijn eigen stamboom hierin publiek zetten?** Dat is aan jou, maar loop hem eerst na op
gegevens van levende mensen. `stamboom.json` staat daarom niet in git, en `CLAUDE.md` heeft er
een sectie over.

---

## Meedoen

Vondsten die het gereedschap scherper maken zijn het meest welkom: een veld dat de API wel geeft
maar het script niet print, een zoektechniek die een muur openbrak, een archief dat nog niet in de
bronnengids staat, een gebeurtenis die in de kalender hoort. Dat is hoe dit project is ontstaan —
elke les erin is een keer duur betaald.

MIT-licentie. Doe ermee wat je wil.

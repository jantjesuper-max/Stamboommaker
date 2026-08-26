# Werkinstructies voor AI-sessies

Dit is een stamboom- en boekproject. Wie de eigenaar is, hoe het boek heet en welke
familielijnen er zijn staat in **`stamboom.json`** — nergens anders. Is dat bestand er nog
niet, vraag dan eerst `py instellen.py` te draaien, of doe het samen via `/opstarten`.

Taal: **Nederlands**, ook in bestanden en commits.

**Rolverdeling:** de eigenaar is verteller, opdrachtgever en eindredacteur; de AI doet het
verwerkings- en zoekwerk én **schrijft het boek**, in de stem die in `boek/stijlgids.md` is
vastgelegd. Lees die stijlgids vóór elke schrijfsessie — de tone of voice
(keukentafelverteller, geen AI-tics) is een harde eis.

## Gouden regel

**Verzin NOOIT genealogische feiten.** Elke datum, plaats, naam of relatie heeft óf een bron,
óf wordt expliciet gemarkeerd als hypothese (`?`). Een aanname zonder akte is nooit "bewezen".
Bij twijfel tussen naamgenoten: markeer met `⚠` en beschrijf het verwarringsgevaar in het dossier.

Een dossier met drie regels en een eerlijk `[niets gevonden]` is meer waard dan een verzonnen
datum — en het is bovendien sneller, dus er is ook geen excuus.

## Betrouwbaarheidscodes

- `✓` bewezen — primaire bron (akte, doopregister) gezien en vastgelegd
- `◐` waarschijnlijk — indirect bewijs (patroniem, vernoemingspatroon, samenloop)
- `?` hypothese — alleen afgeleid, nog niets gevonden
- `⚠` verwarringsgevaar — naamgenoot bekend, extra bewijslast nodig

Een status verhogen (bijv. `◐` → `✓`) mag alleen met een concrete bronvermelding erbij.

## Levende personen

Van iemand die nog leeft komt **niets uit een archief in dit project** en niets wat niet
gedeeld mag worden. Concreet:

- Van levende personen alleen wat de eigenaar zelf aanlevert, en alleen met hun instemming.
- Geen geboortedata, adressen of medische gegevens van levenden in dossiers of in het boek.
- De burgerlijke stand is voor recente jaren om deze reden gesloten (geboorte 100 jaar,
  huwelijk 75, overlijden 50). Respecteer die grens ook waar een index verder gaat.
- Wordt de repo gedeeld of gepubliceerd: nog één keer nalopen op wat er over levenden in
  staat. Zet zulke gegevens desnoods buiten git (zie `.gitignore`).

## Het gereedschap

| Commando | Waarvoor |
|----------|----------|
| `py test/controleer.py` | meet werklijst tegen dossiers en zegt **wie er aan de beurt is** |
| `py test/controleer.py --fix` | idem, en werkt het voortgangscijfer in de werklijst bij |
| `py test/test_gereedschap.py` | controleert de scripts zelf — draai dit na elke wijziging in `scripts/` |
| `py scripts/zoek_openarch.py zoek "Naam"` | zoeken in Open Archieven (geen API-key nodig) |
| `py scripts/zoek_openarch.py toon <id>` | bronvermelding, rollen, opmerkingenvelden en scan-URL's |
| `py scripts/download_scans.py [persoon-id]` | scans binnenhalen op volledige resolutie |
| `py scripts/lees_scan.py overzicht \| strook` | een scan werkelijk kunnen lezen (uitsnede + contrast) |
| `py scripts/tijdsbeeld.py kandidaten <id>` | welke geschiedenis raakte dit leven? |
| `py scripts/verhalen.py index \| lijst \| controleer` | de verhalenverzameling beheren |
| `py scripts/bouw_boek.py` | hoofdstukken → `boek/manuscript.md` (met pandoc ook Word) |
| `py scripts/pdf.py persoon <id>` | dossier, verhaal of tijdsbeeld als nette A4-uitdraai |
| `py website/server.py` | de lokale website op <http://localhost:8123> |

## Conventies

### Bewerk bestanden nooit via een PowerShell-pijplijn
Gebruik de Edit- en Write-tools. `Get-Content -Raw ... | Set-Content -Encoding utf8` **maakt
UTF-8-bestanden stuk**: PowerShell 5.1 leest een bestand zonder BOM als ANSI, dus alle
accenten en tekens als `·`, `—`, `✓` raken dubbel gecodeerd (Élke wordt Ã‰lke). Herstel gaat
met `git checkout -- <bestand>`. Voor zoeken en vervangen over meerdere bestanden: een klein
Python-script met expliciete `encoding='utf-8'`.

### Geen emoji's
Gebruik **nergens** emoji's: niet in dossiers, indexen, scripts, kalenders, verhalen of
commits. De betrouwbaarheidscodes `✓ ◐ ? ⚠` zijn de enige toegestane symbolen.

### Persoons-ID
`achternaam-voornamen-geboortejaar`, kleine letters, zonder accenten, spaties → koppelteken.
Voorbeeld: `bakker-hendrik-jan-1933`, `vermeulen-remigius-1600ca` (bij circa-jaar: `ca`
erachter). Heeft iemand vóór 1811 geen familienaam, dan is het `voornaam-patroniem-jaar`:
`jan-sienes-1740ca`. Dit ID is de bestandsnaam in `personen/` én de mapnaam in `documenten/`.

### Documentnaamgeving
`JJJJ-MM-DD_type_persoon-id.ext` — datum van de akte, niet van de scan.
Typen: `geboorteakte`, `doopakte`, `huwelijksakte`, `overlijdensakte`, `bevolkingsregister`,
`militieregister`, `militieattest`, `gevangenisregister`, `krantenbericht`, `foto`,
`notarieel`, `overig`. Het type mag alleen kleine letters bevatten, geen streepje.
Voorbeeld: `1933-08-27_geboorteakte_bakker-hendrik-jan-1933.pdf`
Onbekende dag/maand: `1933-00-00_...`.

Heeft één akte **meer dan één scan** (een spread over twee bladzijden), dan krijgen de
vervolgscans een `_2`, `_3` achter de naam:
`1833-07-07_huwelijksakte_bakker-jan-hendriks-1808_2.jpg`. Eén beschrijvingsbestand op de
**basisnaam** dekt ze samen; vervolgscans krijgen geen eigen `.md`.

**Een akte over iemand anders die een voorouder bewijst.** De overlijdensakte van een kind
noemt het beroep van de vader; de akte van een zuster noemt de ouders. Zulke documenten horen
erbij, maar er komt géén dossier en géén werklijstregel voor die persoon (zie
`boek/zijtakken.md`). Regel: de **map** is die van de voorouder wiens dossier het stuk
onderbouwt, de **bestandsnaam** draagt de id van de persoon over wie het document gaat, en het
beschrijvingsbestand zegt in de frontmatter (`overledene:`) wie dat is. Zo:

```
documenten/jansen-jan-hendriks-1813/1859-01-09_overlijdensakte_jansen-hiltje-1856ca.jpg
```

Dat leest goed op beide manieren: de map zegt bij welk dossier het hoort, de naam zegt over
wie de akte gaat. Noem zo'n bestand nooit naar de voorouder — dan lijkt het diens eigen
overlijdensakte. `test/controleer.py` eist alleen dat de **map** een werklijst-ID is, dus dit
past binnen de controle.

### Dossiers
Eén bestand per voorouder in `personen/`, opgezet volgens `personen/_TEMPLATE.md`.
Relaties als wikilinks: `[[bakker-jan-hendriks-1813]]`. Elk feit in de kerngegevens-tabel
krijgt een bron en een status.

### Documenten downloaden + beschrijvingsbestand
Vind je online een akte of scan: **download het bestand** naar `documenten/<persoon-id>/`
(conventie hierboven) en maak er een **los beschrijvingsbestand naast** met dezelfde naam
plus `.md`: transcriptie (letterlijk, onzekere lezingen als `[?]`), korte samenvatting, en de
volledige bronvermelding. Sjabloon: `documenten/_TEMPLATE.md`.

**Kan downloaden niet** (viewer-only, betaalmuur, rechten): neem dan in elk geval de
**volledige bronvermelding** op in het dossier én in het logboek — archief, toegangsnummer,
inventarisnummer, aktenummer, datum, plaats en directe URL — zodat het document later alsnog
opgehaald kan worden. Markeer met `[nog te downloaden]`.

### Bronvermelding-format
`Archief, toegang inv.nr., aktenummer, datum, plaats (geraadpleegd via …, URL, datum raadpleging).`

### Onderzoekslogs: reproduceerbaar, met links
Elke regel in een onderzoekslog (in het dossier én in `onderzoek/logboek.md`) moet door een
lezer na te lopen zijn zonder het zoekwerk over te doen — de website maakt markdown-links
klikbaar, dus wie het boek naleest kan elke bewering nachecken. Concreet:

- **Gevonden record** → de **permalink** van Open Archieven als markdown-link:
  `https://www.openarchieven.nl/<code>`, waarbij `<code>` het `toon`-argument is
  (bijv. `frl:6bad72b2-…`). `zoek_openarch.py toon` print die permalink zelf.
- **Zoekopdracht, ook zonder treffer** → het volledige commando in `code`-opmaak:
  `py scripts/zoek_openarch.py zoek "Sijbren Reins" --type Trouwen`. Dat commando ís de
  reproductie van een negatief resultaat; "gezocht op X" zonder commando is dat niet.
- **Webbron of literatuur** → volledige URL plus datum van raadpleging, óók als de bron
  alleen een muur bevestigt. Vier bronnen bij naam noemen zonder URL kost een dag later een
  extra sessie om de vindplaats terug te vinden; dat is een keer gebeurd en het is zonde.
- **Gedownload document** → relatieve link naar het beschrijvingsbestand in `documenten/…`.
- **Geen URL mogelijk** (studiezaal, papieren boek) → vindplaats zo precies dat iemand het
  stuk kan opvragen: archief, toegang, inv.nr., folio.

Een datumtabel wint er ook bij: maak in gezins- of documenttabellen de aktedatum zelf de link
(`[13-10-1695](https://www.openarchieven.nl/frl:…)`), dan blijft de tabel smal.

### Scans: formaat en grootte
JPG/PNG/PDF, maximaal ± 5 MB per bestand. Download de hoogste resolutie die zonder inloggen
beschikbaar is. **Gebruik `py scripts/download_scans.py [persoon-id]`**: die haalt bij elk
beschrijvingsbestand de scan op via het `download/fullsize`-endpoint van de
Memorix-beeldserver (volledige resolutie, werkt ook voor de jp2-pad-URI's waar de
thumb-endpoints 404 geven) en valt boven de 5 MB terug op 2000×2000. Het script werkt de
`status:`- en `bestand:`-regels zelf bij; extra bladen krijgen `_2.jpg` enz. Lukt het ook zo
niet (endpoint geeft niets, ander archief), zet dan
`status: gedownload (lage resolutie — volledige scan nog te downloaden via viewer)` met de
viewer-URL erbij. Transcribeer alleen wat écht leesbaar is; de rest is `[onleesbaar]` — nooit
gokken.

## Archieven boven wiki's

Wikipedia, Genealogieonline, StamboomNederland, Geneanet en Geni zijn **aanwijzingen, geen
bronnen**. Ze mogen een spoor opleveren, maar een feit wordt pas `✓` als het in een register
staat: een akte, doopboek, bevolkingsregister, notariële akte, haardstedenregister. Noem in
een dossier nooit een wiki als bron zonder de onderliggende akte erbij te zoeken; lukt dat
niet, dan blijft de status `◐` of `?` met de wiki genoemd als *aanwijzing*.

Het vaste patroon is dan ook: **eerst breed sporen jagen** (websweep over Genealogieonline,
Geneanet, Stamboomforum, FamilySearch e.d. — die noemen vaak precies de aktedatums en plaatsen
waar je moet zijn), **dan smal bewijzen** in de registers. Zie stap 4a/4b in de
doorwerk-skill. Een online stamboom zonder bronvermelding heeft vaker dan je denkt twee
naamgenoten samengesmolten.

## Vaste werkwijzen

### Werklijst en doorwerken
`onderzoek/werklijst-dossiers.md` is de werkvoorraad van alle voorouders (groeit bij
vondsten). De skill `/doorwerk` handelt er één per ronde af: dossier maken, archieven
afzoeken, loggen, afvinken, committen. `py test/controleer.py` meet of werklijst en dossiers
synchroon lopen en rekent uit wie er aan de beurt is volgens de voorouderroute:

1. **afmaken** — heeft een afgevinkte voorouder nog open vragen, dan gaat die vóór;
2. **omhoog** — ouders van afgeronde dossiers, diepste generatie eerst, vader vóór moeder;
3. **opzij** — bij een muur de diepste nog open tak; jongste generaties als terugval.

`--fix` werkt het voortgangscijfer bij.

**De skill werkt ronde na ronde door.** Eén voorouder per commit, maar na die commit meteen
verder met de volgende, zonder tussenvraag of tussenrapportage. Stoppen gebeurt alleen bij een
leeggewerkte werklijst, een genoemd aantal, twee keer hetzelfde vastlopen, of een
onderbreking. Een cronjob is er **alleen als vangnet** wanneer het doorwerken stilvalt; die
hoeft dus niet vaak te vuren, en de opdracht erin is óók "werk ronde na ronde door".

**Committen naast ander werk:** gebruik geen blinde `git add -A` maar noem de paden
(`personen documenten stamboom onderzoek boek`) — er wordt soms parallel aan andere mappen
zoals `website/` gewerkt.

### De stamboom is een kwartierstaat
**Alleen directe voorouders** staan in de stamboom: vaders én moeders, generatie na generatie.
Broers en zussen van voorouders komen er **nergens** in — niet in `stamboom/overzicht.md`,
niet op de werklijst, niet als dossier, niet als relatie in de frontmatter. Ook hun kinderen,
neven, nichten en aangetrouwden niet.

Kom je ze tegen (en dat gebeurt bijna altijd, want zoeken op de naam van de vader levert de
hele kinderrij op), dan geldt:

- **zegt de vondst iets over ónze voorouder** — een vernoeming naar een gestorven kind,
  kindersterfte als patroon, een akte met bewijswaarde → een verhaal in `boek/verhalen/`;
- **zegt het niets** → één regel in het onderzoekslog van het dossier, zodat niemand dat
  zoekwerk opnieuw doet.

Volledig beleid met voorbeelden: `boek/zijtakken.md`.

### Afvinken: alles dicht
Een voorouder is pas af als **elke vraag onder "Open vragen" gesloten is** — met een antwoord,
of met een expliciete sluiting die de doorzochte bronnen noemt ("niet gevonden in X, Y en Z").
Gesloten vragen blijven staan als `- [x]` met de uitkomst erachter; zo is zichtbaar dat er
gezocht is. Zolang er open vragen staan, stuurt de route je terug naar die persoon in plaats
van naar een nieuwe.

### Zwakke sporen
Elk dossier heeft een tabel **Zwakke sporen** voor vermoedens die te dun zijn om zelfs een
hypothese (`?`) te zijn: een naamgenoot die verdacht goed past, een zeldzame achternaam die
elders in de stamboom opduikt, een online boom zonder bron. Noteer per spoor waaróm het zwak
is en wat het zou betekenen als het klopt. Ze horen dus **niet** bij de open vragen en
**niet** in de kerngegevens — juist zo bouwt een volgende ronde er niet ongemerkt op voort.

### "Verwerk de inbox"
1. Lees elk bestand in `documenten/inbox/`.
2. Transcribeer (letterlijke tekst) en vat samen; noteer twijfelachtige lezingen als `[?]`.
3. Bepaal bij welke persoon het hoort; hernoem volgens conventie en verplaats naar
   `documenten/<persoon-id>/`.
4. Zet transcriptie + samenvatting in het persoonsdossier onder **Documenten**.
5. Werk zo nodig status/feiten bij in dossier en `stamboom/overzicht.md`.
6. Noteer de verwerking in `onderzoek/logboek.md`.

Dit is ook de route voor **eigen materiaal**: een foto van een trouwboekje, een bidprentje uit
een schoenendoos, een gescande brief. Zulke stukken zijn vaak beter dan wat een archief geeft,
en ze staan nergens online.

---

## Zoeken in Open Archieven — de lessen

Dit zijn de valkuilen die dit gereedschap heeft opgeleverd, alle duur betaald. Ze staan hier
omdat ze zich in élk Nederlands stamboomonderzoek opnieuw voordoen.

```
py scripts/zoek_openarch.py zoek "Jan Hendriks Jansen" --type Geboorte --van 1860 --tot 1870
py scripts/zoek_openarch.py toon frl:22b09696-...        # bronvermelding + scan-URL's
```

### De persoon vinden

- **Lees de rollen, niet de volgorde.** `toon` geeft per persoon de rol (Overledene, Vader,
  Moeder, Bruid, Bruidegom, Dopeling, Kind) plus de vermelde leeftijd. Dát is het bewijs.
  Afgaan op de volgorde waarin namen terugkomen leidt tot verkeerde conclusies over hele
  generaties.
- **Een rol in de index kan gewoon fout zijn; de leeftijd verraadt het.** Bij een
  overlijdensakte gaf de index het dode kind de rol **Vader**, omdat het naar zijn vader was
  genoemd — twee keer dezelfde naam in één akte. Alleen het veld `Age` (4 jaar, *zonder
  beroep*) wees uit wie de overledene was. Lees dus rol **én** leeftijd **én** beroep, en
  wantrouw een akte waarin twee personen dezelfde naam dragen.
- **Zoek ook op de naam zónder patroniem** ("Hendrik Bakker" i.p.v. "Hendrik Eelkes Bakker")
  — aktes indexeren vaak de korte naam.
- **Zoek op de naam van de váder**: dat levert in één keer de hele kinderrij op, en soms een
  akte die onder de eigen naam onvindbaar is.
- **Onvindbare man met een gewone naam? Zoek op de naam van zijn vrouw of zijn ouders.**
  Een veelvoorkomende naam kan duizenden overlijdenstreffers geven waar de naam van zijn vrouw
  er tientallen geeft — en daartussen zit de akte, want een overlijdensakte noemt óók de
  partner en de ouders. Dit is de belangrijkste enkele truc in dit hele bestand.
- **Zoek bij overlijden op de dorpsnaam, niet de gemeente.** Een gemeentenaam kan nul treffers
  geven waar de dorpsnaam de akte geeft. Let er ook op dat iemand in een *ander* dorp van
  dezelfde gemeente kan zijn gestorven dan waar hij woonde.
- **En soms is `--plaats` juist de valstrik.** Een plaatsfilter gooit records weg waarbij de
  plaats alleen in de bron staat en niet in het gebeurtenisveld. Bij gaardersregisters vond
  een plaatsfilter twee van de zes begrafenissen; dezelfde zes kwamen wél boven met een
  zoekopdracht op naam plus `--van`/`--tot`. Gebruik de plaatsfilter om een brede naam
  hanteerbaar te maken, maar nooit als bewijs dat er in dat dorp niets is.
- **In DTB-boeken: zoek op de ouder, niet op de persoon.** Voornamen staan daar zoals de
  dominee ze hoorde. "Hil" stond in het doopboek als **Hill**, en zoeken op "Hil" gaf nul
  dopen; zoeken op de naam van de váder met plaats en periode gaf haar doop, haar ouders, haar
  grootouders en twee broers. Reken ook op meerdere spellingen van één man: Sjoerd Tijsses,
  Sjoerd Tysses, Sjoert Tijsses en Sioerd Tijsses gaven elk een ánder deel van hetzelfde gezin.
- **Eén letter verschil in een achternaam is een andere zoekopdracht, en er zit geen systeem
  in.** Bij een familie waarvan de naam op **-hout** of **-houd** kon eindigen, wisselde de
  spelling **per klerk**, heen en terug, van 1820 tot 1954. Er is geen richting en geen
  periode, dus "zoek met de spelling van die tijd" helpt niet. Wat wél helpt is beide vormen
  bij **elke** zoekopdracht proberen: de index zoekt letterlijk en het verschil is alles of
  niets — de ene voorouder was alleen met een **d** te vinden, de geboorteakte van haar
  grootvader alleen met een **t**. **Dit geldt ook voor negatieve resultaten:** een "nul
  treffers" op één spelling is geen meting.
- **Vóór ongeveer 1820: verdenk de familienaam.** De naamsaanneming van 1811 was net gebeurd
  en klerken wisselden jaren lang tussen de aangenomen naam en de dorpsbijnaam. Eén
  geboorteakte van 1813 was met vijfendertig doorzochte treffers "niet in de index" — het gezin
  heette in het ene dorp anders dan in het andere, in dezelfde jaren. **Zoek dan op de naam van
  de moeder** — vrouwennamen veranderden niet mee. Zo kwam die akte alsnog boven nadat hij al
  als muur was opgeschreven.
- **De vernoemingsorde is een controlemiddel, geen bewijs.** In Friesland (en elders) kreeg het
  eerste kind de naam van een grootouder in een vaste orde: eerste dochter naar de moeder van
  de moeder, eerste zoon naar de vader van de vader, dan de andere twee. Bij één gezin klopte
  dat vier keer op rij — precies de vier grootouders uit de doopboeken. Gebruik het om een
  koppeling te **bevestigen** of te wantrouwen, nooit als enige grond voor een `✓`. Een naam
  die buiten de orde valt is juist een aanwijzing naar een generatie hoger.
- **Bij een naamgenoot: bewijs het wegstrepen.** Iemand afschrijven is net zo goed een
  bewering als iemand identificeren, en vraagt hetzelfde bewijs — de **ouders** en de
  **leeftijd** in de akte. Dit is een keer misgegaan: een tweede man met dezelfde naam werd
  afgeschreven als "gevaarlijke naamgenoot" omdat de voornamen in dat gezin katholiek klonken
  en de gemeente een andere was. Het bleek dezelfde man, hertrouwd; de huwelijksakte noemde
  zíjn ouders. Klank van een voornaam, gemeentegrens of geloofsindruk zijn geen bewijs.

**Naamgenoten zijn de grootste valkuil** — een treffer telt pas na controle van datum, plaats
én relaties (ouders/partner in het record).

### De juiste ingang kiezen

- **Geldige gebeurtenistypen (`--type`).** Verzin hier niets: een onbekende waarde geeft
  **stilzwijgend nul treffers** en dat lijkt op een muur. Geldig zijn: `Geboorte · Doop ·
  Ondertrouw · Trouwen · Huwelijk · Overlijden · Begrafenis · Registratie · Inschrijving ·
  Notariële inschrijving`. Het script waarschuwt bij een onbekend type.
- Vóór 1811 zijn alleen **Doop, Ondertrouw, Trouwen en Begrafenis** bruikbaar;
  Geboorte/Huwelijk/Overlijden bestaan pas met de burgerlijke stand. **Begrafenis** (DTB
  Begraven) is de enige ingang op een sterfgeval vóór 1811 en wordt gemakkelijk vergeten.
- Een **bróntype** (DTB Lidmaten, DTB Begraven, Bevolkingsregister, Stamboeken, BS Huwelijk,
  Gevangenisregister) is iets anders dan een gebeurtenistype en zit niet in het API-filter.
  Daarvoor is `--brontype`, dat na het ophalen filtert.
- Sommige bronnen hebben een gebeurtenistype dat met `other:` begint —
  `other:Gevangenisregister`, `other:DTB Dopen`. Die zijn met `--type` **onbereikbaar** en
  alleen met `--brontype` te vinden. Zo kwamen vier gevangenisinschrijvingen boven met
  `--brontype Gevangenis`, met beroep, lengte en handtekening erin.
- **Loop bij elke voorouder één keer de brontypen langs die je nog niet hebt geprobeerd.** Een
  naam die in de burgerlijke stand niets nieuws meer geeft, kan in een bevolkings-, militie-,
  lidmaten- of gevangenisregister een heel leven opleveren.
- **Het notarieel archief is een vaste halte, ook zonder scan.** `--brontype Notarieel`, en
  `--type "Notariële inschrijving"`. De index noemt de **aktesoort** en soms een hele alinea,
  en dat is vaak al genoeg: boedelscheidingen, voogdijstellingen, plaatsvervangingen,
  schuldbekentenissen, koop- en huurcontracten en testamenten zijn de plaatsen waar arme
  families toch uitgebreid op papier komen, met bedragen en bezittingen erbij. **Neem zulke
  indexteksten letterlijk over** in het onderzoekslog en in het beschrijvingsbestand, in de
  spelling van het archief: dat is de grondstof voor een citaat.
- Bij een huwelijk na 1811: kijk of er **huwelijksbijlagen** zijn. Daar zitten vaak
  geboorteaktes van de ouders in — de goedkoopste manier om een generatie terug te komen.

### De velden die het script eerst weggooide

Elk van deze velden is een keer de oorzaak geweest van een valse muur. Ze staan nu alle in
`toon`. **Zie je in de ruwe JSON een veld dat het script niet print: dat is de volgende bug.**

- **`PersonNamePatronym`** — patroniemen staan in een eigen veld en zijn vóór 1811 het énige
  wat twee naamgenoten scheidt. Zonder dat veld verschenen de ouders bij een doop als
  "Sjoert en Hil" in plaats van met hun patroniem, en de akte leek onkoppelbaar.
- **`SourceRemark`** — sommige collecties zetten daar een volledige biografische alinea in.
  In één veld stond dat een man arbeider te X was, zoon van Y en Z, plaatsvervanger voor een
  boerenzoon uit W, met de notarisakte en de trouwdatum erbij.
- **`EventRemark` is het rijkste veld van de hele API.** Wat erin staat hangt af van de
  collectie, en juist daarom is het gemakkelijk over het hoofd te zien:
  - bij een **bevolkingsregister** staat er het **kaartnummer** in. Zonder dat nummer is "hij
    staat in het bevolkingsregister van dat dorp" een mededeling zonder vindplaats; mét dat
    nummer is het *toegang 145.1.02, inv.nr. 460, gezinskaart 916* en kun je de kaart
    aanvragen;
  - bij een **gewone akte van de burgerlijke stand** staat er het **tijdstip** (geboren om
    15:00, gestorven om 22:15), het **huisnummer** (*nr. 48*, *wijk B nr. 225*) en de
    **aktesoort**. Met de huisnummers uit een kinderrij lees je een verhuisgeschiedenis;
  - bij **notariële aktes** zit de hele samenvatting erin: **`Soort akte`** (taxatie,
    boedelscheiding, voogdij, schuldbekentenis) en **`Onderwerp`** — een volledige alinea over
    wat er in de akte gebeurt, met woonplaatsen erbij. Zo bleek dat iemand "te Bodegraven" in
    1760 met drie anderen een nalatenschap taxeerde op verzoek van de voogden over de wezen
    van een ander. Dat is een woonplaats, een status en een citeerbare passage in één veld.
    ⚠ Het veld is **niet altijd gevuld**: van zes aktes op dezelfde naam had er één een
    `Onderwerp` en vijf niet. Een lege `Onderwerp` betekent dus niet dat de akte niets zegt,
    alleen dat het origineel gelezen moet worden.
  - Let op de vorm: `EventRemark` kan één dict zijn óf een lijst, en de sleutel heeft een
    nietszeggend veldnummer ervoor (`12 Kaart`, `92 Kaart`).
- **`SourceIndexDate`** — de periode die het *register* dekt (gezinskaarten 1920-1938), niet
  de datum van een gebeurtenis. Bij bevolkingsregisters is dat het antwoord op de vraag die je
  werkelijk hebt: welke jaren van dit leven staan op deze kaart?
- **`Archive`** — het toegangsnummer dat in elke bronvermelding hoort.

### Wanneer "nul treffers" geen meting is

- **Een lege lijst na een eigen filter is geen muur.** `--van`, `--tot` en `--brontype` zitten
  niet in de API en worden ná het ophalen toegepast. Het script pagineert daarom **zelf door**
  (tot `PAGINEER_MAX`, standaard 600) zodra je zo'n filter gebruikt, en meldt onderaan hoeveel
  treffers het doorzocht heeft en hoeveel niet. Staat er **"N treffer(s) niet doorzocht"**, dan
  is de zoekopdracht níet af. Dit was twee keer de oorzaak van een valse muur: geboorte- én
  overlijdensakte stonden gewoon op pagina twee.
- **Verhoog dan de grens met `--grens`.** Bij een veelvoorkomende naam is 600 veel te weinig:
  een zoekopdracht met `--brontype Naamsaanneming` gaf **nul** treffers op 600 van de 9526, en
  dat las als een muur. Met `--grens 9600` bleken er **zeven** naamsaannemingen te zijn,
  waaronder één in een dorp dat tot dan toe buiten beeld was gebleven.
- **Maar een brede achternaam kún je niet afmaken.** De API matcht losjes op naam: een gewone
  achternaam kan 35.958 treffers geven. Bij zo'n aantal is doorpagineren geen optie — dat zijn
  honderden verzoeken. Beperk dan met **`--plaats`** per dorp: vijf kleine zoekopdrachten van
  elk enkele tientallen records, alle vijf compleet, in plaats van één onafmaakbare. **Een som
  van complete zoekopdrachten is een meting; een afgebroken brede zoekopdracht is dat niet.**
- **Het derde soort muur: een index die ophoudt.** Naast een echte muur en een
  gereedschapsprobleem is er de openbaarheidstermijn. Meet die vóór je een conclusie trekt,
  door **een veelvoorkomende naam uit de streek jaar voor jaar te tellen**. Zo bleek een
  geboorte-index te eindigen met **1902**: 1899 gaf 21 treffers, 1902 nog vijftien, en 1903 tot
  en met 1910 elk **nul**. Wie daar een geboorte van 1903 mist, mist niets — hij zoekt buiten
  het register. Termijnen: geboorte 100 jaar, huwelijk 75, overlijden 50, maar de índex kan bij
  een ander jaar ophouden dan de termijn voorschrijft, dus meet het.
- **Een muur kan uit twee fouten tegelijk bestaan.** Eén doop is drie rondes lang "niet
  gevonden" geweest door twee bekende valkuilen die elkaar versterkten: er werd op de **man**
  gezocht in plaats van op de **vrouw**, én met `--type Doop` terwijl die records
  `other:DTB Dopen` als gebeurtenistype hebben (met `--type` onbereikbaar). Elk van de twee
  alleen had de akte al verborgen; samen leverden ze drie keer een overtuigende nul op. **Les:
  als een akte er hóórt te zijn, varieer dan niet één ding maar twee** — de persoon én de
  ingang.
- Nog een detail uit diezelfde vondst: in sommige doopregisters heeft het kind de rol **`Kind`**
  en niet `Dopeling`. Wie op `Dopeling` filtert, ziet de namen van de kinderen niet.
- Vraag je ten slotte af of de bron wel in deze index zit. DTB-boeken en kohieren zijn maar
  deels ontsloten; dan is het geen muur maar een verkeerde ingang, en hoort in het logboek
  *welke* ingang dan nodig is.

### Muur of gereedschapsprobleem?

Vind je iets niet terwijl het er hóórt te zijn, **verdenk dan eerst het script en niet het
archief.** Haal de ruwe JSON op (`curl` naar
`api.openarch.nl/1.1/records/show.json?...`) en kijk of er velden zijn die het script weggooit;
zo ja, pas `scripts/zoek_openarch.py` aan met een comment waarom dat veld ertoe doet. Elke keer
dat dit speelde lag het aan het gereedschap. **Een verbetering aan het script werkt door in elke
volgende ronde en is net zoveel waard als een gevonden akte.**

Gaat het niet om een bron maar om een **zoektechniek**, dan hoort die hierboven bij de lessen
én in de doorwerk-skill. Zo wordt het gereedschap elke ronde iets scherper in plaats van dat
dezelfde ontdekking steeds opnieuw gedaan wordt.

**Repareer je een script, laat de meting dan achter.** Zet in `test/test_gereedschap.py` een
regel die de fout aantoont, en generaliseer daarbij: één verkeerde koppeling is een voorbeeld
van een klasse, niet een los geval. Toen bleek dat de plaatsvergelijking »echt« (Limburg) in
»Utrecht« vond, waren »assen« in »Wassenaar«, »elburg« in »Middelburg« en »hoorn« in
»Hoornaar« precies dezelfde fout — die staan er nu alle vier in. Draai daarna
`py test/test_gereedschap.py`.

---

## Scans binnenhalen en werkelijk lezen

### Route 1: de fullsize-truc (Memorix — veel regionale archieven)
De API geeft per scan alleen een **thumb**-URL (`.../thumb/640x480/<pad>`), en die geeft bij
**jp2-scans een 404** — waardoor het lijkt of een document viewer-only is. Dat is het niet.
Vervang `thumb/<formaat>/` door `download/fullsize/`:

```
https://<archief>-images.memorix.nl/<code>/thumb/640x480/<pad>     -> 404
https://<archief>-images.memorix.nl/<code>/download/fullsize/<pad> -> volledige scan, MB's
```

`toon` print die FULLSIZE-URL automatisch onder elke thumb. Bij gewone jpg-scans werkt
daarnaast `thumb/2000x2000/` voor de hoogste publieke resolutie. Zo zijn
naamsaannemingsregisters alsnog binnengehaald die eerder als "viewer-only" waren afgeschreven.

### Route 2: IIIF (Erfgoed Leiden en anderen)
Sommige archieven leveren hun scans via een **IIIF-beeldserver**, en dan geeft het veld `Scans`
geen thumb maar de *informatiebeschrijving* van de afbeelding:

```
https://<archief>.memorix.io/resources/iiif/3/<uuid>/info.json               -> JSON, honderden bytes
https://<archief>.memorix.io/resources/iiif/3/<uuid>/full/max/0/default.jpg  -> het hele blad, MB's
```

Wie die `info.json` downloadt houdt metadata over en concludeert dat er geen scan is. `toon`
print de juiste URL automatisch als `FULLSIZE`, net als bij Memorix.

### Kijk opnieuw naar elke akte die als "viewer-only" is afgeboekt
Toen `zoek_openarch.py` de IIIF-route leerde printen, zijn diezelfde middag drie aktes
nagekeken die als *"staat in een eigen viewer, `[nog te downloaden]`"* stonden afgeboekt.
**Alle drie waren gewoon op te halen**, in volledige resolutie, en alle drie leverden gegevens
op die de dossiers niet hadden: twee sterfdata, een uur, een gehucht, en de mededeling dat een
voorouder niet dood was maar **afwezig**. **Regel: een `[nog te downloaden]` van vóór de
laatste gereedschapsverbetering is geen conclusie maar een openstaande taak.**

### Controleer of de scan de akte écht bevat
Een scan-URL uit de API hoort **niet automatisch bij de akte**. Bij één overlijdensakte wees de
link naar folio 4 van hetzelfde register, met vier aktes van andere mensen uit andere maanden.
**Open de gedownloade afbeelding en zoek de naam of de datum** voordat je er een transcriptie
op baseert. Klopt de bladzijde niet, zet dat dan in het beschrijvingsbestand
(`status: gedownload, maar ⚠ VERKEERDE BLADZIJDE`) en vermeld expliciet dat de gegevens uit de
index komen en niet uit een gelezen akte.

### Lees de akte niet op ooghoogte: zoom in
Een spread van 5000 pixels breed lijkt leesbaar en is het niet. Bij één huwelijksakte leverde
inzoomen twee naamcorrecties op — een voornaam én een patroniem bleken anders — en bij een
overlijdensakte veranderde de sterfdag van "negenden" in **zesden**. Zonder inzoomen zouden die
drie fouten in de dossiers hebben gestaan, en daarna in drie bestanden.

**Gebruik `scripts/lees_scan.py`, in twee stappen:**

```
py scripts/lees_scan.py overzicht <scan>                            # welke bladzijde, welk aktenummer
py scripts/lees_scan.py strook <scan> <x> <y> <breedte> <hoogte>    # de regels écht lezen
```

Het overzicht is grijswaarden op 1500 pixels (ongeveer 130 kB) en dient alleen om te zien
**waar** de akte staat; het print de schaalfactor zodat je van het overzicht naar de echte
coördinaten kunt rekenen. De strook is een uitsnede op **volle** resolutie met autocontrast,
vergroot naar 2600 pixels breed (ongeveer 180 kB) — dat is wat je nodig hebt om een naam of
datum te lezen.

**Lees nooit een ruwe archiefscan rechtstreeks in.** Die zijn 3 tot 8 MB, ze zijn op ooghoogte
toch onleesbaar, en achter een inspecterende proxy knapt een groot verzoek af
(`Connection dropped (ECONNRESET)`). Twee kleine bestanden geven een beter resultaat dan één
groot.

### Een extra scan bij een akte kan een ánder document zijn
De tweede "scan" bij een huwelijksakte bleek geen tweede bladzijde maar een **militieattest**:
een huwelijksbijlage met vijf jaar levensloop erop. Kijk elke extra scan apart aan. Blijkt het
een eigen document, geef het dan zijn **eigen naam en datum** in de map
(`1866-10-26_militieattest_<id>.jpg`) en niet `_2` — dat achtervoegsel is alleen voor
bladzijden van dezelfde akte.

---

## Bronnen buiten het archief

Aktes geven datums, deze bronnen geven leven: **Delpher** (kranten én gedigitaliseerde boeken),
streekhistorische verenigingen en uitgegeven **streekboeken**, Google Books en DBNL,
bidprentjes en familieadvertenties via het CBG, online-begraafplaatsen.nl, en
beroepsgeschiedenis (wat deed een turfmaker of pannenbakkersknecht concreet?). Zelden bewijs
voor een datum, wél bron voor het verhaal — noem in het verhaalbestand eerlijk dat het
streekhistorie is en geen akte. Volledig: `onderzoek/bronnengids.md`.

**Nieuwe bron tegengekomen? Schrijf hem bij** in `onderzoek/bronnengids.md`, bij de juiste
regio, met één regel over waar hij goed voor is en wat je er concreet in vond. Datzelfde geldt
voor een register dat blijkt te **ontbreken** of achter een betaalmuur zit.

## "Pak open vraag X op"

1. Lees de vraag in `onderzoek/open-vragen.md` en de betrokken dossiers.
2. Raadpleeg de bronnen uit `onderzoek/bronnengids.md` voor die regio/periode.
3. Leg élk geraadpleegd register vast in `onderzoek/logboek.md` — ook als er niets gevonden is.
4. Gevonden scans: downloaden + beschrijvingsbestand; lukt downloaden niet, dan volledige
   bronvermelding vastleggen met `[nog te downloaden]`.
5. Vondsten: alleen als hypothese (`?` of `◐`) opnemen tot er een akte is.

## Bijzonder verhaal gevonden → boek bijwerken

Komt er bij het verwerken of zoeken een bijzonder verhaal boven (een migratie, een drama, een
opvallend beroep, een krantenbericht, een raadsel dat zich oplost):

1. Eerst het dossier bijwerken (feiten + bronnen).
2. Dan een bestand in `boek/verhalen/` volgens `_TEMPLATE.md` — **altijd**, ook als er die
   ronde geen hoofdstuk komt. Zo verdwijnt geen vondst.
3. Is er genoeg: een hoofdstuk in `boek/hoofdstukken/NN-korte-titel.md`, in de stem van
   `boek/stijlgids.md`, met een voetnoot bij elke bewering uit een bron.
4. Hoofdstukkentabel in `boek/opzet.md` bijwerken en de eigenaar erop wijzen dat er iets te
   lezen valt.

### Laat de akte zelf aan het woord
Is er een citeerbare passage, dan hoort er een **citaatblok** in het verhaal of hoofdstuk.
Notariële aktes leveren hier het meeste op (boedelscheiding, voogdij, plaatsvervanging,
schuldbekentenis, koop, testament), daarna de vaste formules van de burgerlijke stand, het
signalement uit een militie- of gevangenisregister, en de indexalinea uit `SourceRemark`.
Vorm: één regel die zegt waar de woorden vandaan komen, dan het blok met `>` in de spelling van
de akte, dan in gewone taal wat er staat en wat de oude woorden betekenen. Zeg erbij of je de
**akte** citeert of de **index** — dat is bij het schrijven het verschil tussen twee
beweringen.

Markeer bij elke transcriptie de één of twee regels die je aan tafel zou voorlezen, onder een
kopje `## Citaatwaardig` in het beschrijvingsbestand. Dan vindt een latere schrijfsessie het
materiaal in één keer terug met `grep -rn "Citaatwaardig" documenten/`, in plaats van dertig
transcripties opnieuw door te lezen. Geen letterlijke passage gevonden, dan geen citaat:
verzin er nooit een, en laat een akte nooit "oud" klinken omdat het mooi staat.

## Tijdsbeeld: geschiedenis die het leven raakte

Dijkdoorbraken, epidemieën, oorlog, crises — als ze de woonplaats van een voorouder troffen,
horen ze in het dossier én in het boek. Het systeem:

- `tijdsbeeld/_KALENDER.md` — kalender van gebeurtenissen met periode, **gewicht**
  (`groot`/`achtergrond`), gebied en zoekingang. Groeit: een plaatselijke vondst (dorpsbrand,
  bombardement, gezonken schip) krijgt er een regel bij, of meteen een eigen
  gebeurtenisbestand. **De meegeleverde kalender is landelijk en provinciaal — de
  gebeurtenissen die jouw familie werkelijk raakten zijn vaak plaatselijk, dus vul aan.**
- `py scripts/tijdsbeeld.py kandidaten <persoon-id>` — legt leefjaren en woonplaatsen
  (frontmatter `geboren`/`overleden`/`woonplaatsen`) naast de kalender en noemt wat er
  onderzocht moet worden. Vul `woonplaatsen:` zo goed mogelijk in; dat maakt de kandidaten
  scherper. Draait automatisch mee als stap 6 van `/doorwerk`.
- **Het zoeken is verplicht werk, niet decor.** Elke `groot`-kandidaat wordt in de ronde écht
  onderzocht via de zoekingang uit de kalender, met het resultaat in het onderzoekslog — pas
  dan koppelen of beargumenteerd afmelden. Een ronde die stap 6 alleen "draait" zonder te
  zoeken is niet af.
- **Alleen grote gebeurtenissen komen in de dossiers.** `achtergrond`-kandidaten (duurte,
  crisis, strenge winter) worden niet gekoppeld en niet afgemeld; ze mogen als sfeertekening in
  de Levensloop, en krijgen alleen een koppeling als het onderzoek een concreet spoor oplevert.
  Bij gebied `landelijk` is tijdsoverlap nooit genoeg — ook niet bij `groot`: zoek het
  plaatselijke of persoonlijke spoor (sterftepiek in het dorp, militie-inschrijving, verlies in
  het gezin, bericht over de woonplaats).
- Raakvlak gevonden → **eerst ontdubbelen**: `py scripts/tijdsbeeld.py zoek <term>`. Bestaat de
  gebeurtenis al als bestand, voeg de persoon dáár toe — één gebeurtenis, één bestand;
  `controleer` weigert dubbele gebeurtenis-id's. Pas als er niets is: nieuw bestand in
  `tijdsbeeld/` (sjabloon `_TEMPLATE.md`), personen als wikilinks in de frontmatter. Daarna:
  gebeurtenis in de Tijdsbeeld-tabel van het dossier zetten en in de Levensloop verweven.
  Verhaalstof → ook een verhaal in `boek/verhalen/` (rubriek `tijdsbeeld`).
- **Bronnen altijd met vindplaats:** in het gebeurtenisbestand krijgt elke bewering een
  bronvermelding, en bij webbronnen en literatuur hoort daar de volledige URL plus datum van
  raadpleging bij.
- Onderzocht maar geen raakvlak of niets gevonden → afmelden met een regel in
  `tijdsbeeld/_AFGEHANDELD.md`, met de **reden uitgeschreven**. Dan vraagt de volgende ronde er
  niet opnieuw naar.
- **De gouden regel geldt onverkort:** de gebeurtenis zelf mag uit literatuur of krant komen,
  maar de kóppeling is pas ✓ als een bron persoon, gezin of adres direct noemt; aantoonbaar
  wonen in het getroffen gebied is ◐, alleen tijdsoverlap is geen koppeling.
- Afsluiten met `py scripts/tijdsbeeld.py controleer` en `py scripts/tijdsbeeld.py index`.

## Overzicht synchroon houden

`stamboom/overzicht.md` is de leesbare samenvatting; de dossiers zijn de waarheid. Na elke
dossierwijziging die namen/datums/statussen raakt: overzicht bijwerken.

## Praktisch

- Blijf binnen deze projectmap. Tijdelijke bestanden in `test/tijdelijk/` (staat in
  `.gitignore`).
- **Git — controleer eerst de repo-grens.** Draai vóór elke `git add`/`commit`
  `git rev-parse --show-toplevel` en kijk of dat de projectmap is. Op sommige machines is een
  bovenliggende map (bijvoorbeeld de home-map) per ongeluk óók een git-repo; dan raakt een
  `git add` alles wat daar staat. Kom je in zo'n situatie, maak dan eerst een eigen repo in
  deze map (`git init`) en werk daarbinnen.
- Noem bij committen de paden expliciet in plaats van `git add -A`.
- Python 3.10 of hoger. Op Windows heet het commando meestal `py`, elders `python3`. De scripts
  gebruiken alleen de standaardbibliotheek, met één uitzondering: `lees_scan.py` heeft
  **Pillow** nodig (`py -m pip install pillow`).

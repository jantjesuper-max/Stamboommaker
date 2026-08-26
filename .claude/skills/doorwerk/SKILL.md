---
name: doorwerk
description: Werk de dossier-werklijst van de stamboom af met archiefonderzoek en afstrepen — ronde na ronde achter elkaar door, niet één voorouder en dan stoppen. Gebruik dit als de gebruiker vraagt om "doorwerken", "volgende voorouder", "werk de werklijst af", of een lange onbewaakte sessie wil.
---

# Doorwerken aan de dossiers

Je werkt `onderzoek/werklijst-dossiers.md` af langs de voorouderroute: **eerst afmaken, dan
omhoog, dan opzij**.

**Afmaken gaat vóór doorgaan.** Staat er bij een al afgevinkte voorouder nog een open vraag,
dan is dát het werk van deze ronde — niet een nieuwe persoon beginnen. Een vraag is pas dicht
als er een antwoord is, óf als hij expliciet is gesloten: "niet gevonden in bron X, Y en Z"
of "niet te vinden omdat …". Gesloten vragen blijven als `- [x]` staan met de uitkomst
erachter, zodat zichtbaar is dat er gezocht is. `py test/controleer.py` rekent dit uit en
stuurt je naar de diepste voorouder met openstaande vragen. Na elke afgeronde persoon zijn diens ouders aan de beurt (diepste generatie eerst,
vader vóór moeder); zit een lijn muurvast, dan wijst de route vanzelf de diepste open tak
ernaast aan; pas als álle lijnen boven zijn afgewerkt komen de jongste generaties als
terugval. Zo klim je lijn voor lijn de boom in en komt elke tak aan bod — en bovenaan een
lijn probeer je óók voorbij de huidige stamboom te breken (stap 4c).

**Eén voorouder per ronde, maar zoveel rondes achter elkaar als je kunt.** Elke persoon wordt
volledig afgemaakt, afgevinkt en gecommit, en daarna begin je direct aan de volgende — zonder
tussenvraag. Je stopt pas als de werklijst leeg is of je echt vastloopt; zie "Doorgaan"
onderaan. Doordat de voortgang in de werklijst en in git staat, kan het werk over willekeurig
veel korte of lange sessies verdeeld raken zonder dat er half werk kwijtraakt.

Lees vóór je begint: `CLAUDE.md` (conventies, gouden regel), `onderzoek/bronnengids.md`
(welke archieven bij welke regio horen) en `boek/zijtakken.md` (wat je doet met de broers en
zussen die je onderweg tegenkomt).

**Zijtakken in één regel:** de stamboom bevat **alleen directe voorouders** — vaders én
moeders, generatie na generatie. Broers en zussen van voorouders komen **nergens** in de
stamboom: niet in het overzicht, niet op de werklijst, niet als dossier, niet als relatie in
de frontmatter. Kom je ze tegen (en dat gebeurt bijna altijd), dan geldt: zegt de vondst iets
over ónze voorouder → een verhaal in `boek/verhalen/`; zegt het niets → één regel in het
onderzoekslog van het dossier, zodat niemand dat zoekwerk opnieuw doet. Zie
`boek/zijtakken.md`.

## De ronde — negen stappen

**1. Bepaal wie aan de beurt is**

```
py test/controleer.py
```

Dit rekent de route uit en noemt precies één persoon, met de reden erbij: `afmaken: nog N
open vragen te sluiten`, `omhoog: vader van …`, of `nieuwe lijn`. Volg die aanwijzing — de
volgorde zit in het script, niet in je hoofd. Zegt het script **afmaken**, dan doe je deze
ronde geen nieuwe voorouder maar sluit je de openstaande vragen van die persoon: zoeken,
en per vraag óf een antwoord óf een expliciete sluiting met de bronnen die je hebt
nagekeken. Sla nooit iemand over zonder reden; moet het toch, zet dan achter de regel
`· overgeslagen: <reden>` en ga verder (de route slaat die regel dan over; bekijk
overgeslagen regels periodiek opnieuw).

**2. Lees de context**

Zoek de persoon op in `stamboom/overzicht.md`: wie zijn de ouders, partner en kinderen, en
welke ID's hebben die volgens de werklijst? Bekijk het dossier van een al gemaakt familielid
als voorbeeld.

**3. Maak het dossier**

Kopieer `personen/_TEMPLATE.md` naar `personen/<id>.md` en vul de frontmatter volledig:
naam, geboren, overleden, beroep, lijn, generatie, status, en vader/moeder/partner/kinderen
als wikilinks met de ID's uit de werklijst. Nog niet bestaande dossiers linken is prima —
die wikilink markeert simpelweg werk dat later komt.

Het sjabloon heeft naast **Open vragen** ook een tabel **Zwakke sporen**. Daar horen
vermoedens die te dun zijn om zelfs een hypothese te zijn: een naamgenoot die verdacht goed
past, een zeldzame achternaam die elders in de stamboom opduikt, een online boom zonder
bron. Noteer per spoor waaróm het zwak is en wat het zou betekenen als het klopt. Zo bouwt
een volgende ronde er niet op voort en vindt niemand het opnieuw "voor het eerst".

**4. Zoek — eerst breed sporen jagen, dan smal bewijzen**

**4a. De websweep (sporen jagen).** Zoek eerst het open web af met WebSearch, zoals ChatGPT
dat doet — voor de meeste Nederlandse lijnen heeft een hobbyist de puzzel al eens gelegd
en online gezet. Doe per persoon minstens deze zoekopdrachten en varieer de spelling:

- `"<naam>" <geboortejaar> <geboorteplaats>` en `"<naam>" genealogie`
- `"<naam>" "<naam partner>"` (een paar identificeert scherper dan een persoon)
- gericht op de boomsites: Genealogieonline, Geneanet, Stamboomforum, FamilySearch,
  online-begraafplaatsen.nl; ook de permalinks van openarchieven.nl zijn geïndexeerd

Oogst uit die treffers: exacte datums, plaatsen, aktenummers, namen van ouders/broers/
zussen, en generaties die wij nog niet hebben. Maar dit zijn **aanwijzingen, geen bronnen**:
neem ze op in het onderzoekslog met URL en het label *aanwijzing*, nooit rechtstreeks als
feit in de kerngegevens. Een online stamboom zonder bronvermelding heeft vaker dan je
denkt twee naamgenoten samengesmolten.

**4b. De registers (bewijzen).** Ga daarna met die sporen naar de registers zelf en werk
minimaal deze ingangen af, voor zover regio en periode passen
(zie `onderzoek/bronnengids.md` voor de volledige lijst per streek):

- **Open Archieven** — gebruik het projectscript (geen API-key nodig):
  `py scripts/zoek_openarch.py zoek "naam" --type Geboorte --van 1860 --tot 1870` en
  `py scripts/zoek_openarch.py toon archief:identifier` voor bronvermelding + scan-URL's.
  **Lees altijd de rollen** die `toon` per persoon geeft (Overledene, Vader, Moeder, Bruid,
  Kind) plus de vermelde leeftijd — dat is het bewijs, niet de volgorde waarin namen
  verschijnen. Zoek ook op de naam zónder patroniem, en op **de naam van de vader** (dat
  levert in één keer de hele kinderrij). Zoek bij overlijden óók op de **dorpsnaam**, niet
  alleen de gemeente. Controleer treffers altijd op datum, plaats én relaties
  (naamgenoten!). **WieWasWie** als tweede brede ingang.
- **Loop de bróntypen langs die je nog niet hebt geprobeerd.** Een naam die in de burgerlijke
  stand niets nieuws meer geeft, kan in een ander register een heel leven opleveren:
  `--brontype Bevolkingsregister`, `--brontype Gevangenis`, `--brontype Lidmaten`,
  `--brontype Stamboek`. Sommige daarvan hebben een gebeurtenistype dat met `other:` begint en
  zijn met `--type` onbereikbaar. Zo kwamen vier gevangenisinschrijvingen van één voorouder
  boven, met haar beroep, haar lengte en haar handtekening erin.
- **Het notarieel archief is een vaste halte, ook zonder scan.** `--brontype Notarieel`, en
  `--type "Notariële inschrijving"`. De index noemt de **aktesoort** (`AkteSoort`) en soms een
  hele alinea in `SourceRemark`, en dat is vaak al genoeg: boedelscheidingen, voogdijstellingen,
  plaatsvervangingen, schuldbekentenissen, koop- en huurcontracten en testamenten zijn de
  plaatsen waar arme families toch uitgebreid op papier komen, met bedragen en bezittingen erbij.
  Bij één dorp in 1812 stond er `plaatsvervanging`, en dat bewees een remplaçantencontract zonder
  dat de akte gelezen was. **Neem zulke indexteksten letterlijk over** in het onderzoekslog en in het
  beschrijvingsbestand, met de spelling van het archief: dat is de grondstof voor een citaat in
  het verhaal (stap 7 en `boek/stijlgids.md`, "Citeer de bron letterlijk").
- **Bij een naamgenoot: bewijs het wegstrepen.** Iemand afschrijven is net zo goed een bewering
  als iemand identificeren, en vraagt hetzelfde bewijs — de **ouders** en de **leeftijd** in de
  akte. Een voornaam die katholiek klinkt of een andere gemeente is géén bewijs. Dat is hier één
  keer misgegaan: een als "gevaarlijke naamgenoot" afgeschreven man bleek de voorouder zelf,
  hertrouwd — de huwelijksakte noemde zíjn ouders.
- Het **regionale archief** van de streek: AlleFriezen, AlleDrenten, Collectie Overijssel,
  Westfries Archief, Erfgoed Leiden, Zeeuwen Gezocht, Rijksarchief België, Archion
**4b-bis. Buiten het archief: waar de verhalen liggen**

Aktes geven datums; deze bronnen geven leven. Loop ze langs zodra iemand een beroep, een
verhuizing of een opvallend voorval heeft:

- **Delpher** — kranten én gedigitaliseerde boeken en tijdschriften: overlijdensadvertenties,
  ongelukken, faillissementen, veilingen, gemeenteberichten, stakingen
- **Streekhistorie**: regionale historische verenigingen, dorpswebsites, uitgegeven
  streekboeken — vraag de historische vereniging van de streek wat er is. Vaak schreef
  iemand al een boek over precies het dorp en het beroep van je voorouder
- **Google Books** en **DBNL** voor oudere lokale geschiedschrijving
- **Bidprentjes en familieadvertenties** via het CBG — in katholieke streken goud waard
- **online-begraafplaatsen.nl** en grafstenen
- **Beroepsgeschiedenis**: wat deed een turfmaker, pannenbakkersknecht of hellingbaas
  concreet? Zoek daar apart op; het is de grondstof voor de scènes die de stijlgids vraagt

Zulke bronnen zijn zelden bewijs voor een datum, maar wél bron voor het verhaal. Neem ze op
met volledige verwijzing en noem in het verhaalbestand eerlijk dat het streekhistorie is en
geen akte.

**Nieuwe bron tegengekomen? Schrijf hem bij.** Kom je een archief, register, website, boek of
zoekingang tegen die nog niet in `onderzoek/bronnengids.md` staat, voeg hem dan in dezelfde
ronde toe — bij de juiste regio, met één regel over waar hij goed voor is en wat je er
concreet in vond. Datzelfde geldt voor een register dat blijkt te **ontbreken** of achter een
betaalmuur zit: dat hoort er ook bij, zodat de volgende ronde er geen tijd aan verliest.

Gaat het niet om een bron maar om een **zoektechniek** (een veld dat je moet uitlezen, een
spelling die wél werkt, een index die op dorp zoekt in plaats van gemeente), dan hoort die
in deze skill en in `CLAUDE.md` bij de zoeklessen — plus zo mogelijk een aanpassing van
`scripts/zoek_openarch.py`. Zo wordt het gereedschap elke ronde iets scherper in plaats van
dat dezelfde ontdekking steeds opnieuw gedaan wordt.
- Bij een huwelijk na 1811: kijk of er **huwelijksbijlagen** zijn. Daar zitten vaak
  geboorteaktes van de ouders in — de goedkoopste manier om een generatie terug te komen.

Voor elke gevonden akte: **download de scan** naar `documenten/<id>/` volgens de naamgeving
in `CLAUDE.md`, met het beschrijvingsbestand (`.md`) ernaast: letterlijke transcriptie,
onzekere lezingen als `[?]`, samenvatting, en de volledige bronvermelding.

**Open de scan altijd en controleer of de akte er werkelijk op staat** — zoek de naam of de
datum in het beeld. Een scan-URL uit de API kan naar een andere bladzijde van hetzelfde
register wijzen; dat is hier één keer gebeurd. Klopt de bladzijde niet, schrijf dan geen
transcriptie maar zet `status: gedownload, maar ⚠ VERKEERDE BLADZIJDE` en vermeld dat de
gegevens uit de index komen. Gebruik de **FULLSIZE**-URL die `toon` print: die geeft de
volledige scan waar de thumb-URL bij jp2-bestanden een 404 geeft.

**En lees de akte niet op ooghoogte: zoom in.** Een spread van 5000 pixels lijkt leesbaar en is
het niet. Snijd de akte in stroken en vergroot die (PIL is beschikbaar; `ImageOps.autocontrast`
helpt bij bleke inkt). Bij één huwelijksakte leverde inzoomen twee naamcorrecties op — een
voornaam én een patroniem moesten anders gelezen worden — en bij een overlijdensakte veranderde
de sterfdag van "negenden" in "zesden". Wie de spread in één keer
bekijkt, neemt fouten over die daarna in drie bestanden staan.

**Een extra scan bij een akte kan een ánder document zijn.** De tweede "scan" bij een
huwelijksakte bleek een **militieattest** met vijf dienstjaren erop. Kijk elke extra
scan apart aan; blijkt het een eigen document, geef het dan zijn eigen naam en datum in de map en
niet `_2`.
Lukt downloaden niet (viewer-only, betaalmuur): neem dan wél de volledige bronvermelding op
met `[nog te downloaden]`. Nooit een feit zonder bron.

**Markeer meteen wat citeerbaar is.** Transcribeer je een akte of neem je een indextekst over,
zet dan de één of twee regels die je aan de keukentafel zou voorlezen apart onderaan het
beschrijvingsbestand:

```markdown
## Citaatwaardig

> als verklarende de comparant vader niet te kunnen schrijven, als zulks niet geleerd hebbende.

De vaste formule bij een aangever die geen handtekening zette. Uit de akte zelf.
```

Zet erbij of het uit de **akte** komt of uit de **index** — dat is bij het schrijven het verschil
tussen twee beweringen. Zo vindt een latere schrijfsessie het materiaal in één keer terug met
`grep -rn "Citaatwaardig" documenten/`, in plaats van dertig transcripties opnieuw door te lezen.
Is er niets bijzonders te citeren, laat het kopje dan weg; een saaie formule opnemen helpt niemand.

Bevestigt het register een spoor uit de websweep, dan pas krijgt het feit zijn status
(✓ bij een akte). Spreekt het register de online boom tegen, noteer dat expliciet — dat
behoedt de volgende zoeker voor dezelfde valkuil.

**4c. Bovenaan een lijn: probeer omhoog te breken**

Zijn de ouders van deze persoon onbekend, dan sta je op een lijn-top en is dít het moment
om de stamboom te laten groeien. Zoek de ouders actief: het doopboek van de persoon zelf,
de huwelijksbijlagen van het huwelijk (daar zit vaak de geboorteakte van de ouders in),
het patroniem als wegwijzer, en de websweep van 4a.

- **Gevonden?** Dan groeit de boom: (1) nieuwe regel(s) in de werklijst, in dezelfde
  sectie, generatie = die van het kind + 1, ID volgens de conventie in `CLAUDE.md`;
  (2) `vader:`/`moeder:`-wikilinks in het dossier van het kind; (3) `stamboom/overzicht.md`
  bijwerken; (4) de bijbehorende open vraag in `onderzoek/open-vragen.md` bijwerken of
  afsluiten. Status eerlijk: akte gezien → ✓, alleen sterke aanwijzing → ◐ of ?.
  De route pakt de nieuwe voorouder in de volgende ronde vanzelf op (omhoog).
- **Niet gevonden?** Stel eerst de vraag uit de volgende paragraaf: is dit een muur, of
  faalt mijn gereedschap? Blijft het een muur, rond het dossier dan eerlijk af (dun dossier
  met `[niets gevonden]` is prima), zet achter de werklijstregel `· muur DD-MM-JJJJ` en
  beschrijf in het logboek wat er is geprobeerd — dan doet niemand dat werk dubbel. Vink af.
  De route gaat daarna vanzelf opzij, naar de diepste nog open tak.

**4d. Muur of gereedschapsprobleem?**

Vind je iets niet terwijl je verwacht dat het er hoort te zijn, dan is "niet gevonden" nog
geen conclusie. **Verdenk eerst het zoekscript.** Dat is hier al twee keer de oorzaak
geweest: de rollen (Overledene/Vader/Moeder) stonden wél in de API maar werden niet geprint,
en overlijdens bleken op **dorpsnaam** geïndexeerd terwijl er op gemeente werd gezocht.

Loop dit rijtje af voordat je een muur opschrijft:

- Haal de **ruwe JSON** op (`curl` naar `api.openarch.nl/1.1/records/show.json?...`) en kijk
  of er velden in zitten die het script weggooit. Zo ja: **pas
  `scripts/zoek_openarch.py` aan**, met een comment dat uitlegt waarom dat veld ertoe doet.
- Varieer de zoekvorm: met en zonder patroniem, de naam van de vader, de dorpsnaam in plaats
  van de gemeente, spellingsvarianten (Matjen/Mattje/Maatje/Matje).
- Probeer een **ander brontype**: `--brontype Gevangenis`, `--brontype Bevolkingsregister`,
  `--brontype Lidmaten`, `--brontype Militairen`, `--brontype Notarieel`. Wat in de burgerlijke
  stand niet staat, staat soms in een register dat je nog niet had aangeraakt. Bij een man geboren
  tussen ongeveer 1770 en 1800 is **"Friese militairen onder Napoleon"** een vaste halte: het
  opmerkingenveld geeft daar soms een hele biografie.
- **Vóór ongeveer 1820: verdenk de familienaam.** De naamsaanneming van 1811 was net gebeurd en
  klerken wisselden jaren lang tussen de aangenomen naam en de dorpsbijnaam. De geboorteakte van
  één voorouder uit 1813 staat er onder een heel andere achternaam: in het ene dorp heette het
  gezin zo, in het buurdorp anders, in dezelfde jaren. **Zoek dan op de naam van de moeder** —
  die veranderde niet mee. Zo kwam die akte alsnog boven nadat ik hem al als muur had opgeschreven.
- **Kijk in de ruwe JSON naar velden die het script niet print.** Dat is hier drie keer de oorzaak
  geweest van een valse muur: de rollen, het patroniem (`PersonNamePatronym`) en het
  opmerkingenveld (`SourceRemark`). Alle drie staan nu in `toon`. Vind je een vierde, pas het
  script aan met een comment waarom dat veld ertoe doet.
- Let op de regel onderaan het zoekresultaat. Sinds 25-08-2026 pagineert het script zelf door
  zodra je `--van`, `--tot` of `--brontype` gebruikt, en meldt het hoeveel treffers het heeft
  doorzocht. Staat er **"N treffer(s) niet doorzocht"**, dan is de zoekopdracht niet af en is
  "niet gevonden" nog geen uitspraak. Dit was hier twee keer de oorzaak van een valse muur: de
  geboorte- én de overlijdensakte van een voorouder stonden gewoon op pagina twee.
- Vraag je af of de bron wel in deze index zit. DTB-boeken en kohieren zijn maar deels
  ontsloten; dan is het geen muur maar een verkeerde ingang, en hoort in het logboek
  *welke* ingang dan nodig is.

Een verbetering aan het script is net zoveel waard als een gevonden akte: hij werkt door in
elke volgende ronde.

**5. Leg ook vast wat je níet vond — en maak elke logregel reproduceerbaar**

Elk geraadpleegd register én elke websweep gaat in het onderzoekslog van het dossier en in
`onderzoek/logboek.md` — óók "niets gevonden in bron X, periode Y". Zonder die negatieve
resultaten doet de volgende sessie hetzelfde werk opnieuw.

En elke regel krijgt zijn klikbare ingang, zodat een lezer het resultaat kan nachecken
zonder het werk over te doen (volledig: CLAUDE.md, "Onderzoekslogs: reproduceerbaar, met
links"): gevonden records als **permalink** (`https://www.openarchieven.nl/<code>` —
`toon` print hem), zoekopdrachten als volledig commando in `code`-opmaak (dat commando ís
de reproductie van "niets gevonden"), webbronnen en literatuur met volledige URL en
raadpleegdatum, gedownloade stukken als relatieve link naar het beschrijvingsbestand. Een
bron bij naam noemen zonder URL betekent dat iemand hem later opnieuw moet zoeken — dat is
bij het Rampjaar-onderzoek gebeurd en het kostte een extra sessie.

**6. Tijdsbeeld: wat gebeurde er om dit leven heen?**

```
py scripts/tijdsbeeld.py kandidaten <persoon-id>
```

Dit legt de leefjaren en woonplaatsen naast de kalender van rampen, oorlogen en epidemieën
(`tijdsbeeld/_KALENDER.md`) en noemt kandidaten: de stormvloed die het dorp onder water
zette, de cholera-golf, de bezetting. Vul eerst `woonplaatsen:` in de frontmatter zo goed
mogelijk in (uit bevolkingsregisters en aktes) — dat maakt de kandidaten scherper.

**Dit is verplicht zoekwerk, geen decor.** Elke **groot**-kandidaat die het script noemt
wordt deze ronde écht onderzocht: minstens één serieuze zoekactie via de zoekingang uit de
kalender (Delpher, schadelijsten, oorlogsbronnen.nl — zie ook de tijdsbeeld-sectie in
`onderzoek/bronnengids.md`), met het resultaat in het onderzoekslog, óók bij niets
gevonden. Kandidaten met gewicht `achtergrond` toont het script apart: die koppel en meld
je **niet** af — hoogstens een zin sfeertekening in de Levensloop, en alleen een koppeling
als er toevallig een concreet spoor opduikt. Per groot-kandidaat:

- **Raakt het dit leven?** Kijk éérst of de gebeurtenis al een bestand heeft:
  `py scripts/tijdsbeeld.py zoek <term>` (de kandidaten-uitvoer waarschuwt hier ook voor).
  Zo ja: voeg de persoon aan dát bestand toe — één gebeurtenis, één bestand. Zo nee: maak
  een nieuw bestand volgens `tijdsbeeld/_TEMPLATE.md`, met bij elke webbron of literatuur
  de volledige URL en de datum van raadpleging. Zet daarna de gebeurtenis in de
  Tijdsbeeld-tabel van het dossier, verweef één of twee zinnen in de Levensloop, en is
  het verhaalstof → stap 7 (rubriek `tijdsbeeld`). Status eerlijk: bron noemt persoon,
  gezin of adres → ✓; woonde aantoonbaar in het getroffen gebied → ◐; alleen
  tijdsoverlap → niet koppelen. Bij gebied `landelijk` is wonen in Nederland nooit
  genoeg: daar moet een plaatselijk of persoonlijk spoor bij (sterftepiek in het dorp,
  militie-inschrijving, verlies in het gezin, bericht over de woonplaats).
- **Geen raakvlak of niets gevonden?** Meld af met een regel in
  `tijdsbeeld/_AFGEHANDELD.md` — dan vraagt de volgende ronde er niet opnieuw naar.

Sluit af met `py scripts/tijdsbeeld.py controleer && py scripts/tijdsbeeld.py index`.
Kom je onderweg een plaatselijke gebeurtenis tegen die de kalender mist (dorpsbrand,
dijkdoorbraak, bombardement): voeg die als regel toe — daar wordt de kalender beter van.

**7. Verhaalstof? Eerst het verhalenschrift, dan eventueel schrijven**

**Altijd:** elke bijzondere vondst krijgt een eigen bestand in `boek/verhalen/`, gemaakt
uit `boek/verhalen/_TEMPLATE.md`, met de naam `<jaar>-<korte-titel>.md`. Vul de frontmatter
volledig: rubriek, deel, lijn, periode, personen, **sterkte** (`sterk` uit aktes / `mager`
deels bron / `vermoeden`) en **landing** (`onverwerkt` tot het in een hoofdstuk zit). De
romp eindigt met een regel `**Bron:**` — zonder bron geen verhaal. Daarna:

```
py scripts/verhalen.py controleer && py scripts/verhalen.py index
```

Dit kost een minuut en zorgt dat geen vondst ooit verdwijnt, ook niet als er die ronde geen
hoofdstuk komt. Twijfel je of iets bijzonder is? Schrijf het op; daar kan niets te veel
liggen.

**Laat de bron zelf aan het woord.** Is er een citeerbare passage, dan hoort er een citaatblok
in het verhaal. Dat is geen versiering maar de kern van de stem van dit boek: een verhaal met
één regel uit de akte erin leest als een document, een verhaal zonder zo'n regel leest als een
samenvatting. Zie `boek/stijlgids.md`, "Citeer de bron letterlijk", voor de vorm: één regel die
zegt waar de woorden vandaan komen, dan het blok met `>` in de spelling van de akte, dan in
gewone taal wat er staat.

Kijk vóór het schrijven expliciet wat er aan materiaal ligt:

```
grep -rn "Citaatwaardig" documenten/<persoon-id>/
grep -rn "^> " documenten/<persoon-id>/
```

**Notariële aktes leveren hier het meeste op** (boedelscheiding, voogdij, plaatsvervanging,
schuldbekentenis, koop, testament), daarna de vaste formules van de burgerlijke stand, het
signalement uit een militie- of gevangenisregister, en de indexalinea uit `SourceRemark`.
Is er niets letterlijks, dan komt er geen citaat: verzin er nooit een, en laat een akte nooit
"oud" klinken omdat het mooi staat. Geen bron, geen citaat.

**Als er genoeg staat voor een verhaal:** vraag eerst wat er al ligt voor dit deel —

```
py scripts/verhalen.py lijst --deel <N> --onverwerkt
```

— en schrijf dan een hoofdstuk of paragraaf in
`boek/hoofdstukken/`, in de stem van `boek/stijlgids.md`, met voetnoten. Lees éérst de
rode draad van het deel in `boek/opzet.md` en spin die verder: elk hoofdstuk binnen een
lijn bouwt voort op het vorige (het scharnier van het deel is waar de lijn naartoe
schrijft). Spreken de feiten de draad tegen, stel dan de draad bij in `boek/opzet.md` en
noteer dat. Werk daarna de hoofdstukkentabel bij. Het boek volgt de dossiers, nooit andersom.

Twijfel je of iets "bijzonder" is? Vraag je af of je het aan tafel zou vertellen. Zo ja:
schrijven. Een dossier met alleen datums levert geen boek op. Verwerk je een verhaal in een
hoofdstuk, gooi het bestand dan niet weg maar zet `landing:` op het hoofdstuk en bouw de
index opnieuw — zo blijft zichtbaar wat al een plek heeft en wat nog wacht.

**8. Afvinken**

Vink de regel in de werklijst af (`- [ ]` → `- [x]`) — maar alleen als aan **alle** zes
voorwaarden is voldaan:

1. het dossier bestaat en de frontmatter is volledig gevuld;
2. vader, moeder en partner staan er als wikilinks;
3. minstens één archiefbron is gezocht (gevonden óf expliciet niets);
4. het onderzoekslog in het dossier is bijgewerkt;
5. **elke vraag onder "Open vragen" is dicht** — met een antwoord, of met een expliciete
   sluiting die de doorzochte bronnen noemt. Wat nog onderzoek nodig heeft mag blijven
   staan, maar dan is de persoon niet af en stuurt de route je terug;
6. de **groot**-kandidaten van stap 6 zijn écht onderzocht (zoekactie in het
   onderzoekslog): elk gekoppeld, beargumenteerd afgemeld of als open vraag genoteerd.
   Achtergrond-kandidaten hoeven niets.

Vermoedens die te dun zijn voor een feit horen niet bij de open vragen maar in de tabel
**Zwakke sporen**, met de reden waarom ze zwak zijn.

Dan meten en het voortgangscijfer bijwerken:

```
py test/controleer.py --fix
```

Bij problemen: eerst oplossen, niet doorgaan.

**9. Vastleggen**

Controleer de repo-grens en commit alleen deze ronde:

```
git rev-parse --show-toplevel        # moet de projectmap zijn, niet een map erboven
git add personen documenten stamboom onderzoek boek
git commit -m "Dossier <naam> (<jaren>)"
```

Eén commit per voorouder, zodat elke ronde los terug te draaien is. Noem de paden expliciet
in plaats van `git add -A`: er wordt soms parallel aan andere mappen gewerkt.

**Daarna niet stoppen** — meteen door naar stap 1 met de volgende persoon. Zie "Doorgaan".

## Doorgaan — dit is de kern van de skill

**Stop niet na één voorouder.** Na stap 9 begin je onmiddellijk opnieuw bij stap 1 met de
volgende persoon, in dezelfde sessie, zonder tussenvraag en zonder tussenrapportage. Ronde na
ronde achter elkaar. De commit en het logboek zijn het verslag; een samenvatting per ronde is
verspilde tijd.

Wat je tussen de rondes **niet** doet: vragen of je verder mag, uitgebreid terugblikken, of
wachten op bevestiging. Doorwerken betekent doorwerken.

Stop alleen als een van deze vier zich voordoet:

1. **De gebruiker noemde een aantal** ("doe er tien") en dat aantal is bereikt.
2. **De werklijst is leeg** en er staan geen open vragen meer.
3. **Je loopt twee keer achter elkaar op hetzelfde vast** — bijvoorbeeld een archief dat niet
   reageert. Noteer dat in `onderzoek/logboek.md`, sla de persoon over met reden
   (`· overgeslagen: <reden>`), en ga verder met de volgende. Pas als ook dát niet lukt,
   stop je en zeg je wat er kapot is.
4. **De gebruiker onderbreekt je.**

Verzin nooit gegevens om een dossier "af" te krijgen. Een dossier met drie regels en een
eerlijk `[niets gevonden]` is meer waard dan een verzonnen datum — en het is bovendien
sneller, dus er is ook geen excuus.

## De hele nacht doorwerken

De skill loopt vanzelf door, dus in principe is één `/doorwerk` genoeg: die blijft rondes
draaien tot de werklijst leeg is of de sessie eindigt.

Een cronjob is er **alleen als vangnet**, voor het geval het doorwerken stilvalt (een sessie
die eindigt, een vastgelopen aanroep). Zo'n taak hoeft dus niet vaak te vuren — elk half uur
is ruim genoeg — en de opdracht erin moet óók "werk ronde na ronde door" zijn, niet "doe één
voorouder". Ditzelfde geldt voor `/loop /doorwerk`.

Omdat de voortgang in de werklijst en in git staat en niet in het gesprek, kost een
afgebroken nacht niets: de volgende sessie rekent de route opnieuw uit en gaat verder waar
hij was.

## Committen naast ander werk

Aan dit project wordt soms parallel gewerkt (bijvoorbeeld aan `website/`). Gebruik daarom
**geen blinde `git add -A`** maar noem de paden die bij deze ronde horen:

```
git add personen documenten stamboom onderzoek boek
git commit -m "Dossier <naam> (<jaren>)"
```

Zo blijft elke commit één afgeronde voorouder, en trek je niemand anders zijn halve werk mee.

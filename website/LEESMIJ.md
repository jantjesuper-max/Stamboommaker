# Stamboomwebsite

Een lokale website om de stamboom te bekijken en door alle mappen en
md-bestanden van het project te bladeren. Draait volledig op je eigen
laptop; er gaat niets van het project het internet op. (Eén uitzondering
de andere kant op: het **Kaart**-tabblad haalt zijn achtergrondkaart als
plaatjes op bij OpenStreetMap/CARTO — zonder internet blijven de stippen
en filters daar gewoon werken, alleen de achtergrond ontbreekt dan.)

## Starten

Windows: dubbelklik op **`start-website.cmd`** in deze map.
macOS/Linux: `./website/start-website.sh`.
Of vanaf de projectmap:

```
py website/server.py          (Windows)
python3 website/server.py     (macOS/Linux)
```

De browser opent vanzelf op <http://localhost:8123>. Stoppen: **Ctrl+C**
in het zwarte venster (of het venster sluiten).

Handig om te weten:

- **Andere poort:** `py website/server.py 8200`
- **Zonder browser openen:** `py website/server.py --geen-browser`
- Alles wordt **live van schijf** gelezen: pas je een dossier aan, dan is
  dat na een verversing (F5) meteen zichtbaar. De server hoeft niet
  herstart te worden.

## Op het wifinetwerk

Wil je de site ook op een telefoon, tablet of andere computer in huis
bekijken, dubbelklik dan op **`start-website-netwerk.cmd`** (of start
`py website/server.py --netwerk`). Het venster toont dan de
netwerkadressen; op het andere apparaat typ je het adres dat met
`192.168` begint, bijvoorbeeld `http://192.168.178.49:8123`.

Let op:

- Beide apparaten moeten op **hetzelfde wifinetwerk** zitten.
- Iedereen op dat netwerk kan dan de hele projectmap inzien (de site
  serveert nog steeds niets daarbuiten, en niets gaat het internet op).
- De **eerste keer** kan Windows Firewall toestemming vragen; kies dan
  "Toegang toestaan" voor particuliere netwerken. Zonder die toestemming
  werkt de site wel op de computer zelf, maar niet op andere apparaten.

## Eén kant delen: het takkenfilter

Onder de menubalk staat op elke pagina de balk **Weergave**: Hele stamboom ·
Vaderskant · Moederskant, plus een keuzelijst om één familielijn apart te
bekijken. Staat een kant aangevinkt, dan toont die keuzelijst alleen de
lijnen die onder die kant vallen. De keuze staat als `?tak=…` **vóór** de hash in het adres en blijft
dus staan terwijl je klikt — en zo'n adres is deelbaar:

```
http://localhost:8123/?tak=vaderskant        alles boven de vader van de proband
http://localhost:8123/?tak=moederskant       alles boven de moeder van de proband
http://localhost:8123/?tak=lijn:<lijnnaam>   één familielijn apart
```

(Deel je op het wifinetwerk, gebruik dan het `192.168`-adres in plaats van
`localhost`.) Wie zo'n link opent ziet alléén die kant: de stamboom, de
personenlijst, de kaart, de verhalen en het tijdsbeeld zijn er allemaal op
toegesneden, en de zoeksuggesties ook. Een verhaal telt mee als het iemand
uit de tak raakt of bij een lijn van de tak hoort. De knop **"Deel deze
weergave"** kopieert de volledige link (inclusief de pagina waar je op staat).
Een kant is daarbij "die persoon plus al zijn voorouders", geklommen langs de
vader- en moeder-wikilinks in de dossiers — geen handbijgehouden lijstje, dus
nieuwe dossiers doen vanzelf mee.

## Wat je ziet

- **Stamboom** — een sleep- en zoombare kwartierstaat, opgebouwd uit de
  dossier-frontmatter (vader/moeder-links), van jong (links) naar oud
  (rechts), met een kolom per generatie. Slepen verschuift het beeld,
  Ctrl+scroll of de knoppen zoomen, en de ronde knop op een kaartje klapt
  een hele tak in of uit — zo blijft de boom ook met honderden personen
  overzichtelijk. Klikken op een kaartje opent het dossier. Voorouders
  zonder dossier staan er gestippeld bij ("nog geen dossier").
  Boven de boom staat de voorkant van de site: één zin die vertelt hoe ver
  het onderzoek reikt, met de kerncijfers als tegels eronder (die rekenen
  mee met een takkenfilter). De boom opent met de jongste generatie in
  beeld, elk kaartje draagt een monogram in de kleur van de familielijn,
  de verbindingslijnen kleuren mee met de tak waar ze naartoe lopen, en de
  knop **Volledig scherm** klapt het vlak over het hele scherm (Esc sluit;
  er zweeft dan een eigen zoombalkje rechtsonder).
- **Personen** — alle dossiers, gegroepeerd per generatie, met filters op
  lijn, generatie en betrouwbaarheidsstatus en een omschakeling tussen
  kaartjes en een compacte tabel. Het zoekveld rechtsboven geeft vanaf elk
  tabblad directe suggesties (pijltjestoetsen + Enter werken).
- **Kaart** — alle woonplaatsen uit de dossiers op een echte kaart van
  Nederland. Elke stip is een plaats: hoe groter, hoe meer voorouders er
  woonden, en de kleur (of taartverdeling) is de familielijn. Zweven over
  een stip toont wie er woonden; klikken zet de lijst vast, met links naar
  de dossiers. Filteren kan per familielijn (de gekleurde chips) en per
  generatie; de afspeelknop loopt de generaties af van oud naar jong, en
  bij één gekozen generatie tonen open rondjes waar de ouders woonden met
  stromende verhuislijnen van ouderplaats naar kindplaats. Dieplink:
  `#/kaart/8` opent meteen generatie 8. De coördinaten per plaatsnaam
  staan in `website/static/plaatsen.json` — mist er een plaats, dan meldt
  de kaart dat onderaan en voeg je hem daar toe (`py scripts/plaatsen.py`
  somt op wat er ontbreekt).
- **Tijdsbeeld** — de tijdlijn van rampen, oorlogen en epidemieën die de
  woonplaatsen van voorouders raakten, met per gebeurtenis een eigen pagina
  en de gekoppelde dossiers.
- **Verhalen** — alle losse vondsten uit `boek/verhalen/`, als kaarten met
  jaartal, openingszin en een score-balkje, gegroepeerd op hoe bijzonder een
  verhaal is (1-20) of per decennium. Filteren kan op rubriek (de chips), op
  lijn, en met het eigen zoekveldje; klikken opent het verhaal met bron en
  gekoppelde personen.
- **Cijfers** — het onderzoek in getallen, live uit de dossiers gerekend:
  kerncijfers als tegels, voorouders per familielijn (balkjes in de
  lijnkleuren, elk met naam en aantal als tekst erbij), de verdeling van de
  betrouwbaarheidsstatussen, voorouders per generatie, records (verste
  spoor, langste leven, dikste dossier) en de meest voorkomende voornamen,
  beroepen en woonplaatsen. Met een takkenfilter erop tellen alleen de
  dossiers van die kant mee.
- **Verkenner** — de hele projectmap: dossiers, documentenmappen, het boek,
  onderzoeksbestanden. Md-bestanden worden leesbaar weergegeven (inclusief
  tabellen, wikilinks en voetnoten), scans worden getoond mét de
  transcriptie uit het bijbehorende beschrijvingsbestand eronder (ook
  vervolgscans `_2`, `_3` vallen terug op dat ene beschrijvingsbestand),
  een link naar de archiefpagina waar de scan vandaan komt, en pdf's
  openen in de pagina.
- In een **dossier** staan bovenaan de kerngegevens, de naaste familie als
  klikbare kaartjes, de gebeurtenissen uit het tijdsbeeld, en de
  documentenmap als galerij met miniaturen. De knop "Toon in de stamboom"
  springt naar de plek van de persoon in de boom en licht die even op.

## De leespagina's

Een dossier, een verhaal, een gebeurtenis en een md-bestand in de verkenner
worden alle vier op dezelfde manier gelezen:

- **Inhoudsopgave.** Vanaf drie kopjes komt er een index bij: op een breed
  scherm in de rechtermarge (hij blijft meelopen tijdens het scrollen en licht
  op waar je bent), op een smal scherm als schuivende strip boven de tekst.
  Een dossier is al snel 17.000 pixels lang; hiermee spring je in één klik naar
  de Kerngegevens, de Levensloop of het Onderzoekslog. Rechtsonder verschijnt
  een knopje terug naar boven.
- **De tekst houdt een leesbare regelbreedte**, maar **tabellen lopen door tot
  de volle kolombreedte** — anders werden de vier kolommen van de
  kerngegevens- en onderzoekslogtabellen tot een paar woorden per regel
  samengeperst en viel de rechterkolom weg. Op een telefoon wordt elke
  tabelrij een kaartje met de kolomnaam als etiket.
- **Een pad in `code`-opmaak is klikbaar** als het bestand bestaat:
  `personen/…` opent het dossier, `boek/verhalen/…` het verhaal,
  `tijdsbeeld/…` de gebeurtenis, de rest de verkenner.
- **Voetnoten werken.** Een klik op het nummertje springt naar de noot en het
  pijltje eronder weer terug. (Dat waren gewone ankerlinks, en omdat de site op
  de hash routeert gooide een klik erop je naar de stamboom.) Zweven over een
  nummertje toont de noot bovendien als voorproefje op de plek waar je leest.
- **Je ziet waar je bent.** Onder de menubalk groeit een dun gouden lijntje mee
  met hoe ver je in de tekst bent. Een verhaal opent met een initiaal en meldt
  de leestijd; een dossier zegt in de kop hoe oud iemand geworden is. De
  sneltoets `/` springt vanaf elke pagina naar het zoekveld.
- **Een titel met een gedachtestreepje** wordt titel plus ondertitel, en een
  citaatblok met `>` leest als doorlopende tekst — zacht afgebroken regels
  worden aan elkaar geplakt, zodat vet en cursief over de regelovergang heen
  blijven werken.

## Download als PDF

Op elke dossier-, verhaal- en tijdsbeeldpagina staat een knop
**"Download als PDF"**: de server draait het markdown-bestand dan om tot
een nette A4-uitdraai (met kopkaart, tabellen, statustekens en
paginanummers) die je kunt bewaren of naar familie kunt doorsturen. Het
bouwen gebeurt met Edge of Chrome in headless-stand en duurt de eerste
keer een paar seconden; daarna komt hetzelfde bestand uit de cache in
`pdf/` (een bouwproduct, staat niet in git).

Hetzelfde kan ook los van de website, met meer mogelijkheden (alles in
één keer, of een gebundeld boekje met omslag en inhoudsopgave):

```
py scripts/pdf.py lijst                       wat valt er uit te draaien?
py scripts/pdf.py persoon <id>                een dossier
py scripts/pdf.py verhaal 1814-de-schuitenmaker        deel van de naam mag ook
py scripts/pdf.py persoon --alle --bundel     alle dossiers als één boekje
py scripts/pdf.py alles --bundel              personen + tijdsbeeld + verhalen
```

## Techniek

- `server.py` — kleine HTTP-server, alleen Python-standaardbibliotheek,
  niets te installeren. Luistert standaard uitsluitend op 127.0.0.1
  (alleen deze computer); met `--netwerk` ook op het lokale netwerk.
  Serveert in beide gevallen geen bestanden buiten de projectmap.
- De **menubalk blijft bovenaan staan** tijdens het scrollen, op elke pagina en
  tot onderaan. ⚠ Zet nooit `height: 100%` op `body` in `stijl.css`: dat geeft
  het body-vak de hoogte van één schermvulling, en `position: sticky` is
  begrensd door het vak waarin het staat — de balk plakte daardoor maar 830
  pixels en scrolde daarna gewoon weg, net als de bestandsboom in de verkenner.
  `min-height: 100vh` doet wat nodig is. De echte hoogte van de balk wisselt met
  de schermbreedte (de tabbladen slaan om), dus `app.js` meet hem en zet hem in
  `--kop-hoogte`; alles wat eronderuit moet komen rekent daarmee.
- `static/` — de webpagina zelf (`index.html`, `app.js`, `stijl.css`),
  plus het lokaal meegeleverde [Leaflet](https://leafletjs.com)
  (`leaflet.js`, `leaflet.css`, BSD-licentie) voor het kaart-tabblad en
  `plaatsen.json` met de coördinaten per plaatsnaam. Er hoeft niets
  geïnstalleerd te worden; alleen de kaartachtergrond (tegels van
  OpenStreetMap/CARTO) vraagt internet.

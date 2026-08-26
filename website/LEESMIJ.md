# Stamboomwebsite

Een lokale website om de stamboom te bekijken en door alle mappen en
md-bestanden van het project te bladeren. Draait volledig op je eigen
computer; er gaat niets het internet op.

De naam boven de pagina komt uit `stamboom.json` (`website.titel`), net als
de standaardpoort.

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
bekijken, gebruik dan **`start-website-netwerk.cmd`** (Windows) of
**`start-website-netwerk.sh`** (macOS/Linux), of start
`py website/server.py --netwerk`. Het venster toont dan de
netwerkadressen; op het andere apparaat typ je het adres dat met
`192.168` begint, bijvoorbeeld `http://192.168.178.49:8123`.

Let op:

- Beide apparaten moeten op **hetzelfde wifinetwerk** zitten.
- Iedereen op dat netwerk kan dan de hele projectmap inzien (de site
  serveert nog steeds niets daarbuiten, en niets gaat het internet op).
- De **eerste keer** kan Windows Firewall toestemming vragen; kies dan
  "Toegang toestaan" voor particuliere netwerken. Zonder die toestemming
  werkt de site wel op de computer zelf, maar niet op andere apparaten.

## Wat je ziet

- **Stamboom** — een sleep- en zoombare kwartierstaat, opgebouwd uit de
  dossier-frontmatter (vader/moeder-links), van jong (links) naar oud
  (rechts), met een kolom per generatie. Slepen verschuift het beeld,
  Ctrl+scroll of de knoppen zoomen, en de ronde knop op een kaartje klapt
  een hele tak in of uit — zo blijft de boom ook met honderden personen
  overzichtelijk. Klikken op een kaartje opent het dossier. Voorouders
  zonder dossier staan er gestippeld bij ("nog geen dossier").
- **Personen** — alle dossiers, gegroepeerd per generatie, met filters op
  lijn, generatie en betrouwbaarheidsstatus en een omschakeling tussen
  kaartjes en een compacte tabel. Het zoekveld rechtsboven geeft vanaf elk
  tabblad directe suggesties (pijltjestoetsen + Enter werken).
- **Tijdsbeeld** — de tijdlijn van rampen, oorlogen en epidemieën die de
  woonplaatsen van voorouders raakten, met per gebeurtenis een eigen pagina
  en de gekoppelde dossiers.
- **Verhalen** — alle losse vondsten uit `boek/verhalen/`, als kaarten met
  jaartal, openingszin en een score-balkje, gegroepeerd op hoe bijzonder een
  verhaal is (1-20) of per decennium. Filteren kan op rubriek (de chips), op
  lijn, en met het eigen zoekveldje; klikken opent het verhaal met bron en
  gekoppelde personen.
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
py scripts/pdf.py verhaal 1814-de-schuitenmaker   deel van de naam mag ook
py scripts/pdf.py persoon --alle --bundel     alle dossiers als één boekje
py scripts/pdf.py alles --bundel              personen + tijdsbeeld + verhalen
```

## Techniek

- `server.py` — kleine HTTP-server, alleen Python-standaardbibliotheek,
  niets te installeren. Luistert standaard uitsluitend op 127.0.0.1
  (alleen deze computer); met `--netwerk` ook op het lokale netwerk.
  Serveert in beide gevallen geen bestanden buiten de projectmap.
- `static/` — de webpagina zelf (`index.html`, `app.js`, `stijl.css`),
  zonder externe afhankelijkheden, dus werkt ook zonder internet.

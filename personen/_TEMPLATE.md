---
id: achternaam-voornamen-geboortejaar
naam:
geboren:            # DD-MM-JJJJ, plaats (ged. = gedoopt als geen geboortedatum bekend); statuscode ervoor mag
overleden:          # DD-MM-JJJJ, plaats
beroep:             # zoals de klerk het schreef, met jaartallen: "dienstknecht (1882-1889), arbeider (1891-1905)"
woonplaatsen:       # - Plaats (van–tot, waaruit bekend), één regel per woonplaats; voedt scripts/tijdsbeeld.py en de kaart
lijn:               # een van de familielijnen uit stamboom.json / boek/opzet.md
generatie:          # t.o.v. jezelf = 0; ouders = 1, grootouders = 2, enz.
status:             # ✓ | ◐ | ? | ⚠
vader: "[[id-vader]]"
moeder: "[[id-moeder]]"
partner: "[[id-partner]]"
kinderen:
  - "[[id-kind]]"
---

# Naam (geboortejaar–sterfjaar): één regel die zegt wie dit was

_De ondertitel na de dubbele punt is de kern van dit leven in de woorden van de bronnen: "de
knecht die een ander zijn dienstplicht afkocht", "de boer met de stelle van vijftien madden".
Geen samenvatting van de stamboom, maar wat deze mens onderscheidt. Pas als het dossier dat
weet; tot die tijd alleen de naam en de jaren._

**De opening is een moment, vetgedrukt: één alinea die begint bij een akte, een krant, een
handtekening. Wat er die dag op papier kwam, wie erbij was, wat er stond. Dat is de regel uit
`boek/stijlgids.md`: eerst het moment, dan de persoon, dan de context. Verzin niets dat niet in
de bron staat.**

![Bron, datum: de kern in de woorden van de bron](../boek/verhalen/beeld/JJJJ-MM-DD-bron-onderwerp.jpg)

_Direct onder de opening het knipsel van dat moment, gemaakt met `py scripts/knipsel.py`
(zie CLAUDE.md, "Knipsels: laat de lezer de bron zien"). Daarna één alinea die het hele leven
in vijf zinnen vertelt: waar vandaan, wat voor werk, met wie, waarheen, hoe het eindigde.
Is de identificatie zelf nog ◐ of ?, zeg dat hier met ⚠ en verwijs naar het kopje
"Waarom hij hier staat" hieronder._

## Kerngegevens

_Elk feit één regel, met de bron als klikbare permalink of als link naar het beschrijvingsbestand
in `documenten/`, en een status. Niet alleen geboorte, huwelijk en overlijden: ook elk
bevolkingsregister, elke notariële akte, elke militie-inschrijving, en wat ze zeggen (huisnummer,
beroep per jaar, tijdstip, wie tekende). Wat vetgedrukt staat is wat de bron bewijst._

| Feit | Gegeven | Bron | Status |
|------|---------|------|--------|
| Geboorte/doop | | | |
| Ouders | | | |
| Huwelijk | | | |
| Beroep | | | |
| Woonplaatsen | | | |
| Overlijden | | | |
| Kon schrijven | | | |

### De kinderen

_Alleen als de registers een kinderrij geven: geboortedatum, naam, plaats en wat er van hen
werd voor zover een bron dat zegt. ⚠ Dit zijn geen voorouders en ze krijgen geen dossier; zie
`boek/zijtakken.md`. De voorouder in de rij krijgt een wikilink._

| Geboren | Kind | Waar | Later |
|---------|------|------|-------|

## Waarom hij hier staat

_Alleen bij een ◐- of ?-identificatie: wat de koppeling aan het kind draagt (patroniem,
vernoemingsorde, het dorp, de enige naamgenoot in het register) en wat ertegen pleit. Bij
een ✓ dit kopje weglaten._

## Levensloop

_Dit is de kern van de pagina en de grondstof voor het boek. Schrijf in de stem van
`boek/stijlgids.md`, niet in telegramstijl, en deel het leven in met gedateerde tussenkopjes:
`### Knecht, 1882-1889`, `### Naar Oudshoorn, 1905-1908`. Elk tussenkopje is een episode die
de bronnen dragen; een leeg tijdvak krijgt geen kopje. Per episode: wat de akte zegt, zo
mogelijk een citaat in de spelling van de bron, en het knipsel van die passage vlak bij het
citaat. Een dossier met drie bronnen heeft drie kopjes, een dossier met één bron één._

_Houvast voor wat er per episode in hoort:_

- _**Herkomst en huis.** Waar geboren, in welk dorp, gehucht of buurschap, en op welk
  huisnummer: `EventRemark` draagt dat bij vrijwel elke akte van de burgerlijke stand.
  Verhuizingen met een jaartal erbij; een jonger kind met een andere geboorteplaats dateert er
  vaak één._
- _**Werk en stand.** Het beroep zoals de klerk het schreef, per akte en mét het jaar: vier
  beroepen over vijftig jaar zijn een loopbaan, één beroep is een los feit. Standsaanduidingen
  liggen gratis in de bronnen: de impostklasse, `pro deo`, het bedrag in een haardstedegeld, en
  of iemand zelf tekende of een kruisje zette._
- _**Het huishouden.** Partner en huwelijksdatum, hoeveel kinderen er waren en hoeveel er
  jong stierven. ⚠ Broers en zussen van déze voorouder horen hier **niet** (zie
  `boek/zijtakken.md`)._
- _**Wat de krant zag.** Een advertentie, een boelgoed, een ongeluk, een jubileum: de
  krantenbanken zijn de enige plek waar deze mensen iets doen in plaats van geboren worden en
  sterven. Citaat plus knipsel._
- _**Het einde.** Sterfdag, plaats en leeftijd zoals de akte ze geeft, en wie er aangifte deed
  in welke hoedanigheid. ⚠ Een beroepsrol in een akte (aanspreker, buurman, gemeentewerkman)
  is geen verwantschap, ook niet bij dezelfde achternaam._

### Episode, jaartal

Tekst van de episode. De bron zegt het zo:

> het citaat, letterlijk, in de spelling van de akte of de krant

![Bron, datum: de kern in de woorden van de bron](../boek/verhalen/beeld/JJJJ-MM-DD-bron-onderwerp.jpg)

In gewone taal wat er staat en wat de oude woorden betekenen. Streekhistorie of een webbron
krijgt een voetnoot met URL en raadpleegdatum.[^bron]

[^bron]: Titel, auteur of instelling, <https://…> (geraadpleegd DD-MM-JJJJ).

## Tijdsbeeld

_Rampen, oorlog, epidemieën die dit leven raakten — één bestand per gebeurtenis in
`tijdsbeeld/`. Kandidaten opsporen: `py scripts/tijdsbeeld.py kandidaten <persoon-id>`.
Een koppeling is pas ✓ met een bron die persoon, gezin of adres direct noemt; wonen in
het getroffen gebied is ◐. Een afgemelde kandidaat krijgt hier de reden, kort. Geraakte
gebeurtenissen ook verweven in de Levensloop._

| Periode | Gebeurtenis | Raakvlak | Status |
|---------|-------------|----------|--------|

## Documenten

_Eén regel per gedownload stuk, met de link naar het beschrijvingsbestand en of de scan
werkelijk gelezen is._

| Aktedatum | Type | Beschrijving |
|-----------|------|--------------|

## Open vragen

_Elke vraag moet dicht voordat deze persoon wordt afgevinkt: óf met een antwoord, óf met een
expliciete sluiting ("niet gevonden in X, Y, Z" of "niet te vinden omdat …"), met de
commando's erbij. Een gesloten vraag blijft staan als `- [x]` met de uitkomst erachter,
zodat zichtbaar is dat er gezocht is. Een vraag die alleen in een studiezaal te beantwoorden
is, sluit je met de vindplaats als uitweg._

- [ ]

## Zwakke sporen

_Vermoedens die te dun zijn om een feit of zelfs een hypothese te zijn, maar te opvallend om
te vergeten. Hier staan ze geparkeerd met de reden waarom ze zwak zijn, zodat een volgende
ronde ze niet als nieuwe vondst aanziet en er ook niet op voortbouwt._

| Spoor | Waarom zwak | Wat het zou betekenen |
|-------|-------------|-----------------------|

## Onderzoekslog

_Elke regel reproduceerbaar, zodat een lezer het kan nachecken: gevonden records als
permalink (`[akte](https://www.openarchieven.nl/frl:…)`), zoekopdrachten — ook zonder
treffer — als volledig commando in `code`-opmaak, ook de krantenzoekopdrachten, webbronnen en
literatuur met volledige URL en raadpleegdatum. Zie CLAUDE.md, "Onderzoekslogs:
reproduceerbaar, met links"._

| Datum | Bron geraadpleegd | Resultaat |
|-------|-------------------|-----------|

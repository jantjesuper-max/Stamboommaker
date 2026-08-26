---
id: achternaam-voornamen-geboortejaar
naam:
geboren:            # DD-MM-JJJJ, plaats (ged. = gedoopt als geen geboortedatum bekend)
overleden:          # DD-MM-JJJJ, plaats
beroep:
woonplaatsen:       # - Plaats (van–tot), één regel per woonplaats; voedt scripts/tijdsbeeld.py
lijn:               # een van de familielijnen uit stamboom.json / boek/opzet.md
generatie:          # t.o.v. jezelf = 0; ouders = 1, grootouders = 2, enz.
status:             # ✓ | ◐ | ? | ⚠
vader: "[[id-vader]]"
moeder: "[[id-moeder]]"
partner: "[[id-partner]]"
kinderen:
  - "[[id-kind]]"
---

# Naam (geboortejaar–sterfjaar)

## Kerngegevens

| Feit | Gegeven | Bron | Status |
|------|---------|------|--------|
| Geboorte/doop | | | |
| Huwelijk | | | |
| Overlijden | | | |
| Beroep | | | |

## Levensloop

_Verhalende aantekeningen: waar woonde deze persoon, wat gebeurde er, tijdsbeeld.
Dit is de grondstof voor het boek._

_Broers en zussen van voorouders horen niet in dit dossier en niet in de stamboom — zie
`boek/zijtakken.md`. Zegt een vondst over hen iets over déze voorouder, dan gaat dat naar
`boek/verhalen/`; zo niet, dan één regel in het onderzoekslog onderaan._

## Tijdsbeeld

_Rampen, oorlog, epidemieën die dit leven raakten — één bestand per gebeurtenis in
`tijdsbeeld/`. Kandidaten opsporen: `py scripts/tijdsbeeld.py kandidaten <persoon-id>`.
Een koppeling is pas ✓ met een bron die persoon, gezin of adres direct noemt; wonen in
het getroffen gebied is ◐. Geraakte gebeurtenissen ook verweven in de Levensloop._

| Periode | Gebeurtenis | Raakvlak | Status |
|---------|-------------|----------|--------|

## Documenten

| Aktedatum | Type | Bestand | Transcriptie in dossier |
|-----------|------|---------|-------------------------|

## Open vragen

_Elke vraag moet dicht voordat deze persoon wordt afgevinkt: óf met een antwoord, óf met een
expliciete sluiting ("niet gevonden in X, Y, Z" of "niet te vinden omdat …"). Een gesloten
vraag blijft staan als `- [x]` met de uitkomst erachter, zodat zichtbaar is dat er gezocht
is._

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
treffer — als volledig commando in `code`-opmaak, webbronnen en literatuur met volledige
URL en raadpleegdatum. Zie CLAUDE.md, "Onderzoekslogs: reproduceerbaar, met links"._

| Datum | Bron geraadpleegd | Resultaat |
|-------|-------------------|-----------|

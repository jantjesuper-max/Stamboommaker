---
name: herzie
description: Herzie de pagina van één voorouder (of een hele lijn) die al een dossier heeft — meer onderzoek, de scans écht gelezen, de kranten doorzocht, knipsels erbij, en de pagina opnieuw opgezet met de levensloop centraal. Gebruik dit als de gebruiker een dossier of een website-link noemt en vraagt om "mooier maken", "meer onderzoek", "knipsels toevoegen", "pagina herzien", "deze lijn netter", of "doe zijn vader op dezelfde manier".
---

# Herzien — van dossier naar pagina

`/doorwerk` maakt dossiers; deze skill maakt er pagina's van. De aanleiding is bijna altijd
dezelfde zin: *"Kan je hier meer onderzoek naar doen, mooier maken, knipsels toevoegen en een
mooie levensloop."* De gebruiker noemt een persoon-id, een naam of een link van de website
(`…#/persoon/<id>`), en soms een hele lijn ("maak deze lijn netter", "en nu zijn vader op
dezelfde manier").

Lees vóór je begint `CLAUDE.md` (de gouden regel, "De dossierpagina: levensloop centraal",
"Kranten: verplicht bij elke voorouder", "Knipsels: laat de lezer de bron zien") en
`boek/stijlgids.md`. Het eindresultaat is een pagina zoals `personen/_TEMPLATE.md` die
beschrijft; de maat is: zou je deze pagina aan de keukentafel voorlezen?

**Wat herzien niet is:** feiten verzinnen om de pagina voller te maken, broers en zussen een
dossier geven, of oude metingen wissen. Een pagina wordt mooier door meer bron, niet door
minder eerlijkheid.

## De ronde — acht stappen per persoon

**1. Lees wat er ligt**

Het dossier, elk beschrijvingsbestand in `documenten/<id>/`, de verhalen waarin de persoon
voorkomt (`py scripts/verhalen.py lijst --persoon <id>`), de regels over hem in
`onderzoek/logboek.md` en `stamboom/overzicht.md`. Noteer voor jezelf: welke feiten rusten
op een gelezen akte, welke alleen op een index, welke op een online boom? Welke open vragen
zijn gesloten met "niet gevonden", en met welke commando's? Die sluitingen zijn van vóór de
laatste gereedschapsverbetering en dus een openstaande taak, geen conclusie.

**2. Lees de scans opnieuw, op volle resolutie**

Elke scan in `documenten/<id>/` die als "index" of "niet gelezen" staat, of waarvan de
transcriptie kort is: `py scripts/lees_scan.py overzicht <scan>` en dan `strook`, regel voor
regel. Inzoomen levert altijd iets op: het uur van de geboorte, het huisnummer, wie tekende en
wie "verklaarde niet te kunnen schrijven", een doorhaling, een kantmelding. Werk de
transcriptie en de samenvatting bij, en markeer de regels die je zou voorlezen onder
`## Citaatwaardig`. Controleer bij elke scan dat de akte er werkelijk op staat; een extra scan
kan een ander document zijn (een militieattest bij een huwelijk) en krijgt dan zijn eigen
naam.

**3. Zoek de registers die nog niet zijn aangeraakt**

Draai per persoon de ingangen die het dossier nog mist, en lees de rollen en leeftijden in
`toon`:

```
py scripts/zoek_openarch.py zoek "<naam> <geboortejaar>" --archief <code>      # alle records op de eigen naamvorm
py scripts/zoek_openarch.py zoek "<naam>" --brontype Bevolkingsregister          # huisnummer, vestiging, vertrek, inwonenden
py scripts/zoek_openarch.py zoek "<naam>" --brontype Notarieel                   # koop, schuld, boedel, voogdij, plaatsvervanging
py scripts/zoek_openarch.py zoek "<naam>" --brontype Militie                     # lotnummer, lengte, vrijstelling
py scripts/zoek_openarch.py zoek "<naam partner>"                                # de akten waarin hij alleen als man of vader staat
py scripts/zoek_openarch.py varianten "<naam>" --plaats <dorp>                   # de schrijfwijzen die je nog niet had
```

Elk bevolkingsregisterblad van het gezin is een vindplaats: het geeft de knechtenjaren, de
verhuisdatums, de buren en wie er inwoonde. Download alles wat je gebruikt met
`py scripts/download_scans.py <id>` en maak het beschrijvingsbestand. Een akte over een kind
of een partner die de voorouder bewijst, komt in zíjn map met de id van het kind in de
bestandsnaam (zie `CLAUDE.md`, "Documentnaamgeving").

**4. Kranten, per streek**

Volg `CLAUDE.md`, "Kranten: verplicht bij elke voorouder", en de tabel *Kranten per streek*
in `onderzoek/bronnengids.md`: Delpher met `AND` tussen de woorden, de regionale bank van de
streek, en spellingsvarianten. Zoek op naam + dorp, naam + beroep, de partner, de kinderen
(een familieadvertentie noemt hen met hun echtgenoten), en op de gebeurtenissen die de akten
geven (een verdrinking, een veiling, een jubileum, een vertrek). Lees elke treffer na op de
OCR en de scan. Dit is het werk dat de pagina een leven geeft; bij een lange sweep mag een
subagent het leeswerk doen, met de opdracht niets te wijzigen en alles met URL en datum terug
te melden. Zet elk commando in het onderzoekslog, ook bij nul.

**5. Knip wat je citeert**

Voor elk citaat dat in de pagina of in een verhaal komt: het knipsel, volgens `CLAUDE.md`,
"Knipsels: laat de lezer de bron zien". De geboorteakte met de handtekening van de vader, de
regel in het bevolkingsregister, de advertentie, de passage uit het contract. Knip het bericht,
niet de pagina; lees het eerst op de scan; noem bron en datum in het onderschrift. Een pagina
die is herzien heeft er doorgaans tussen de vijf en de twintig.

**6. Schrijf de pagina opnieuw**

Zet het dossier om naar de opbouw van `personen/_TEMPLATE.md`:

- de frontmatter vol: `beroep` met jaartallen, `woonplaatsen` met jaren en waaruit bekend,
  de statuscodes in `geboren`/`overleden`;
- titel met ondertitel, de vetgedrukte opening bij een moment, het knipsel van dat moment, het
  leven in vijf zinnen;
- kerngegevens die álles dragen wat je in stap 2 en 3 vond, met permalinks en status, en de
  tabel *De kinderen* als de registers een kinderrij geven;
- de levensloop in gedateerde episodes, met per episode het citaat en het knipsel, in de stem
  van de stijlgids. Streekhistorie (wat een *stelle* is, waarom iedereen op 12 mei verhuisde)
  krijgt een voetnoot met URL en raadpleegdatum;
- bij een ◐- of ?-identificatie het kopje *Waarom hij hier staat*;
- Tijdsbeeld bijgewerkt (`py scripts/tijdsbeeld.py kandidaten <id>`; nieuwe woonplaatsen geven
  nieuwe kandidaten), Documenten compleet, Open vragen opnieuw langsgelopen: wat nu beantwoord
  is krijgt het antwoord, wat nog open is krijgt de vindplaats als uitweg;
- Zwakke sporen en het Onderzoekslog aangevuld, met de oude regels intact.

**Verandert een lezing** (een ander beroep, een andere sterfdag, "hij pachtte" wordt "hij
bezat"), zet dan een ⚠-zin in de pagina die zegt wat er eerder stond, waarom het nu anders is,
en welke verhalen of dossiers daardoor mee moeten veranderen. Pas die ook aan.

**7. Verhalen, overzicht, kaart**

Elke vondst die je aan tafel zou vertellen krijgt een bestand in `boek/verhalen/` (sjabloon,
citaat, knipsel, `**Bron:**`), en bestaande verhalen over deze persoon krijgen de nieuwe
knipsels en de gecorrigeerde lezing. Dan `stamboom/overzicht.md` bijwerken als namen, datums
of statussen zijn veranderd, en:

```
py scripts/verhalen.py controleer && py scripts/verhalen.py index
py scripts/tijdsbeeld.py controleer && py scripts/tijdsbeeld.py index
py scripts/plaatsen.py
py test/controleer.py --fix
```

Bij problemen eerst oplossen. Nieuwe woonplaatsen krijgen met de hand een coördinaat in
`website/static/plaatsen.json`, met streekcontrole.

**8. Vastleggen**

Eén regel in `onderzoek/logboek.md` met wat de herziening opleverde, en één commit per
persoon, die zegt wat er nieuw is:

```
git rev-parse --show-toplevel
git add personen documenten stamboom onderzoek boek website/static/plaatsen.json
git commit -m "<Naam> (g<N>): pagina herzien; <de drie belangrijkste nieuwe dingen>"
```

## Doorgaan langs de lijn

Vraagt de gebruiker om een lijn ("maak deze hele lijn netter", "en nu zijn vader op dezelfde
manier"), dan ga je na de commit door met de volgende persoon in die lijn, omhoog, zonder
tussenvraag: vader, dan moeder, dan hun ouders. Stop bij het einde van de lijn, bij een
genoemd aantal, of als de gebruiker onderbreekt. Een voorouder met een dun dossier (een muur
van drie regels) wordt ook herzien: juist daar levert `varianten`, `bronnen` en de kranten
soms de doorbraak op die de eerste ronde niet had.

Werk je naast een andere sessie in dezelfde repo, noem dan de paden in `git add` en raak
alleen de dossiers van jouw persoon aan.

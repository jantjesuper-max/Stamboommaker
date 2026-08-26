# Boekopzet

**Werktitel:** _(staat in `stamboom.json` onder `boek.titel`; alternatieven verzamel je hier)_

**Voor wie:** _(vul in — voor je kind, voor de familie, voor jezelf. Dit bepaalt de toon
meer dan wat ook. Zie `stijlgids.md`.)_

**Wie schrijft:** de AI schrijft, in de stem van de keukentafelverteller uit `stijlgids.md`;
jij bent verteller, opdrachtgever en eindredacteur. Elk hoofdstuk is pas af als jij het
gelezen hebt.

## De grote lijn

_Hier komt in een paar regels waar dit boek over gaat: de beweging die alle lijnen samen
maken. Bij bijna elke Nederlandse familie is er zo'n beweging te vinden — van het land naar
de stad, van het veen naar de fabriek, van armoede naar een vak, van een dorp naar de
Randstad, of van over de grens naar hier._

_Zoek die beweging pas als je een paar generaties per lijn hebt staan. Verzin hem niet
vooraf: de feiten winnen altijd van de rode draad._

**Het patroon dat je zoekt:** elke lijn eindigt op dezelfde plek — daar waar dit boek wordt
verteld. Elk deel eindigt daarom met zijn *scharnier*: de stap, de verhuizing of het huwelijk
dat die lijn aan het geheel vastmaakt.

## Delen en rode draden

Eén deel per familielijn. De rode draad per deel is een **werkhypothese**: hij stuurt wat je
zoekt en hoe hoofdstukken op elkaar voortbouwen, maar de feiten winnen altijd. Spreekt een
vondst de draad tegen, dan stel je de draad bij — hier, in dit bestand — en nooit de feiten.

<!-- Vul aan zodra een lijn genoeg dossiers heeft. Zo ziet een ingevuld deel eruit:

1. **Achternaam — drie generaties arbeider.** Wat de aktes zeggen over het werk: vader, zoon
   en kleinzoon staan alle drie als *arbeider* in de registers — het woord voor wie zijn
   handen verhuurde en geen grond had. Pas de generatie daarna krijgt een vak. De voornaam
   die vier generaties meereist. *Scharnier:* de verhuizing van 1904 en de vroege dood in
   het nieuwe dorp (hoofdstuk 01).
-->

| Deel | Lijn | Rode draad | Scharnier | Dossiers |
|------|------|------------|-----------|----------|
| | | | | |

## Van dossier naar hoofdstuk

Zo wordt een dossier tekst. Dit is het recept; elk hoofdstuk is een herhaling ervan.

| Dossierdeel | Voedt in het hoofdstuk |
|-------------|------------------------|
| Kerngegevens (datums, plaatsen, beroep) | het geraamte: wanneer, waar, wat voor werk |
| Levensloop | de scènes en de volgorde van het verhaal |
| Tijdsbeeld | wat er om dit leven heen gebeurde; nooit als decor, alleen met bron |
| Documenten → `## Citaatwaardig` | de citaatblokken: de bron zelf aan het woord |
| Onderzoekslog | de voetnoten, en soms het verhaal van de zoektocht zelf |
| Open vragen | de losse draden waarmee een hoofdstuk mag eindigen |
| Zwakke sporen | niets — die horen niet in het boek |

En zo vertaalt een status zich naar taal:

| Status | In de tekst |
|--------|-------------|
| ✓ bewezen | gewoon vertellen: "hij trouwde op 14 mei 1865" |
| ◐ waarschijnlijk | "vermoedelijk", "vrijwel zeker", met in de voetnoot waarom |
| ? hypothese | benoemen als vraag: "wie zijn vader was, weten we niet" |
| ⚠ naamgenoot | het probleem zelf vertellen — dat is vaak een goed verhaal |

## Hoofdstukken

Nieuw hoofdstuk: kopieer `hoofdstukken/_TEMPLATE.md` naar
`hoofdstukken/NN-korte-titel.md` (het nummer bepaalt de volgorde). Bouwen:
`py scripts/bouw_boek.py` plakt alles aan elkaar tot `boek/manuscript.md`, en met pandoc
erbij ook een Word-bestand.

| Nr | Titel | Deel | Personen | Status |
|----|-------|------|----------|--------|
| | | | | |

Status: `opzet` · `geschreven` · `gelezen` · `af`.

## Wat er nog aan verhalen ligt

Losse vondsten wachten in `boek/verhalen/`, met een score voor hoe bijzonder ze zijn.
Voordat je een hoofdstuk begint, vraag wat er ligt:

```
py scripts/verhalen.py lijst --deel 1 --onverwerkt
py scripts/verhalen.py index
```

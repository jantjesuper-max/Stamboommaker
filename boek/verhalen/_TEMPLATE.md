---
titel: Korte pakkende titel, geen samenvatting
rubriek: verlies          # verlies | migratie | werk | krant | raadsel | namen | bureaucratie | verband | geloof | geld | tijdsbeeld
deel: 1                   # nummer uit boek/opzet.md; 0 = nog geen deel
lijn: Achternaam          # een familielijn uit stamboom.json, of 'meerdere'
periode: 1865             # jaar of "1830-1850"
personen:
  - "[[persoon-id]]"
sterkte: sterk            # sterk = uit aktes | mager = deels bron | vermoeden = nog niet bewezen
score: 12                 # 1-20, hoe bijzonder — 1-4 administratief · 5-8 informatief
                           # · 9-12 opvallend · 13-16 bijzondere wending · 17-20 uitzonderlijk
landing: onverwerkt       # onverwerkt | hoofdstuk-01 | opzet.md | ...
gevonden: DD-MM-JJJJ
---

De vondst in een paar alinea's, in gewone taal — nog geen boekproza, maar wel zo
opgeschreven dat je het over een jaar nog begrijpt. Zeg expliciet wat vaststaat en wat nog
vermoeden is.

Is er een citeerbare passage, laat de bron dan zelf aan het woord: eerst één regel die zegt
waar de woorden vandaan komen, dan het citaat in de spelling van de akte, dan in gewone taal
wat er staat. Notariële aktes leveren hier het meeste op. Kijk in
`documenten/<persoon-id>/*.md` (kopje `## Citaatwaardig`) wat er al ligt.

> De notaris zegt het zo, in de spelling van 1812: […]

![Bron, datum: de kern in de woorden van de bron](beeld/JJJJ-MM-DD-bron-onderwerp.jpg)

En laat de lezer de bron zíen: het krantenbericht, de advertentie of het stuk akte dat je
citeert komt er als knipsel bij, vlak onder het citaat, gemaakt met
`py scripts/knipsel.py <scan> <x> <y> <breedte> <hoogte> <JJJJ-MM-DD-bron-onderwerp>`. Het
onderschrift noemt bron en datum en de kern in de woorden van de bron. Knip precies het
bericht, niet de pagina. Zie CLAUDE.md, "Knipsels: laat de lezer de bron zien".

Geen letterlijke passage gevonden? Dan geen citaat en geen knipsel. Verzin er nooit een. Zie
`boek/stijlgids.md`, "Citeer de bron letterlijk".

**Bron:** volledige bronvermelding of dossierverwijzing — krant, datum, pagina en URL, of
archief, toegang, inventarisnummer, akte en permalink. Het knipsel vervangt dit niet. Zonder
bron geen verhaal.

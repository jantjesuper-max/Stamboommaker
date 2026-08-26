<!-- stamboommaker:plaatshouder -->
# Werklijst dossiers — de afstreeplijst

**Dit bestand is een plaatshouder.** Draai `py instellen.py` en het wordt vervangen door een
werklijst met een sectie per familielijn. Daarna vult `/opstarten` de regels.

---

Elke voorouder uit `stamboom/overzicht.md` staat hier één keer. Dit is de werkvoorraad van
de doorwerk-skill. De **volgorde** bepaalt `py test/controleer.py`: na elk afgerond dossier
zijn de óuders van die persoon aan de beurt (omhoog, diepste generatie eerst), bij een
muurvaste lijn gaat de route opzij naar de diepste open tak, en de lijstvolgorde hieronder
is alleen de terugval. Bovenaan een lijn probeert de skill de ontbrekende ouders te
vínden — gevonden voorouders komen er hier als nieuwe regels bij, dus deze lijst groeit.

**Regelformat:** `- [ ] gN · persoon-id — Naam (jaren) status`
`gN` = generatie t.o.v. jezelf = g0; ouders = g1, grootouders = g2.
Status: ✓ bewezen · ◐ waarschijnlijk · ? hypothese · ⚠ naamgenoot-gevaar.
Markeringen achter een regel: `· muur DD-MM-JJJJ` (lijn-top, ouders niet gevonden — zie
logboek) en `· overgeslagen: <reden>` (route slaat deze over; periodiek herzien).

**Afvinken mag pas als:** dossier bestaat volgens `personen/_TEMPLATE.md`, vader/moeder/partner
als wikilinks ingevuld, minstens één archiefbron gezocht (gevonden óf `[niets gevonden]`),
het onderzoekslog in het dossier is bijgewerkt, en elke open vraag is gesloten.

Voortgang: **0 / 0** afgevinkt. (Bijwerken met `py test/controleer.py --fix`.)

---

## Vaderskant — Achternaam

<!-- Zo zien ingevulde regels eruit:
- [x] g2 · bakker-hendrik-1901 — Hendrik Bakker (1901-1978) ✓ · schipper
- [x] g3 · bakker-jan-1870 — Jan Bakker (ca.1870-1941) ◐ · muur 04-03-2026 · doopboek nog niet ingezien
- [ ] g3 · de-boer-anna-1872 — Anna de Boer (ca.1872-1939) ?
-->

## Moederskant — Achternaam

---
name: opstarten
description: Zet een verse Stamboommaker-kloon om in een werkend stamboomproject: vraagt uit wat de gebruiker van zijn familie weet, en bouwt daaruit de stamboom, de werklijst en de eerste dossiers. Gebruik dit bij "opstarten", "beginnen", "mijn stamboom invullen", "eerste keer", of wanneer stamboom.json of de werklijst nog leeg is.
---

# Opstarten — van lege repo naar werkend onderzoek

Dit is de eerste sessie van een nieuw project. Aan het eind moet er een stamboom staan met
alles wat de gebruiker uit zijn hoofd en uit zijn papieren weet, en moet `/doorwerk` kunnen
beginnen met archiefonderzoek.

**Het gesprek is het werk.** Niet één lange vragenlijst afvuren, maar één onderwerp per keer,
en tussendoor vastleggen wat je hebt. Iemand die zich zijn oma herinnert, herinnert zich vaak
tien minuten later ook nog de naam van háár moeder.

Lees eerst `CLAUDE.md` (de conventies en de gouden regel). Wat de gebruiker vertelt is een
**mededeling, geen akte**: het gaat er als `◐` of `?` in, niet als `✓`. Dat is geen
wantrouwen — familieverhalen zitten er vaak een generatie of een dorp naast, en `/doorwerk`
gaat het later bewijzen.

## Stap 1 — de instellingen

Kijk of `stamboom.json` er al is:

```
py instellen.py --toon
```

Staat er niets, dan haal je in het gesprek op wat er nodig is (volledige naam, geboortejaar,
geboorteplaats, werktitel van het boek, naam boven de website, de achternamen van de
familielijnen) en zet je het in één keer neer:

```
py instellen.py --naam "Voornaam Achternaam" --jaar 1990 --plaats "Plaats" --lijnen "Achternaam,Meisjesnaam" --stil
```

Laat de gebruiker het niet zelf interactief invullen als je het gesprek toch al voert — dat is
dubbel werk. Vraag wel expliciet naar de werktitel van het boek en voor wie het bedoeld is; dat
laatste zet je in `boek/opzet.md` onder **Voor wie**, want het bepaalt de toon van alles wat er
later geschreven wordt (zie `boek/stijlgids.md`).

## Stap 2 — het interview

Werk van jong naar oud, één generatie per keer. Vraag per persoon wat er bekend is: **volledige
naam, geboortedatum en -plaats, sterfdatum en -plaats, beroep, waar ze woonden, en met wie ze
trouwden.** "Ongeveer 1920" en "ergens in Friesland" zijn goede antwoorden — schrijf ze zo op.

De vaste vragen die het meeste opleveren:

1. **Je ouders** — namen, geboortejaren, geboorteplaatsen, de meisjesnaam van je moeder.
2. **Je grootouders** — vier mensen. Meestal weet iemand hier nog van alles: beroepen,
   woonplaatsen, wanneer ze stierven.
3. **Je overgrootouders** — acht mensen. Hier houdt het geheugen vaak op, en precies daar
   begint het archiefwerk. Ook een half antwoord ("de vader van oma kwam uit Groningen, hij
   was schipper") is genoeg om mee te zoeken.
4. **Hebben jullie papieren in huis?** Dit is de belangrijkste vraag van het hele gesprek. Een
   trouwboekje, bidprentjes, een rouwkaart, een militair zakboekje, een schoolrapport, een
   persoonsbewijs uit de oorlog, foto's met iets op de achterkant, een oude stamboom die een
   oom eens maakte. Zulke stukken staan nergens online en zijn vaak beter dan wat een archief
   geeft. Zeg dat ze die kunnen fotograferen en in `documenten/inbox/` zetten; dan verwerk je ze
   ("verwerk de inbox", zie `CLAUDE.md`).
5. **Wie leeft er nog die het kan weten?** Een oudtante van tweeëntachtig is een bron met een
   houdbaarheidsdatum. Zet die vragen in `onderzoek/open-vragen.md` onder "Vragen die alleen de
   familie kan beantwoorden", en zeg erbij dat dit voorgaat op archiefwerk.
6. **Is er al eens iets uitgezocht?** Een bestaande stamboom op Genealogieonline of een
   GEDCOM-bestand van een familielid scheelt maanden. Behandel het als **aanwijzing**, nooit als
   bron: overnemen mag, maar als `◐`/`?` met de herkomst erbij.

**Vraag niet door tot in het oneindige.** Zodra iemand drie keer "dat weet ik niet" zegt, is die
lijn klaar voor het archief. Dat is geen mislukking; dat is waar `/doorwerk` voor is.

## Stap 3 — vastleggen

Doe dit *tijdens* het gesprek, niet aan het eind — dan raakt niets kwijt als de sessie afbreekt.

**Levende personen: terughoudend.** Zet van iemand die nog leeft alleen wat de gebruiker zelf
aanlevert, en geen geboortedata of adressen. Een regel op de werklijst met alleen een naam is
genoeg; het dossier komt er later, als het mag. Zie de sectie "Levende personen" in `CLAUDE.md`.

Per persoon, in deze volgorde:

1. **Werklijstregel** in `onderzoek/werklijst-dossiers.md`, in de sectie van de juiste lijn:
   `- [ ] gN · persoon-id — Naam (jaren) status`. Generatie is het aantal stappen vanaf de
   gebruiker (ouders = g1, grootouders = g2). ID volgens de conventie in `CLAUDE.md`.
2. **Dossier** in `personen/<id>.md` uit `personen/_TEMPLATE.md`, voor iedereen die overleden
   is en van wie je meer weet dan alleen een naam. Frontmatter volledig vullen; wat je niet weet
   laat je leeg, niet gevuld met een gok. Zet de mondelinge herkomst in het onderzoekslog:
   *"05-03-2026 · mondeling, [naam gebruiker] · geboortejaar en beroep · nog geen akte gezien"*.
   Vink het dossier **niet** af: er is nog geen archiefbron.
3. **Overzicht** — bouw `stamboom/overzicht.md` op tot de kwartierstaat die je nu kent, in de
   ASCII-vorm die er al staat. Doe dit één keer aan het eind van een lijn, niet per persoon.

Alleen **directe voorouders**: vaders en moeders, generatie na generatie. Broers, zussen, ooms
en tantes horen er niet in — zie `boek/zijtakken.md`. Komen ze in het gesprek voorbij met een
mooi verhaal, dan is dat een bestand in `boek/verhalen/`, geen dossier.

## Stap 4 — de kalender op de eigen streek zetten

`tijdsbeeld/_KALENDER.md` wordt geleverd met regio's op provincieniveau. Zet nu de **dorpen en
steden** erbij die in het interview zijn gevallen, in de regiotabel bij de juiste provincie —
het script matcht op deelstrings, dus een dorpsnaam erbij zetten is genoeg.

Is één streek belangrijk voor een hele lijn, maak er dan een eigen, kleinere regio van
(`friesland-zuidwest`, `kop-overijssel`, `west-friesland`) en zet de gebeurtenissen die daar
speelden op die regio. Een kleinere regio geeft veel scherpere kandidaten dan een hele
provincie.

Controleren:

```
py scripts/tijdsbeeld.py controleer
```

## Stap 5 — de bronnengids op de eigen streek zetten

Zoek per streek het **streekarchief** op dat de bevolkingsregisters en de plaatselijke kranten
heeft, en zet naam en URL in `onderzoek/bronnengids.md` onder "Jouw regio's". Dat is een paar
minuten werk en het scheelt elke volgende ronde tijd.

## Stap 6 — meten en overdragen

```
py test/controleer.py
```

Dit moet zonder problemen doorlopen en eindigen met wie er aan de beurt is. Lost een probleem
niet op, repareer het dan nu — een scheve werklijst zit `/doorwerk` alle rondes daarna in de weg.

Zet de website even aan zodat de gebruiker ziet wat er staat:

```
py website/server.py
```

Sluit af met een korte vertelling van wat er nu ligt, en wat er hierna gebeurt:

- hoeveel voorouders er op de werklijst staan en hoeveel generaties diep de boom komt;
- welke lijn het verst terug gaat, en welke het eerst vastloopt;
- de openstaande familievragen uit `onderzoek/open-vragen.md` — **met de nadruk dat die het
  eerst moeten**, want daar loopt de klok;
- dat `/doorwerk` nu het archiefwerk kan doen, voorouder na voorouder, en dat dat uren of
  nachten achter elkaar door kan lopen.

Vraag tot slot of ze meteen willen doorwerken. Zo ja: begin aan `/doorwerk` en stel geen
verdere vragen.

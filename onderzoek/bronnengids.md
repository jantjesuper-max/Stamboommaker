# Bronnengids per regio

> **Wiki's zijn geen bronnen.** Genealogieonline, Geni, StamboomNederland, Geneanet en
> Wikipedia mogen een spoor opleveren, maar een feit wordt pas `✓` als het in een register
> staat: een akte, doopboek, bevolkingsregister, notariële akte, haardstedenregister.
> Ga altijd door naar het archief hieronder.

Welke archieven en websites raadpleeg je voor welke tak. Bij elke zoekactie: het resultaat
(**óók** "niets gevonden") vastleggen in `logboek.md`. Scans waar mogelijk downloaden naar
`documenten/` volgens de conventies in `CLAUDE.md`.

**Deze gids groeit met je onderzoek.** Kom je een archief, register, website, boek of
zoekingang tegen die hier niet staat, voeg hem dan in dezelfde ronde toe: bij de juiste
regio, met één regel over waar hij goed voor is en wat je er concreet in vond. Datzelfde
geldt voor een register dat blijkt te **ontbreken** of achter een betaalmuur zit — dat hoort
er ook bij, zodat een volgende ronde er geen tijd aan verliest. Voeg per streek ook de
**inventarisnummers** toe die je gebruikt hebt (welk deel dekt welk dorp); dat is precies de
kennis die je anders elke keer opnieuw opzoekt.

---

## Landelijk (Nederland)

- **Open Archieven** — openarchieven.nl — aggregator van tientallen archieven, vaak met
  scanlinks en permalinks. **Dit is de eerste ingang**, en er zit een script bij:
  `py scripts/zoek_openarch.py`. Geen API-key nodig
- **WieWasWie** — wiewaswie.nl — tweede brede ingang op de burgerlijke stand 1811-1950;
  heeft soms wat Open Archieven niet heeft en omgekeerd
- **FamilySearch** — familysearch.org — gratis (account nodig), heel veel gescande
  registers, ook DTB waar de Nederlandse indexen ophouden. Onmisbaar vóór 1811
- **Delpher** — delpher.nl — kranten, boeken en tijdschriften. Overlijdensadvertenties,
  ongelukken, faillissementen, veilingen, gemeenteberichten, stakingen. Geeft zelden een
  datum die je nog niet had, maar bijna altijd het verhaal eromheen
- **CBG Centrum voor familiegeschiedenis** — cbg.nl — familieadvertenties, bidprentjes
  (in katholieke streken goud waard), heraldiek, persoonskaarten na 1938
- **Nationaal Archief** — nationaalarchief.nl — o.a. de VOC- en marinebronnen, notariële
  archieven van Zuid-Holland, en de index op de militieregisters
- **Oorlogsbronnen** — oorlogsbronnen.nl — de gezamenlijke ingang op alles rond 1940-1945:
  onderduik, razzia's, Arbeitseinsatz, kampen, verzet, oorlogsslachtoffers
- **online-begraafplaatsen.nl** en **graftombe.nl** — grafstenen en begraafplaatsadministratie
- **Openarch permalinks zijn geïndexeerd door Google.** Een gewone websearch op
  `"naam" genealogie` vindt daardoor vaak precies de akte die je zoekt

## Per provincie — waar de scans liggen

Elke provincie heeft een eigen portaal. Die zijn vaak vollediger dan de landelijke
aggregators, en ze hebben de scans.

| Streek | Portaal | Sterk in |
|--------|---------|----------|
| Friesland | allefriezen.nl (Tresoar) | BS + DTB met scans; naamsaannemingsregisters 1811; gevangenisregisters |
| Groningen | allegroningers.nl | BS + DTB met scans |
| Drenthe | alledrenten.nl | BS + DTB; veenkoloniën |
| Overijssel | collectieoverijssel.nl | BS + DTB; kop van Overijssel |
| Gelderland | Gelders Archief, gelderlandinbeeld.nl | BS, DTB, rechterlijke archieven |
| Utrecht | hetutrechtsarchief.nl | BS + DTB met scans |
| Noord-Holland | noord-hollandsarchief.nl, westfriesarchief.nl | BS, DTB, notarieel |
| Zuid-Holland | erfgoedleiden.nl, archiefleiden, streekarchieven per regio | BS, DTB; IIIF-scans (zie CLAUDE.md) |
| Zeeland | zeeuwengezocht.nl (Zeeuws Archief) | BS + DTB; Krantenbank Zeeland |
| Noord-Brabant | bhic.nl, regionaalarchieftilburg.nl | BS, DTB, notarieel; goed ontsloten |
| Limburg | rhcl.nl | BS + DTB |

Zoek het **streekarchief** van het dorp erbij: die hebben de bevolkingsregisters, de
gemeenteverslagen, de bouwtekeningen en de plaatselijke kranten die geen enkel landelijk
portaal heeft. Zet de naam en de URL hieronder zodra je hem hebt gebruikt.

## Buiten Nederland

- **België** — search.arch.be (Rijksarchief, gratis, veel scans), en per provincie de
  gemeentearchieven. Voor Vlaanderen ook **Geneanet** en de parochieregisters
- **Duitsland** — **Archion** (archion.de, betaald, kerkboeken) en **Ancestry**;
  voor Oost-Friesland het Landesarchiv en de Ostfriesische Landschaft
- **Verenigde Staten** (voor wie vertrok) — Ellis Island-passagierslijsten,
  census-jaren via FamilySearch, en de vertrekregisters aan Nederlandse kant

---

## De bronnen die verder gaan dan datums

Deze registers geven wat een geboorteakte niet geeft: een beroep, een lichaam, een
verhuizing, een schuld, een misstap. Loop ze langs bij elke voorouder — niet alleen als je
vastloopt.

- **Bevolkingsregisters en gezinskaarten** (bij het streekarchief; deels in Open Archieven).
  Hierin staat het hele huishouden op één blad, met verhuizingen, beroepen en geloof. Het
  `EventRemark`-veld in de API geeft het **kaartnummer**, en dat is wat je nodig hebt om de
  kaart bij het archief op te vragen
- **Notariële archieven.** Boedelscheidingen, voogdijstellingen, testamenten,
  schuldbekentenissen, koop- en huurcontracten, plaatsvervangingen. **Dit is waar arme
  families toch uitgebreid op papier komen, met bedragen en bezittingen erbij.** De index
  noemt vaak de aktesoort en soms een hele alinea samenvatting — dat is al bruikbaar zonder
  de akte te lezen. Zoek met `--brontype Notarieel` en `--type "Notariële inschrijving"`
- **Militieregisters en stamboeken.** Signalement, lengte, beroep, geletterdheid, ouders.
  Voor een man geboren tussen ongeveer 1770 en 1800 is het register van de troepen onder
  Napoleon een vaste halte; het opmerkingenveld geeft daar soms een hele biografie
- **Huwelijksbijlagen** (na 1811). Daar zitten geboorteaktes van de ouders in, en soms een
  overlijdensakte of een militieattest. **De goedkoopste manier om een generatie terug te
  komen**
- **Gevangenisregisters.** Naam met patroniem, **beide ouders**, geboorteplaats, laatste
  woonplaats, leeftijd, burgerlijke staat, beroep, gezindte, **lengte in centimeters**, een
  volledig signalement, of iemand lager onderwijs had genoten, en soms de handtekening.
  Vaak het rijkste document over een arme voorouder dat er bestaat
- **Lidmatenregisters** van hervormde gemeenten — noemen óók vrouwen bij naam. **Dit is de
  ingang voor een voorouder die uit de lucht komt vallen:** wie naar een andere gemeente
  verhuisde werd daar met een **attestatie** van zijn oude kerk aangenomen, en die
  inschrijving noemt de **plaats van herkomst**
- **Quotisatiekohieren, haardstedenregisters, verpondingen** — belastinglijsten van vóór
  1811. Ze noemen het gezinshoofd, het aantal personen, en of iemand kon betalen. Vaak de
  enige plek waar een achttiende-eeuwse arbeider met naam staat
- **Weeskamerarchieven** — bij een overleden ouder werd een voogd benoemd en de bezittingen
  opgeschreven. Een inventaris van een sterfhuis is de meest concrete bron die er is
- **Het trouwboek zelf, op de studiezaal.** De index laat weg wat er in het boek wél staat:
  bij een bruid of bruidegom van buiten noteerde de koster vaak de herkomst ("van Warns",
  "van Balk"). Bij een muur is dat soms het enige wat nog opengaat

## Voor het verhaal, niet voor het bewijs

- **Streekhistorie:** regionale historische verenigingen, dorpswebsites, uitgegeven
  streekboeken. Vaak schreef iemand al een boek over precies het dorp en het beroep van je
  voorouder
- **Google Books** en **DBNL** voor oudere lokale geschiedschrijving
- **Beroepsgeschiedenis** — wat deed een turfmaker, pannenbakkersknecht, dienstbode of
  hellingbaas concreet? Zoek daar apart op; het is de grondstof voor de scènes die
  `boek/stijlgids.md` vraagt
- **Kadaster en historische kaarten** (topotijdreis.nl, hisgis.nl) — waar stond het huis,
  hoe ver was het naar de kerk, waar lag het veen

Zulke bronnen zijn zelden bewijs voor een datum, wél bron voor het verhaal. Neem ze op met
volledige verwijzing en noem in het verhaalbestand eerlijk dat het streekhistorie is en
geen akte.

## Tijdsbeeld

Voor de gebeurtenissen uit `tijdsbeeld/_KALENDER.md`:

- **Delpher** voor kranten — de eerste ingang bij elke ramp, staking of epidemie
- **Overlijdensregisters als meetinstrument.** Een sterftepiek in één dorp in één jaar is de
  hardste plaatselijke aanwijzing die er is voor een epidemie
- **Gemeenteverslagen** en de *Verslagen aan den Koning betrekkelijk den staat der Openbare
  Gezondheid* — per gemeente per jaar, met sterftecijfers en oorzaken
- **Schadecommissie-archieven** na een watersnood: die noemen namen en bedragen
- **watersnoodmuseum.nl** (slachtofferregister 1953), **oorlogsbronnen.nl** (1940-1945)

---

## Jouw regio's

_Voeg hieronder een kop per streek toe waar je voorouders wonen, met de archieven,
inventarisnummers en zoekingangen die je daar hebt gebruikt. Wat je hier opschrijft hoef je
nooit meer op te zoeken._

<!-- Voorbeeld van hoe zo'n kop eruitziet als hij is ingevuld:

## Friesland — lijn Achternaam

- **AlleFriezen** — allefriezen.nl — BS + DTB met scans; zoek bij overlijden op de
  **dorpsnaam**, niet op de gemeente
- **Register van familienamen 1811** (Tresoar): deel 0081 dekt dorp A, B en C; deel 0024
  dekt dorp D en E. Noemt de kinderen mét leeftijd — een van de sterkste bronnen voor
  gezinssamenstelling rond 1811
- ⚠ **DTB Begraven van deze grietenij is niet ontsloten** — een overlijden vóór 1811 is met
  de index niet te vinden; dat is geen muur maar een verkeerde ingang
-->

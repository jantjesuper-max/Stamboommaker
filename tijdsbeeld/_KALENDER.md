# Kalender van gebeurtenissen — wat het land deed terwijl zij leefden

Rampen, oorlogen, epidemieën en crises die de streken van je voorouders raakten.
`py scripts/tijdsbeeld.py kandidaten <persoon-id>` legt deze kalender naast de leefjaren
en woonplaatsen van een dossier en noemt wat er onderzocht moet worden.

**Dit zijn zoekaanwijzingen, geen feiten over personen.** Dat de stormvloed van 1825 de
Zuiderzeekust onder water zette is geschiedenis; dat hij óns gezin raakte is pas ✓ als een
bron persoon, gezin of adres noemt (schadelijst, krantenbericht, akte). Aantoonbaar wonen in
het getroffen gebied is ◐. Alleen tijdsoverlap is geen koppeling.

**Gewicht: alleen grote gebeurtenissen komen in de dossiers.** Elke regel heeft een gewicht:

- `groot` — een gebeurtenis die levens zichtbaar omgooide (dijkdoorbraak, oorlog, dodelijke
  epidemie, staking in het eigen dorp). Deze kandidaten worden **elke ronde echt
  onderzocht**: gekoppeld of beargumenteerd afgemeld.
- `achtergrond` — tijdskleuring (duurte, crisis, strenge winter). Niet koppelen en niet
  afmelden; alleen een koppeling maken als het onderzoek toevallig een **concreet spoor**
  oplevert (een krantenbericht met naam, een verhuizing die erdoor verklaard wordt). Wel
  vrij te gebruiken als sfeertekening in de Levensloop, zonder koppeling.

Bij gebied `landelijk` is tijdsoverlap nooit genoeg voor een koppeling — ook niet bij
`groot`: zoek het plaatselijke of persoonlijke spoor (sterftepiek in het dorp,
militie-inschrijving, verlies in het gezin, bericht over de woonplaats).

**De kalender groeit, en dat is de bedoeling.** Deze lijst is landelijk en provinciaal; de
gebeurtenissen die jouw familie werkelijk raakten zijn vaak plaatselijk. Vind je een
dorpsbrand, dijkdoorbraak, bombardement, ontploffing of gezonken schip: voeg hier een regel
toe met soort `plaatselijk` en het dorp als gebied, of maak direct een gebeurtenisbestand in
deze map. Landelijke gebeurtenissen die hier nog missen mogen er ook bij — met periode en
gebied zo precies mogelijk.

## Regio's

Plaatsnamen klein geschreven. Het script vergelijkt op **hele woorden**: »alphen« vindt ook
»Alphen aan den Rijn« en »koudekerk« ook »Koudekerk aan den Rijn«, want de toevoeging staat
achteraan. Een toevoeging vóóraan maakt juist een ándere plaats, dus »amsterdam« vindt niet
»Nieuw-Amsterdam« en »echt« (Limburg) niet »Utrecht«.

**Dit is een startset op provincieniveau.** Zet je eigen dorpen
erbij — of maak een eigen, kleinere regio aan zodra een streek belangrijk wordt in je
onderzoek (`friesland-zuidwest`, `kop-overijssel`, `west-friesland`, `rijnstreek`): een
kleinere regio geeft scherpere kandidaten dan een hele provincie.

| Regio | Plaatsen |
|-------|----------|
| friesland | leeuwarden, sneek, heerenveen, drachten, dokkum, harlingen, franeker, bolsward, workum, stavoren, lemmer, wolvega, oosterwolde, gorredijk, joure, grou, burgum, sint annaparochie, holwerd, ameland, terschelling, vlieland, schiermonnikoog |
| groningen | groningen, appingedam, delfzijl, winschoten, veendam, hoogezand, sappemeer, stadskanaal, ter apel, leek, zuidhorn, uithuizen, bedum, loppersum, pekela, oude pekela, nieuwe pekela, vlagtwedde |
| drenthe | assen, meppel, hoogeveen, emmen, coevorden, roden, beilen, smilde, dwingeloo, diever, havelte, zuidlaren, gieten, borger, klazienaveen, nieuw-amsterdam, erica |
| overijssel | zwolle, deventer, enschede, hengelo, almelo, kampen, steenwijk, oldenzaal, rijssen, raalte, ommen, hardenberg, dalfsen, vollenhove, blokzijl, giethoorn, wanneperveen, staphorst |
| gelderland | arnhem, nijmegen, apeldoorn, ede, doetinchem, zutphen, harderwijk, tiel, culemborg, zevenaar, winterswijk, wageningen, barneveld, elburg, lochem, groenlo |
| utrecht | utrecht, amersfoort, veenendaal, zeist, nieuwegein, woerden, montfoort, ijsselstein, rhenen, wijk bij duurstede, bunschoten, breukelen, maarssen |
| noord-holland | amsterdam, haarlem, alkmaar, hoorn, enkhuizen, zaandam, hilversum, purmerend, den helder, edam, medemblik, andijk, wervershoof, texel, beverwijk, weesp, naarden, monnickendam |
| zuid-holland | rotterdam, den haag, leiden, dordrecht, delft, gouda, alphen, koudekerk, oudshoorn, aarlanderveen, woubrugge, bodegraven, zwammerdam, hazerswoude, ter aar, katwijk, noordwijk, schiedam, vlaardingen, gorinchem, brielle, goeree, overflakkee |
| zeeland | middelburg, vlissingen, goes, terneuzen, hulst, zierikzee, tholen, sluis, oostburg, axel, kapelle, borsele, schouwen, walcheren, zuid-beveland, noord-beveland, hontenisse, kloosterzande |
| noord-brabant | eindhoven, tilburg, breda, den bosch, s-hertogenbosch, helmond, roosendaal, bergen op zoom, oss, waalwijk, uden, veghel, boxtel, valkenswaard, cuijk |
| limburg | maastricht, venlo, sittard, heerlen, roermond, weert, kerkrade, geleen, venray, gennep, echt, valkenburg |
| belgie-vlaanderen | antwerpen, gent, brugge, sint-niklaas, beveren, kallo, mechelen, aalst, oostende, kortrijk, hasselt, leuven, dendermonde, lokeren |
| duitsland-noordwest | emden, norden, aurich, leer, arle, oldenburg, bremen, wilhelmshaven, papenburg, meppen |

## Gebeurtenissen

Gebied: regionamen uit de tabel hierboven, losse plaatsnamen, of `landelijk` (raakt iedereen
die toen leefde). Periode: `JJJJ` of `JJJJ-JJJJ`. Gewicht: `groot` of `achtergrond`.

| Id | Periode | Gebeurtenis | Soort | Gewicht | Gebied | Zoekingang |
|----|---------|-------------|-------|---------|--------|------------|
| 1636-pest | 1635-1637 | Pestepidemie: zware sterfte in de steden van Holland en Utrecht | epidemie | groot | noord-holland, zuid-holland, utrecht | begraafboeken (sterftepiek), stadsarchieven, literatuur |
| 1672-rampjaar | 1672-1673 | Rampjaar: invasie door Frankrijk, Münster en Keulen; het platteland geplunderd, steden bezet, de Hollandse Waterlinie onder water | oorlog | groot | landelijk, gelderland, overijssel, utrecht | literatuur, stadsarchieven, resoluties |
| 1713-runderpest | 1713-1720 | Runderpest, eerste grote golf: veestapels geruimd, veehouders verarmd | veepest | achtergrond | landelijk | dorpsrekeningen, literatuur |
| 1717-kerstvloed | 1717 | Kerstvloed 24-25 december: de zwaarste stormvloed van de noordkust; duizenden doden in Groningen en Oost-Friesland | ramp | groot | groningen, friesland, duitsland-noordwest | begraafboeken, schadelijsten, literatuur |
| 1731-paalworm | 1730-1732 | Paalworm vreet de houten zeeweringen aan: paniek en dure dijkverzwaring, hoge omslagen voor de boeren | economie | achtergrond | friesland, noord-holland, zeeland | dijkrekeningen, literatuur |
| 1744-runderpest | 1744-1765 | Runderpest, tweede golf — de zwaarste; hele stallen dood | veepest | groot | landelijk | dorpsrekeningen, quotisatiekohieren, literatuur |
| 1747-pachtersoproer | 1747-1748 | Pachtersoproer: huizen van belastingpachters bestormd | economie | achtergrond | landelijk | literatuur, stadsarchieven |
| 1768-runderpest | 1768-1786 | Runderpest, derde golf | veepest | achtergrond | landelijk | dorpsrekeningen, literatuur |
| 1775-zuiderzeevloeden | 1775-1776 | Twee novemberstormen in twee jaar zetten de Zuiderzeekust onder water | ramp | groot | friesland, overijssel, noord-holland | kerkboek-memoriaalnotities, schadelijsten, literatuur |
| 1780-engelse-oorlog | 1780-1784 | Vierde Engels-Nederlandse Oorlog: handel en visserij vallen stil | oorlog | achtergrond | landelijk | Delpher, literatuur |
| 1795-franse-tijd | 1795-1813 | Franse tijd: inkwartiering, zware belastingen, continentaal stelsel, verarming | oorlog | achtergrond | landelijk | gemeentearchief, literatuur |
| 1799-invasie-noord-holland | 1799 | Engels-Russische invasie in Noord-Holland: gevechten, inkwartiering, gevorderd vee en wagens | oorlog | groot | noord-holland | gemeentearchief, literatuur |
| 1807-ramp-van-leiden | 1807 | Buskruitramp Leiden 12 januari: 150 doden, een hele wijk weggevaagd | ramp | groot | leiden | Erfgoed Leiden, literatuur |
| 1811-conscriptie | 1810-1813 | Inlijving bij Frankrijk: conscriptie (loting voor jonge mannen), naamsaanneming 1811, invoering burgerlijke stand | wet | groot | landelijk | militieregisters, registers van naamsaanneming |
| 1816-jaar-zonder-zomer | 1816-1817 | "Jaar zonder zomer" na de Tambora-uitbarsting: misoogsten, duurte, honger | honger | achtergrond | landelijk | Delpher, gemeenteverslagen |
| 1825-stormvloed | 1825 | Stormvloed 3-5 februari: de Zuiderzeekust overstroomd, zwaar in Overijssel, Friesland en Gelderland; honderden doden | ramp | groot | friesland, overijssel, gelderland, noord-holland, utrecht | Delpher, schadecommissie-archieven, literatuur |
| 1826-koortsepidemie | 1826-1827 | Koortsepidemie (malaria) na de natte rampjaren: hoge sterfte, vooral in het noorden en de veengebieden | epidemie | groot | friesland, groningen, overijssel, noord-holland | overlijdensregisters (sterftepiek), gemeenteverslagen |
| 1830-belgische-opstand | 1830-1839 | Belgische afscheiding: mobilisatie van schutterij en militie; de nieuwe grens snijdt streken in tweeën | oorlog | groot | landelijk, zeeland, noord-brabant, limburg, belgie-vlaanderen | militieregisters, schutterijarchieven, literatuur |
| 1832-cholera | 1832-1833 | Eerste cholera-epidemie in Nederland | epidemie | groot | landelijk | overlijdensregisters, gemeenteverslagen |
| 1845-hongerjaren | 1845-1847 | Aardappelziekte: misoogsten, duurte, hongeroproeren in 1847 | honger | groot | landelijk | Delpher, gemeenteverslagen |
| 1848-cholera | 1848-1849 | Tweede grote cholera-golf (nasleep tot 1855) | epidemie | groot | landelijk | overlijdensregisters, gemeenteverslagen |
| 1855-watersnood | 1855 | Watersnood maart: doorbraak van de Grebbedijk, de Gelderse Vallei en het Kromme Rijngebied onder water | ramp | groot | gelderland, utrecht | Delpher, waterschapsarchieven, literatuur |
| 1859-difterie | 1859-1863 | Reeks epidemieën: difterie 1859-1861, rode loop (dysenterie) 1862, tyfus en roodvonk 1863 | epidemie | groot | landelijk | overlijdensregisters (sterftepiek), Verslagen aan den Koning betrekkelijk den staat der Openbare Gezondheid |
| 1865-veepest | 1865-1867 | Veepest, vooral in Holland en Utrecht: stallen geruimd, boeren geruïneerd | veepest | achtergrond | zuid-holland, noord-holland, utrecht | Delpher, gemeenteverslagen |
| 1866-cholera | 1866-1867 | Laatste grote cholera-epidemie: ruim 20.000 doden | epidemie | groot | landelijk | overlijdensregisters (sterftepiek zomer 1866), gemeenteverslagen |
| 1878-landbouwcrisis | 1878-1895 | Grote landbouwcrisis: graan- en zuivelprijzen storten in; landarbeiders trekken naar de stad of naar Amerika | economie | achtergrond | landelijk | bevolkingsregisters (verhuisbewegingen), Delpher, vertrekregisters |
| 1888-veenstakingen | 1888-1890 | Veenarbeidersstakingen in Friesland en Drenthe; opkomst van het socialisme op het platteland | plaatselijk | groot | friesland, drenthe | Delpher, literatuur |
| 1890-strenge-winter | 1890-1891 | Strenge winter: maandenlange vorst, stilgevallen werk, bedelingen | weer | achtergrond | landelijk | Delpher, armbestuurarchieven |
| 1906-stormvloed | 1906 | Stormvloed 12 maart: Zeeuws-Vlaanderen en delen van Zeeland overstroomd | ramp | groot | zeeland | Krantenbank Zeeland, Delpher, Zeeuws Archief |
| 1914-wo1 | 1914-1918 | Eerste Wereldoorlog: mobilisatie, Belgische vluchtelingen, dodendraad op de grens, distributienood; België zelf bezet | oorlog | groot | landelijk, zeeland, noord-brabant, limburg, belgie-vlaanderen | militieregisters, Delpher, gemeenteverslagen, vluchtelingenregisters |
| 1916-zuiderzeevloed | 1916 | Zuiderzeevloed 13-14 januari: Noord-Holland en de Zaanstreek onder water; gaf de doorslag voor de Afsluitdijk | ramp | groot | noord-holland, friesland | Delpher, waterschapsarchieven |
| 1918-spaanse-griep | 1918-1919 | Spaanse griep: sterftepiek november 1918, vooral onder jonge volwassenen | epidemie | groot | landelijk | overlijdensregisters (november-december 1918), Delpher |
| 1929-crisisjaren | 1929-1936 | Crisisjaren: werkloosheid, steun, werkverschaffing, het Jordaanoproer van 1934 | economie | achtergrond | landelijk | Delpher, gemeenteverslagen, werkverschaffingsarchieven |
| 1932-afsluitdijk | 1932 | Afsluitdijk dicht: de Zuiderzee wordt IJsselmeer, einde van de Zuiderzeevisserij | economie | achtergrond | friesland, noord-holland, overijssel | Delpher, literatuur |
| 1940-meidagen | 1940 | Duitse inval 10-15 mei: gevechten om de Grebbeberg, de Afsluitdijk en de Zeeuwse eilanden; bombardement op Rotterdam en Middelburg | oorlog | groot | landelijk, utrecht, gelderland, zeeland, zuid-holland | oorlogsbronnen.nl, NIOD, gemeentearchief |
| 1940-wo2 | 1940-1945 | Bezetting: bombardementen, razzia's, Arbeitseinsatz (mannen 18-45), onderduik, evacuaties, deportaties | oorlog | groot | landelijk | oorlogsbronnen.nl, NIOD, Nationaal Archief, gemeentearchief |
| 1944-slag-om-de-schelde | 1944 | Slag om de Schelde (september-november): bevrijding én verwoesting van Zeeland, Zeeuws-Vlaanderen en het Waasland; Walcheren onder water gebombardeerd | oorlog | groot | zeeland, belgie-vlaanderen | oorlogsbronnen.nl, Krantenbank Zeeland, gemeentearchief |
| 1944-market-garden | 1944 | Operatie Market Garden en de frontlinie langs de Rijn: evacuatie van Arnhem en de Betuwe, maanden frontgebied | oorlog | groot | gelderland, noord-brabant, limburg | oorlogsbronnen.nl, gemeentearchief, evacuatieregisters |
| 1944-hongerwinter | 1944-1945 | Hongerwinter in het bezette westen: voedseltochten, kou, kinderen geëvacueerd naar het noorden, duizenden hongerdoden | honger | groot | zuid-holland, noord-holland, utrecht | oorlogsbronnen.nl, gemeentearchief, familieverhalen |
| 1953-watersnood | 1953 | Watersnood 1 februari: Zeeland, de Zuid-Hollandse eilanden en West-Brabant; 1836 doden | ramp | groot | zeeland, zuid-holland, noord-brabant | watersnoodmuseum.nl (slachtofferregister), Krantenbank Zeeland |
| 1962-mijnsluiting | 1965-1974 | Sluiting van de Limburgse mijnen: tienduizenden banen weg, streek in de knel | economie | achtergrond | limburg | Delpher, RHCL, literatuur |

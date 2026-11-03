/* Stamboommaker — frontend van de lokale stamboomwebsite.
   Routes (hash): #/boom  #/boom/<id>  #/personen  #/persoon/<id>  #/kaart
                  #/tijdsbeeld  #/gebeurtenis/<id>  #/verhalen  #/verhaal/<id>
                  #/verkenner  #/verkenner/<pad>

   Ontworpen om honderden dossiers aan te kunnen: de stamboom is een sleep- en
   zoombare kwartierstaat met inklapbare takken, de personenlijst heeft filters,
   groepering per generatie en een tabelweergave, en het zoekveld geeft directe
   suggesties vanaf elk tabblad. */

"use strict";

let PERSONEN = [];
let PERSOON_MAP = {};
let VERKENNER = [];
let TIJDSBEELD = [];
let GEBEURTENIS_MAP = {};
let VERHALEN = [];
let INSTELLINGEN = {};   // titel en generatie-uitleg uit stamboom.json (/api/instellingen)
let VERHAAL_MAP = {};
let ZOEKTERM = "";
const OPEN_MAPPEN = new Set(["personen", "documenten", "boek"]);
const KLAP = new Set();       // ingeklapte takken in de stamboom (persoon-id's)
let ZOOM = 1;                 // zoomniveau van de stamboom
let BOOM_BREEDTE = 0;         // canvasbreedte van de laatste boomweergave
const FILTER = { lijn: "", gen: "", status: new Set(), weergave: "kaarten" };
const FILTER_V = { lijn: "", rubriek: "", sort: "score", zoek: "" };

/* Takkenfilter — het "grote filter" waarmee je één kant van de stamboom deelt.
   De waarde staat als ?tak=… in de query VÓÓR de hash (bijv.
   http://localhost:<poort>/?tak=vaderskant#/boom), want de hash wisselt bij elke
   klik en de query blijft dan staan. Zo'n link is dus deelbaar: wie hem opent
   ziet alléén die kant — personen, stamboom, kaart, verhalen én tijdsbeeld.
   Een kant is "die persoon plus al zijn voorouders", geklommen langs de
   vader-/moeder-wikilinks; daarnaast kan elke familielijn apart (?tak=lijn:…). */
const TAKKEN = {
  vaderskant:  { naam: "Vaderskant",  anker: "", uitleg: "" },
  moederskant: { naam: "Moederskant", anker: "", uitleg: "" },
};

/* De ankers worden uit de boom zelf afgeleid: de proband is de persoon op
   generatie 0 met ouders in de dossiers, en de twee kanten zijn diens vader
   en moeder plus al hún voorouders. Zo hoeven hier geen namen te staan en
   werkt het filter in elke stamboom die dit format volgt. */
function bepaalTakken() {
  const proband = PERSONEN
    .filter(p => +p.generatie === 0)
    .find(p => (p.vader && PERSOON_MAP[p.vader]) || (p.moeder && PERSOON_MAP[p.moeder]));
  if (!proband) return;
  const zet = (sleutel, id) => {
    const ouder = id && PERSOON_MAP[id];
    if (!ouder) return;
    TAKKEN[sleutel].anker = id;
    TAKKEN[sleutel].uitleg = ouder.naam + " en alle voorouders daarboven";
  };
  zet("vaderskant", proband.vader);
  zet("moederskant", proband.moeder);
}
let TAK = "";          // actieve filterwaarde uit de URL ("" = hele stamboom)
let TAK_TITEL = "";    // leesbare naam voor de balk en de paginatitel
let LIJNEN_VOL = [];   // alle familielijnen vóór het filteren (voor de keuzelijst)
let TAK_KEUZES = [];   // welke takken echt bestaan (anker heeft een dossier)

const inhoud = document.getElementById("inhoud");

/* ------------------------------------------------------------------ iconen */

const IKONEN = {
  map: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  doc: '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v4h4"/><path d="M9 12h6M9 16h6"/>',
  beeld: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="m21 16-5-5-8 8"/>',
  boek: '<path d="M4 19V5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
  code: '<path d="m8 8-4 4 4 4M16 8l4 4-4 4"/>',
  klem: '<path d="m21 12-8.5 8.5a5 5 0 0 1-7-7L14 5a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-3-3L15 8"/>',
  extern: '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M20 13v7H4V4h7"/>',
  boompje: '<circle cx="12" cy="8" r="4"/><circle cx="7.5" cy="11.5" r="3"/><circle cx="16.5" cy="11.5" r="3"/><path d="M12 21v-9"/>',
  afdruk: '<path d="M12 3v11"/><path d="m8 10 4 4 4-4"/><path d="M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
  speel: '<path d="M8 5.5v13l10.5-6.5z"/>',
  stop: '<rect x="6.5" y="6.5" width="11" height="11" rx="1.5"/>',
  links: '<path d="m14.5 5.5-6.5 6.5 6.5 6.5"/>',
  rechts: '<path d="m9.5 5.5 6.5 6.5-6.5 6.5"/>',
  pijl: '<path d="M4 12h16"/><path d="m14 6 6 6-6 6"/>',
  omhoog: '<path d="M12 20V5"/><path d="m6 11 6-6 6 6"/>',
  lijst: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>',
};

function ikoon(naam) {
  return '<svg class="ik" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"' +
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (IKONEN[naam] || "") + "</svg>";
}

/* ------------------------------------------------------------------ hulpjes */

function esc(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function bestandUrl(pad) {
  return "/bestand/" + pad.split("/").map(encodeURIComponent).join("/");
}

function verkennerHash(pad) {
  return "#/verkenner/" + encodeURIComponent(pad);
}

function persoonHash(id) {
  return "#/persoon/" + encodeURIComponent(id);
}

function verhaalHash(id) {
  return "#/verhaal/" + encodeURIComponent(id);
}

function jaarUit(tekst) {
  const m = /(\d{4})/.exec(tekst || "");
  if (!m) return "";
  return (/\b(ca|circa)\b/i.test(tekst) ? "ca. " : "") + m[1];
}

function jarenVan(p) {
  const g = jaarUit(p.geboren), o = jaarUit(p.overleden);
  if (!g && !o) return "";
  return (g || "?") + " – " + (o || "?");
}

const STATUS_KLASSE = { "✓": "ok", "◐": "half", "?": "vraag", "⚠": "waak" };
const STATUS_WOORD = { "✓": "bewezen", "◐": "waarschijnlijk", "?": "hypothese", "⚠": "verwarringsgevaar" };

function statusKlasse(s) { return STATUS_KLASSE[s] || "leeg"; }

function statusHtml(s) {
  if (!s) return "";
  return '<span class="status s-' + statusKlasse(s) + '" title="' + esc(STATUS_WOORD[s] || "betrouwbaarheid") + '">' + esc(s) + "</span>";
}

function statusBadge(s) {
  if (!s) return '<span class="badge b-leeg">nog geen status</span>';
  return '<span class="badge b-' + statusKlasse(s) + '">' + esc(s) + " " + esc(STATUS_WOORD[s] || "") + "</span>";
}

/* Monogram: initialen in de kleur van de familielijn. Er zijn geen foto's van
   mensen uit 1700, maar zo krijgen de boom, de personenlijst en de dossiers
   toch één gezicht — en de kleur is overal dezelfde als op de kaart. */
function initialen(naam) {
  const delen = String(naam || "").split(/\s+/).filter(d => /^\p{Lu}/u.test(d));
  if (!delen.length) return "?";
  return (delen[0][0] + (delen.length > 1 ? delen[delen.length - 1][0] : "")).toUpperCase();
}

function monogramHtml(p, klasse) {
  return '<span class="monogram' + (klasse ? " " + klasse : "") + '" style="--mk:' +
    lijnKleur(p.lijn) + '" aria-hidden="true">' + esc(initialen(p.naam)) + "</span>";
}

/* Hoe oud iemand werd: exact als beide datums volledig zijn, anders het
   verschil tussen de jaartallen met "ongeveer" ervoor. */
function leeftijdVan(p) {
  const vol = s => /(\d{2})-(\d{2})-(\d{4})/.exec(s || "");
  const jaar = s => { const m = /(\d{4})/.exec(s || ""); return m ? +m[1] : null; };
  const gj = jaar(p.geboren), oj = jaar(p.overleden);
  if (gj == null || oj == null) return "";
  const g = vol(p.geboren), o = vol(p.overleden);
  let n, circa = /\b(ca|circa|vermoedelijk|voor|vóór|na)\b/i.test(p.geboren + " " + p.overleden);
  if (g && o && !circa) {
    n = +o[3] - +g[3];
    if (+o[2] < +g[2] || (+o[2] === +g[2] && +o[1] < +g[1])) n--;
  } else {
    n = oj - gj;
    circa = true;
  }
  if (n < 0 || n > 115) return "";
  return (circa ? "ongeveer " : "") + n + " jaar geworden";
}

/* Schermvullend tonen van een vlak (boom of kaart); Esc of dezelfde knop sluit. */
function volledigScherm(el) {
  if (!el) return;
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else if (el.requestFullscreen) {
    el.requestFullscreen();
  }
}

// na het wisselen moet Leaflet zijn maat opnieuw opmeten
document.addEventListener("fullscreenchange", () => {
  if (KAART_MAP) setTimeout(() => KAART_MAP.invalidateSize(), 150);
});

function leestijdChip(tekst) {
  const woorden = String(tekst || "").split(/\s+/).length;
  const minuten = Math.max(1, Math.round(woorden / 200));
  return '<span class="chip chip-stil" title="' + woorden + ' woorden">± ' + minuten +
    " min lezen</span>";
}

const GENERATIETERMEN = ["jijzelf", "ouders", "grootouders", "overgrootouders",
  "betovergrootouders", "oudouders", "oudgrootouders", "oudovergrootouders",
  "oudbetovergrootouders", "stamouders", "stamgrootouders", "stamovergrootouders",
  "stambetovergrootouders"];

function generatieTerm(g) {
  if (g < 0) return "kinderen";   // generatie -1: onder de proband
  return GENERATIETERMEN[g] || (isNaN(g) ? "" : "generatie " + g);
}

function padOuder(pad) {
  const i = pad.lastIndexOf("/");
  return i < 0 ? "" : pad.slice(0, i);
}

function padNormaliseer(basis, rel) {
  if (rel.startsWith("/")) return rel.slice(1);
  const delen = (basis ? basis.split("/") : []).concat(rel.split("/"));
  const uit = [];
  for (const d of delen) {
    if (d === "" || d === ".") continue;
    if (d === "..") uit.pop(); else uit.push(d);
  }
  return uit.join("/");
}

// het beschrijvingsbestand van een scan: zelfde naam met .md, waarbij
// vervolgscans (_2, _3) terugvallen op de basisnaam (één .md dekt alle bladen)
function beschrijvingsPad(pad) {
  return pad.replace(/(_\d+)?\.[^.]+$/, ".md");
}

function zoekKnoop(pad, knopen) {
  for (const k of (knopen || VERKENNER)) {
    if (k.pad === pad) return k;
    if (k.type === "map" && pad.startsWith(k.pad + "/")) {
      const r = zoekKnoop(pad, k.kinderen);
      if (r) return r;
    }
  }
  return null;
}

/* PDF-uitdraai: de server bouwt de PDF op verzoek (dat kan een paar seconden
   duren), de knop laat zien dat er gewerkt wordt en start daarna de download.
   Zo kan een bezoeker een dossier of verhaal als één net bestand doorsturen. */
function pdfKnop(soort, id, stil) {
  return '<button class="knopje' + (stil ? " stil" : "") + ' pdf-knop" data-pdf="' +
    esc(soort) + "/" + esc(id) + '" title="maak er een PDF van om te bewaren of door te sturen">' +
    ikoon("afdruk") + " Download als PDF</button>";
}

function koppelPdfKnoppen() {
  inhoud.querySelectorAll(".pdf-knop").forEach(knop => knop.addEventListener("click", async e => {
    e.preventDefault();
    if (knop.classList.contains("bezig")) return;
    const oud = knop.innerHTML;
    knop.classList.add("bezig");
    knop.innerHTML = ikoon("afdruk") + " PDF wordt gemaakt…";
    try {
      const antwoord = await fetch("/pdf/" + knop.dataset.pdf);
      if (!antwoord.ok) throw new Error(await antwoord.text());
      const blob = await antwoord.blob();
      const m = /filename="([^"]+)"/.exec(antwoord.headers.get("Content-Disposition") || "");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = m ? m[1] : knop.dataset.pdf.replace("/", "-") + ".pdf";
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 30000);
      knop.innerHTML = ikoon("afdruk") + " PDF staat in je downloads";
    } catch (fout) {
      knop.innerHTML = ikoon("afdruk") + " Mislukt — probeer het nog eens";
    }
    setTimeout(() => { knop.innerHTML = oud; knop.classList.remove("bezig"); }, 3500);
  }));
}

function zoekTekst(p) {
  return [p.naam, p.id, p.geboren, p.overleden, p.beroep, p.lijn,
    (p.woonplaatsen || []).join(" ")].join(" ").toLowerCase();
}

/* Het opsommingsteken van een lijstregel. Maximaal drie cijfers vóór de punt:
   met \d+ werd een regel die met een jaartal begint ("1839. Doorzocht op beide
   spellingen…") een genummerd lijstitem, en dan valt de tekst uit elkaar. Eén
   constante, want het patroon wordt op twee plaatsen gebruikt en die liepen
   uiteen — dat was op zichzelf al een bug. */
const LIJSTTEKEN = /^(\s*)([-*]|\d{1,3}\.)\s+(.*)$/;

/* --------------------------------------------------------------- leespagina's
   Een dossier heeft acht tot vijftien kopjes en wordt tienduizend pixels lang.
   Deze hulpjes maken daar een navigeerbare leespagina van: een inhoudsopgave
   uit de kopjes, en scrollen zónder de hash aan te raken — want de router
   leest de hash, en een gewone ankerlink (#vn-1 onder een voetnoot) gooide je
   daardoor uit het dossier naar de stamboom. */

// de kopregel zoals een lezer hem wil zien: zonder markdown-tekens, zonder
// wikilink-haakjes en zonder de statustekens die vooraan een kopje staan
function platteTekst(s) {
  return String(s ?? "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, id, alias) => alias || id)
    .replace(/\[\^[^\]]+\]/g, "")
    .replace(/\*+/g, "")
    .replace(/^[\s✓◐?⚠⛔ⓘ]+/, "")
    .replace(/\s+/g, " ")
    .trim();
}

// accenten hoeven er niet af: alles buiten a-z0-9 wordt toch een streepje
function slugMaak(s) {
  const slug = platteTekst(s).toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || "kop";
}

/* Een pad in `code`-opmaak dat naar een bestand van dit project verwijst, wordt
   klikbaar — een dossier naar zijn dossierpagina, een verhaal naar het verhaal,
   de rest naar de verkenner. Alleen als het bestand echt bestaat: een pad met
   een … erin (afgekapt in de tekst) blijft gewoon tekst. */
function projectPadHref(pad) {
  if (!/^[a-z0-9_.-]+\/[^\s]+$/i.test(pad)) return null;
  const mPersoon = /^personen\/([a-z0-9-]+)\.md$/.exec(pad);
  if (mPersoon && PERSOON_MAP[mPersoon[1]]) return persoonHash(mPersoon[1]);
  const mVerhaal = /^boek\/verhalen\/([a-z0-9-]+)\.md$/.exec(pad);
  if (mVerhaal && VERHAAL_MAP[mVerhaal[1]]) return verhaalHash(mVerhaal[1]);
  const mTb = /^tijdsbeeld\/([a-z0-9-]+)\.md$/.exec(pad);
  if (mTb && GEBEURTENIS_MAP[mTb[1]]) return "#/gebeurtenis/" + encodeURIComponent(mTb[1]);
  return zoekKnoop(pad) ? verkennerHash(pad) : null;
}

/* De inhoudsopgave, uit de kopjes van niveau 2. Onder de drie kopjes is een
   index meer ruis dan hulp, dus dan komt hij er niet. */
function inhoudsopgaveHtml(kopjes) {
  const items = (kopjes || []).filter(k => k.niveau === 2 && k.tekst);
  if (items.length < 3) return "";
  let h = '<nav class="inhoudsopgave" aria-label="Op deze pagina">' +
    '<p class="io-kop">' + ikoon("lijst") + " Op deze pagina</p><ol>";
  for (const k of items) {
    h += '<li><button type="button" class="io-link" data-naar="' + esc(k.id) +
      '" title="' + esc(k.tekst) + '">' + esc(k.tekst) + "</button></li>";
  }
  h += "</ol></nav>";
  return h;
}

/* De tekstlaag van een leespagina: de inhoudsopgave naast (breed scherm) of
   boven (smal scherm) het artikel. In de verkenner staat links al een
   bestandsboom; daar blijft het bij de strip bovenaan, anders navigeren twee
   kolommen naast elkaar om dezelfde aandacht. */
function leeslaag(html, kopjes, klasse) {
  const io = inhoudsopgaveHtml(kopjes);
  return '<div class="leeslaag' + (io ? "" : " geen-io") + (klasse ? " " + klasse : "") + '">' +
    io + '<article class="md">' + html + "</article></div>";
}

/* De menubalk plakt bovenaan en is 66 px hoog op een breed scherm, maar 90 tot
   160 px zodra de tabbladen omslaan. Alles wat eronderuit moet komen — een
   kopje waar je naartoe springt, de plakkende inhoudsopgave, de bestandsboom —
   rekent met --kop-hoogte, dus die wordt hier gemeten in plaats van geraden. */
function meetKopHoogte() {
  const kop = document.getElementById("kop");
  if (kop) document.documentElement.style.setProperty("--kop-hoogte", kop.offsetHeight + "px");
}
window.addEventListener("resize", meetKopHoogte);

function scrollNaarAnker(id) {
  const doel = document.getElementById(id);
  if (!doel) return;
  doel.scrollIntoView({ behavior: "smooth", block: "start" });
  doel.classList.add("oplicht");
  setTimeout(() => doel.classList.remove("oplicht"), 1900);
}

/* Eén klikafhandelaar voor de hele inhoud: hij overleeft het vervangen van
   innerHTML, dus elke leespagina krijgt hem gratis. */
document.addEventListener("click", e => {
  if (e.target.closest("[data-boven]")) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  const naar = e.target.closest("[data-naar]");
  if (!naar) return;
  e.preventDefault();
  scrollNaarAnker(naar.dataset.naar);
});

/* De leesvoortgangsbalk: een dun gouden lijntje onder de menubalk dat meegroeit
   met hoe ver je in een dossier of verhaal bent. Alleen op leespagina's. */
const LEESBALK = document.createElement("div");
LEESBALK.id = "leesbalk";
document.body.appendChild(LEESBALK);

/* Welk kopje lees je nu? De inhoudsopgave licht het op, en op een smal scherm
   schuift de strip mee zodat je ziet waar je bent. */
let ioWacht = false;
function werkLeespaginaBij() {
  const naarBoven = document.getElementById("naar-boven");
  if (naarBoven) naarBoven.classList.toggle("zichtbaar", window.scrollY > 700);
  if (inhoud.querySelector(".leeslaag article.md")) {
    const hoogte = document.documentElement.scrollHeight - window.innerHeight;
    LEESBALK.style.width = (hoogte > 60
      ? Math.min(100, Math.max(0, window.scrollY / hoogte * 100)) : 0) + "%";
    LEESBALK.classList.add("aan");
  } else {
    LEESBALK.classList.remove("aan");
  }
  const nav = inhoud.querySelector(".inhoudsopgave");
  if (!nav) return;
  const knoppen = Array.from(nav.querySelectorAll(".io-link"));
  let actief = knoppen[0];
  for (const k of knoppen) {
    const doel = document.getElementById(k.dataset.naar);
    if (doel && doel.getBoundingClientRect().top <= 150) actief = k;
  }
  for (const k of knoppen) {
    const was = k.classList.contains("nu");
    k.classList.toggle("nu", k === actief);
    // alleen bij een wisseling meeschuiven, anders vecht dit met handmatig scrollen
    if (!was && k === actief && nav.scrollWidth > nav.clientWidth + 4) {
      k.scrollIntoView({ block: "nearest", inline: "center" });
    }
  }
}
window.addEventListener("scroll", () => {
  if (ioWacht) return;
  ioWacht = true;
  requestAnimationFrame(() => { ioWacht = false; werkLeespaginaBij(); });
}, { passive: true });

/* ------------------------------------------------------------- markdown-weergave */

function mdRender(bron, basisMap) {
  const tokens = [];
  const tok = html => { tokens.push(html); return "\u0000" + (tokens.length - 1) + "\u0000"; };

  // frontmatter afsplitsen
  let fm = null;
  let regels = bron.split(/\r?\n/);
  if (regels[0] && regels[0].trim() === "---") {
    const einde = regels.findIndex((r, i) => i > 0 && r.trim() === "---");
    if (einde > 0) {
      fm = regels.slice(1, einde);
      regels = regels.slice(einde + 1);
    }
  }

  // codeblokken (```) veiligstellen
  const blokTokens = [];
  const zonderFences = [];
  for (let i = 0; i < regels.length; i++) {
    if (/^```/.test(regels[i])) {
      const buffer = [];
      i++;
      while (i < regels.length && !/^```/.test(regels[i])) buffer.push(regels[i++]);
      blokTokens.push('<pre class="codeblok">' + esc(buffer.join("\n")) + "</pre>");
      zonderFences.push("" + (blokTokens.length - 1));
    } else {
      zonderFences.push(regels[i]);
    }
  }
  regels = zonderFences;

  function inline(s) {
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, (_, c) => {
      // een verwijzing naar een gebeurtenisbestand wordt een klikbare titel
      const mTb = /^tijdsbeeld\/([a-z0-9-]+)\.md$/.exec(c);
      if (mTb && GEBEURTENIS_MAP[mTb[1]]) {
        const g = GEBEURTENIS_MAP[mTb[1]];
        return tok('<a class="tb-verwijzing" href="#/gebeurtenis/' + encodeURIComponent(g.id) + '">' + esc(g.titel) + "</a>");
      }
      // en elk ander projectpad dat echt bestaat wordt een klikbaar pad
      // (c is hier al door esc() heen; projectpaden bevatten geen &, < of >)
      const href = projectPadHref(c);
      if (href) return tok('<a class="padlink" href="' + href + '"><code>' + c + "</code></a>");
      return tok("<code>" + c + "</code>");
    });
    // Onderschriften van knipsels citeren de bron en bevatten soms een weglating "[...]" of een
    // aanvulling "[zoon]"; sta daarom één niveau rechte haken binnen de alt-tekst toe. Zonder
    // dit werd zo'n knipsel als platte tekst getoond.
    s = s.replace(/!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]+)\)/g, (_, alt, src) => {
      if (/^https?:/.test(src)) return tok('<img src="' + src + '" alt="' + alt + '">');
      return tok('<img src="' + bestandUrl(padNormaliseer(basisMap, decodeURIComponent(src))) + '" alt="' + alt + '" loading="lazy">');
    });
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) => {
      if (/^https?:/.test(u)) return tok('<a href="' + u + '" target="_blank" rel="noopener">' + t + "</a>");
      const doel = padNormaliseer(basisMap, decodeURIComponent(u.replace(/#.*$/, "")));
      return tok('<a href="' + verkennerHash(doel) + '">' + t + "</a>");
    });
    s = s.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, id, alias) => {
      id = id.trim();
      // een wikilink kan naar een persoon wijzen, maar ook naar een verhaal of
      // een gebeurtenis (bijv. de bronregel onder een verhaal) — allemaal klikbaar
      const p = PERSOON_MAP[id];
      if (p) return tok('<a class="wikilink" href="' + persoonHash(id) + '">' + esc(alias || p.naam) + "</a>");
      const v = VERHAAL_MAP[id];
      if (v) return tok('<a class="wikilink" href="' + verhaalHash(id) + '">' + esc(alias || v.titel) + "</a>");
      const g = GEBEURTENIS_MAP[id];
      if (g) return tok('<a class="wikilink" href="#/gebeurtenis/' + encodeURIComponent(id) + '">' + esc(alias || g.titel) + "</a>");
      return tok('<span class="wikilink ontbreekt" title="nog geen dossier">' + esc(alias || id) + "</span>");
    });
    // géén href="#vn-1": dat is een hashwissel, en de router zou de pagina verlaten
    s = s.replace(/\[\^([^\]]+)\]/g, (_, n) =>
      tok('<sup class="vn-ref" id="vnref-' + esc(n) + '">' +
        '<button type="button" data-naar="vn-' + esc(n) + '" title="naar de voetnoot">' + esc(n) + "</button></sup>"));
    // een losse * mag binnen het vette stuk staan (cursief binnen vet), maar
    // ** niet — anders zou één vetblok tot het volgende doorlopen. Zonder deze
    // uitzondering bleef "**acht van de negen … in *Spanbroek*.**" met sterretjes
    // en al op de pagina staan.
    s = s.replace(/\*\*((?:[^*]|\*(?!\*))+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[\s(>„“"])\*([^*\n]+)\*/g, "$1<em>$2</em>");
    s = s.replace(/✓/g, '<span class="s-ok">✓</span>')
         .replace(/◐/g, '<span class="s-half">◐</span>')
         .replace(/⚠/g, '<span class="s-waak">⚠</span>')
         .replace(/⛔/g, '<span class="s-waak">⛔</span>');
    return s;
  }

  const uit = [];
  const voetnoten = [];
  const kopjes = [];              // voor de inhoudsopgave van de leespagina
  const gebruikteIds = new Set();
  let paragraaf = [];
  const lijstStack = [];

  function kopId(tekst) {
    let id = "k-" + slugMaak(tekst);
    let n = 2;
    while (gebruikteIds.has(id)) id = "k-" + slugMaak(tekst) + "-" + n++;
    gebruikteIds.add(id);
    return id;
  }

  function sluitParagraaf() {
    if (paragraaf.length) {
      uit.push("<p>" + inline(paragraaf.join(" ")) + "</p>");
      paragraaf = [];
    }
  }
  function sluitLijsten(totIndent) {
    while (lijstStack.length && lijstStack[lijstStack.length - 1].indent >= totIndent) {
      uit.push("</li></" + lijstStack.pop().tag + ">");
    }
  }
  function sluitAlleLijsten() { sluitLijsten(-1); }

  for (let i = 0; i < regels.length; i++) {
    const regel = regels[i];

    const mTok = /^(\d+)$/.exec(regel.trim());
    if (mTok) { sluitParagraaf(); sluitAlleLijsten(); uit.push(blokTokens[+mTok[1]]); continue; }

    if (!regel.trim()) { sluitParagraaf(); sluitAlleLijsten(); continue; }

    const mVoet = /^\[\^([^\]]+)\]:\s*(.*)$/.exec(regel);
    if (mVoet) {
      sluitParagraaf(); sluitAlleLijsten();
      let tekst = mVoet[2];
      while (i + 1 < regels.length && /^\s{2,}\S/.test(regels[i + 1])) tekst += " " + regels[++i].trim();
      voetnoten.push({ n: mVoet[1], tekst });
      continue;
    }

    const mKop = /^(#{1,6})\s+(.*)$/.exec(regel);
    if (mKop) {
      sluitParagraaf(); sluitAlleLijsten();
      const niveau = mKop[1].length;
      const rauw = mKop[2];
      const plat = platteTekst(rauw);
      const id = kopId(plat);
      if (niveau === 2 || niveau === 3) kopjes.push({ niveau, tekst: plat, id });
      // "Naam (1770 – 1862) — tweeënnegentig jaar oud" is een titel plus een
      // ondertitel; op twee regels leest dat veel beter dan als één lange kop
      const mSplits = niveau === 1 ? /^(.{4,}?)\s+—\s+(.+)$/.exec(rauw) : null;
      const binnen = mSplits
        ? '<span class="md-titel-hoofd">' + inline(mSplits[1]) + "</span>" +
          '<span class="md-titel-onder">' + inline(mSplits[2]) + "</span>"
        : inline(rauw);
      uit.push("<h" + niveau + ' id="' + id + '">' + binnen + "</h" + niveau + ">");
      continue;
    }

    if (/^\s*(---+|\*\*\*+)\s*$/.test(regel)) { sluitParagraaf(); sluitAlleLijsten(); uit.push("<hr>"); continue; }

    /* Citaatblok. De 315 meerregelige citaten in dit project zijn allemaal
       zacht afgebroken alinea's (geen enkele met een harde markdown-breuk),
       dus de regels van één alinea worden aan elkaar geplakt. Regel per regel
       renderen scheurde vet en cursief dat over de regelovergang liep uit
       elkaar — dan stond er letterlijk "**Een huismanswoning" in het citaat.
       Een lege > -regel scheidt alinea's; twee spaties of een \ aan het eind
       van een regel blijft een echte regelbreuk. */
    if (/^\s*>/.test(regel)) {
      sluitParagraaf(); sluitAlleLijsten();
      const buffer = [];
      while (i < regels.length && /^\s*>/.test(regels[i])) buffer.push(regels[i++].replace(/^\s*>\s?/, ""));
      i--;
      const alineas = [];
      let nu = [];
      for (const r of buffer) {
        if (!r.trim()) { if (nu.length) { alineas.push(nu); nu = []; } continue; }
        nu.push(r);
      }
      if (nu.length) alineas.push(nu);
      const blok = alineas.map(a => {
        let t = "";
        a.forEach((r, n) => {
          const hard = /(\s\s|\\)$/.test(r);
          t += r.replace(/(\s\s|\\)+$/, "").trim();
          if (n < a.length - 1) t += hard ? "\n" : " ";
        });
        return "<p>" + inline(t).replace(/\n/g, "<br>") + "</p>";
      }).join("");
      uit.push("<blockquote>" + (blok || "") + "</blockquote>");
      continue;
    }

    // tabel
    if (/^\s*\|/.test(regel) && i + 1 < regels.length && /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(regels[i + 1])) {
      sluitParagraaf(); sluitAlleLijsten();
      const cellen = r => r.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim());
      const koppen = cellen(regel);
      i += 2;
      const rijen = [];
      while (i < regels.length && /^\s*\|/.test(regels[i])) rijen.push(cellen(regels[i++]));
      i--;
      let t = '<div class="tabelwikkel"><table><thead><tr>';
      t += koppen.map(k => "<th>" + inline(k) + "</th>").join("");
      t += "</tr></thead><tbody>";
      // data-kop draagt de kolomnaam mee: op een telefoon wordt elke rij een
      // kaartje met die naam als etiket, in plaats van vier woorden per regel
      const etiketten = koppen.map(k => platteTekst(k));
      for (const rij of rijen)
        t += "<tr>" + koppen.map((_, k) =>
          '<td data-kop="' + esc(etiketten[k]) + '">' + inline(rij[k] || "") + "</td>").join("") + "</tr>";
      t += "</tbody></table></div>";
      uit.push(t);
      continue;
    }

    // lijst (met nesting en taakvinkjes); zie LIJSTTEKEN over de jaartallen
    const mLijst = LIJSTTEKEN.exec(regel);
    if (mLijst) {
      sluitParagraaf();
      const indent = mLijst[1].length;
      const tag = /\d/.test(mLijst[2]) ? "ol" : "ul";
      const top = lijstStack[lijstStack.length - 1];
      if (!top || indent > top.indent) {
        lijstStack.push({ indent, tag });
        uit.push("<" + tag + ">");
      } else {
        while (lijstStack.length > 1 && indent < lijstStack[lijstStack.length - 1].indent) {
          uit.push("</li></" + lijstStack.pop().tag + ">");
        }
        uit.push("</li>");
      }
      let item = mLijst[3];
      /* Zacht afgebroken vervolgregels horen bij dit item en worden er hier
         aan geplakt. Regel per regel renderen scheurde vet en cursief dat over
         de regelovergang liep uit elkaar — precies dezelfde fout als in een
         citaatblok, en zij raakte 132 van de 278 leespagina's: elke "Open
         vragen"-lijst van dit project is zo geschreven, en daar stond dus
         letterlijk "** Huijbert Jacobse van Schie, gedoopt" op de pagina. */
      while (i + 1 < regels.length
             && /^\s{2,}\S/.test(regels[i + 1])
             && !LIJSTTEKEN.test(regels[i + 1])
             && !/^\s*[|>]/.test(regels[i + 1])
             && !/^\s*#{1,6}\s/.test(regels[i + 1])) {
        item += " " + regels[++i].trim();
      }
      const mTaak = /^\[( |x|X)\]\s*(.*)$/.exec(item);
      if (mTaak) {
        const vink = mTaak[1].toLowerCase() === "x";
        item = '<span class="taak' + (vink ? " aan" : "") + '"></span> ' + inline(mTaak[2]);
      } else {
        item = inline(item);
      }
      uit.push("<li>" + item);
      continue;
    }
    if (lijstStack.length && /^\s{2,}\S/.test(regel)) { // doorlopende lijstregel
      uit.push(" " + inline(regel.trim()));
      continue;
    }

    sluitAlleLijsten();
    paragraaf.push(regel.trim());
  }
  sluitParagraaf();
  sluitAlleLijsten();

  if (voetnoten.length) {
    uit.push('<div class="voetnoten" id="k-voetnoten"><h4>Voetnoten</h4><ol>');
    for (const v of voetnoten)
      uit.push('<li id="vn-' + esc(v.n) + '" value="' + esc(v.n) + '">' + inline(v.tekst) +
               ' <button type="button" class="vn-terug" data-naar="vnref-' + esc(v.n) +
               '" title="terug naar de tekst">↑</button></li>');
    uit.push("</ol></div>");
    kopjes.push({ niveau: 2, tekst: "Voetnoten", id: "k-voetnoten" });
  }

  let html = uit.join("\n");
  for (let ronde = 0; ronde < 5 && /\u0000\d+\u0000/.test(html); ronde++) {
    html = html.replace(/\u0000(\d+)\u0000/g, (_, n) => tokens[+n]);
  }
  return { html, frontmatter: fm, kopjes };
}

function frontmatterTabel(fm) {
  if (!fm || !fm.length) return "";
  const rijen = fm
    .filter(r => r.trim() && !r.trim().startsWith("#"))
    .map(r => {
      const sleutel = r.includes(":") ? r.split(":")[0].trim() : "";
      const waarde = (r.includes(":") ? r.slice(r.indexOf(":") + 1).trim() : r.trim()).replace(/^["']|["']$/g, "");
      const getoond = /^https?:\/\/\S+$/.test(waarde)
        ? '<a href="' + esc(waarde) + '" target="_blank" rel="noopener">' + esc(waarde) + "</a>"
        : esc(waarde);
      return "<tr><td>" + esc(sleutel) + "</td><td>" + getoond + "</td></tr>";
    });
  return '<details class="fm-blok"><summary>metadata</summary><table>' + rijen.join("") + "</table></details>";
}

/* ------------------------------------------------------------------ stamboom */

function telVoorouders(id, bezocht) {
  const p = PERSOON_MAP[id];
  if (!p || bezocht.has(id)) return 0;
  bezocht.add(id);
  let n = 0;
  for (const oid of [p.vader, p.moeder]) if (oid) n += 1 + telVoorouders(oid, bezocht);
  return n;
}

function boomModel() {
  const alsOuder = new Set();
  for (const p of PERSONEN) { if (p.vader) alsOuder.add(p.vader); if (p.moeder) alsOuder.add(p.moeder); }
  const wortels = PERSONEN.filter(p => !alsOuder.has(p.id))
    .sort((a, b) => (+a.generatie || 0) - (+b.generatie || 0) || a.naam.localeCompare(b.naam));

  const knopen = [];
  let rij = 0, minGen = Infinity, maxGen = 0, maxRij = 0;

  function leg(id, gen, padSet) {
    const p = PERSOON_MAP[id] || null;
    const eigenGen = p && p.generatie !== "" && !isNaN(+p.generatie) ? +p.generatie : gen;
    minGen = Math.min(minGen, eigenGen);
    maxGen = Math.max(maxGen, eigenGen);
    const k = { id, p, gen: eigenGen, ouders: [], dicht: !!p && KLAP.has(id), verborgen: 0, rij: 0 };
    if (p && !k.dicht && !padSet.has(id)) {
      padSet.add(id);
      for (const oid of [p.vader, p.moeder]) if (oid) k.ouders.push(leg(oid, eigenGen + 1, padSet));
      padSet.delete(id);
    }
    if (k.dicht) k.verborgen = telVoorouders(id, new Set([id])) - 0;
    k.rij = k.ouders.length
      ? k.ouders.reduce((s, o) => s + o.rij, 0) / k.ouders.length
      : rij++;
    maxRij = Math.max(maxRij, k.rij);
    knopen.push(k);
    return k;
  }

  for (const w of wortels) { leg(w.id, +w.generatie || 0, new Set()); rij += 0.35; }
  if (!isFinite(minGen)) { minGen = 0; }
  return { knopen, wortels, minGen, maxGen, maxRij };
}

function boomStats() {
  const telling = {};
  for (const p of PERSONEN) if (p.status) telling[p.status] = (telling[p.status] || 0) + 1;
  const gens = PERSONEN.map(p => +p.generatie).filter(g => !isNaN(g));
  const diepst = gens.length ? Math.max(...gens) : 0;
  let h = "<strong>" + PERSONEN.length + "</strong> dossiers";
  for (const s of ["✓", "◐", "?", "⚠"]) {
    if (telling[s]) h += ' · <span class="status s-' + statusKlasse(s) + '" title="' + esc(STATUS_WOORD[s]) + '">' + s + " " + telling[s] + "</span>";
  }
  const term = generatieTerm(diepst);
  h += " · tot generatie " + diepst + (term ? " (" + term + ")" : "");
  return h;
}

function boomKaart(k, B, x, y) {
  let h = '<div class="knoop" style="left:' + x + "px;top:" + y + 'px">';
  if (!k.p) {
    h += '<span class="bkaart spook" title="nog geen dossier">' +
      '<span class="bk-naam">' + esc(k.id) + '</span>' +
      '<span class="bk-sub">nog geen dossier</span></span>';
    return h + "</div>";
  }
  const p = k.p;
  h += '<a class="bkaart rand-' + statusKlasse(p.status) + '" data-pid="' + esc(p.id) + '" href="' + persoonHash(p.id) + '">' +
    monogramHtml(p, "bk-mono") +
    '<span class="bk-tekst"><span class="bk-naam" title="' + esc(p.naam) + '">' + esc(p.naam) + "</span>" +
    '<span class="bk-sub">' + (esc(jarenVan(p)) || "&nbsp;") + statusHtml(p.status) +
    (p.documenten ? '<span class="bk-doc" title="' + p.documenten + ' documenten in de map">' + ikoon("doc") + p.documenten + "</span>" : "") +
    "</span></span></a>";
  if (p.vader || p.moeder) {
    h += '<button class="klapknop" data-klap="' + esc(p.id) + '" title="' +
      (k.dicht ? "tak uitklappen (" + k.verborgen + " verborgen)" : "tak inklappen") + '">' +
      (k.dicht ? "+" + k.verborgen : "−") + "</button>";
  }
  return h + "</div>";
}

/* De voorkant van de site: één zin die vertelt hoe ver dit onderzoek reikt,
   met de kerncijfers eronder. Rekent op de (eventueel op een tak gefilterde)
   lijsten, dus een gedeelde vaderskant-link krijgt zijn eigen cijfers. */
function boomHero() {
  if (!PERSONEN.length) return "";
  const jaartal = p => { const m = /(\d{4})/.exec(p.geboren || ""); return m ? +m[1] : null; };
  const metJaar = PERSONEN.filter(p => jaartal(p) != null);
  const oudsteJaar = metJaar.length ? Math.min(...metJaar.map(jaartal)) : null;
  const gens = PERSONEN.map(p => +p.generatie).filter(g => !isNaN(g));
  const generaties = gens.length ? Math.max(...gens) - Math.min(...gens) + 1 : 0;
  const docs = PERSONEN.reduce((s, p) => s + (+p.documenten || 0), 0);
  const jongste = [...PERSONEN].sort((a, b) => (+a.generatie || 0) - (+b.generatie || 0))[0];
  const jongsteJaar = jongste ? jaartal(jongste) : null;
  const span = oudsteJaar && jongsteJaar ? jongsteJaar - oudsteJaar : null;

  let titel;
  if (jongste && jongsteJaar && oudsteJaar) {
    titel = "Van " + esc(jongste.naam.split(" ")[0]) + " (" + jongsteJaar + ") tot het jaar " + oudsteJaar;
  } else {
    titel = "De familie, generatie voor generatie";
  }
  let h = '<section class="hero">';
  h += '<p class="hero-boven">' + esc(TAK_TITEL || "de hele familie in kaart") + "</p>";
  h += '<h1 class="hero-titel">' + titel + "</h1>";
  h += '<p class="hero-onder">' + PERSONEN.length + " voorouders" +
    (span ? ", " + span + " jaar familiegeschiedenis" : "") +
    ". Elk feit draagt een bron, elke stip op de kaart is een gelezen akte.</p>";
  h += '<div class="hero-tegels">' +
    heroTegel(PERSONEN.length, "voorouders") +
    heroTegel(generaties, "generaties") +
    (span ? heroTegel(span, "jaar terug") : "") +
    heroTegel(docs, "documenten") +
    heroTegel(VERHALEN.length, "verhalen") +
    heroTegel(TIJDSBEELD.length, "gebeurtenissen") +
    "</div>";
  h += '<div class="hero-acties">' +
    '<a class="knopje" href="#/kaart">' + ikoon("map") + " Bekijk de kaart</a>" +
    '<a class="knopje" href="#/verhalen">' + ikoon("boek") + " Lees de verhalen</a>" +
    '<a class="knopje stil" href="#/cijfers">' + ikoon("lijst") + " Alle cijfers</a>" +
    "</div>";
  h += "</section>";
  return h;
}

function heroTegel(waarde, label) {
  return '<div class="hero-tegel"><strong>' + waarde + "</strong><span>" + esc(label) + "</span></div>";
}

function toonBoom(focusId, herstel) {
  const m = boomModel();
  const B = { kb: 200, kh: 62, kolom: 262, rij: 80, rand: 36, kop: 56 };
  const kolommen = m.maxGen - m.minGen + 1;
  const breedte = B.rand * 2 + (kolommen - 1) * B.kolom + B.kb;
  const hoogte = B.kop + (m.maxRij + 1) * B.rij + B.rand;
  BOOM_BREEDTE = breedte;

  const X = k => B.rand + (k.gen - m.minGen) * B.kolom;
  const Y = k => B.kop + k.rij * B.rij;

  let h = '<div class="vol">';
  h += boomHero();
  h += '<div class="boom-balk"><div class="boom-stats">' + boomStats() + "</div>" +
    '<div class="boom-zoom">' +
    '<button data-zoom="uit" title="verkleinen">−</button>' +
    '<button data-zoom="reset" class="zoompct" title="terug naar 100%">' + Math.round(ZOOM * 100) + "%</button>" +
    '<button data-zoom="in" title="vergroten">+</button>' +
    '<button data-zoom="fit" title="hele breedte in beeld">Passend</button>' +
    '<button data-zoom="vol" title="de boom schermvullend; Esc sluit weer">Volledig scherm</button>' +
    "</div></div>";
  h += '<p class="boom-uitleg">Van jong (links) naar oud (rechts): elke vertakking zijn de ouders. ' +
    "Sleep om te verschuiven, Ctrl+scroll of de knoppen om te zoomen, en de ronde knop op een kaartje " +
    'klapt een tak in of uit. Het volledige beeld staat in <a href="' + verkennerHash("stamboom/overzicht.md") + '">stamboom/overzicht.md</a>.</p>';

  if (!m.knopen.length) {
    h += '<div class="leeg-melding">Nog geen dossiers gevonden in <code>personen/</code>.</div></div>';
    inhoud.innerHTML = h;
    return;
  }

  h += '<div class="boom-vlak" id="boomvlak"><div class="boom-canvas" id="boomcanvas" style="width:' +
    breedte + "px;height:" + hoogte + 'px">';

  // verbindingslijnen (kind -> ouders)
  let paden = "";
  for (const k of m.knopen) {
    if (!k.ouders.length) continue;
    const x1 = X(k) + B.kb, y1 = Y(k) + B.kh / 2;
    for (const o of k.ouders) {
      const x2 = X(o), y2 = Y(o) + B.kh / 2;
      const buig = Math.max(24, (x2 - x1) / 2);
      // de lijn draagt de kleur van de tak waar hij naartoe loopt — dezelfde
      // kleuren als de kaart en de monogrammen; spoken houden de neutrale lijn
      const kleur = o.p ? ' style="stroke:' + lijnKleur(o.p.lijn) + '"' : "";
      paden += '<path' + kleur + ' d="M' + x1 + " " + y1 + " C" + (x1 + buig) + " " + y1 + ", " +
        (x2 - buig) + " " + y2 + ", " + x2 + " " + y2 + '"/>';
    }
  }
  h += '<svg class="boom-lijnen" width="' + breedte + '" height="' + hoogte +
    '" viewBox="0 0 ' + breedte + " " + hoogte + '">' + paden + "</svg>";

  // kolomkoppen per generatie
  for (let g = m.minGen; g <= m.maxGen; g++) {
    const term = generatieTerm(g);
    h += '<div class="kolomkop" style="left:' + (B.rand + (g - m.minGen) * B.kolom) + 'px">Generatie ' + g +
      (term ? "<small>" + esc(term) + "</small>" : "") + "</div>";
  }

  // kaartjes
  for (const k of m.knopen) h += boomKaart(k, B, X(k), Y(k));

  h += "</div>";
  // zweeft alleen in de schermvullende stand in beeld: daar is de gewone
  // zoombalk buiten het beeld gevallen, dus krijgt de boom er zelf een
  h += '<div class="vol-balk">' +
    '<button data-zoom="uit" title="verkleinen">−</button>' +
    '<button data-zoom="reset" class="zoompct">' + Math.round(ZOOM * 100) + "%</button>" +
    '<button data-zoom="in" title="vergroten">+</button>' +
    '<button data-zoom="vol">Sluit volledig scherm</button></div>';
  h += "</div></div>";
  inhoud.innerHTML = h;

  const vlak = document.getElementById("boomvlak");
  const canvas = document.getElementById("boomcanvas");

  function zetZoom(z) {
    ZOOM = Math.min(1.6, Math.max(0.25, z));
    canvas.style.zoom = ZOOM;
    inhoud.querySelectorAll(".zoompct").forEach(el => { el.textContent = Math.round(ZOOM * 100) + "%"; });
  }
  zetZoom(ZOOM);

  inhoud.querySelectorAll("[data-zoom]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.zoom === "in") zetZoom(ZOOM * 1.2);
    else if (b.dataset.zoom === "uit") zetZoom(ZOOM / 1.2);
    else if (b.dataset.zoom === "fit") zetZoom((vlak.clientWidth - 24) / BOOM_BREEDTE);
    else if (b.dataset.zoom === "vol") volledigScherm(vlak);
    else zetZoom(1);
  }));

  vlak.addEventListener("wheel", e => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    zetZoom(ZOOM * (e.deltaY < 0 ? 1.1 : 1 / 1.1));
  }, { passive: false });

  // slepen om te verschuiven
  let sleep = null;
  vlak.addEventListener("pointerdown", e => {
    if (e.target.closest("a,button")) return;
    sleep = { x: e.clientX, y: e.clientY, l: vlak.scrollLeft, t: vlak.scrollTop };
    vlak.setPointerCapture(e.pointerId);
    vlak.classList.add("sleept");
  });
  vlak.addEventListener("pointermove", e => {
    if (!sleep) return;
    vlak.scrollLeft = sleep.l - (e.clientX - sleep.x);
    vlak.scrollTop = sleep.t - (e.clientY - sleep.y);
  });
  const sleepKlaar = () => { sleep = null; vlak.classList.remove("sleept"); };
  vlak.addEventListener("pointerup", sleepKlaar);
  vlak.addEventListener("pointercancel", sleepKlaar);

  // in-/uitklappen van takken, met behoud van scrollpositie
  inhoud.querySelectorAll(".klapknop").forEach(b => b.addEventListener("click", () => {
    const id = b.dataset.klap;
    if (KLAP.has(id)) KLAP.delete(id); else KLAP.add(id);
    toonBoom(null, { l: vlak.scrollLeft, t: vlak.scrollTop });
  }));

  if (herstel) {
    vlak.scrollLeft = herstel.l;
    vlak.scrollTop = herstel.t;
  } else if (!focusId && m.knopen.length) {
    // open niet op een leeg stuk canvas maar met de wortel (de jongste
    // generatie) verticaal in beeld; de scrollmaat schaalt mee met de zoom
    const wortel = m.knopen.find(k => k.p && m.wortels.some(w => w.id === k.id));
    if (wortel) {
      vlak.scrollTop = Math.max(0, (B.kop + wortel.rij * B.rij + B.kh / 2) * ZOOM - vlak.clientHeight / 2);
    }
  }

  if (focusId) {
    const doel = inhoud.querySelector('.bkaart[data-pid="' + CSS.escape(focusId) + '"]');
    if (doel) {
      doel.classList.add("flits");
      setTimeout(() => doel.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" }), 60);
    }
  }
}

/* ------------------------------------------------------------------ personen */

function persoonTegel(p) {
  let h = '<a class="p-tegel" href="' + persoonHash(p.id) + '">';
  h += '<div class="p-tegel-kop">' + monogramHtml(p, "pt-mono") +
    "<strong>" + esc(p.naam) + "</strong>" + statusHtml(p.status) + "</div>";
  if (p.geboren) h += '<div class="p-regel"><span class="gd">*</span> ' + esc(p.geboren) + "</div>";
  if (p.overleden) h += '<div class="p-regel"><span class="gd">†</span> ' + esc(p.overleden) + "</div>";
  if (p.beroep) h += '<div class="p-regel"><span class="gd">&nbsp;</span> ' + esc(p.beroep) + "</div>";
  h += '<div class="p-tegel-voet">' +
    (p.lijn ? '<span class="chip">' + esc(p.lijn) + "</span>" : "") +
    (p.documenten ? '<span class="chip chip-stil">' + p.documenten + " doc.</span>" : "") +
    "</div></a>";
  return h;
}

function toonPersonen() {
  const term = ZOEKTERM.toLowerCase();
  const lijnen = [...new Set(PERSONEN.map(p => p.lijn).filter(Boolean))].sort();
  const gens = [...new Set(PERSONEN.map(p => p.generatie).filter(g => g !== ""))]
    .sort((a, b) => +a - +b);

  let lijst = PERSONEN.filter(p => !term || zoekTekst(p).includes(term));
  if (FILTER.lijn) lijst = lijst.filter(p => p.lijn === FILTER.lijn);
  if (FILTER.gen !== "") lijst = lijst.filter(p => String(p.generatie) === FILTER.gen);
  if (FILTER.status.size) lijst = lijst.filter(p => FILTER.status.has(p.status));
  lijst.sort((a, b) => (+a.generatie || 99) - (+b.generatie || 99) || a.naam.localeCompare(b.naam));

  const gefilterd = term || FILTER.lijn || FILTER.gen !== "" || FILTER.status.size;

  let h = '<div class="paneel"><h2>Personen</h2>';
  h += '<div class="werkbalk">';
  h += '<label>Lijn <select id="f-lijn"><option value="">alle</option>' +
    lijnen.map(l => '<option' + (FILTER.lijn === l ? " selected" : "") + ">" + esc(l) + "</option>").join("") +
    "</select></label>";
  h += '<label>Generatie <select id="f-gen"><option value="">alle</option>' +
    gens.map(g => '<option value="' + esc(g) + '"' + (FILTER.gen === String(g) ? " selected" : "") + ">" +
      esc(g) + (generatieTerm(+g) ? " — " + generatieTerm(+g) : "") + "</option>").join("") +
    "</select></label>";
  h += ["✓", "◐", "?", "⚠"].map(s =>
    '<button class="f-status s-' + statusKlasse(s) + (FILTER.status.has(s) ? " aan" : "") +
    '" data-status="' + s + '" title="' + esc(STATUS_WOORD[s]) + '">' + s + "</button>").join("");
  h += '<span class="w-toggle">' +
    '<button data-weergave="kaarten"' + (FILTER.weergave === "kaarten" ? ' class="aan"' : "") + ">Kaarten</button>" +
    '<button data-weergave="tabel"' + (FILTER.weergave === "tabel" ? ' class="aan"' : "") + ">Tabel</button></span>";
  h += '<span class="teller">' + lijst.length + " van " + PERSONEN.length + " dossiers" +
    (gefilterd ? ' · <button class="wis-filters" id="wisfilters">wis filters</button>' : "") + "</span>";
  h += "</div>";

  if (!lijst.length) {
    h += '<div class="leeg-melding">Geen dossiers gevonden' +
      (term ? ' voor “' + esc(ZOEKTERM) + "”" : "") + ".</div>";
  } else if (FILTER.weergave === "tabel") {
    h += '<div class="tabelwikkel"><table class="p-tabel"><thead><tr>' +
      "<th>Naam</th><th>Geboren</th><th>Overleden</th><th>Beroep</th><th>Lijn</th><th>Gen.</th><th>Doc.</th>" +
      "</tr></thead><tbody>";
    for (const p of lijst) {
      h += '<tr data-pid="' + esc(p.id) + '">' +
        '<td class="t-naam">' + esc(p.naam) + statusHtml(p.status) + "</td>" +
        '<td class="t-plaats">' + esc(p.geboren) + "</td>" +
        '<td class="t-plaats">' + esc(p.overleden) + "</td>" +
        '<td class="t-beroep">' + esc(p.beroep) + "</td>" +
        "<td>" + esc(p.lijn) + "</td>" +
        "<td>" + esc(p.generatie) + "</td>" +
        "<td>" + (p.documenten || "") + "</td></tr>";
    }
    h += "</tbody></table></div>";
  } else {
    // kaarten, gegroepeerd per generatie
    const groepen = new Map();
    for (const p of lijst) {
      const sleutel = p.generatie === "" ? "onbekend" : String(p.generatie);
      if (!groepen.has(sleutel)) groepen.set(sleutel, []);
      groepen.get(sleutel).push(p);
    }
    for (const [g, groep] of groepen) {
      const term2 = g === "onbekend" ? "" : generatieTerm(+g);
      h += '<div class="groepkop"><span class="groep-gen">' +
        (g === "onbekend" ? "Generatie onbekend" : "Generatie " + esc(g)) + "</span>" +
        (term2 ? '<span class="groep-term">' + esc(term2) + "</span>" : "") +
        '<span class="groep-aantal">' + groep.length + "</span></div>";
      h += '<div class="p-rooster">' + groep.map(persoonTegel).join("") + "</div>";
    }
  }
  h += "</div>";
  inhoud.innerHTML = h;

  const fLijn = document.getElementById("f-lijn");
  if (fLijn) fLijn.addEventListener("change", () => { FILTER.lijn = fLijn.value; toonPersonen(); });
  const fGen = document.getElementById("f-gen");
  if (fGen) fGen.addEventListener("change", () => { FILTER.gen = fGen.value; toonPersonen(); });
  inhoud.querySelectorAll(".f-status").forEach(b => b.addEventListener("click", () => {
    const s = b.dataset.status;
    if (FILTER.status.has(s)) FILTER.status.delete(s); else FILTER.status.add(s);
    toonPersonen();
  }));
  inhoud.querySelectorAll("[data-weergave]").forEach(b => b.addEventListener("click", () => {
    FILTER.weergave = b.dataset.weergave;
    toonPersonen();
  }));
  const wis = document.getElementById("wisfilters");
  if (wis) wis.addEventListener("click", () => {
    FILTER.lijn = ""; FILTER.gen = ""; FILTER.status.clear();
    ZOEKTERM = "";
    document.getElementById("zoek").value = "";
    toonPersonen();
  });
  inhoud.querySelectorAll(".p-tabel tbody tr").forEach(r =>
    r.addEventListener("click", () => { location.hash = persoonHash(r.dataset.pid); }));
}

/* ------------------------------------------------------------------ kaart
   Woonplaatsen uit de dossiers op een echte kaart (Leaflet, lokaal meegeleverd;
   de achtergrondtegels komen van OpenStreetMap/CARTO en vragen dus internet —
   zonder verbinding blijven de stippen en filters gewoon werken).

   De coördinaten per plaatsnaam staan in website/static/plaatsen.json; een
   woonplaats in een dossier mag een periode tussen haakjes dragen
   ("Eesterga (1843 - ca. 1865)") — die wordt eraf geknipt en in de lijst bij
   de stip getoond. Filters: familielijnen (chips) en generatie (knoppenbalk
   met afspeelfunctie). Bij één gekozen generatie tonen open rondjes waar de
   ouders van die generatie woonden en lopen er stromende verhuislijnen van
   ouderplaats naar kindplaats (telkens de eerst bekende woonplaats). */

const FILTER_K = { lijnen: new Set(), geinit: false, gen: "alle", verhuis: true };
let PLAATSEN_GIDS = null;   // inhoud van plaatsen.json, eenmalig geladen
let KAART_MODEL = null;     // stippen van de huidige weergave
let KAART_MAP = null;       // Leaflet-kaart (bestaat alleen op het kaart-tabblad)
let KAART_LAGEN = null;     // laag met stippen, rondjes en verhuislijnen
let KAART_SPELER = null;    // timer van de afspeelknop
let KAART_TEGELFOUT = false;

const K_KLEUREN = ["#2e5c46", "#a2543a", "#3d5a80", "#b08d3f", "#6b4d77",
  "#3e7c7b", "#9c4a5e", "#556b2f"];

function kaartLijnen() {
  return [...new Set(PERSONEN.map(p => p.lijn).filter(Boolean))].sort();
}

function lijnKleur(lijn) {
  const i = kaartLijnen().indexOf(lijn);
  return i < 0 ? "#8a8171" : K_KLEUREN[i % K_KLEUREN.length];
}

function kaartGens() {
  // oudste generatie eerst, zodat stappen en afspelen van oud naar jong lopen
  return [...new Set(PERSONEN.filter(p => p.generatie !== "" && !isNaN(+p.generatie))
    .map(p => +p.generatie))].sort((a, b) => b - a);
}

// "Eesterga (1843 - ca. 1865)" -> naam "Eesterga", periode "1843 - ca. 1865"
function woonplaatsDelen(w) {
  const m = /^(.*?)\s*\(([^)]*)\)\s*$/.exec(w);
  return m ? { naam: m[1].trim(), periode: m[2].trim() } : { naam: String(w).trim(), periode: "" };
}

function plaatsCoord(naam) {
  if (!PLAATSEN_GIDS || !naam) return null;
  const gids = PLAATSEN_GIDS;
  const probeer = [naam,
    naam.replace(/,\s*gem\..*$/i, "").trim(),
    naam.replace(/\s+e\.o\.$/i, "").trim()];
  for (let s of probeer) {
    if (!s) continue;
    if ((gids.alias || {})[s]) s = gids.alias[s];
    const c = (gids.plaatsen || {})[s];
    if (c) return { naam: s, lat: c[0], lon: c[1] };
  }
  return null;
}

/* Een plaatsnaam uit een geboren-/overleden-veld halen:
   "20-04-1790, Koudekerk aan den Rijn (gedoopt 25-04-1790)" -> Koudekerk.
   Datums, "onbekend" en gemeentenamen zonder coördinaat vallen af; een
   voorvoegsel als "vermoedelijk" blijft als markering bewaard. */
function plekUitVeld(veld) {
  if (!veld) return null;
  const zonderHaakjes = String(veld).replace(/\([^)]*\)/g, " ");
  for (let deel of zonderHaakjes.split(",")) {
    deel = deel.trim();
    if (!deel || /onbekend/i.test(deel)) continue;
    const vermoed = /^(vermoedelijk|waarschijnlijk|mogelijk)\s+/i.test(deel);
    // ook de tekst na " te " proberen: "waarschijnlijk 23-11-1808 te Koudekerk"
    for (let naam of [deel, deel.split(/\s+te\s+/i).pop()]) {
      naam = naam.replace(/^(vermoedelijk|waarschijnlijk|mogelijk)\s+/i, "")
        .replace(/^(te|in)\s+/i, "")
        .replace(/^onder\s+(de\s+stad\s+)?/i, "").trim();
      if (!naam || /^\d/.test(naam) || /^ca\.?\s*\d/i.test(naam)) continue;
      const c = plaatsCoord(naam);
      if (c) return { plaats: c, vermoed };
    }
  }
  return null;
}

/* De levensloop van één persoon als rij plekken: geboorteplaats, dan de
   woonplaatsen in dossiervolgorde, dan de sterfplaats — zonder direct
   opeenvolgende herhalingen. Elke overgang in dit pad is een verhuizing. */
function levenspad(p) {
  const pad = [];
  const voeg = (plaats, label) => {
    if (!plaats) return;
    if (pad.length && pad[pad.length - 1].plaats.naam === plaats.naam) {
      if (label) pad[pad.length - 1].labels.push(label);
      return;
    }
    pad.push({ plaats, labels: label ? [label] : [] });
  };
  const g = plekUitVeld(p.geboren);
  if (g) voeg(g.plaats, "geboren hier" + (g.vermoed ? " (vermoedelijk)" : ""));
  for (const w of (p.woonplaatsen || [])) {
    if (!w || w === "[]") continue;
    const { naam, periode } = woonplaatsDelen(w);
    const c = plaatsCoord(naam);
    if (c) voeg(c, periode);
  }
  const o = plekUitVeld(p.overleden);
  if (o) voeg(o.plaats, "overleden hier" + (o.vermoed ? " (vermoedelijk)" : ""));
  return pad;
}

function kaartZichtbaar(gen) {
  let lijst = PERSONEN.filter(p => FILTER_K.lijnen.has(p.lijn || ""));
  if (gen !== "alle") lijst = lijst.filter(p => String(p.generatie) === String(gen));
  return lijst;
}

function kaartModelMaken(gen) {
  const stippen = new Map(), onbekend = new Map(), zonder = [];
  const bogen = new Map(), spoken = new Map();

  const stipVoeg = (plaats, p, label) => {
    if (!stippen.has(plaats.naam)) {
      stippen.set(plaats.naam, { naam: plaats.naam, lat: plaats.lat, lon: plaats.lon, personen: [] });
    }
    const stip = stippen.get(plaats.naam);
    const al = stip.personen.find(r => r.p.id === p.id);
    if (al) { if (label && !al.periodes.includes(label)) al.periodes.push(label); }
    else stip.personen.push({ p, periodes: label ? [label] : [] });
  };
  const boogVoeg = (van, naar, p, soort) => {
    if (!FILTER_K.verhuis || van.naam === naar.naam) return;
    const sleutel = van.naam + "|" + naar.naam + "|" + (p.lijn || "");
    if (!bogen.has(sleutel)) bogen.set(sleutel, { van, naar, lijn: p.lijn || "", n: 0, wie: [] });
    const boog = bogen.get(sleutel);
    boog.n++;
    boog.wie.push({ p, soort });
  };

  for (const p of kaartZichtbaar(gen)) {
    // onvindbare plaatsnamen alleen melden voor het woonplaatsen-veld zelf
    for (const w of (p.woonplaatsen || [])) {
      if (!w || w === "[]") continue;
      const { naam } = woonplaatsDelen(w);
      if (!plaatsCoord(naam)) onbekend.set(naam, (onbekend.get(naam) || 0) + 1);
    }
    // één bekende plek is genoeg om op de kaart te staan — desnoods alleen
    // de sterfplaats; het etiket zegt eerlijk wat de plek betekent
    const pad = levenspad(p);
    if (!pad.length) { zonder.push(p); continue; }
    for (const stap of pad) stipVoeg(stap.plaats, p, stap.labels.join("; "));
    // de eigen verhuizingen: elke overgang in de levensloop
    for (let i = 0; i + 1 < pad.length; i++) {
      boogVoeg(pad[i].plaats, pad[i + 1].plaats, p, "eigen verhuizing");
    }
    // de sprong tussen de generaties: van de laatst bekende plek van een
    // ouder naar de eerste plek van dit leven
    for (const oid of [p.vader, p.moeder]) {
      const o = oid && PERSOON_MAP[oid];
      if (!o) continue;
      const oPad = levenspad(o);
      if (!oPad.length) continue;
      const van = oPad[oPad.length - 1].plaats;
      if (gen !== "alle") {
        if (!spoken.has(van.naam)) spoken.set(van.naam, { naam: van.naam, lat: van.lat, lon: van.lon, n: 0 });
        spoken.get(van.naam).n++;
      }
      boogVoeg(van, pad[0].plaats, p, "na " + o.naam);
    }
  }
  // een ouder die op de plek van een stip woont heeft geen eigen rondje nodig
  if (gen !== "alle") for (const s of stippen.keys()) spoken.delete(s);
  return { stippen, spoken, bogen, onbekend, zonder };
}

/* tooltip op een verhuislijn: de route, het aantal en wie er trokken */
function boogTipHtml(b) {
  let h = '<div class="kt-kop"><span class="kt-route">' + esc(b.van.naam) +
    '<span class="kr-pijl">' + ikoon("pijl") + "</span>" + esc(b.naar.naam) + "</span>" +
    '<span class="kt-n">' + b.n + (b.n === 1 ? " verhuizing" : " verhuizingen") + "</span></div>";
  const max = 8;
  const markeer = new Set([b.van.naam, b.naar.naam]);
  const kleur = lijnKleur(b.lijn);
  h += '<div class="kt-groep" style="--kleur:' + kleur + '">';
  if (b.lijn) {
    h += '<div class="kt-lijn"><span class="kt-bol" style="background:' + kleur + '"></span>' +
      esc(b.lijn) + "</div>";
  }
  for (const w of b.wie.slice(0, max)) {
    h += '<div class="kt-rij"><span class="kt-wie">' + esc(w.p.naam) + '</span><span class="kt-jaren">' +
      esc(w.soort) + "</span></div>";
    h += reisHtml(w.p, markeer);
  }
  h += "</div>";
  if (b.wie.length > max) h += '<div class="kt-voet">en nog ' + (b.wie.length - max) + "</div>";
  return h;
}

function stipStraal(n) {
  return Math.min(17, 5.5 + Math.sqrt(Math.max(0, n - 1)) * 3.2);
}

/* de stip zelf: een taartdiagram per familielijn, met het aantal erin */
function stipIcoon(stip) {
  const R = stipStraal(stip.personen.length);
  const D = Math.ceil(R * 2 + 4), c = D / 2;
  const per = new Map();
  for (const r of stip.personen) {
    const l = r.p.lijn || "";
    per.set(l, (per.get(l) || 0) + 1);
  }
  let svg = '<svg width="' + D + '" height="' + D + '" viewBox="0 0 ' + D + " " + D + '">';
  if (per.size === 1) {
    svg += '<circle cx="' + c + '" cy="' + c + '" r="' + R.toFixed(1) + '" fill="' + lijnKleur([...per.keys()][0]) + '"/>';
  } else {
    let hoek = -Math.PI / 2;
    for (const [lijn, n] of [...per.entries()].sort()) {
      const tot = hoek + (n / stip.personen.length) * Math.PI * 2;
      const groot = tot - hoek > Math.PI ? 1 : 0;
      svg += '<path d="M' + c + " " + c +
        " L" + (c + Math.cos(hoek) * R).toFixed(2) + " " + (c + Math.sin(hoek) * R).toFixed(2) +
        " A" + R.toFixed(2) + " " + R.toFixed(2) + " 0 " + groot + " 1 " +
        (c + Math.cos(tot) * R).toFixed(2) + " " + (c + Math.sin(tot) * R).toFixed(2) +
        ' Z" fill="' + lijnKleur(lijn) + '"/>';
      hoek = tot;
    }
  }
  svg += '<circle cx="' + c + '" cy="' + c + '" r="' + R.toFixed(1) + '" fill="none" stroke="#fffdf6" stroke-width="1.6"/>';
  if (stip.personen.length > 1 && R >= 9) {
    svg += '<text x="' + c + '" y="' + c + '" text-anchor="middle" dy=".34em" class="k-getal">' + stip.personen.length + "</text>";
  }
  svg += "</svg>";
  const html = svg + '<span class="k-label">' + esc(stip.naam) + "</span>";
  return L.divIcon({ html, className: "k-stipicoon", iconSize: [D, D], iconAnchor: [c, c] });
}

/* de verhuislijn als zachte boog: 24 tussenpunten op een kwadratische kromme */
function boogPunten(van, naar) {
  const mLat = (van.lat + naar.lat) / 2 + (naar.lon - van.lon) * 0.12;
  const mLon = (van.lon + naar.lon) / 2 - (naar.lat - van.lat) * 0.12;
  const punten = [];
  for (let i = 0; i <= 24; i++) {
    const t = i / 24, u = 1 - t;
    punten.push([u * u * van.lat + 2 * u * t * mLat + t * t * naar.lat,
                 u * u * van.lon + 2 * u * t * mLon + t * t * naar.lon]);
  }
  return punten;
}

/* de reis van één leven als ketting van plaatsjes met pijltjes ertussen:
   geboorteplaats, woonplaatsen, sterfplaats. De plek(ken) waar de bezoeker
   op zweeft lichten groen op, zodat je ziet waar deze stip of lijn in de
   reis valt. Eén plek is geen reis: dan niets. */
function reisHtml(p, markeer) {
  const pad = levenspad(p);
  if (pad.length < 2) return "";
  return '<div class="kt-reis">' + pad.map(stap =>
    '<span class="kr-stap' + (markeer.has(stap.plaats.naam) ? " hier" : "") + '">' +
    esc(stap.plaats.naam) + "</span>")
    .join('<span class="kr-pijl">' + ikoon("pijl") + "</span>") + "</div>";
}

function kaartTipHtml(stip, vast) {
  const perLijn = new Map();
  for (const r of stip.personen) {
    const l = r.p.lijn || "zonder lijn";
    if (!perLijn.has(l)) perLijn.set(l, []);
    perLijn.get(l).push(r);
  }
  let h = '<div class="kt-kop">' + esc(stip.naam) + '<span class="kt-n">' + stip.personen.length +
    (stip.personen.length === 1 ? " persoon" : " personen") + "</span></div>";
  // in de zweeflijst maximaal vijf personen — met reis en jaartallen erbij wordt
  // een lange lijst anders een toren; de klik-lijst (vast) toont iedereen
  const plafond = vast ? Infinity : 5;
  const hier = new Set([stip.naam]);
  let getoond = 0, verborgen = 0;
  for (const [lijn, rijen] of [...perLijn.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    if (getoond >= plafond) { verborgen += rijen.length; continue; }
    const kleur = lijnKleur(lijn === "zonder lijn" ? "" : lijn);
    h += '<div class="kt-groep" style="--kleur:' + kleur + '">';
    h += '<div class="kt-lijn"><span class="kt-bol" style="background:' + kleur + '"></span>' +
      esc(lijn) + "</div>";
    rijen.sort((a, b) => (+b.p.generatie || 0) - (+a.p.generatie || 0) || a.p.naam.localeCompare(b.p.naam));
    for (const r of rijen) {
      if (getoond >= plafond) { verborgen++; continue; }
      getoond++;
      const jaren = jarenVan(r.p);
      h += '<div class="kt-rij"><a href="' + persoonHash(r.p.id) + '">' + esc(r.p.naam) + "</a>" +
        (jaren ? '<span class="kt-jaren">' + esc(jaren) + "</span>" : "") + "</div>";
      const sub = [r.p.generatie !== "" ? "generatie " + r.p.generatie : "", r.periodes.join("; ")]
        .filter(Boolean).join(" · ");
      if (sub) h += '<div class="kt-sub">' + esc(sub) + "</div>";
      h += reisHtml(r.p, hier);
    }
    h += "</div>";
  }
  if (verborgen) h += '<div class="kt-voet">nog ' + verborgen + " — klik op de stip voor de hele lijst</div>";
  else h += '<div class="kt-voet">' + (vast ? "klik op een naam voor het dossier"
    : "klik op de stip om de lijst vast te zetten") + "</div>";
  return h;
}

function chipsHtml() {
  const lijnen = kaartLijnen();
  if (PERSONEN.some(p => !p.lijn)) lijnen.push("");
  return lijnen.map(l => {
    const aan = FILTER_K.lijnen.has(l);
    const n = PERSONEN.filter(p => (p.lijn || "") === l).length;
    return '<button class="k-chip' + (aan ? " aan" : "") + '" data-klijn="' + esc(l) +
      '" style="--kleur:' + lijnKleur(l) + '" title="' + (aan ? "lijn verbergen" : "lijn tonen") + '">' +
      esc(l || "zonder lijn") + "<span>" + n + "</span></button>";
  }).join("");
}

function genbalkHtml(gens) {
  let h = '<button class="k-gen' + (FILTER_K.gen === "alle" ? " aan" : "") +
    '" data-kgen="alle">alle generaties</button>';
  for (const g of gens) {
    const term = generatieTerm(g);
    h += '<button class="k-gen' + (String(FILTER_K.gen) === String(g) ? " aan" : "") +
      '" data-kgen="' + g + '"' + (term ? ' title="' + esc(term) + '"' : "") + ">" + g + "</button>";
  }
  h += '<span class="k-genknoppen">' +
    '<button class="k-stapknop" data-kstap="-1" title="een generatie ouder">' + ikoon("links") + "</button>" +
    '<button class="k-stapknop" data-kstap="1" title="een generatie jonger">' + ikoon("rechts") + "</button>" +
    '<button class="k-stapknop" id="k-speel" title="loop de generaties af, van oud naar jong">' +
    ikoon(KAART_SPELER ? "stop" : "speel") + (KAART_SPELER ? " stop" : " afspelen") + "</button>" +
    '<button class="k-stapknop' + (FILTER_K.verhuis ? " aan" : "") +
    '" id="k-verhuis" title="verhuislijnen aan of uit">verhuislijnen</button></span>';
  const term = FILTER_K.gen === "alle" ? "" : generatieTerm(+FILTER_K.gen);
  h += '<span class="k-genterm">' + (FILTER_K.gen === "alle" ? "alle generaties tegelijk"
    : "generatie " + esc(FILTER_K.gen) + (term ? " · " + esc(term) : "")) + "</span>";
  return h;
}

function kaartVoetHtml(model) {
  let h = "";
  const legenda = [];
  if (model.bogen.size) {
    legenda.push('<span class="k-booglegenda"></span> verhuizing — de streepjes stromen van vertrek ' +
      "naar aankomst; zweef over een lijn om te zien wie er trokken");
  }
  if (FILTER_K.gen !== "alle" && model.spoken.size) {
    legenda.push('<span class="k-spooklegenda"></span> waar de ouders van deze generatie woonden');
  }
  if (legenda.length) h += '<div class="k-voetregel">' + legenda.join(" · ") + "</div>";
  if (model.zonder.length) {
    h += '<div class="k-voetregel">Nog geen enkele plaats bekend (de muren): ' +
      model.zonder.map(p => '<a href="' + persoonHash(p.id) + '">' + esc(p.naam) + "</a>").join(" · ") + "</div>";
  }
  if (model.onbekend.size) {
    h += '<div class="k-voetregel">Plaats nog niet in <code>plaatsen.json</code>: ' +
      [...model.onbekend.entries()].map(([n, a]) => esc(n) + (a > 1 ? " (" + a + ")" : "")).join(", ") + "</div>";
  }
  return h;
}

function stopKaartSpeler() {
  if (KAART_SPELER) { clearInterval(KAART_SPELER); KAART_SPELER = null; }
}

function ruimKaartOp() {
  stopKaartSpeler();
  if (KAART_MAP) { KAART_MAP.remove(); KAART_MAP = null; KAART_LAGEN = null; }
}

function kaartStap(richting) {
  const gens = kaartGens();
  if (!gens.length) return;
  if (FILTER_K.gen === "alle") {
    FILTER_K.gen = String(richting < 0 ? gens[0] : gens[gens.length - 1]);
  } else {
    const i = gens.indexOf(+FILTER_K.gen);
    FILTER_K.gen = String(gens[Math.min(gens.length - 1, Math.max(0, i + richting))]);
  }
  werkKaartBij();
}

function speelKaart() {
  if (KAART_SPELER) { stopKaartSpeler(); werkKaartBij(); return; }
  const gens = kaartGens();
  if (!gens.length) return;
  FILTER_K.gen = String(gens[0]);
  KAART_SPELER = setInterval(() => {
    if (!KAART_MAP || !/^#\/kaart/.test(location.hash)) { stopKaartSpeler(); return; }
    const i = kaartGens().indexOf(+FILTER_K.gen);
    if (i < 0 || i >= kaartGens().length - 1) { stopKaartSpeler(); werkKaartBij(); return; }
    FILTER_K.gen = String(kaartGens()[i + 1]);
    werkKaartBij();
  }, 2000);
  werkKaartBij();
}

function werkKaartBij(meteen) {
  if (!KAART_MAP) return;
  if (!FILTER_K.geinit) {
    FILTER_K.geinit = true;
    kaartLijnen().forEach(l => FILTER_K.lijnen.add(l));
    if (PERSONEN.some(p => !p.lijn)) FILTER_K.lijnen.add("");
  }
  const gens = kaartGens();
  if (FILTER_K.gen !== "alle" && !gens.includes(+FILTER_K.gen)) FILTER_K.gen = "alle";
  const model = kaartModelMaken(FILTER_K.gen);
  KAART_MODEL = model;

  document.getElementById("k-chips").innerHTML = chipsHtml();
  document.getElementById("k-genwrap").innerHTML = genbalkHtml(gens);
  const uniek = new Set([...model.stippen.values()].flatMap(s => s.personen.map(r => r.p.id))).size;
  const totaal = kaartZichtbaar(FILTER_K.gen).length;
  document.getElementById("k-teller").innerHTML = uniek + " van " + totaal +
    (totaal === 1 ? " persoon" : " personen") + " op de kaart · " +
    model.stippen.size + (model.stippen.size === 1 ? " plaats" : " plaatsen");
  document.getElementById("k-voet").innerHTML = kaartVoetHtml(model);
  const leeg = document.getElementById("kaart-leeg");
  if (leeg) leeg.hidden = !!model.stippen.size;

  KAART_LAGEN.clearLayers();
  for (const b of model.bogen.values()) {
    const boog = L.polyline(boogPunten(b.van, b.naar), {
      color: lijnKleur(b.lijn), weight: Math.min(4.5, 1.2 + b.n * 0.5), opacity: .55,
      dashArray: "7 5", className: "k-boog",
    });
    boog.bindTooltip(boogTipHtml(b), { sticky: true, opacity: 1, className: "k-tip" });
    boog.addTo(KAART_LAGEN);
  }
  for (const s of model.spoken.values()) {
    L.circleMarker([s.lat, s.lon], {
      radius: stipStraal(s.n), color: "#6e6455", weight: 1.6, dashArray: "4 3",
      fill: false, opacity: .8, interactive: false,
    }).addTo(KAART_LAGEN);
  }
  for (const stip of model.stippen.values()) {
    const R = stipStraal(stip.personen.length);
    const mk = L.marker([stip.lat, stip.lon], { icon: stipIcoon(stip), riseOnHover: true, keyboard: false });
    mk.bindTooltip(kaartTipHtml(stip, false),
      { direction: "top", offset: [0, -R - 4], opacity: 1, className: "k-tip" });
    mk.bindPopup(kaartTipHtml(stip, true),
      { maxWidth: 330, className: "k-tip-vast", autoPanPadding: [40, 40] });
    mk.on("click", () => mk.closeTooltip());
    mk.addTo(KAART_LAGEN);
  }

  const punten = [...model.stippen.values(), ...model.spoken.values()].map(s => [s.lat, s.lon]);
  if (punten.length) {
    const grenzen = L.latLngBounds(punten).pad(0.25);
    if (meteen) KAART_MAP.fitBounds(grenzen, { maxZoom: 11 });
    else KAART_MAP.flyToBounds(grenzen, { maxZoom: 11, duration: 0.7 });
  }
}

async function toonKaart(genArg) {
  ruimKaartOp();
  // dieplink: #/kaart/8 opent meteen generatie 8
  if (genArg != null && genArg !== "") {
    FILTER_K.gen = genArg === "alle" ? "alle" : String(parseInt(genArg, 10));
    if (FILTER_K.gen === "NaN") FILTER_K.gen = "alle";
  }
  if (typeof L === "undefined") {
    inhoud.innerHTML = '<div class="paneel"><h2>Kaart</h2><div class="leeg-melding">' +
      "<code>leaflet.js</code> is niet geladen — hoort in <code>website/static/</code> te staan. " +
      "Herstart de server en ververs de pagina.</div></div>";
    return;
  }
  if (!PLAATSEN_GIDS) {
    inhoud.innerHTML = '<p class="laadtekst">Kaart laden…</p>';
    try {
      PLAATSEN_GIDS = await fetch("/plaatsen.json")
        .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
    } catch (fout) {
      inhoud.innerHTML = '<div class="paneel"><h2>Kaart</h2><div class="leeg-melding">Kon ' +
        "<code>plaatsen.json</code> niet laden (" + esc(String(fout)) +
        "). Dit bestand kwam er samen met het kaart-tabblad bij — herstart de server.</div></div>";
      return;
    }
    if (!/^#\/kaart/.test(location.hash)) return;
  }

  let h = '<div class="paneel kaartpaneel" id="kaartpaneel"><h2>Kaart — wie woonde waar</h2>';
  h += '<p class="uitleg">Elke stip is een plek uit de dossiers — woonplaats, geboorteplaats of sterfplaats; ' +
    "één bekende plek is genoeg om op de kaart te staan, en het etiket in de lijst zegt wat de plek betekent " +
    "(geboren hier, overleden hier, of de woonjaren). Hoe groter de stip, hoe meer voorouders; de kleur is de " +
    "familielijn. Zweef over een stip om te zien wie — wie verhuisde krijgt daar zijn hele reis bij, met deze " +
    "plek vetgedrukt — en klik voor de lijst met dossierlinks. De stromende lijnen " +
    "zijn de verhuizingen — binnen een leven én van ouder naar kind; zweef erover om te zien wie er trokken. " +
    "Kies een generatie om de familie door de tijd te volgen, of laat de generaties afspelen. " +
    'Plaatscoördinaten staan in <a href="' + verkennerHash("website/static/plaatsen.json") + '">plaatsen.json</a>; ' +
    "de achtergrondkaart komt van OpenStreetMap en vraagt een internetverbinding.</p>";
  h += '<div class="werkbalk kaart-balk"><div class="k-chips" id="k-chips"></div>' +
    '<span class="teller" id="k-teller"></span></div>';
  h += '<div class="k-genbalk" id="k-genwrap"></div>';
  h += '<div class="kaart-vlak" id="kaartvlak"><div id="kaartdoek"></div>' +
    '<div class="kaart-zoom"><button data-kzoom="fit" title="alle stippen in beeld">Passend</button>' +
    '<button data-kzoom="nl" title="heel Nederland">NL</button>' +
    '<button data-kzoom="vol" title="de kaart schermvullend; Esc sluit weer">Volledig scherm</button></div>' +
    '<div id="kaart-offline" class="kaart-melding" hidden>Geen verbinding met de kaartserver — ' +
    "de achtergrondkaart ontbreekt, maar de stippen en filters werken gewoon.</div>" +
    '<div id="kaart-leeg" class="kaart-melding kaart-leeg" hidden>Geen personen binnen de gekozen lijnen en generatie.</div></div>';
  h += '<div class="kaart-voet" id="k-voet"></div></div>';
  inhoud.innerHTML = h;

  KAART_TEGELFOUT = false;
  KAART_MAP = L.map("kaartdoek", { zoomSnap: 0.5 }).setView([52.3, 5.3], 7);
  const tegels = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
    subdomains: "abcd", maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-bijdragers &copy; <a href="https://carto.com/attributions">CARTO</a>',
  });
  tegels.on("tileerror", () => {
    if (KAART_TEGELFOUT) return;
    KAART_TEGELFOUT = true;
    const m = document.getElementById("kaart-offline");
    if (m) m.hidden = false;
  });
  tegels.addTo(KAART_MAP);
  KAART_LAGEN = L.layerGroup().addTo(KAART_MAP);
  KAART_MAP.on("zoomend", () => {
    const doek = document.getElementById("kaartdoek");
    if (doek) doek.classList.toggle("k-metlabels", KAART_MAP.getZoom() >= 9);
  });

  // één klik-afhandelaar voor alle knoppen (overleeft het verversen van de balkjes)
  document.getElementById("kaartpaneel").addEventListener("click", e => {
    const chip = e.target.closest("[data-klijn]");
    if (chip) {
      const l = chip.dataset.klijn;
      if (FILTER_K.lijnen.has(l)) FILTER_K.lijnen.delete(l); else FILTER_K.lijnen.add(l);
      werkKaartBij();
      return;
    }
    const gen = e.target.closest("[data-kgen]");
    if (gen) { stopKaartSpeler(); FILTER_K.gen = gen.dataset.kgen; werkKaartBij(); return; }
    const stap = e.target.closest("[data-kstap]");
    if (stap) { stopKaartSpeler(); kaartStap(+stap.dataset.kstap); return; }
    if (e.target.closest("#k-speel")) { speelKaart(); return; }
    if (e.target.closest("#k-verhuis")) { FILTER_K.verhuis = !FILTER_K.verhuis; werkKaartBij(); return; }
    const zoomKnop = e.target.closest("[data-kzoom]");
    if (zoomKnop && KAART_MAP) {
      if (zoomKnop.dataset.kzoom === "vol") { volledigScherm(document.getElementById("kaartvlak")); return; }
      if (zoomKnop.dataset.kzoom === "nl") { KAART_MAP.flyTo([52.2, 5.35], 7, { duration: 0.7 }); return; }
      const punten = KAART_MODEL
        ? [...KAART_MODEL.stippen.values(), ...KAART_MODEL.spoken.values()].map(s => [s.lat, s.lon]) : [];
      if (punten.length) KAART_MAP.flyToBounds(L.latLngBounds(punten).pad(0.25), { maxZoom: 11, duration: 0.7 });
    }
  });

  werkKaartBij(true);
}

/* ------------------------------------------------------------------ tijdsbeeld */

/* Eén etiket met een rij namen erachter. Vroeger kreeg elke naam zijn eigen
   "raakt" of "personen" ervoor — bij twaalf gekoppelde personen stond het woord
   twaalf keer in de kop en verdronken de namen erin. */
function relatieGroep(label, items) {
  if (!items || !items.length) return "";
  return '<div class="relaties"><span class="rol">' + esc(label) + "</span>" +
    '<span class="relatie-lijst">' + items.join('<span class="scheider">·</span>') + "</span></div>";
}

function gebeurtenisPersonen(g) {
  return g.personen.map(id => {
    const p = PERSOON_MAP[id];
    return p
      ? '<a class="wikilink" href="' + persoonHash(id) + '">' + esc(p.naam) + "</a>"
      : '<span class="wikilink ontbreekt" title="nog geen dossier">' + esc(id) + "</span>";
  });
}

function toonTijdsbeeld() {
  let h = '<div class="paneel"><h2>Tijdsbeeld — wat het land deed terwijl zij leefden</h2>';
  h += '<p class="uitleg">Rampen, oorlogen en epidemieën die de woonplaatsen van de voorouders raakten, ' +
       "gekoppeld aan hun dossiers. Een koppeling is pas ✓ als een bron persoon, gezin of adres direct " +
       "noemt; ◐ betekent: woonde aantoonbaar in het getroffen gebied. De volledige kalender van " +
       'kandidaat-gebeurtenissen staat in <a href="' + verkennerHash("tijdsbeeld/_KALENDER.md") + '">de kalender</a>.</p>';
  if (!TIJDSBEELD.length) {
    h += "<p>Nog geen gebeurtenissen gekoppeld. De doorwerk-skill vult <code>tijdsbeeld/</code> bij elke ronde (stap 6).</p>";
  }
  h += '<ul class="tijdlijn">';
  for (const g of TIJDSBEELD) {
    h += '<li><div class="tb-jaar">' + esc(g.periode) + "</div>";
    h += '<a class="tb-kaart" href="#/gebeurtenis/' + encodeURIComponent(g.id) + '">';
    h += '<div class="tb-kop"><strong>' + esc(g.titel) + "</strong>" + statusHtml(g.status) + "</div>";
    h += '<div class="tb-meta"><span class="chip">' + esc(g.soort) + "</span>" +
         g.plaatsen.map(p => '<span class="chip chip-stil">' + esc(p) + "</span>").join("") + "</div>";
    h += "</a>";
    const pers = gebeurtenisPersonen(g);
    if (pers.length) h += '<div class="tb-personen"><span class="rol">raakt</span> ' + pers.join(" · ") + "</div>";
    h += "</li>";
  }
  h += "</ul></div>";
  inhoud.innerHTML = h;
}

async function toonGebeurtenis(id) {
  const g = GEBEURTENIS_MAP[id];
  if (!g) {
    inhoud.innerHTML = '<div class="paneel"><a class="terug" href="#/tijdsbeeld">← tijdsbeeld</a>' +
      "<h2>" + esc(id) + '</h2><p>Geen gebeurtenisbestand gevonden in <code>tijdsbeeld/</code>.</p></div>';
    return;
  }
  inhoud.innerHTML = '<p class="laadtekst">Gebeurtenis laden…</p>';
  const tekst = await fetch(bestandUrl(g.bestand)).then(r => r.text());
  const { html, kopjes } = mdRender(tekst, "tijdsbeeld");

  let kop = '<div class="info-kaart">';
  kop += '<div class="info-kop"><h2>' + esc(g.titel) + "</h2>" + statusBadge(g.status) +
    leestijdChip(tekst) + "</div>";
  kop += '<div class="info-rooster">';
  kop += "<div><span>periode</span>" + esc(g.periode) + "</div>";
  if (g.soort) kop += "<div><span>soort</span>" + esc(g.soort) + "</div>";
  if (g.plaatsen.length) kop += "<div><span>plaatsen</span>" + esc(g.plaatsen.join(", ")) + "</div>";
  if (g.landing) kop += "<div><span>landing</span>" + esc(g.landing) + "</div>";
  kop += "</div>";
  kop += relatieGroep("raakt", gebeurtenisPersonen(g));
  kop += '<div class="held-acties">' + pdfKnop("tijdsbeeld", g.id, true) + "</div>";
  kop += '<div class="info-voet">bron: <a href="' + verkennerHash(g.bestand) + '">' + esc(g.bestand) + "</a></div>";
  kop += "</div>";

  inhoud.innerHTML = '<div class="paneel lees">' +
    '<a class="terug" href="#/tijdsbeeld">← alle gebeurtenissen</a>' +
    kop + leeslaag(html, kopjes) + "</div>";
  koppelPdfKnoppen();
  werkLeespaginaBij();
}

/* De twee "queries" onderaan een dossier: in welke tijdsbeeld-gebeurtenissen
   en in welke verhalen komt deze persoon voor? Gekoppeld via de frontmatter,
   of alleen genoemd in de lopende tekst — dat laatste krijgt een eigen label. */

function tijdsbeeldStrip(persoonId) {
  const items = TIJDSBEELD.filter(g =>
    g.personen.includes(persoonId) || (g.genoemd || []).includes(persoonId));
  if (!items.length) return "";
  let h = '<h3 class="galerij-kop">Wat er om dit leven heen gebeurde ' +
          '<a class="mapje" href="#/tijdsbeeld">alle gebeurtenissen</a></h3>';
  h += '<div class="tb-strip">';
  for (const g of items) {
    const alleenGenoemd = !g.personen.includes(persoonId);
    h += '<a class="tb-mini" href="#/gebeurtenis/' + encodeURIComponent(g.id) + '">' +
      '<span class="tb-jaar">' + esc(g.periode) + "</span>" +
      '<span class="tb-titel">' + esc(g.titel) + "</span>" +
      '<span class="tb-voet"><span class="chip">' + esc(g.soort) + "</span>" + statusHtml(g.status) +
      (alleenGenoemd ? '<span class="chip chip-stil" title="komt voor in de tekst, niet als gekoppelde persoon">genoemd in de tekst</span>' : "") +
      "</span></a>";
  }
  h += "</div>";
  return h;
}

function verhalenStrip(persoonId) {
  const items = VERHALEN.filter(v =>
    (v.personen || []).includes(persoonId) || (v.genoemd || []).includes(persoonId));
  if (!items.length) return "";
  items.sort((a, b) => (jaarGetal(a) || 9999) - (jaarGetal(b) || 9999) ||
    String(a.titel).localeCompare(String(b.titel)));
  let h = '<h3 class="galerij-kop">Verhalen waarin deze persoon voorkomt ' +
          '<a class="mapje" href="#/verhalen">alle verhalen</a></h3>';
  h += '<div class="tb-strip">';
  for (const v of items) {
    const alleenGenoemd = !(v.personen || []).includes(persoonId);
    h += '<a class="tb-mini v-mini" href="' + verhaalHash(v.id) + '">' +
      '<span class="tb-jaar">' + esc(v.periode || "—") + "</span>" +
      '<span class="tb-titel">' + esc(v.titel) + "</span>" +
      '<span class="tb-voet">' +
      (v.rubriek ? '<span class="chip">' + esc(v.rubriek) + "</span>" : "") +
      '<span class="chip chip-stil" title="hoe bijzonder (1-20)">' + (v.score != null ? v.score : "?") + "/20</span>" +
      (alleenGenoemd ? '<span class="chip chip-stil" title="komt voor in de tekst, niet als hoofdpersoon">genoemd in de tekst</span>' : "") +
      "</span></a>";
  }
  h += "</div>";
  return h;
}

/* ------------------------------------------------------------------ verhalen */

function verhaalPersonenNamen(v) {
  return (v.personen || []).map(id => (PERSOON_MAP[id] ? PERSOON_MAP[id].naam : id));
}

/* De score 1-20 uit de frontmatter, vertaald naar de banden uit het sjabloon.
   Die banden zijn ook de groepkoppen als er op bijzonderheid gesorteerd wordt. */
const SCORE_BANDEN = [
  [17, "uitzonderlijk", "b5"],
  [13, "bijzondere wending", "b4"],
  [9, "opvallend", "b3"],
  [5, "informatief", "b2"],
  [1, "administratief", "b1"],
];

function scoreBand(score) {
  if (score == null) return { naam: "nog niet gescoord", klasse: "b0" };
  for (const [vanaf, naam, klasse] of SCORE_BANDEN) {
    if (score >= vanaf) return { naam, klasse };
  }
  return { naam: "administratief", klasse: "b1" };
}

const STERKTE_UITLEG = {
  sterk: "sterk — volgt uit aktes",
  mager: "mager — deels uit een bron",
  vermoeden: "vermoeden — nog niet bewezen",
};

function verhaalKaart(v) {
  const namen = verhaalPersonenNamen(v);
  const band = scoreBand(v.score);
  let h = '<a class="v-kaart" href="' + verhaalHash(v.id) + '">';
  h += '<div class="v-kop"><span class="v-periode">' + esc(v.periode || "—") + "</span>" +
    '<span class="v-score ' + band.klasse + '" title="' + esc(band.naam) + " — score " +
    (v.score != null ? v.score : "?") + ' van 20"><span class="v-baan"><span class="v-vulling" style="width:' +
    (v.score ? Math.min(100, v.score * 5) : 0) + '%"></span></span>' +
    (v.score != null ? v.score : "?") + "</span></div>";
  h += "<h3>" + esc(v.titel) + "</h3>";
  if (v.aanhef) h += '<p class="v-aanhef">' + esc(v.aanhef) + "</p>";
  h += '<div class="v-voet">' +
    (v.rubriek ? '<span class="chip">' + esc(v.rubriek) + "</span>" : "") +
    (v.lijn ? '<span class="chip chip-stil">' + esc(v.lijn) + "</span>" : "") +
    (v.sterkte ? '<span class="sterkte sterkte-' + esc(v.sterkte) + '" title="' +
      esc(STERKTE_UITLEG[v.sterkte] || v.sterkte) + '">' + esc(v.sterkte) + "</span>" : "") +
    "</div>";
  if (namen.length) h += '<div class="v-personen">' + esc(namen.join(" · ")) + "</div>";
  h += "</a>";
  return h;
}

function verhaalZoektekst(v) {
  return [v.titel, v.periode, v.rubriek, v.lijn, v.aanhef, verhaalPersonenNamen(v).join(" ")]
    .join(" ").toLowerCase();
}

function jaarGetal(v) {
  const m = /(\d{4})/.exec(String(v.periode || ""));
  return m ? +m[1] : 0;
}

function decenniumVan(v) {
  const jaar = jaarGetal(v);
  if (!jaar) return "periode onbekend";
  const begin = Math.floor(jaar / 10) * 10;
  return begin + "–" + (begin + 9);
}

function toonVerhalen() {
  const lijnen = [...new Set(VERHALEN.map(v => v.lijn).filter(Boolean))].sort();
  const rubriekTelling = new Map();
  for (const v of VERHALEN) {
    if (v.rubriek) rubriekTelling.set(v.rubriek, (rubriekTelling.get(v.rubriek) || 0) + 1);
  }
  const rubrieken = [...rubriekTelling.keys()].sort();
  const term = FILTER_V.zoek.trim().toLowerCase();

  let lijst = VERHALEN.filter(v =>
    (!FILTER_V.lijn || v.lijn === FILTER_V.lijn) &&
    (!FILTER_V.rubriek || v.rubriek === FILTER_V.rubriek) &&
    (!term || verhaalZoektekst(v).includes(term)));
  if (FILTER_V.sort === "periode") {
    lijst.sort((a, b) => (jaarGetal(a) || 9999) - (jaarGetal(b) || 9999) ||
      String(a.titel).localeCompare(String(b.titel)));
  } else {
    lijst.sort((a, b) => (b.score || 0) - (a.score || 0) || String(a.titel).localeCompare(String(b.titel)));
  }

  const gefilterd = FILTER_V.lijn || FILTER_V.rubriek || term;

  let h = '<div class="paneel">';
  h += '<div class="v-hoofd"><div><h2>Verhalen</h2>' +
    '<p class="uitleg">Wat er tussen de aktes vandaan kwam: losse vondsten met bron, ' +
    "de voorraadkamer van het boek. Elk verhaal heeft een score voor hoe bijzonder het is (1-20) " +
    "en de familielijn waar het bij hoort.</p></div>" +
    '<div class="v-totaal"><strong>' + VERHALEN.length + "</strong><span>verhalen</span></div></div>";

  h += '<div class="werkbalk v-werkbalk">';
  h += '<span class="v-zoekwikkel"><input id="v-zoek" type="search" placeholder="Zoek in de verhalen" ' +
    'autocomplete="off" value="' + esc(FILTER_V.zoek) + '"></span>';
  h += '<label>Lijn <select id="v-lijn"><option value="">alle</option>' +
    lijnen.map(l => "<option" + (FILTER_V.lijn === l ? " selected" : "") + ">" + esc(l) + "</option>").join("") +
    "</select></label>";
  h += '<label>Sorteer <select id="v-sort">' +
    '<option value="score"' + (FILTER_V.sort === "score" ? " selected" : "") + ">bijzonderheid</option>" +
    '<option value="periode"' + (FILTER_V.sort === "periode" ? " selected" : "") + ">periode</option>" +
    "</select></label>";
  h += '<span class="teller">' + lijst.length + " van " + VERHALEN.length +
    (gefilterd ? ' · <button class="wis-filters" id="v-wisfilters">wis filters</button>' : "") + "</span>";
  h += "</div>";

  h += '<div class="rubriek-balk">' + rubrieken.map(r =>
    '<button class="rub-chip' + (FILTER_V.rubriek === r ? " aan" : "") + '" data-rubriek="' + esc(r) + '">' +
    esc(r) + '<span class="rub-n">' + rubriekTelling.get(r) + "</span></button>").join("") + "</div>";

  if (!lijst.length) {
    h += '<div class="leeg-melding">Geen verhalen die aan de filters voldoen' +
      (term ? ' voor “' + esc(FILTER_V.zoek) + "”" : "") + ".</div>";
  } else {
    // groeperen: op bijzonderheid in banden, op periode per decennium
    const groepen = new Map();
    for (const v of lijst) {
      const sleutel = FILTER_V.sort === "periode" ? decenniumVan(v) : scoreBand(v.score).naam;
      if (!groepen.has(sleutel)) groepen.set(sleutel, []);
      groepen.get(sleutel).push(v);
    }
    for (const [naam, groep] of groepen) {
      h += '<div class="groepkop"><span class="groep-gen">' + esc(naam) + "</span>" +
        '<span class="groep-aantal">' + groep.length + "</span></div>";
      h += '<div class="v-rooster">' + groep.map(verhaalKaart).join("") + "</div>";
    }
  }
  h += "</div>";
  inhoud.innerHTML = h;

  const vZoek = document.getElementById("v-zoek");
  vZoek.addEventListener("input", () => {
    FILTER_V.zoek = vZoek.value;
    const cursor = vZoek.selectionStart;
    toonVerhalen();
    const nieuw = document.getElementById("v-zoek");
    nieuw.focus();
    nieuw.setSelectionRange(cursor, cursor);
  });
  const fLijn = document.getElementById("v-lijn");
  if (fLijn) fLijn.addEventListener("change", () => { FILTER_V.lijn = fLijn.value; toonVerhalen(); });
  const fSort = document.getElementById("v-sort");
  if (fSort) fSort.addEventListener("change", () => { FILTER_V.sort = fSort.value; toonVerhalen(); });
  inhoud.querySelectorAll(".rub-chip").forEach(knop => knop.addEventListener("click", () => {
    FILTER_V.rubriek = FILTER_V.rubriek === knop.dataset.rubriek ? "" : knop.dataset.rubriek;
    toonVerhalen();
  }));
  const wis = document.getElementById("v-wisfilters");
  if (wis) wis.addEventListener("click", () => {
    FILTER_V.lijn = ""; FILTER_V.rubriek = ""; FILTER_V.zoek = "";
    toonVerhalen();
  });
}

async function toonVerhaal(id) {
  const v = VERHAAL_MAP[id];
  if (!v) {
    inhoud.innerHTML = '<div class="paneel"><a class="terug" href="#/verhalen">← verhalen</a>' +
      "<h2>" + esc(id) + '</h2><p>Geen verhaal gevonden in <code>boek/verhalen/</code>.</p></div>';
    return;
  }
  inhoud.innerHTML = '<p class="laadtekst">Verhaal laden…</p>';
  const tekst = await fetch(bestandUrl(v.bestand)).then(r => r.text());
  const { html, kopjes } = mdRender(tekst, "boek/verhalen");

  let kop = '<div class="info-kaart">';
  kop += '<div class="info-kop"><h2>' + esc(v.titel) + "</h2>" +
    '<span class="chip" title="hoe bijzonder (1-20)">' + (v.score != null ? v.score : "?") + "/20</span>" +
    leestijdChip(tekst) + "</div>";
  kop += '<div class="info-rooster">';
  if (v.periode) kop += "<div><span>periode</span>" + esc(v.periode) + "</div>";
  if (v.rubriek) kop += "<div><span>rubriek</span>" + esc(v.rubriek) + "</div>";
  if (v.lijn) kop += "<div><span>lijn</span>" + esc(v.lijn) + "</div>";
  if (v.sterkte) kop += "<div><span>sterkte</span>" + esc(v.sterkte) + "</div>";
  kop += "</div>";
  const pers = (v.personen || []).map(pid => {
    const p = PERSOON_MAP[pid];
    return p
      ? '<a class="wikilink" href="' + persoonHash(pid) + '">' + esc(p.naam) + "</a>"
      : '<span class="wikilink ontbreekt" title="nog geen dossier">' + esc(pid) + "</span>";
  });
  kop += relatieGroep(pers.length === 1 ? "persoon" : "personen", pers);
  kop += '<div class="held-acties">' + pdfKnop("verhaal", v.id, true) + "</div>";
  kop += '<div class="info-voet">bron: <a href="' + verkennerHash(v.bestand) + '">' + esc(v.bestand) + "</a></div>";
  kop += "</div>";

  inhoud.innerHTML = '<div class="paneel lees">' +
    '<a class="terug" href="#/verhalen">← alle verhalen</a>' +
    kop + leeslaag(html, kopjes, "verhaal-lees") + "</div>";
  koppelPdfKnoppen();
  werkLeespaginaBij();
}

/* ------------------------------------------------------------- persoonsdossier */

function familieKaart(id, rol) {
  if (!id) return "";
  const p = PERSOON_MAP[id];
  if (p) {
    return '<a class="fkaart" href="' + persoonHash(id) + '">' + monogramHtml(p, "fk-mono") +
      '<span class="fk-tekst"><span class="rol">' + esc(rol) + "</span>" +
      '<span class="fk-naam">' + esc(p.naam) + "</span>" +
      '<span class="fk-jaren">' + (esc(jarenVan(p)) || "&nbsp;") + "</span></span></a>";
  }
  return '<span class="fkaart spook" title="nog geen dossier"><span class="rol">' + esc(rol) + "</span>" +
    '<span class="fk-naam">' + esc(id) + '</span><span class="fk-jaren">nog geen dossier</span></span>';
}

function docDatumType(naam) {
  const m = /^(\d{4})-(\d{2})-(\d{2})_([a-z]+)/.exec(naam);
  if (!m) return { datum: "", type: "" };
  let datum = m[1];
  if (m[2] !== "00") datum = m[3] !== "00" ? m[3] + "-" + m[2] + "-" + m[1] : m[2] + "-" + m[1];
  return { datum, type: m[4] };
}

function documentGalerij(persoonId) {
  const map = zoekKnoop("documenten/" + persoonId);
  if (!map || !map.kinderen || !map.kinderen.length) return "";
  const bestanden = map.kinderen.filter(k => k.type === "bestand");
  const scans = bestanden.filter(b => !b.naam.endsWith(".md"));
  // vervolgscans (_2, _3) hebben geen eigen beschrijvingsbestand: hun basisnaam telt
  const scanBasis = new Set(scans.map(b => b.naam.replace(/(_\d+)?\.[^.]+$/, "")));
  const losseMd = bestanden.filter(b => b.naam.endsWith(".md") && !scanBasis.has(b.naam.slice(0, -3)));

  let h = '<h3 class="galerij-kop">Documentenmap <a class="mapje" href="' + verkennerHash(map.pad) + '">' +
    ikoon("map") + " " + esc(map.pad) + "</a></h3>";
  h += '<div class="galerij">';
  for (const b of scans.concat(losseMd)) {
    const { datum, type } = docDatumType(b.naam);
    const isBeeld = /\.(jpe?g|png|gif|webp)$/i.test(b.naam);
    const isPdf = /\.pdf$/i.test(b.naam);
    const mBlad = /_(\d+)\.[^.]+$/.exec(b.naam);
    // archief-URL: staat op het beschrijvingsbestand (de scan zelf heeft er geen)
    const mdKnoop = b.naam.endsWith(".md") ? b : zoekKnoop(beschrijvingsPad(b.pad), map.kinderen);
    const archiefUrl = mdKnoop && mdKnoop.url;
    h += '<div class="doc-kaart">';
    h += '<a class="doc-binnen" href="' + verkennerHash(b.pad) + '" title="' + esc(b.naam) + '">';
    if (isBeeld) h += '<img src="' + bestandUrl(b.pad) + '" loading="lazy" alt="">';
    else h += '<div class="doc-icoon">' + ikoon(isPdf ? "boek" : "doc") + "</div>";
    h += '<div class="doc-tekst"><strong>' + esc(type || b.naam) + (mBlad ? " (blad " + mBlad[1] + ")" : "") + "</strong>" +
         (datum ? "<span>" + esc(datum) + "</span>" : "") + "</div></a>";
    if (archiefUrl) {
      h += '<a class="doc-archief" href="' + esc(archiefUrl) + '" target="_blank" rel="noopener" title="' +
        esc(archiefUrl) + '">' + ikoon("extern") + " bekijk in het archief</a>";
    }
    h += "</div>";
  }
  h += "</div>";
  return h;
}

async function toonPersoon(id) {
  const p = PERSOON_MAP[id];
  if (!p) {
    inhoud.innerHTML = '<div class="paneel"><a class="terug" href="javascript:history.back()">← terug</a>' +
      "<h2>" + esc(id) + '</h2><p>Voor deze persoon is nog geen dossier aangemaakt in <code>personen/</code>.</p></div>';
    return;
  }
  inhoud.innerHTML = '<p class="laadtekst">Dossier laden…</p>';
  const antwoord = await fetch(bestandUrl(p.bestand));
  const tekst = await antwoord.text();
  const { html, kopjes } = mdRender(tekst, padOuder(p.bestand));

  const leeftijd = leeftijdVan(p);
  let kop = '<div class="held rand-' + statusKlasse(p.status) + '">';
  kop += '<div class="held-kop">' + monogramHtml(p, "held-mono") +
    "<h2>" + esc(p.naam) + "</h2>" +
    (jarenVan(p) ? '<span class="held-jaren">' + esc(jarenVan(p)) +
      (leeftijd ? ' <span class="held-leeftijd">· ' + esc(leeftijd) + "</span>" : "") + "</span>" : "") +
    statusBadge(p.status) + "</div>";
  kop += '<div class="held-feiten">';
  if (p.geboren) kop += "<div><span>geboren</span>* " + esc(p.geboren) + "</div>";
  if (p.overleden) kop += "<div><span>overleden</span>† " + esc(p.overleden) + "</div>";
  if (p.beroep) kop += "<div><span>beroep</span>" + esc(p.beroep) + "</div>";
  if (p.lijn) kop += "<div><span>lijn</span>" + esc(p.lijn) + "</div>";
  if (p.generatie !== "") {
    const term = generatieTerm(+p.generatie);
    kop += '<div><span>generatie</span><abbr title="' + esc(INSTELLINGEN.generatie_uitleg || "t.o.v. jezelf = 0") + '">' + esc(p.generatie) + "</abbr>" +
      (term ? " · " + esc(term) : "") + "</div>";
  }
  if ((p.woonplaatsen || []).length) kop += "<div><span>woonplaatsen</span>" + esc(p.woonplaatsen.join("; ")) + "</div>";
  kop += "</div>";
  kop += '<div class="held-acties">' +
    '<a class="knopje" href="#/boom/' + encodeURIComponent(p.id) + '">' + ikoon("boompje") + " Toon in de stamboom</a>" +
    pdfKnop("persoon", p.id) +
    '<a class="knopje stil" href="' + verkennerHash(p.bestand) + '">' + ikoon("doc") + " Dossierbestand</a></div>";
  kop += '<div class="held-voet">bron: ' + esc(p.bestand) +
    (p.bijgewerkt ? " · bijgewerkt " + esc(p.bijgewerkt) : "") + "</div>";
  kop += "</div>";

  const familie = familieKaart(p.vader, "vader") + familieKaart(p.moeder, "moeder") +
    familieKaart(p.partner, "partner") + p.kinderen.map(k => familieKaart(k, "kind")).join("");

  inhoud.innerHTML = '<div class="paneel lees">' +
    '<a class="terug" href="javascript:history.back()">← terug</a>' +
    kop +
    (familie ? '<div class="familie">' + familie + "</div>" : "") +
    documentGalerij(p.id) +
    leeslaag(html, kopjes) +
    verhalenStrip(p.id) + tijdsbeeldStrip(p.id) + "</div>";
  koppelPdfKnoppen();
  werkLeespaginaBij();
}

/* ------------------------------------------------------------------ verkenner */

const BESTAND_IKONEN = [
  [/\.md$/i, "doc"], [/\.(jpe?g|png|gif|webp)$/i, "beeld"], [/\.pdf$/i, "boek"],
  [/\.(py|cmd|bat|ps1|js|css|html|json)$/i, "code"],
];

function bestandIkoon(naam) {
  for (const [re, ic] of BESTAND_IKONEN) if (re.test(naam)) return ikoon(ic);
  return ikoon("klem");
}

function verkennerTak(knopen, selectie) {
  let h = "<ul>";
  for (const k of knopen) {
    if (k.type === "map") {
      const open = OPEN_MAPPEN.has(k.pad) || (selectie && selectie.startsWith(k.pad + "/"));
      if (open) OPEN_MAPPEN.add(k.pad);
      h += '<li><details data-map="' + esc(k.pad) + '"' + (open ? " open" : "") + ">" +
           "<summary>" + ikoon("map") + esc(k.naam) + "</summary>" +
           verkennerTak(k.kinderen || [], selectie) + "</details></li>";
    } else {
      const actief = k.pad === selectie ? ' class="actief"' : "";
      h += "<li><a" + actief + ' href="' + verkennerHash(k.pad) + '">' + bestandIkoon(k.naam) + esc(k.naam) + "</a></li>";
    }
  }
  return h + "</ul>";
}

async function bestandWeergave(pad) {
  const naam = pad.split("/").pop();
  const kruimels = '<div class="kruimels">' + pad.split("/").map((d, i, alle) =>
    i === alle.length - 1 ? "<strong>" + esc(d) + "</strong>" : esc(d)).join(" / ") + "</div>";

  if (/\.(jpe?g|png|gif|webp)$/i.test(naam)) {
    let h = kruimels + '<a href="' + bestandUrl(pad) + '" target="_blank" title="open origineel in nieuw tabblad">' +
      '<img class="scan" src="' + bestandUrl(pad) + '" alt="' + esc(naam) + '"></a>';
    const mdPad = beschrijvingsPad(pad);
    const mdKnoop = zoekKnoop(mdPad);
    if (mdKnoop && mdKnoop.url) {
      h += '<p class="archief-regel"><a href="' + esc(mdKnoop.url) + '" target="_blank" rel="noopener">' +
        ikoon("extern") + " bekijk in het archief (" +
        esc(mdKnoop.url.replace(/^https?:\/\/(www\.)?/, "").split("/")[0]) + ")</a></p>";
    }
    if (mdKnoop) {
      const tekst = await fetch(bestandUrl(mdPad)).then(r => r.text());
      const { html, frontmatter, kopjes } = mdRender(tekst, padOuder(mdPad));
      h += '<div class="beschrijving"><h3>Transcriptie &amp; bronvermelding</h3>' +
           frontmatterTabel(frontmatter) + leeslaag(html, kopjes, "strip-alleen") + "</div>";
    }
    return h;
  }
  if (/\.pdf$/i.test(naam)) {
    return kruimels + '<object class="pdf" data="' + bestandUrl(pad) + '" type="application/pdf">' +
      '<p>PDF kan hier niet worden getoond — <a href="' + bestandUrl(pad) + '" target="_blank">open in nieuw tabblad</a>.</p></object>';
  }
  if (/\.(md|txt|py|cmd|json|gitignore)$/i.test(naam) || !/\./.test(naam)) {
    const tekst = await fetch(bestandUrl(pad)).then(r => r.text());
    if (/\.md$/i.test(naam)) {
      // in de verkenner staat links al een bestandsboom; de inhoudsopgave komt
      // hier daarom als strip bovenaan en niet als tweede kolom ernaast
      const { html, frontmatter, kopjes } = mdRender(tekst, padOuder(pad));
      return kruimels + frontmatterTabel(frontmatter) + leeslaag(html, kopjes, "strip-alleen");
    }
    return kruimels + '<pre class="codeblok">' + esc(tekst) + "</pre>";
  }
  return kruimels + '<p><a href="' + bestandUrl(pad) + '" target="_blank">' + ikoon("klem") + " " + esc(naam) + " openen/downloaden</a></p>";
}

async function toonVerkenner(selectiePad) {
  const rechts = '<p class="uitleg">Kies links een bestand. Mappen klappen open en dicht; ' +
    "md-bestanden worden leesbaar weergegeven, scans met hun transcriptie eronder.</p>";
  inhoud.innerHTML =
    '<div class="verkenner">' +
    '<nav class="v-boom">' + verkennerTak(VERKENNER, selectiePad) + "</nav>" +
    '<section class="v-weergave" id="v-weergave">' +
    (selectiePad ? '<p class="laadtekst">Laden…</p>' : rechts) + "</section></div>";

  // open/dicht-status onthouden
  inhoud.querySelectorAll("details[data-map]").forEach(d => {
    d.addEventListener("toggle", () => {
      if (d.open) OPEN_MAPPEN.add(d.dataset.map); else OPEN_MAPPEN.delete(d.dataset.map);
    });
  });

  if (selectiePad) {
    const weergave = document.getElementById("v-weergave");
    try {
      weergave.innerHTML = await bestandWeergave(selectiePad);
    } catch (fout) {
      weergave.innerHTML = "<p>Kon bestand niet laden: " + esc(String(fout)) + "</p>";
    }
    const actief = inhoud.querySelector(".v-boom a.actief");
    if (actief) actief.scrollIntoView({ block: "center" });
    werkLeespaginaBij();
  }
}

/* ------------------------------------------------------------------ zoeken */

const zoekveld = document.getElementById("zoek");
const zoeklijst = document.getElementById("zoeklijst");
let SUG_IDX = -1;

function verbergSuggesties() {
  zoeklijst.hidden = true;
  zoeklijst.innerHTML = "";
  SUG_IDX = -1;
}

function bouwSuggesties() {
  const term = ZOEKTERM.toLowerCase();
  if (!term) { verbergSuggesties(); return; }
  const treffers = PERSONEN.filter(p => zoekTekst(p).includes(term));
  const top = treffers.slice(0, 8);
  SUG_IDX = -1;
  let h = top.map(p =>
    '<a class="zoek-item" href="' + persoonHash(p.id) + '">' + monogramHtml(p, "zs-mono") +
    '<span class="zi-tekst"><strong>' + esc(p.naam) + "</strong>" +
    "<span>" + esc([jarenVan(p), p.beroep, p.lijn].filter(Boolean).join(" · ")) + "</span></span></a>").join("");
  if (!treffers.length) {
    h = '<span class="zoek-leeg">Geen persoon gevonden voor “' + esc(ZOEKTERM) + "”</span>";
  } else {
    h += '<a class="zoek-alles" href="#/personen">Alle ' + treffers.length + " treffers in Personen</a>";
  }
  zoeklijst.innerHTML = h;
  zoeklijst.hidden = false;
}

function suggestieItems() {
  return [...zoeklijst.querySelectorAll(".zoek-item, .zoek-alles")];
}

zoekveld.addEventListener("input", () => {
  ZOEKTERM = zoekveld.value.trim();
  const opPersonen = /^#\/personen/.test(location.hash);
  if (opPersonen) { verbergSuggesties(); toonPersonen(); }
  else bouwSuggesties();
});

zoekveld.addEventListener("keydown", e => {
  const items = suggestieItems();
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    if (!items.length) return;
    e.preventDefault();
    SUG_IDX = e.key === "ArrowDown"
      ? (SUG_IDX + 1) % items.length
      : (SUG_IDX - 1 + items.length) % items.length;
    items.forEach((el, i) => el.classList.toggle("actief", i === SUG_IDX));
  } else if (e.key === "Enter") {
    if (SUG_IDX >= 0 && items[SUG_IDX]) items[SUG_IDX].click();
    else location.hash = "#/personen";
    verbergSuggesties();
  } else if (e.key === "Escape") {
    verbergSuggesties();
  }
});

zoekveld.addEventListener("focus", () => { if (ZOEKTERM && !/^#\/personen/.test(location.hash)) bouwSuggesties(); });
document.addEventListener("click", e => { if (!e.target.closest(".zoekdoos")) verbergSuggesties(); });

// de sneltoets van elke leeswebsite: "/" springt naar het zoekveld
document.addEventListener("keydown", e => {
  if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
  const doel = e.target;
  if (doel && (doel.tagName === "INPUT" || doel.tagName === "TEXTAREA" || doel.tagName === "SELECT" || doel.isContentEditable)) return;
  e.preventDefault();
  zoekveld.focus();
  zoekveld.select();
});

/* ------------------------------------------------------------------ zweefkaart
   Wie over een link naar een persoon, gebeurtenis of verhaal zweeft, krijgt na
   een korte pauze een voorproefje: naam, jaren, beroep, plaatsen. Alles komt
   uit de al geladen lijsten, dus er is geen extra serververkeer. De kaart
   vangt zelf geen muis (pointer-events: none) en kan dus nooit een klik
   blokkeren. Grote kaarten die deze informatie al tonen (personen-tegels,
   verhaal- en tijdsbeeldkaarten, zoeksuggesties) slaan we over. */

const zweefkaart = document.createElement("div");
zweefkaart.className = "zweefkaart";
zweefkaart.hidden = true;
document.body.appendChild(zweefkaart);

let ZWEEF_TIMER = null;
let ZWEEF_ANKER = null;

function persoonNaamVan(id) {
  const p = PERSOON_MAP[id];
  return p ? p.naam : id;
}

function zkRegel(html) {
  return html ? '<div class="zk-regel">' + html + "</div>" : "";
}

/* één regel in de feiten-grid van de persoonszweefkaart: piepklein etiket
   links, de waarde rechts. Lege waarden verdwijnen geruisloos. */
function zweefFeit(label, inhoudHtml) {
  if (!inhoudHtml) return "";
  return '<div class="zk-feit"><span>' + label + "</span><div>" + inhoudHtml + "</div></div>";
}

function zweefPersoon(p) {
  let h = '<div class="zk-soort">persoon</div>';
  h += '<div class="zk-kop">' + esc(p.naam) + statusHtml(p.status) + "</div>";
  const ouders = [p.vader, p.moeder].filter(Boolean).map(persoonNaamVan);
  // de reis van dit leven (geboorteplaats, woonplaatsen, sterfplaats);
  // vraagt plaatsen.json, dat start() alvast meelaadt
  const reis = PLAATSEN_GIDS ? reisHtml(p, new Set()) : "";
  h += '<div class="zk-feiten">' +
    zweefFeit("geboren", p.geboren ? esc(p.geboren) : "") +
    zweefFeit("overleden", p.overleden ? esc(p.overleden) : "") +
    zweefFeit("beroep", p.beroep ? esc(p.beroep) : "") +
    zweefFeit("woonde", (p.woonplaatsen || []).length ? esc(p.woonplaatsen.join("; ")) : "") +
    zweefFeit("reis", reis) +
    zweefFeit("ouders", ouders.length ? esc(ouders.join(" en ")) : "") +
    zweefFeit("partner", p.partner ? esc(persoonNaamVan(p.partner)) : "") +
    "</div>";
  let voet = "";
  if (p.lijn) voet += '<span class="chip">' + esc(p.lijn) + "</span>";
  if (p.generatie !== "" && generatieTerm(+p.generatie)) {
    voet += '<span class="chip chip-stil">' + esc(generatieTerm(+p.generatie)) + "</span>";
  }
  if (p.documenten) voet += '<span class="chip chip-stil">' + p.documenten + " doc.</span>";
  if (voet) h += '<div class="zk-voet">' + voet + "</div>";
  return h;
}

function zweefGebeurtenis(g) {
  let h = '<div class="zk-soort">tijdsbeeld</div>';
  h += '<div class="zk-kop">' + esc(g.titel) + statusHtml(g.status) + "</div>";
  h += zkRegel([g.periode, g.soort].filter(Boolean).map(esc).join(" · "));
  if (g.plaatsen.length) {
    h += zkRegel(esc(g.plaatsen.slice(0, 6).join(", ")) + (g.plaatsen.length > 6 ? " …" : ""));
  }
  if (g.personen.length) h += zkRegel("raakt " + esc(g.personen.map(persoonNaamVan).join(" · ")));
  return h;
}

function zweefVerhaal(v) {
  const band = scoreBand(v.score);
  let h = '<div class="zk-soort">verhaal</div>';
  h += '<div class="zk-kop">' + esc(v.titel) + "</div>";
  h += zkRegel([v.periode, v.rubriek, v.lijn].filter(Boolean).map(esc).join(" · "));
  if (v.aanhef) h += '<div class="zk-aanhef">' + esc(v.aanhef) + "</div>";
  const namen = verhaalPersonenNamen(v);
  if (namen.length) h += zkRegel("personen: " + esc(namen.join(" · ")));
  let voet = '<span class="chip">' + (v.score != null ? v.score : "?") + "/20 — " + esc(band.naam) + "</span>";
  if (v.sterkte) voet += '<span class="chip chip-stil">' + esc(v.sterkte) + "</span>";
  h += '<div class="zk-voet">' + voet + "</div>";
  return h;
}

function zweefInhoud(href) {
  const m = /^#\/(persoon|gebeurtenis|verhaal)\/(.+)$/.exec(href || "");
  if (!m) return "";
  const id = decodeURIComponent(m[2]);
  if (m[1] === "persoon") { const p = PERSOON_MAP[id]; return p ? zweefPersoon(p) : ""; }
  if (m[1] === "gebeurtenis") { const g = GEBEURTENIS_MAP[id]; return g ? zweefGebeurtenis(g) : ""; }
  const v = VERHAAL_MAP[id];
  return v ? zweefVerhaal(v) : "";
}

function verbergZweefkaart() {
  clearTimeout(ZWEEF_TIMER);
  ZWEEF_TIMER = null;
  ZWEEF_ANKER = null;
  zweefkaart.classList.remove("zichtbaar");
  zweefkaart.hidden = true;
}

function plaatsZweefkaart(anker, html) {
  zweefkaart.innerHTML = html;
  zweefkaart.hidden = false;
  const r = anker.getBoundingClientRect();
  const b = zweefkaart.getBoundingClientRect();
  const x = Math.min(Math.max(8, r.left), window.innerWidth - b.width - 8);
  let y = r.bottom + 8;
  if (y + b.height > window.innerHeight - 8) y = Math.max(8, r.top - b.height - 8);
  zweefkaart.style.left = x + "px";
  zweefkaart.style.top = y + "px";
  requestAnimationFrame(() => zweefkaart.classList.add("zichtbaar"));
}

// alleen op apparaten met een echte muisaanwijzer; op een tablet stoort het
if (window.matchMedia("(hover: hover)").matches) {
  document.addEventListener("mouseover", e => {
    if (!e.target.closest) return;
    const anker = e.target.closest('a[href^="#/"], .vn-ref button');
    if (!anker || anker === ZWEEF_ANKER) return;
    verbergZweefkaart();
    let html = "";
    if (anker.matches(".vn-ref button")) {
      // de voetnoot als voorproefje op de plek waar je leest, in plaats van
      // eerst naar de onderkant van de pagina te moeten springen
      const noot = document.getElementById(anker.dataset.naar || "");
      if (!noot) return;
      const kopie = noot.cloneNode(true);
      kopie.querySelectorAll(".vn-terug").forEach(b => b.remove());
      html = '<div class="zk-soort">voetnoot ' + esc(noot.getAttribute("value") || "") + "</div>" +
        '<div class="zk-vn">' + kopie.innerHTML + "</div>";
    } else {
      if (anker.matches(".p-tegel, .v-kaart, .tb-kaart, .zoek-item")) return;
      html = zweefInhoud(anker.getAttribute("href"));
    }
    if (!html) return;
    ZWEEF_ANKER = anker;
    ZWEEF_TIMER = setTimeout(() => plaatsZweefkaart(anker, html), 350);
  });
  document.addEventListener("mouseout", e => {
    if (ZWEEF_ANKER && !ZWEEF_ANKER.contains(e.relatedTarget)) verbergZweefkaart();
  });
  document.addEventListener("pointerdown", verbergZweefkaart, true);
  document.addEventListener("scroll", verbergZweefkaart, true);
  window.addEventListener("hashchange", verbergZweefkaart);
}

/* ------------------------------------------------------------------ cijfers
   Het onderzoek in getallen, live gerekend uit de geladen dossiers. Alle
   kleuren zijn de vaste entiteitskleuren van de site (lijnen, statussen), en
   elke balk of staaf draagt zijn eigen label en aantal in gewone tekst —
   niemand hoeft kleuren uit elkaar te houden om de cijfers te kunnen lezen. */

function toonCijfers() {
  const nuJaar = new Date().getFullYear();
  const jaartal = veld => { const m = /(\d{4})/.exec(veld || ""); return m ? +m[1] : null; };

  const gens = PERSONEN.map(p => +p.generatie).filter(g => !isNaN(g));
  const diepst = gens.length ? Math.max(...gens) : 0;
  const docs = PERSONEN.reduce((s, p) => s + (+p.documenten || 0), 0);
  const geboortes = PERSONEN.map(p => ({ p, j: jaartal(p.geboren) })).filter(r => r.j);
  const oudste = geboortes.length ? geboortes.reduce((a, b) => (a.j <= b.j ? a : b)) : null;

  const perLijn = new Map();
  for (const p of PERSONEN) { const l = p.lijn || ""; perLijn.set(l, (perLijn.get(l) || 0) + 1); }
  const lijnRijen = [...perLijn.entries()].sort((a, b) => b[1] - a[1]);
  const lijnMax = Math.max(1, ...lijnRijen.map(r => r[1]));

  const statusTelling = {};
  for (const p of PERSONEN) if (p.status) statusTelling[p.status] = (statusTelling[p.status] || 0) + 1;

  const perGen = new Map();
  for (const g of gens) perGen.set(g, (perGen.get(g) || 0) + 1);
  const genRijen = [...perGen.entries()].sort((a, b) => a[0] - b[0]);
  const genMax = Math.max(1, ...genRijen.map(r => r[1]));

  const metLeeftijd = PERSONEN.map(p => {
    const g = jaartal(p.geboren), o = jaartal(p.overleden);
    return g && o && o >= g && o - g <= 115 ? { p, n: o - g } : null;
  }).filter(Boolean);
  const oudsteMens = metLeeftijd.length ? metLeeftijd.reduce((a, b) => (a.n >= b.n ? a : b)) : null;

  const tel = (kaart, sleutel) => { if (sleutel) kaart.set(sleutel, (kaart.get(sleutel) || 0) + 1); };
  const voornamen = new Map();
  for (const p of PERSONEN) {
    const v = String(p.naam).split(/\s+/)[0];
    if (v && v.length > 1) tel(voornamen, v);
  }
  const beroepen = new Map();
  for (const p of PERSONEN) {
    for (let b of String(p.beroep || "").split(/[,;\/]|\ben later\b|\blater\b/)) {
      b = b.trim().toLowerCase();
      if (!b || b === "onbekend" || b === "zonder beroep") continue;
      tel(beroepen, b);
    }
  }
  const plaatsen = new Map();
  for (const p of PERSONEN) {
    for (const w of (p.woonplaatsen || [])) {
      if (!w || w === "[]") continue;
      tel(plaatsen, woonplaatsDelen(w).naam);
    }
  }
  const top = (kaart, n) => [...kaart.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
  const topDocs = [...PERSONEN].filter(p => p.documenten)
    .sort((a, b) => b.documenten - a.documenten).slice(0, 3);

  const persoonLink = p => '<a class="wikilink" href="' + persoonHash(p.id) + '">' + esc(p.naam) + "</a>";
  const record = (etiket, inhoudHtml, sub) =>
    '<div class="c-record"><span class="rol">' + esc(etiket) + "</span>" +
    '<div class="c-record-wat">' + inhoudHtml + "</div>" +
    (sub ? '<div class="c-record-sub">' + sub + "</div>" : "") + "</div>";

  let h = '<div class="paneel cijfers"><h2>Cijfers — het onderzoek in getallen</h2>';
  h += '<p class="uitleg">Alles op deze pagina wordt live uit de dossiers gerekend' +
    (TAK_TITEL ? ", binnen de weergave " + esc(TAK_TITEL) : "") +
    ". Verandert er morgen een dossier, dan veranderen deze cijfers mee.</p>";

  h += '<div class="hero-tegels c-tegels">' +
    heroTegel(PERSONEN.length, "voorouders") +
    heroTegel(diepst + (gens.some(g => g < 0) ? 2 : 1), "generaties") +
    (oudste ? heroTegel(nuJaar - oudste.j, "jaar terug in de tijd") : "") +
    heroTegel(docs, "gescande documenten") +
    heroTegel(VERHALEN.length, "verhalen") +
    heroTegel(TIJDSBEELD.length, "gebeurtenissen") +
    "</div>";

  h += '<section class="c-blok"><h3>Voorouders per familielijn</h3><div class="c-balken">';
  for (const [l, n] of lijnRijen) {
    h += '<div class="c-rij"><span class="c-label">' + esc(l || "zonder lijn") + "</span>" +
      '<span class="c-baan"><span class="c-vul" style="width:' + (n / lijnMax * 100).toFixed(1) +
      "%;background:" + lijnKleur(l) + '"></span></span>' +
      '<span class="c-n">' + n + "</span></div>";
  }
  h += "</div></section>";

  const statusTotaal = ["✓", "◐", "?", "⚠"].reduce((s, k) => s + (statusTelling[k] || 0), 0);
  if (statusTotaal) {
    h += '<section class="c-blok"><h3>Hoe hard het bewijs is</h3><div class="c-status">';
    for (const s of ["✓", "◐", "?", "⚠"]) {
      const n = statusTelling[s] || 0;
      if (!n) continue;
      h += '<span class="c-seg cs-' + statusKlasse(s) + '" style="flex-grow:' + n +
        '" title="' + esc(STATUS_WOORD[s]) + ": " + n + '"></span>';
    }
    h += "</div><div class='c-statuslegenda'>";
    for (const s of ["✓", "◐", "?", "⚠"]) {
      const n = statusTelling[s] || 0;
      if (!n) continue;
      h += '<span class="c-legchip"><span class="status s-' + statusKlasse(s) + '">' + s + "</span> " +
        esc(STATUS_WOORD[s]) + ' <span class="c-n">' + n + "</span></span>";
    }
    h += "</div></section>";
  }

  if (genRijen.length) {
    h += '<section class="c-blok"><h3>Voorouders per generatie</h3><div class="c-kolommen">';
    for (const [g, n] of genRijen) {
      const term = generatieTerm(g);
      h += '<div class="c-kolom" title="generatie ' + g + (term ? " (" + esc(term) + ")" : "") + ": " + n + '">' +
        '<span class="c-kn">' + n + "</span>" +
        '<span class="c-staaf" style="height:' + Math.max(4, Math.round(n / genMax * 110)) + 'px"></span>' +
        '<span class="c-kg">' + g + "</span></div>";
    }
    h += '</div><p class="c-voetnoot">Generatie 0 is de persoon waar de telling begint; hoe hoger het nummer, hoe verder terug in de tijd.</p></section>';
  }

  h += '<section class="c-blok"><h3>Records</h3><div class="c-records">';
  if (oudste) {
    h += record("Verste spoor", persoonLink(oudste.p),
      "geboren rond " + oudste.j + ", zo'n " + (nuJaar - oudste.j) + " jaar geleden");
  }
  if (oudsteMens) {
    h += record("Langste leven", persoonLink(oudsteMens.p), "ongeveer " + oudsteMens.n + " jaar oud geworden");
  }
  if (topDocs.length) {
    h += record("Dikste dossier", topDocs.map(persoonLink).join(" · "),
      topDocs.map(p => p.documenten + " doc.").join(" · "));
  }
  h += record("Diepste generatie", "generatie " + diepst,
    esc(generatieTerm(diepst) || "") || "");
  h += "</div></section>";

  const woordenblok = (kop, rijen, eenheid) => {
    if (!rijen.length) return "";
    return '<div class="c-woorden"><h4>' + esc(kop) + "</h4><div class='c-chips'>" +
      rijen.map(([w, n]) => '<span class="chip chip-stil">' + esc(w) +
        ' <span class="c-n">' + n + "</span></span>").join("") + "</div></div>";
  };
  h += '<section class="c-blok"><h3>De familie in woorden</h3><div class="c-woordenrij">' +
    woordenblok("Meest voorkomende voornamen", top(voornamen, 8)) +
    woordenblok("Beroepen", top(beroepen, 8)) +
    woordenblok("Woonplaatsen", top(plaatsen, 8)) +
    "</div></section>";

  h += "</div>";
  inhoud.innerHTML = h;
}

/* ------------------------------------------------------------- takkenfilter */

/* Een persoon plus alle voorouders daarboven, geklommen langs vader/moeder. */
function voorouderSet(anker) {
  const set = new Set();
  const klim = id => {
    const p = id && PERSOON_MAP[id];
    if (!p || set.has(id)) return;
    set.add(id);
    klim(p.vader);
    klim(p.moeder);
  };
  klim(anker);
  return set;
}

/* Leest ?tak=… uit de URL en snijdt de geladen lijsten erop toe. De site doet
   daarna alsof alleen deze dossiers bestaan: wat buiten de tak valt, verschijnt
   nergens — ook niet in de zoeksuggesties of op de kaart. Een verhaal of
   gebeurtenis blijft staan als hij iemand uit de tak raakt (gekoppeld of in de
   tekst genoemd), een verhaal ook als zijn familielijn binnen de tak valt. */
function pasTakToe() {
  TAK = new URLSearchParams(location.search).get("tak") || "";
  if (!TAK) return;
  let set = null;
  const mLijn = /^lijn:(.+)$/.exec(TAK);
  if (TAKKEN[TAK] && PERSOON_MAP[TAKKEN[TAK].anker]) {
    set = voorouderSet(TAKKEN[TAK].anker);
    TAK_TITEL = TAKKEN[TAK].naam.toLowerCase();
  } else if (mLijn && PERSONEN.some(p => p.lijn === mLijn[1])) {
    set = new Set(PERSONEN.filter(p => p.lijn === mLijn[1]).map(p => p.id));
    TAK_TITEL = "lijn " + mLijn[1];
  } else {
    TAK = "";   // onbekende of lege tak: gewoon alles tonen
    return;
  }
  PERSONEN = PERSONEN.filter(p => set.has(p.id));
  PERSOON_MAP = Object.fromEntries(PERSONEN.map(p => [p.id, p]));
  const lijnen = new Set(PERSONEN.map(p => p.lijn).filter(Boolean));
  const raakt = x => (x.personen || []).some(id => set.has(id)) ||
    (x.genoemd || []).some(id => set.has(id));
  TIJDSBEELD = TIJDSBEELD.filter(raakt);
  VERHALEN = VERHALEN.filter(v => raakt(v) || (v.lijn && lijnen.has(v.lijn)));
  GEBEURTENIS_MAP = Object.fromEntries(TIJDSBEELD.map(g => [g.id, g]));
  VERHAAL_MAP = Object.fromEntries(VERHALEN.map(v => [v.id, v]));
  document.title = (INSTELLINGEN.titel || "Stamboom") + " — " + TAK_TITEL;
}

/* Dezelfde pagina, maar met een andere tak in de query (de hash blijft staan). */
function takUrl(waarde) {
  const url = new URL(location.href);
  if (waarde) url.searchParams.set("tak", waarde);
  else url.searchParams.delete("tak");
  return url.toString();
}

/* Kopieert de volledige URL (mét tak en hash) — dat is de deelbare link.
   navigator.clipboard bestaat alleen op https/localhost; op een netwerkadres
   (http://192.168.…) valt dit terug op het oude execCommand-kopiëren. */
async function kopieerLink(knop) {
  const url = location.href;
  let gelukt = false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      gelukt = true;
    }
  } catch (fout) { /* val terug op het tekstveld hieronder */ }
  if (!gelukt) {
    const veld = document.createElement("textarea");
    veld.value = url;
    veld.style.position = "fixed";
    veld.style.opacity = "0";
    document.body.appendChild(veld);
    veld.select();
    try { gelukt = document.execCommand("copy"); } catch (fout) { gelukt = false; }
    veld.remove();
  }
  const oud = knop.innerHTML;
  knop.innerHTML = gelukt ? "Gekopieerd — plak hem in een bericht" : esc(url);
  setTimeout(() => { knop.innerHTML = oud; }, 2600);
}

function toonTakbalk() {
  const balk = document.getElementById("takbalk");
  if (!balk) return;
  let h = '<span class="tak-etiket">Weergave</span>';
  h += '<a class="tak-knop' + (!TAK ? " aan" : "") + '" href="' + esc(takUrl("")) +
    '" title="alle lijnen en generaties">Hele stamboom</a>';
  for (const sleutel of TAK_KEUZES) {
    const tak = TAKKEN[sleutel];
    h += '<a class="tak-knop' + (TAK === sleutel ? " aan" : "") + '" href="' + esc(takUrl(sleutel)) +
      '" title="' + esc(tak.uitleg) + '">' + esc(tak.naam) + "</a>";
  }
  const actieveLijn = /^lijn:(.+)$/.exec(TAK);
  // binnen een kant toont de keuzelijst alleen de lijnen die eronder vallen
  const lijnKeuzes = TAKKEN[TAK]
    ? [...new Set(PERSONEN.map(p => p.lijn).filter(Boolean))].sort()
    : LIJNEN_VOL;
  h += '<select id="tak-lijn" title="één familielijn apart bekijken">' +
    '<option value="">één lijn…</option>' +
    lijnKeuzes.map(l => '<option value="lijn:' + esc(l) + '"' +
      (actieveLijn && actieveLijn[1] === l ? " selected" : "") + ">" + esc(l) + "</option>").join("") +
    "</select>";
  h += '<button type="button" class="tak-kopieer" id="tak-kopieer" ' +
    'title="kopieer de link van deze weergave om te delen">' + ikoon("klem") + " Deel deze weergave</button>";
  if (TAK) {
    h += '<span class="tak-stand">' + PERSONEN.length +
      (PERSONEN.length === 1 ? " dossier" : " dossiers") + " in deze weergave</span>";
  }
  balk.innerHTML = h;
  balk.hidden = false;
  const keuze = document.getElementById("tak-lijn");
  keuze.addEventListener("change", () => { location.href = takUrl(keuze.value); });
  document.getElementById("tak-kopieer").addEventListener("click", e => kopieerLink(e.currentTarget));
}

/* ------------------------------------------------------------------ routering */

function route() {
  verbergSuggesties();
  const hash = decodeURIComponent(location.hash.replace(/^#\/?/, "")) || "boom";
  const scheiding = hash.indexOf("/");
  const kop = scheiding < 0 ? hash : hash.slice(0, scheiding);
  const rest = scheiding < 0 ? "" : hash.slice(scheiding + 1);

  // de kaart heeft een levend Leaflet-object; opruimen bij het verlaten
  if (kop !== "kaart") ruimKaartOp();

  document.querySelectorAll("#tabs a").forEach(a => {
    const tab = a.dataset.tab;
    const actief = tab === kop || (tab === "verkenner" && kop === "bestand") ||
                   (tab === "personen" && kop === "persoon") ||
                   (tab === "tijdsbeeld" && kop === "gebeurtenis") ||
                   (tab === "verhalen" && kop === "verhaal");
    a.classList.toggle("actief", actief);
  });

  if (kop === "personen") toonPersonen();
  else if (kop === "kaart") toonKaart(rest || null);
  else if (kop === "persoon" && rest) toonPersoon(rest);
  else if (kop === "tijdsbeeld") toonTijdsbeeld();
  else if (kop === "gebeurtenis" && rest) toonGebeurtenis(rest);
  else if (kop === "verhalen") toonVerhalen();
  else if (kop === "verhaal" && rest) toonVerhaal(rest);
  else if (kop === "cijfers") toonCijfers();
  else if (kop === "verkenner") toonVerkenner(rest || null);
  else toonBoom(rest || null);
  window.scrollTo(0, 0);
  werkLeespaginaBij();
}

async function start() {
  try {
    [PERSONEN, VERKENNER, TIJDSBEELD, VERHALEN, INSTELLINGEN] = await Promise.all([
      fetch("/api/personen").then(r => r.json()),
      fetch("/api/verkenner").then(r => r.json()),
      fetch("/api/tijdsbeeld").then(r => r.ok ? r.json() : []).catch(() => []),
      fetch("/api/verhalen").then(r => r.ok ? r.json() : []).catch(() => []),
      fetch("/api/instellingen").then(r => r.ok ? r.json() : {}).catch(() => ({})),
    ]);
  } catch (fout) {
    inhoud.innerHTML = "<p>Kon de gegevens niet laden. Draait de server nog? (" + esc(String(fout)) + ")</p>";
    return;
  }
  PERSOON_MAP = Object.fromEntries(PERSONEN.map(p => [p.id, p]));
  GEBEURTENIS_MAP = Object.fromEntries(TIJDSBEELD.map(g => [g.id, g]));
  VERHAAL_MAP = Object.fromEntries(VERHALEN.map(v => [v.id, v]));
  // naam en titel komen uit stamboom.json; verder weet de site niet wiens boom dit is
  const merk = document.getElementById("merknaam");
  if (merk && INSTELLINGEN.titel) merk.textContent = INSTELLINGEN.titel;
  if (INSTELLINGEN.titel) document.title = INSTELLINGEN.titel;
  // takkenfilter: eerst onthouden wat er allemaal bestaat (voor de balk),
  // dan pas de lijsten toesnijden op de tak uit de URL
  LIJNEN_VOL = [...new Set(PERSONEN.map(p => p.lijn).filter(Boolean))].sort();
  bepaalTakken();
  TAK_KEUZES = Object.keys(TAKKEN).filter(k => PERSOON_MAP[TAKKEN[k].anker]);
  pasTakToe();
  toonTakbalk();
  // plaatsen.json alvast meeladen (klein bestand, niet blokkerend): zo kan de
  // zweefkaart bij een persoon de reis tonen zonder dat het kaart-tabblad
  // eerst open is geweest
  fetch("/plaatsen.json").then(r => r.ok ? r.json() : null)
    .then(g => { if (g && !PLAATSEN_GIDS) PLAATSEN_GIDS = g; })
    .catch(() => {});
  meetKopHoogte();
  route();
}

window.addEventListener("hashchange", route);

start();

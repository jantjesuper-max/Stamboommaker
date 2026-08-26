"""Lokale website voor je stamboomproject.

Starten:   py website/server.py          (of dubbelklik op website/start-website.cmd)
Bekijken:  http://localhost:8123

Alleen Python-standaardbibliotheek, niets te installeren. De server leest de
persoonsdossiers (personen/*.md) en de mappenstructuur live van schijf: elke
wijziging in een dossier is na een verversing (F5) meteen zichtbaar.

Opties:
    py website/server.py 8200            # andere poort
    py website/server.py --geen-browser  # browser niet automatisch openen
    py website/server.py --netwerk       # ook bereikbaar voor andere apparaten
                                         # op hetzelfde (wifi)netwerk
"""

import importlib.util
import json
import mimetypes
import os
import re
import socket
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

WEBSITEMAP = os.path.dirname(os.path.abspath(__file__))
PROJECTMAP = os.path.dirname(WEBSITEMAP)
STATISCHEMAP = os.path.join(WEBSITEMAP, "static")

# stamboom.json is de enige plek waar dit project persoonlijk wordt (naam boven
# de pagina, generatie-uitleg, standaardpoort). Zie scripts/instellingen.py.
sys.path.insert(0, os.path.join(PROJECTMAP, "scripts"))
import instellingen  # noqa: E402

VERBORGEN = {".git", ".claude", "__pycache__", "node_modules"}
WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")

# ---------------------------------------------------------------------------
# PDF-uitdraai (leunt op scripts/pdf.py, dat de markdown door een headless
# browser haalt; hier alleen laden, cachen en één tegelijk draaien)
# ---------------------------------------------------------------------------

_PDF_MODULE = None
_PDF_SLOT = threading.Lock()  # één headless browser tegelijk is genoeg


def pdf_module():
    global _PDF_MODULE
    if _PDF_MODULE is None:
        spec = importlib.util.spec_from_file_location(
            "stamboom_pdf", os.path.join(PROJECTMAP, "scripts", "pdf.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _PDF_MODULE = module
    return _PDF_MODULE


# ---------------------------------------------------------------------------
# Dossiers inlezen
# ---------------------------------------------------------------------------

def lees_frontmatter(pad):
    """Leest het YAML-achtige blok tussen de eerste twee '---'-regels.

    Bewust een simpele parser (geen PyYAML-afhankelijkheid): sleutel: waarde,
    en lijstjes met '- "..."' onder een sleutel.
    """
    try:
        with open(pad, encoding="utf-8") as f:
            regels = f.read().splitlines()
    except OSError:
        return {}
    if not regels or regels[0].strip() != "---":
        return {}
    data = {}
    lijstsleutel = None
    for regel in regels[1:]:
        if regel.strip() == "---":
            break
        if not regel.strip() or regel.strip().startswith("#"):
            continue
        m_lijst = re.match(r"^\s+-\s*(.+)$", regel)
        if m_lijst and lijstsleutel:
            data.setdefault(lijstsleutel, []).append(m_lijst.group(1).strip().strip('"').strip("'"))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", regel)
        if not m:
            continue
        sleutel, waarde = m.group(1), m.group(2).strip()
        # commentaar achter de waarde weghalen (maar niet binnen aanhalingstekens)
        if not waarde.startswith(('"', "'")) and " #" in waarde:
            waarde = waarde.split(" #", 1)[0].strip()
        waarde = waarde.strip().strip('"').strip("'")
        if waarde == "":
            lijstsleutel = sleutel
            data[sleutel] = data.get(sleutel, [])
        else:
            lijstsleutel = None
            data[sleutel] = waarde
    return data


def wikilink_doel(waarde):
    if not isinstance(waarde, str):
        return None
    m = WIKILINK.search(waarde)
    return m.group(1).strip() if m else None


def wikilinks_in_romp(pad):
    """Alle wikilink-doelen uit de romp (ná de frontmatter) van een md-bestand.

    De frontmatter noemt de hoofdpersonen; de tekst zelf noemt er vaak meer
    (getuigen, kinderen, buren). Zo kan de site bij een persoon laten zien in
    welke verhalen en gebeurtenissen die óók genoemd wordt.
    """
    try:
        with open(pad, encoding="utf-8") as f:
            tekst = f.read()
    except OSError:
        return []
    if tekst.startswith("---"):
        einde = tekst.find("\n---", 3)
        if einde != -1:
            tekst = tekst[einde + 4:]
    doelen = []
    for m in WIKILINK.finditer(tekst):
        doel = m.group(1).strip()
        if doel and doel not in doelen:
            doelen.append(doel)
    return doelen


def personen_ophalen():
    """Alle dossiers uit personen/ als lijst van dicts."""
    personenmap = os.path.join(PROJECTMAP, "personen")
    resultaat = []
    if not os.path.isdir(personenmap):
        return resultaat
    for naam in sorted(os.listdir(personenmap)):
        if not naam.endswith(".md") or naam.startswith("_"):
            continue
        pad = os.path.join(personenmap, naam)
        fm = lees_frontmatter(pad)
        pid = fm.get("id") or naam[:-3]
        kinderen = fm.get("kinderen") or []
        if isinstance(kinderen, str):
            kinderen = [kinderen]
        woonplaatsen = fm.get("woonplaatsen") or []
        if isinstance(woonplaatsen, str):
            woonplaatsen = [woonplaatsen]
        try:
            bijgewerkt = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(pad)))
        except OSError:
            bijgewerkt = ""
        docmap = os.path.join(PROJECTMAP, "documenten", pid)
        aantal_docs = 0
        if os.path.isdir(docmap):
            aantal_docs = sum(
                1 for b in os.listdir(docmap)
                if not b.endswith(".md") and not b.startswith(".")
            )
        resultaat.append({
            "id": pid,
            "naam": fm.get("naam") or pid,
            "geboren": fm.get("geboren") or "",
            "overleden": fm.get("overleden") or "",
            "beroep": fm.get("beroep") or "",
            "lijn": fm.get("lijn") or "",
            "generatie": fm.get("generatie") or "",
            "status": fm.get("status") or "",
            "woonplaatsen": woonplaatsen,
            "vader": wikilink_doel(fm.get("vader")),
            "moeder": wikilink_doel(fm.get("moeder")),
            "partner": wikilink_doel(fm.get("partner")),
            "kinderen": [wikilink_doel(k) for k in kinderen if wikilink_doel(k)],
            "bestand": f"personen/{naam}",
            "documenten": aantal_docs,
            "bijgewerkt": bijgewerkt,
        })
    return resultaat


# ---------------------------------------------------------------------------
# Verhalen (losse vondsten uit boek/verhalen/, met bron)
# ---------------------------------------------------------------------------

def eerste_alinea(pad, maximum=230):
    """De eerste gewone alinea van de romp, ontdaan van markdown-opmaak.

    Voor de verhalenkaarten: een leesbare aanhef zegt meer dan drie chips.
    """
    try:
        with open(pad, encoding="utf-8") as f:
            tekst = f.read()
    except OSError:
        return ""
    if tekst.startswith("---"):
        einde = tekst.find("\n---", 3)
        if einde != -1:
            tekst = tekst[einde + 4:]
    for blok in re.split(r"\n\s*\n", tekst):
        blok = " ".join(blok.strip().splitlines())
        # koppen, tabellen, citaten en lijstjes overslaan: we willen lopende tekst
        if not blok or blok.startswith(("#", "|", ">", "- ", "* ", "_")):
            continue
        blok = WIKILINK.sub(lambda m: m.group(1), blok)
        blok = re.sub(r"\*\*(.+?)\*\*", r"\1", blok)
        blok = re.sub(r"\*(.+?)\*", r"\1", blok)
        blok = re.sub(r"`([^`]+)`", r"\1", blok)
        blok = blok.strip()
        if len(blok) > maximum:
            afgeknipt = blok[:maximum]
            blok = afgeknipt[:afgeknipt.rfind(" ")] + " …"
        return blok
    return ""


def verhalen_ophalen():
    """Alle verhalen uit boek/verhalen/ als lijst van dicts."""
    map_ = os.path.join(PROJECTMAP, "boek", "verhalen")
    resultaat = []
    if not os.path.isdir(map_):
        return resultaat
    for naam in sorted(os.listdir(map_)):
        if not naam.endswith(".md") or naam.startswith("_"):
            continue
        pad = os.path.join(map_, naam)
        fm = lees_frontmatter(pad)
        personen = fm.get("personen") or []
        if isinstance(personen, str):
            personen = [personen]
        personen_fm = [wikilink_doel(p) for p in personen if wikilink_doel(p)]
        try:
            score = int(str(fm.get("score")))
        except (TypeError, ValueError):
            score = None
        resultaat.append({
            "id": naam[:-3],
            "titel": fm.get("titel") or naam[:-3],
            "rubriek": fm.get("rubriek") or "",
            "deel": fm.get("deel") or "",
            "lijn": fm.get("lijn") or "",
            "periode": fm.get("periode") or "",
            "personen": personen_fm,
            # in de tekst genoemd, maar niet als hoofdpersoon in de frontmatter
            "genoemd": [d for d in wikilinks_in_romp(pad) if d not in personen_fm],
            "sterkte": fm.get("sterkte") or "",
            "score": score,
            "landing": fm.get("landing") or "",
            "gevonden": fm.get("gevonden") or "",
            "aanhef": eerste_alinea(os.path.join(map_, naam)),
            "bestand": f"boek/verhalen/{naam}",
        })
    resultaat.sort(key=lambda v: str(v["periode"]))
    return resultaat


# ---------------------------------------------------------------------------
# Tijdsbeeld (historische gebeurtenissen gekoppeld aan personen)
# ---------------------------------------------------------------------------

def tijdsbeeld_ophalen():
    """Alle gebeurtenisbestanden uit tijdsbeeld/ (zonder _-bestanden) als lijst."""
    map_ = os.path.join(PROJECTMAP, "tijdsbeeld")
    resultaat = []
    if not os.path.isdir(map_):
        return resultaat
    for naam in sorted(os.listdir(map_)):
        if not naam.endswith(".md") or naam.startswith("_"):
            continue
        pad = os.path.join(map_, naam)
        fm = lees_frontmatter(pad)
        personen = fm.get("personen") or []
        if isinstance(personen, str):
            personen = [personen]
        personen_fm = [wikilink_doel(p) for p in personen if wikilink_doel(p)]
        plaatsen = fm.get("plaatsen") or []
        if isinstance(plaatsen, str):
            plaatsen = [plaatsen]
        resultaat.append({
            "id": naam[:-3],
            "titel": fm.get("titel") or naam[:-3],
            "gebeurtenis": fm.get("gebeurtenis") or naam[:-3],
            "periode": fm.get("periode") or "",
            "soort": fm.get("soort") or "",
            "plaatsen": plaatsen,
            "personen": personen_fm,
            # in de tekst genoemd, maar niet gekoppeld in de frontmatter
            "genoemd": [d for d in wikilinks_in_romp(pad) if d not in personen_fm],
            "status": fm.get("status") or "",
            "landing": fm.get("landing") or "",
            "bestand": f"tijdsbeeld/{naam}",
        })
    resultaat.sort(key=lambda g: str(g["periode"]))
    return resultaat


# ---------------------------------------------------------------------------
# Mappenstructuur (verkenner)
# ---------------------------------------------------------------------------

def boomstructuur(map_abs, map_rel):
    knopen = []
    try:
        namen = sorted(os.listdir(map_abs), key=str.lower)
    except OSError:
        return knopen
    mappen = [n for n in namen if os.path.isdir(os.path.join(map_abs, n))]
    bestanden = [n for n in namen if os.path.isfile(os.path.join(map_abs, n))]
    for n in mappen:
        if n in VERBORGEN or n.startswith("."):
            continue
        rel = f"{map_rel}/{n}" if map_rel else n
        knopen.append({
            "naam": n,
            "pad": rel,
            "type": "map",
            "kinderen": boomstructuur(os.path.join(map_abs, n), rel),
        })
    for n in bestanden:
        if n.startswith("."):
            continue
        rel = f"{map_rel}/{n}" if map_rel else n
        knoop = {"naam": n, "pad": rel, "type": "bestand"}
        # beschrijvingsbestanden in documenten/ dragen de archief-URL mee,
        # zodat de site onder elke scan naar de bron kan linken
        if n.endswith(".md") and rel.startswith("documenten/"):
            fm = lees_frontmatter(os.path.join(map_abs, n))
            if fm.get("url"):
                knoop["url"] = fm["url"]
        knopen.append(knoop)
    return knopen


# ---------------------------------------------------------------------------
# HTTP-server
# ---------------------------------------------------------------------------

TEKST_TYPES = {
    ".md": "text/plain",
    ".txt": "text/plain",
    ".py": "text/plain",
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".cmd": "text/plain",
    ".gitignore": "text/plain",
}


class StamboomHandler(BaseHTTPRequestHandler):

    def log_message(self, formaat, *args):  # rustige console
        pass

    def _stuur(self, code, inhoud, contenttype):
        if contenttype.startswith(("text/", "application/javascript", "application/json")):
            contenttype += "; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", contenttype)
        self.send_header("Content-Length", str(len(inhoud)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(inhoud)

    def _stuur_json(self, obj):
        self._stuur(200, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json")

    def _stuur_fout(self, code, tekst):
        self._stuur(code, tekst.encode("utf-8"), "text/plain")

    def _stuur_statisch(self, bestandsnaam):
        pad = os.path.join(STATISCHEMAP, bestandsnaam)
        if not os.path.isfile(pad):
            return self._stuur_fout(404, "Niet gevonden")
        ext = os.path.splitext(bestandsnaam)[1].lower()
        ctype = TEKST_TYPES.get(ext) or mimetypes.guess_type(bestandsnaam)[0] or "application/octet-stream"
        with open(pad, "rb") as f:
            self._stuur(200, f.read(), ctype)

    def _stuur_projectbestand(self, rel_pad):
        rel_pad = rel_pad.replace("\\", "/").lstrip("/")
        abs_pad = os.path.realpath(os.path.join(PROJECTMAP, rel_pad))
        wortel = os.path.realpath(PROJECTMAP)
        if not abs_pad.startswith(wortel + os.sep) and abs_pad != wortel:
            return self._stuur_fout(403, "Pad valt buiten de projectmap")
        if not os.path.isfile(abs_pad):
            return self._stuur_fout(404, f"Bestand niet gevonden: {rel_pad}")
        ext = os.path.splitext(abs_pad)[1].lower()
        ctype = TEKST_TYPES.get(ext) or mimetypes.guess_type(abs_pad)[0] or "application/octet-stream"
        with open(abs_pad, "rb") as f:
            self._stuur(200, f.read(), ctype)

    def _stuur_pdf(self, soort, ident):
        """Bouwt (of pakt uit de cache) de PDF van één document en stuurt die
        als download. Het bouwen kan een paar seconden duren; de browser van
        de bezoeker wacht daar gewoon op."""
        try:
            module = pdf_module()
            with _PDF_SLOT:
                pdf_pad = module.maak_pdf(soort, ident)
        except FileNotFoundError:
            return self._stuur_fout(404, f"Geen {soort} met id {ident}")
        except Exception as fout:
            return self._stuur_fout(500, f"PDF maken lukte niet: {fout}")
        voorvoegsel = {"persoon": "dossier", "tijdsbeeld": "tijdsbeeld", "verhaal": "verhaal"}
        bestandsnaam = f"{voorvoegsel.get(soort, soort)}-{ident}.pdf"
        with open(pdf_pad, "rb") as f:
            inhoud = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{bestandsnaam}"')
        self.send_header("Content-Length", str(len(inhoud)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(inhoud)

    def do_GET(self):
        pad = unquote(urlparse(self.path).path)
        try:
            m_pdf = re.match(r"^/pdf/(persoon|tijdsbeeld|verhaal)/([a-z0-9-]+)$", pad)
            if m_pdf:
                return self._stuur_pdf(m_pdf.group(1), m_pdf.group(2))
            if pad in ("/", "/index.html"):
                self._stuur_statisch("index.html")
            elif pad in ("/app.js", "/stijl.css"):
                self._stuur_statisch(pad[1:])
            elif pad == "/api/personen":
                self._stuur_json(personen_ophalen())
            elif pad == "/api/tijdsbeeld":
                self._stuur_json(tijdsbeeld_ophalen())
            elif pad == "/api/verhalen":
                self._stuur_json(verhalen_ophalen())
            elif pad == "/api/instellingen":
                self._stuur_json({
                    "titel": instellingen.website_titel(),
                    "generatie_uitleg": instellingen.generatie_uitleg(),
                    "eigenaar": instellingen.waarde("eigenaar.naam"),
                    "boektitel": instellingen.waarde("boek.titel"),
                })
            elif pad == "/api/verkenner":
                self._stuur_json(boomstructuur(PROJECTMAP, ""))
            elif pad.startswith("/bestand/"):
                self._stuur_projectbestand(pad[len("/bestand/"):])
            elif pad == "/favicon.ico":
                self._stuur(204, b"", "image/x-icon")
            else:
                self._stuur_fout(404, "Niet gevonden")
        except BrokenPipeError:
            pass
        except ConnectionAbortedError:
            pass
        except Exception as fout:  # nooit de server laten omvallen op één verzoek
            try:
                self._stuur_fout(500, f"Serverfout: {fout}")
            except Exception:
                pass


def netwerk_adressen():
    """Alle IPv4-adressen van deze computer, behalve loopback.

    Niet de gebruikelijke truc met een UDP-connect naar buiten: die geeft bij
    een actieve VPN het VPN-adres terug, en daar kan een apparaat op het
    wifinetwerk niets mee. Het wifi-adres begint meestal met 192.168.
    """
    adressen = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                adressen.add(ip)
    except OSError:
        pass
    return sorted(adressen)


def main():
    try:
        poort = int(instellingen.waarde("website.poort", 8123))
    except (TypeError, ValueError):
        poort = 8123
    browser_openen = True
    netwerk = False
    for arg in sys.argv[1:]:
        if arg == "--geen-browser":
            browser_openen = False
        elif arg == "--netwerk":
            netwerk = True
        elif arg.isdigit():
            poort = int(arg)
    adres = f"http://localhost:{poort}"
    # Windows-valkuil: door SO_REUSEADDR lukt het binden óók als er al een
    # (bijv. verweesd) serverproces op de poort draait — de oude blijft dan
    # geluidloos het verkeer beantwoorden. Daarom eerst zelf controleren.
    proef = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proef.settimeout(1)
    al_bezet = proef.connect_ex(("127.0.0.1", poort)) == 0
    proef.close()
    if al_bezet:
        print(f"Poort {poort} is al in gebruik — er draait al een server (mogelijk een")
        print("achtergebleven python-proces). Stop die eerst, of kies een andere poort:")
        print(f"  PowerShell:  Get-NetTCPConnection -LocalPort {poort} -State Listen")
        print(f"               Stop-Process -Id <PID> -Force")
        print(f"  of:          py website/server.py {poort + 1}")
        sys.exit(1)
    # zonder --netwerk uitsluitend 127.0.0.1: alleen deze computer kan erbij
    host = "0.0.0.0" if netwerk else "127.0.0.1"
    server = ThreadingHTTPServer((host, poort), StamboomHandler)
    print(f"{instellingen.website_titel()} draait op {adres}")
    if netwerk:
        for ip in netwerk_adressen():
            print(f"  op het netwerk:   http://{ip}:{poort}")
        print("Andere apparaten op hetzelfde wifinetwerk gebruiken zo'n netwerkadres")
        print("(meestal het adres dat met 192.168 begint).")
    print("Stoppen: Ctrl+C")
    if browser_openen:
        threading.Timer(0.6, lambda: webbrowser.open(adres)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGestopt.")


if __name__ == "__main__":
    main()

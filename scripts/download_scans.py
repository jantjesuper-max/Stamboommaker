"""Haal scans bij beschrijvingsbestanden op — op volledige resolutie.

Gebruik (vanuit de projectmap):
  py scripts/download_scans.py                  # alle documenten/**.md langslopen
  py scripts/download_scans.py bakker-hendrik-1901    # alleen die persoonsmap

Werkwijze per beschrijvingsbestand:
1. record-id uit het url:-veld → Open Archieven API (show.json) → scan-URI's
2. per scan downloaden, groot naar klein: **download/fullsize** (de volledige scan,
   werkt zonder inloggen op de Memorix-beeldservers, ook voor de pad-vorm-URI's
   waar de thumb-endpoints 404 geven), dan thumb/2000x2000, thumb/1000x1000,
   en als laatste de oorspronkelijke URI. Boven de 5 MB-projectgrens valt een maat
   automatisch door naar de volgende.
3. geldigheidscontrole (JPEG-magic, > 10 kB, <= 5 MB); alleen vervangen als het
   nieuwe bestand groter is dan wat er ligt
4. status:-regel (en bij nieuwe bestanden de bestand:-regel) in de .md bijwerken;
   tweede en volgende scans krijgen het achtervoegsel _2, _3, ... en een
   bestand2:-regel in de frontmatter

Let op: dit script downloadt en administreert alleen. Transcriberen en het dossier
bijwerken blijft handwerk (zie CLAUDE.md, "Documenten downloaden").
"""

import json
import os
import re
import struct
import subprocess
import sys
import time

DOCMAP = "documenten"
MAX_BYTES = 5 * 1024 * 1024

# proxy.archieven.nl (Westfries Archief, Noord-Hollands Archief en de andere archieven
# die via archieven.nl leveren) antwoordt met een **301** naar preserve-<archief>.archieven.nl,
# en weigert zonder browser-User-Agent. Zonder -L levert curl dan een leeg 301-lichaam op,
# waarna de JPEG-controle hieronder faalt en de scan er "geblokkeerd" uitziet. Dat is drie
# rondes lang ten onrechte als "HTTP 403 - bot was blocked" opgeschreven.
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
CURL_BASIS = ["curl", "-s", "--fail", "-L", "-A", BROWSER_UA]


def api_show(record):
    archief, _, identifier = record.partition(":")
    url = f"https://api.openarch.nl/1.1/records/show.json?archive={archief}&identifier={identifier}&lang=nl"
    uitvoer = subprocess.run(CURL_BASIS + [url], capture_output=True, timeout=60, check=True)
    return json.loads(uitvoer.stdout.decode("utf-8"))


def scan_uris(data):
    records = data if isinstance(data, list) else [data]
    uris = []
    for record in records:
        bron = record.get("Source") or {}
        scans = (bron.get("SourceAvailableScans") or {}).get("Scan")
        if not scans:
            continue
        scans = scans if isinstance(scans, list) else [scans]
        for s in scans:
            # Sommige archieven (Stadsarchief Amsterdam) vullen 'Uri' niet en zetten de
            # thumb in 'UriViewer' of 'UriPreview'; zonder deze terugval lijkt zo'n record
            # scanloos.
            uri = s.get("Uri") or s.get("UriViewer") or s.get("UriPreview")
            if uri and uri not in uris:
                uris.append(uri)
    return uris


def jpeg_afmetingen(data):
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
        else:
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def kandidaat_urls(uri):
    """De URL's om te proberen, groot naar klein, afhankelijk van de beeldserver."""
    # IIIF (Erfgoed Leiden e.d.): .../info.json is metadata, niet de scan zelf.
    if uri.endswith("/info.json"):
        return [uri[: -len("info.json")] + "full/max/0/default.jpg", uri]
    # hdl.handle.net stuurt door naar een archief-VIEWER (403 zonder sessie), maar de
    # doorstuur-URL bevat `miguid` (bestands-id) en `miadt` (toegangsnummer) -- en daarmee
    # is de scan gewoon op te halen via het gewone download-pad van archieven.nl.
    if "hdl.handle.net" in uri:
        kandidaten = []
        try:
            r = subprocess.run(["curl", "-sIL", "-A", BROWSER_UA, uri],
                               capture_output=True, text=True, timeout=60)
            m = re.search(r"miguid=([0-9A-Fa-f]+).*?miadt=(\d+)", r.stdout or "")
            if m:
                kandidaten.append(f"https://proxy.archieven.nl/download/{m.group(2)}/{m.group(1)}")
        except Exception:
            pass
        return kandidaten + [uri]
    # archieven.nl levert maar één maat; de thumb-varianten hieronder bestaan daar niet.
    if "archieven.nl" in uri:
        return [uri]
    kandidaten = [re.sub(r"/thumb/\d+x\d+/", "/download/fullsize/", uri)]
    for maat in ("2000x2000", "1000x1000"):
        vervangen = re.sub(r"/thumb/\d+x\d+/", f"/thumb/{maat}/", uri)
        if vervangen != uri or maat in uri:
            kandidaten.append(vervangen)
    kandidaten.append(uri)  # origineel als laatste redmiddel
    return kandidaten


def download_hires(uri):
    """Probeer groot naar klein; geef (bytes, gebruikte_url) of (None, None)."""
    for url in kandidaat_urls(uri):
        try:
            uitvoer = subprocess.run(CURL_BASIS + ["--max-time", "120", url],
                                     capture_output=True, timeout=180, check=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        data = uitvoer.stdout
        if data[:2] != b"\xff\xd8" or len(data) <= 10_000:
            continue
        if len(data) <= MAX_BYTES:
            return data, url
        # Boven de projectgrens NIET weggooien maar comprimeren op VOLLE PIXELMAAT.
        # archieven.nl levert maar één maat, en die is bij sommige archieven stelselmatig
        # 8-9 MB (6000 x 5000). Zulke scans afwijzen met "MISLUKT" laat ze als
        # [nog te downloaden] in de dossiers staan. Verkleinen mag niet (een jaartal beslaat
        # zeventig pixels), dus alleen de JPEG-kwaliteit gaat omlaag.
        kleiner = comprimeer(data)
        if kleiner:
            return kleiner, url
    return None, None


def comprimeer(data):
    """Slaat een te grote JPEG opnieuw op met lagere kwaliteit, zonder te verkleinen."""
    try:
        import io as _io
        from PIL import Image
    except ImportError:
        return None
    try:
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(_io.BytesIO(data))
        im.load()
    except Exception:
        return None
    for kwaliteit in (72, 60, 50, 40):
        buf = _io.BytesIO()
        im.save(buf, "JPEG", quality=kwaliteit, optimize=True)
        if buf.tell() <= MAX_BYTES:
            print(f"    (gecomprimeerd op volle pixelmaat: {len(data)//1024} kB -> "
                  f"{buf.tell()//1024} kB, kwaliteit {kwaliteit})")
            return buf.getvalue()
    return None


def verwerk_md(md_pad):
    with open(md_pad, encoding="utf-8") as f:
        tekst = f.read()
    m_url = re.search(r"^url:\s*(\S+)", tekst, re.M)
    if not m_url:
        print(f"  OVERGESLAGEN (geen url): {md_pad}")
        return 0
    # Let op de hoofdletters: frl-id's zijn kleine letters, maar het Westfries Archief en
    # het Noord-Hollands Archief geven HOOFDLETTER-hex (wfa:BCCBB35C-7109-...). Met het oude
    # patroon [0-9a-f-]+ werd elk record van die twee archieven stilzwijgend overgeslagen.
    m_record = re.search(r"openarchieven\.nl/([a-z]+:[0-9A-Fa-f-]+)", m_url.group(1))
    if not m_record:
        print(f"  OVERGESLAGEN (geen record-id): {md_pad}")
        return 0

    try:
        uris = scan_uris(api_show(m_record.group(1)))
    except Exception as fout:
        print(f"  FOUT bij API voor {md_pad}: {fout}")
        return 0
    if not uris:
        print("  geen scans bij dit record — status blijft zoals hij is")
        return 0

    basis = md_pad[:-3]  # zonder .md
    nieuwe_bestanden = []
    for i, uri in enumerate(uris):
        doel = f"{basis}.jpg" if i == 0 else f"{basis}_{i + 1}.jpg"
        oud_bytes = os.path.getsize(doel) if os.path.exists(doel) else 0
        data, _gebruikt = download_hires(uri)
        if not data:
            print(f"  MISLUKT: {uri}")
            continue
        if len(data) <= oud_bytes:
            print(f"  al even groot, niet vervangen: {os.path.basename(doel)}")
            continue
        with open(doel, "wb") as f:
            f.write(data)
        afm = jpeg_afmetingen(data)
        afm_tekst = f"{afm[0]}x{afm[1]}" if afm else "?"
        nieuwe_bestanden.append(afm_tekst)
        print(f"  {os.path.basename(doel)}: {oud_bytes // 1024} kB -> {len(data) // 1024} kB ({afm_tekst})")
        time.sleep(0.5)

    if not nieuwe_bestanden:
        return 0

    afmetingen = ", ".join(nieuwe_bestanden)
    if len(uris) > 1:
        status = f"status: gedownload (volledige scan, {len(uris)} scans: {afmetingen})"
    else:
        status = f"status: gedownload (volledige scan, {afmetingen})"
    tekst = re.sub(r"^status:.*$", status, tekst, count=1, flags=re.M)
    eerste = os.path.basename(f"{basis}.jpg")
    tekst = re.sub(r'^bestand:\s*"?\[nog te downloaden\]"?\s*$', f"bestand: {eerste}", tekst, count=1, flags=re.M)
    for i in range(1, len(uris)):
        extra = os.path.basename(f"{basis}_{i + 1}.jpg")
        if f"bestand{i + 1}:" not in tekst and os.path.exists(f"{basis}_{i + 1}.jpg"):
            tekst = re.sub(r"^(bestand:.*)$", f"\\1\nbestand{i + 1}: {extra}", tekst, count=1, flags=re.M)
    with open(md_pad, "w", encoding="utf-8", newline="\n") as f:
        f.write(tekst)
    return len(nieuwe_bestanden)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    filter_map = sys.argv[1] if len(sys.argv) > 1 else None
    totaal = 0
    documenten = 0
    for map_, _, bestanden in os.walk(DOCMAP):
        if map_.endswith("inbox"):
            continue
        if filter_map and os.path.basename(map_) != filter_map:
            continue
        for naam in sorted(bestanden):
            if not naam.endswith(".md") or naam.startswith("_"):
                continue
            print(naam)
            aantal = verwerk_md(os.path.join(map_, naam))
            if aantal:
                totaal += aantal
                documenten += 1
            time.sleep(0.5)
    print(f"\nKlaar: {totaal} scan(s) opgehaald/vervangen voor {documenten} document(en).")


if __name__ == "__main__":
    main()

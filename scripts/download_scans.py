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


def api_show(record):
    archief, _, identifier = record.partition(":")
    url = f"https://api.openarch.nl/1.1/records/show.json?archive={archief}&identifier={identifier}&lang=nl"
    uitvoer = subprocess.run(["curl", "-s", "--fail", url], capture_output=True, timeout=60, check=True)
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
            if s.get("Uri") and s["Uri"] not in uris:
                uris.append(s["Uri"])
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


def download_hires(uri):
    """Probeer groot naar klein; geef (bytes, gebruikte_url) of (None, None)."""
    kandidaten = [re.sub(r"/thumb/\d+x\d+/", "/download/fullsize/", uri)]
    for maat in ("2000x2000", "1000x1000"):
        vervangen = re.sub(r"/thumb/\d+x\d+/", f"/thumb/{maat}/", uri)
        if vervangen != uri or maat in uri:
            kandidaten.append(vervangen)
    kandidaten.append(uri)  # origineel als laatste redmiddel
    for url in kandidaten:
        try:
            uitvoer = subprocess.run(["curl", "-s", "--fail", "--max-time", "60", url],
                                     capture_output=True, timeout=90, check=True)
        except subprocess.CalledProcessError:
            continue
        data = uitvoer.stdout
        if data[:2] == b"\xff\xd8" and 10_000 < len(data) <= MAX_BYTES:
            return data, url
    return None, None


def verwerk_md(md_pad):
    with open(md_pad, encoding="utf-8") as f:
        tekst = f.read()
    m_url = re.search(r"^url:\s*(\S+)", tekst, re.M)
    if not m_url:
        print(f"  OVERGESLAGEN (geen url): {md_pad}")
        return 0
    m_record = re.search(r"openarchieven\.nl/([a-z]+:[0-9a-f-]+)", m_url.group(1))
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

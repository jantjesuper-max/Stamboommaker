"""Krantenbank Zeeland (zoeken.collectiezeeland.nl): zoeken en de tekst rond een woord lezen.

Gebruik:
  py scripts/zoek_kbz.py zoek "Jansen Graauw" --van 01-01-1860 --tot 31-12-1870 [--woord jansen] [--breedte 300] [--max 400]
  py scripts/zoek_kbz.py scan https://zoeken.collectiezeeland.nl/ISSUE/TNC/1943-04-16/EDITION/NULL/PAGE/3 --uit test/tijdelijk/krant/tnc.jpg

Wat je moet weten (gemeten):
- woorden worden met EN gecombineerd, per krantenpagina;
- ⚠ Periode_tot zonder Periode_van wordt door de server GENEGEERD (dan krijg je alle jaren). Dit script
  vult daarom bij alleen --tot zelf --van 01-01-1700 in. Geef altijd --van én --tot;
- ⚠ wie de krantenpagina's mét de sessiecookie ophaalt, krijgt bij een deel van de verzoeken de tekst
  van een eerder bekeken pagina terug. De zoekpagina's gaan daarom mét cookie, de krantenpagina's zónder;
- een kale `Mozilla/5.0` krijgt een Cloudflare-pagina; de volledige browser-UA hieronder werkt;
- de volledige paginascan komt van /HttpHandler/icoon.ico?file=<id> (JPEG, 4000-6000 px); het id staat in de
  pagina-HTML onder "image". Lees hem met scripts/lees_scan.py en knip met scripts/knipsel.py.
"""
import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

BASIS = "https://zoeken.collectiezeeland.nl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TMP = tempfile.mkdtemp(prefix="kbz_")
CJ = os.path.join(TMP, "cj")


def haal(url, cookie=True):
    uit = os.path.join(TMP, "r.html")
    cmd = ["curl", "-sL", "-A", UA, "-o", uit, url]
    if cookie:
        cmd[2:2] = ["-c", CJ, "-b", CJ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    with open(uit, encoding="utf-8", errors="replace") as f:
        return f.read()


def zoek(args):
    van = args.van or ("01-01-1700" if args.tot else "")
    woord = (args.woord or args.term.split()[0]).lower()
    basis = f"{BASIS}/zoeken/groep=Kranten%20en%20tijdschriften/Vrij_zoeken={quote(args.term)}/"
    if van:
        basis += f"Periode_van={van}/"
    if args.tot:
        basis += f"Periode_tot={args.tot}/"
    basis += "endless_scroll=off/aantalpp=100/"
    treffers, n = [], 1
    while True:
        t = haal(basis + (f"pagina={n}/" if n > 1 else ""))
        gevonden = []
        for rij in t.split('<tr class="custom-table-row')[1:]:
            lk = re.search(r'href="(https://zoeken\.collectiezeeland\.nl/ISSUE/[^"]+)"', rij)
            kop = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", rij)))
            m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*\|\s*([^|]+?)\s*\|\s*(pagina \d+)", kop)
            if lk and m:
                gevonden.append((lk.group(1), m.group(1), m.group(2), m.group(3)))
        bekend = {x[0] for x in treffers}
        nieuw = [g for g in gevonden if g[0] not in bekend]
        if n == 1:
            m = re.search(r"pagina 1 van ([\d.]+)", t)
            print(f"zoekopdracht: {args.term} {van}-{args.tot}  ({m.group(1) if m else '1'} resultatenpagina's van 100)")
        if not nieuw:
            break
        treffers += nieuw
        n += 1
        if len(treffers) >= args.max:
            print(f"⚠ afgekapt op --max {args.max}; de zoekopdracht is niet af")
            break
    print(f"{len(treffers)} krantenpagina's\n")
    for link, datum, krant, blz in treffers:
        t = haal(html.unescape(link), cookie=False)
        tekst = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
        print(f"=== {datum.strip()} | {krant.strip()} | {blz} | {html.unescape(link).split('?')[0]}")
        gezien = -10**9
        for m in re.finditer(re.escape(woord), tekst.lower()):
            if m.start() - gezien < args.breedte:
                continue
            gezien = m.start()
            print("   ...", tekst[max(0, m.start() - args.breedte):m.start() + args.breedte], "...")
        time.sleep(0.3)
    return 0


def scan(args):
    t = haal(args.pad, cookie=False)
    m = re.search(r"icoon\.ico\?file=(\d+)", t)
    if not m:
        print("Geen scan-id gevonden in de pagina.")
        return 1
    url = f"{BASIS}/HttpHandler/icoon.ico?file={m.group(1)}"
    subprocess.run(["curl", "-sL", "-m", "300", "-A", UA, "-o", args.uit, url], check=True)
    print(f"jpg: {args.uit}  ({url}) -- lees met: py scripts/lees_scan.py overzicht {args.uit}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zoek")
    z.add_argument("term")
    z.add_argument("--van", default="", help="dd-mm-jjjj")
    z.add_argument("--tot", default="", help="dd-mm-jjjj")
    z.add_argument("--woord")
    z.add_argument("--breedte", type=int, default=300)
    z.add_argument("--max", type=int, default=400)
    s = sub.add_parser("scan")
    s.add_argument("pad")
    s.add_argument("--uit", required=True)
    a = p.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    return zoek(a) if a.cmd == "zoek" else scan(a)


if __name__ == "__main__":
    sys.exit(main())

"""Zoeken in De Krant van Toen: het archief van de Leeuwarder Courant vanaf 1752, met scans.

De Krant van Toen (dekrantvantoen.nl, Mediahuis Noord, x-cago Archive Express) is voor
Friesland de eerste krantenbank: de Leeuwarder Courant staat er vanaf 1752 in, met de
dorpsberichten, de boelgoeden, de familieadvertenties en de rubriek Burgerlijke Stand.
Delpher heeft die krant maar voor een deel.

Gemeten:
  - zoeken: GET /srch/query.do?v2=true&q=<termen> pubcode: LC date:[JJJJMMDD TO JJJJMMDD]&searcher=alternativeSearcher&from=N
    (searcher=alternativeSearcher = het historische archief vanaf 1752; zonder dat alleen na 2006)
  - order=reverse -> oudste eerst
  - artikel: /vw/pdf.do?id=<id> geeft een PDF met OCR-tekstlaag + bitonale scan

Gebruik:
  py scripts/zoek_dekrantvantoen.py zoek "Jansen Oosterzee" --van 1880 --tot 1940 [--pub LC] [--max 60]
  py scripts/zoek_dekrantvantoen.py zoek "Jansen Oosterzee" --van 1880 --tot 1940 --lees Jansen
  py scripts/zoek_dekrantvantoen.py toon LC-19370702-3014 [--woord Jansen] [--png test/tijdelijk/krant/lc-1937-07-02.png]

Losse woorden zijn AND. Voor `toon` en `--lees` is PyMuPDF nodig (py -m pip install pymupdf);
de png die `toon --png` schrijft is met scripts/lees_scan.py en scripts/knipsel.py te lezen
en te knippen.
"""
import argparse
import html
import os
import re
import subprocess
import sys
import urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# Cookies en tijdelijke pdf's horen niet in scripts/ maar in test/tijdelijk/.
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test", "tijdelijk")
os.makedirs(TMP, exist_ok=True)
CJ = os.path.join(TMP, "dkvt_cookies.txt")
BASIS = "https://www.dekrantvantoen.nl"


def haal(url, binair=False):
    r = subprocess.run(["curl", "-s", "-m", "90", "-L", "-A", UA, "-c", CJ, "-b", CJ, url], capture_output=True)
    return r.stdout if binair else r.stdout.decode("cp1252", errors="replace")


def _fitz():
    try:
        import fitz
    except ImportError:
        sys.exit("PyMuPDF ontbreekt: py -m pip install pymupdf")
    return fitz


def zoek(a):
    q = a.term
    if a.pub:
        q += f" pubcode: {a.pub}"
    q += f" date:[{a.van}0101 TO {a.tot}1231]"
    gezien = []
    van = 0
    totaal = None
    while True:
        url = f"{BASIS}/srch/query.do?v2=true&q={urllib.parse.quote(q)}&searcher=alternativeSearcher&order=reverse"
        if van:
            url += f"&from={van}"
        s = haal(url)
        m = re.search(r"(\d+) artikel(?:en)? gevonden", s)
        if totaal is None:
            totaal = int(m.group(1)) if m else 0
            print(f"De Krant van Toen: {totaal} artikel(en) voor {q!r}")
        blokken = re.findall(r'href="/vw/article\.do\?id=([^"&]+)"[^>]*>(.*?)</a>', s, re.S)
        nieuw = 0
        for aid, kop in blokken:
            if aid in [g[0] for g in gezien]:
                continue
            kop = html.unescape(re.sub(r"<[^>]+>", " ", kop))
            kop = re.sub(r"\s+", " ", kop).strip()
            gezien.append((aid, kop))
            nieuw += 1
        if not nieuw or len(gezien) >= min(totaal, a.max):
            break
        van = len(gezien)
    for aid, kop in gezien[: a.max]:
        m = re.match(r"([A-Z]+)-(\d{4})(\d{2})(\d{2})-(\d+)", aid)
        d = f"{m.group(4)}-{m.group(3)}-{m.group(2)}" if m else ""
        print(f"- {d}  {aid}  {kop[:90]}")
        if a.lees:
            t = pdftekst(aid)
            gevonden = False
            for m in re.finditer(a.lees, t, re.I):
                print("      ...", t[max(0, m.start() - a.ruim): m.end() + a.ruim], "...")
                gevonden = True
            if not gevonden:
                print("      (leeswoord niet in OCR)")
    if totaal > a.max:
        print(f"  ({totaal - a.max} niet getoond; verhoog --max)")


def pdftekst(aid, png=None, dpi=150):
    fitz = _fitz()
    data = haal(f"{BASIS}/vw/pdf.do?id={aid}", binair=True)
    tmp = os.path.join(TMP, "dkvt_tmp.pdf")
    with open(tmp, "wb") as f:
        f.write(data)
    try:
        d = fitz.open(tmp)
    except Exception:
        return ""
    if png:
        d[0].get_pixmap(dpi=dpi).save(png)
    return re.sub(r"\s+", " ", " ".join(p.get_text() for p in d))


def toon(a):
    fitz = _fitz()
    data = haal(f"{BASIS}/vw/pdf.do?id={a.id}", binair=True)
    tmp = os.path.join(TMP, "dkvt_tmp.pdf")
    with open(tmp, "wb") as f:
        f.write(data)
    d = fitz.open(tmp)
    t = " ".join(p.get_text() for p in d)
    t = re.sub(r"\s+", " ", t)
    if a.png:
        d[0].get_pixmap(dpi=a.dpi).save(a.png)
        print("png:", a.png)
    print(f"{BASIS}/vw/article.do?id={a.id}")
    if a.woord:
        for m in re.finditer(re.escape(a.woord), t, re.I):
            print("...", t[max(0, m.start() - a.ruim): m.end() + a.ruim], "...")
            print()
    else:
        print(t[:6000])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    z = sp.add_parser("zoek")
    z.add_argument("term")
    z.add_argument("--van", default="1752")
    z.add_argument("--tot", default="2005")
    z.add_argument("--pub", default="LC", help="krantcode, standaard LC (Leeuwarder Courant)")
    z.add_argument("--max", type=int, default=40)
    z.add_argument("--lees", help="haal per treffer de OCR op en toon de tekst rond dit woord")
    z.add_argument("--ruim", type=int, default=200)
    t = sp.add_parser("toon")
    t.add_argument("id")
    t.add_argument("--woord")
    t.add_argument("--png", help="schrijf de scan van het artikel als png")
    t.add_argument("--dpi", type=int, default=150)
    t.add_argument("--ruim", type=int, default=400)
    a = p.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    {"zoek": zoek, "toon": toon}[a.cmd](a)


if __name__ == "__main__":
    main()

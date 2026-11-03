"""Zoeken in de regionale krantenbanken op het Memorix-krantenplatform (courant.nu-software).

Waarom dit script bestaat: de zoekpagina van zo'n krantenbank geeft op een kale aanroep
**403**, en dat leest als "niet te doorzoeken". Het komt door de ontbrekende
browser-User-Agent, niet door het archief. Mét een UA geeft de zoekpagina gewoon HTML met
het aantal resultaten, de datum, de krant, het paginanummer en een snippet; de paginapagina
bevat de volledige OCR-tekst.

Het plaatselijke nieuws (de dorpsrubrieken, de familieadvertenties, de uitslag van de
zangvereniging) staat grotendeels NIET in Delpher maar bij het regionale archief. Deze
banken zijn daarvoor de ingang.

Gebruik:
  py scripts/zoek_courant.py zoek "Jansen AND Koudekerk" --bank leiden --van 1920 --tot 1940
  py scripts/zoek_courant.py zoek "Bijl AND Nibbixwoud" --bank alkmaar
  py scripts/zoek_courant.py toon https://leiden.courant.nu/issue/LD/1926-01-09/edition/0/page/14 --woord Jansen
  py scripts/zoek_courant.py scan https://leiden.courant.nu/issue/LD/1926-01-09/edition/0/page/14 --uit test/tijdelijk/krant/ld-1926-01-09-p14.png
  py scripts/zoek_courant.py banken

Zoeksyntaxis (gemeten op leiden.courant.nu):
  - de treffer is een PAGINA, niet een artikel: "A AND B" = beide woorden op dezelfde pagina;
    dat is breder dan het lijkt;
  - een frase tussen dubbele aanhalingstekens is wél scherp ("Jansen Koudekerk");
  - losse woorden zonder AND gedragen zich als AND (anders dan Delpher, waar ze een frase worden).
Periode: f_issuedate[0]=JJJJ-01-01T00:00:00Z--+NYEARS (de facetlink van de site zelf).

Nieuwe streek, nieuwe krantenbank. Draait een krantenbank op dezelfde software (URL's als
/issue/<KRANT>/<datum>/edition/0/page/<n> en een zoekpagina /search?query=), zet hem dan in
BANKEN hieronder en controleer met een gewone naam dat er "N resultaten gevonden" terugkomt.
Schrijf hem ook bij in onderzoek/bronnengids.md. Welke kranten waar gedigitaliseerd zijn
staat op https://www.hennekam.net/krantenarchieven-nederland/.
"""
import argparse
import html
import re
import sys
import urllib.parse
import subprocess

BANKEN = {
    # code: (host, omschrijving)
    "leiden": ("leiden.courant.nu", "Historische Kranten Erfgoed Leiden en Omstreken"),
    "alkmaar": ("kranten.archiefalkmaar.nl", "Kranten Regionaal Archief Alkmaar"),
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def haal(url):
    # curl i.p.v. urllib: achter een inspecterende proxy geeft urllib SSL-fouten.
    r = subprocess.run(["curl", "-s", "-L", "-m", "40", "-A", UA, url],
                       capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def botcontrole(s):
    """De bank toont soms een menselijkheidscontrole in plaats van de pagina.

    Gemeten 03-11-2026 bij leiden.courant.nu: HTTP 403 met een pagina "Checking if you're
    human... Please wait." Dat is geen muur en geen gereedschapsprobleem, en het script
    probeert er niet omheen te werken. Zoek dan handmatig in de browser, noteer de URL en
    de datum in het onderzoekslog, en probeer het script later opnieuw.
    """
    return "Checking if you" in s or "cf-challenge" in s or "Just a moment" in s


def meld_botcontrole(url):
    print("De krantenbank toont een bot-controle ('Checking if you're human') in plaats van de "
          "pagina. Dat is geen muur: zoek handmatig in de browser op")
    print(f"  {url}")
    print("noteer URL en datum in het onderzoekslog, en probeer het script later opnieuw.")
    return 2


def banken(args):
    for code, (host, naam) in BANKEN.items():
        print(f"  --bank {code:<10} {naam}  (https://{host})")
    return 0


def zoek(args):
    host, naam = BANKEN[args.bank]
    params = [("query", args.query), ("sort", args.sort)]
    if args.van or args.tot:
        van = args.van or 1700
        tot = args.tot or 2020
        params.append(("f_issuedate[0]", f"{van}-01-01T00:00:00Z--+{tot - van + 1}YEARS"))
    if args.pagina > 1:
        params.append(("page", str(args.pagina)))
    url = f"https://{host}/search?" + urllib.parse.urlencode(params)
    s = haal(url)
    if botcontrole(s):
        return meld_botcontrole(url)
    m = re.search(r'id="results_total">([^<]*)', s)
    if not m:
        print(f"Geen resultatentelling gevonden op {url} -- controleer de bank (lege of foutpagina).")
        return 1
    print(f"{naam}: {m.group(1).strip()}  (pagina {args.pagina}, sortering {args.sort})")
    print(f"  zoek-URL: {url}")
    for blok in re.findall(r'<div class="page[^"]*">(.*?)</article>', s, re.S):
        link = re.search(r'<h1>\s*<a href="([^"]*)"', blok)
        titel = re.search(r'<time[^>]*>([^<]*)</time>\s*\|([^<]*)', blok)
        snip = re.search(r"<p>(.*?)</p>", blok, re.S)
        if not link:
            continue
        pad = html.unescape(link.group(1)).split("?")[0]
        t = f"{titel.group(1)} |{html.unescape(titel.group(2)).strip()}" if titel else ""
        tekst = ""
        if snip:
            tekst = re.sub(r"<[^>]+>", "", snip.group(1))
            tekst = " ".join(html.unescape(tekst).split())
        print(f"- {t}")
        print(f"    https://{host}{pad}")
        if tekst:
            print(f"    {tekst[:300]}")
    if 'class="next"' in s:
        print(f"(meer resultaten: --pagina {args.pagina + 1})")
    return 0


def bank_uit_url(args):
    """Bij een volledige URL bepaalt de host welke bank het is, niet --bank. Zonder dit
    haalt 'toon https://kranten.archiefalkmaar.nl/...' stilzwijgend dezelfde pagina bij
    Leiden op en meldt dan dat het woord 'niet in de OCR' staat."""
    if args.pad.startswith("http"):
        h = urllib.parse.urlparse(args.pad).netloc
        for host, naam in BANKEN.values():
            if host == h:
                return host, naam
    return BANKEN[args.bank]


def _pad(pad):
    if pad.startswith("http"):
        pad = urllib.parse.urlparse(pad).path
    # Git Bash maakt van een los '/issue/...' stilzwijgend 'C:/Program Files/Git/issue/...';
    # knip daarom alles vóór '/issue/' weg en accepteer ook 'issue/...' zonder slash.
    if "/issue/" in pad:
        pad = pad[pad.index("/issue/"):]
    elif pad.startswith("issue/"):
        pad = "/" + pad
    return pad


def toon(args):
    host, naam = bank_uit_url(args)
    url = f"https://{host}{_pad(args.pad)}"
    s = haal(url)
    if botcontrole(s):
        return meld_botcontrole(url)
    titel = re.search(r'og&#x3A;title" content="([^"]*)"', s)
    print(f"{naam}: {html.unescape(titel.group(1)) if titel else url}")
    print(f"  URL: {url}")
    tekst = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    tekst = re.sub(r"<[^>]+>", "\n", tekst)
    tekst = html.unescape(tekst)
    tekst = re.sub(r"\n\s*\n+", "\n", tekst)
    if not args.woord:
        print(tekst[:args.context * 4])
        return 0
    n = 0
    for m in re.finditer(re.escape(args.woord), tekst, re.I):
        n += 1
        a, b = max(0, m.start() - args.context), m.end() + args.context
        print(f"\n--- treffer {n} ---")
        print(tekst[a:b])
    if n == 0:
        print(f"'{args.woord}' niet in de OCR-tekst van deze pagina.")
    return 0


def scan(args):
    """Haalt de paginascan op. De Memorix-fullsize geeft bij deze banken 403, maar
    /imageserver/download/<uuid>.jpg (en als terugval .pdf) werkt. De uuid staat in
    og:image van de paginapagina. Van een pdf wordt met PyMuPDF een PNG gemaakt, zodat
    scripts/lees_scan.py en scripts/knipsel.py hem kunnen lezen."""
    host, naam = bank_uit_url(args)
    s = haal(f"https://{host}{_pad(args.pad)}")
    if botcontrole(s):
        return meld_botcontrole(f"https://{host}{_pad(args.pad)}")
    # De thumbmaat verschilt per bank (Leiden 640x480, Alkmaar 50x72); match daarom elke maat.
    m = re.search(r"thumb&#x2F;\d+x\d+&#x2F;([0-9a-f-]{36})", s)
    if not m:
        print("Geen pagina-uuid gevonden in og:image.")
        return 1
    # Eerst de JPG: bij sommige banken is de pdf een omhulsel van 5 kB met een lage
    # resolutie, terwijl /download/<uuid>.jpg een volwaardig blad geeft.
    jpg_url = f"https://{host}/imageserver/download/{m.group(1)}.jpg"
    jpg = args.uit.rsplit(".", 1)[0] + ".jpg"
    subprocess.run(["curl", "-s", "-L", "-m", "120", "-A", UA, "-o", jpg, jpg_url], check=True)
    try:
        from PIL import Image
        with Image.open(jpg) as im:
            breed, hoog = im.size
        if breed * hoog > 2_000_000:
            print(f"jpg: {jpg}  ({breed} x {hoog}, {jpg_url}) -- lees met: py scripts/lees_scan.py overzicht {jpg}")
            return 0
    except Exception:
        pass
    pdf_url = f"https://{host}/imageserver/download/{m.group(1)}.pdf"
    pdf = args.uit.rsplit(".", 1)[0] + ".pdf"
    subprocess.run(["curl", "-s", "-L", "-m", "120", "-A", UA, "-o", pdf, pdf_url], check=True)
    print(f"pdf: {pdf}  ({pdf_url})")
    try:
        import fitz
    except ImportError:
        print("PyMuPDF ontbreekt (py -m pip install pymupdf); alleen de pdf is opgeslagen.")
        return 0
    d = fitz.open(pdf)
    pix = d[0].get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom))
    pix.save(args.uit)
    print(f"png: {args.uit}  ({pix.width} x {pix.height}) -- lees met: py scripts/lees_scan.py overzicht {args.uit}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zoek")
    z.add_argument("query")
    z.add_argument("--bank", choices=BANKEN, default="leiden")
    z.add_argument("--van", type=int)
    z.add_argument("--tot", type=int)
    z.add_argument("--pagina", type=int, default=1)
    z.add_argument("--sort", default="relevance",
                   help="relevance | 'issuedate ascending' | 'issuedate descending'")
    t = sub.add_parser("toon")
    t.add_argument("pad", help="/issue/... of de volledige URL uit 'zoek'")
    t.add_argument("--bank", choices=BANKEN, default="leiden")
    t.add_argument("--woord")
    t.add_argument("--context", type=int, default=600)
    sc = sub.add_parser("scan", help="paginascan ophalen (jpg, anders pdf + png)")
    sc.add_argument("pad", help="/issue/... of de volledige URL uit 'zoek'")
    sc.add_argument("--bank", choices=BANKEN, default="leiden")
    sc.add_argument("--uit", required=True, help="pad voor de png, bv. test/tijdelijk/krant/pagina.png")
    sc.add_argument("--zoom", type=float, default=3.0)
    sub.add_parser("banken", help="welke krantenbanken kent dit script?")
    args = p.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    return {"zoek": zoek, "toon": toon, "scan": scan, "banken": banken}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

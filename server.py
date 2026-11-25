"""
Local web server for the dashboard.

Serves the tracker folder at http://localhost:8765 and:
  - saves the store restock info you enter to store-notes.json
  - saves what you tick on the dashboard (drop checklists, raffles entered,
    saved flips) to state.json, so the checker can skip raffles you entered
  - looks up recent eBay sold prices for the flip calculator (/api/ebay-sold)
Only reachable from this computer (bound to 127.0.0.1).
"""

import functools
import http.server
import json
import os
import re
import statistics
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAVE_FILES = {"/api/store-notes": HERE / "store-notes.json", "/api/state": HERE / "state.json"}
PORT = 8765
MAX_BODY = 2_000_000

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
# Listings that aren't the real item (empty boxes, proxies, damaged)
JUNK = ["empty", "box only", "no cards", "no packs", "proxy", "custom", "read description",
        "damaged", "opened", "replica", "lot of 0", "for parts"]


def ebay_sold_url(query):
    q = urllib.parse.quote_plus(query)
    return f"https://www.ebay.com/sch/i.html?_nkw={q}&LH_Sold=1&LH_Complete=1&_ipg=120&rt=nc"


def parse_ebay(html, query):
    """Pull (title, price) pairs from an eBay sold-listings page and summarize them."""
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2]
    items = []
    for block in re.split(r"<li[\s>]", html)[1:]:
        t = re.search(r'class="[^"]*(?:s-item__title|s-card__title)[^"]*"[^>]*>(.*?)</(?:div|h3|span)>', block, re.S)
        p = re.search(r'class="[^"]*(?:s-item__price|s-card__price)[^"]*"[^>]*>(.*?)</span>', block, re.S)
        if not (t and p):
            continue
        title = unescape(re.sub(r"<[^>]+>", " ", t.group(1)))
        title = re.sub(r"\s+", " ", title).replace("New Listing", "").strip()
        price_text = re.sub(r"<[^>]+>", " ", p.group(1))
        if not title or title.lower().startswith("shop on ebay") or " to " in price_text:
            continue   # template row, or a price range from a multi-variant listing
        m = re.search(r"\$\s?([\d,]+(?:\.\d{2})?)", price_text)
        if not m:
            continue
        low = title.lower()
        if any(j in low for j in JUNK):
            continue
        if words and sum(w in low for w in words) < max(1, round(0.7 * len(words))):
            continue   # doesn't look like the same product
        items.append((title, float(m.group(1).replace(",", ""))))

    prices = sorted(p for _, p in items)
    if len(prices) >= 5:   # drop outliers outside 1.5x the interquartile range
        q1, q3 = statistics.quantiles(prices, n=4)[0], statistics.quantiles(prices, n=4)[2]
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        kept = [(t, p) for t, p in items if lo <= p <= hi]
        if kept:
            items = kept
            prices = sorted(p for _, p in items)
    if not prices:
        return {"count": 0}
    return {"count": len(prices), "median": round(statistics.median(prices), 2),
            "low": prices[0], "high": prices[-1],
            "examples": [{"title": t, "price": p} for t, p in items[:5]]}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/api/ebay-sold":
            return super().do_GET()
        query = (urllib.parse.parse_qs(url.query).get("q") or [""])[0].strip()[:150]
        if not query:
            return self.send_json(400, {"error": "Type a product name first."})
        link = ebay_sold_url(query)
        try:
            req = urllib.request.Request(link, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read(4_000_000).decode("utf-8", errors="replace")
        except Exception as e:
            return self.send_json(200, {"count": 0, "url": link,
                                        "error": f"eBay didn't answer ({type(e).__name__}). Open the sold listings and enter a price."})
        result = parse_ebay(html, query)
        result["url"] = link
        if not result["count"]:
            result["error"] = ("No matching sold listings found (eBay may have blocked the lookup). "
                               "Open the sold listings and enter a price.")
        self.send_json(200, result)

    def do_POST(self):
        target = SAVE_FILES.get(self.path)
        if not target:
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BODY:
            self.send_error(413)
            return
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("expected an object")
        except ValueError as e:
            self.send_error(400, str(e))
            return
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, target)
        self.send_response(204)
        self.end_headers()

    def send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Always serve fresh data files to the dashboard.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass  # keep the window quiet


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=str(HERE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as srv:
        print(f"Dashboard at http://localhost:{PORT}/index.html")
        srv.serve_forever()

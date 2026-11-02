"""
Restock tracker: stock checker for any product.

Reads products.json, checks each product page, and writes status.js
(which the dashboard, index.html, displays). Uses only the Python
standard library, so there is nothing to install.

Usage:
    python checker.py          check once
    python checker.py --loop   keep checking on the interval in products.json

Each product in products.json:
    name      what to call it
    url       the product page
    retailer  optional, the store name
    category  optional, e.g. "Pokemon TCG", "Sneakers", "Electronics"
    variant   optional, a size/color/storage option to watch, e.g. "10.5" or "Black / 256GB"

How stock is detected (in order):
  1. Shopify stores (URLs with /products/): the store's own product data,
     including per-variant stock when "variant" is set
  2. schema.org data in the page (JSON-LD "availability": InStock / OutOfStock / PreOrder)
  3. Keywords on the page ("add to cart", "sold out", "out of stock", ...)
Many big retailers block automated requests or build pages with JavaScript.
Those show up as "blocked" or "unknown" rather than a wrong answer.
"""

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "products.json"
STATUS_FILE = HERE / "status.js"
HISTORY_CSV = HERE / "history.csv"     # every check, forever (opens in Excel)
HISTORY_JS = HERE / "history.js"       # last 30 days, compacted for the dashboard
HISTORY_DAYS = 30
CSV_FIELDS = ["checked_at", "name", "retailer", "url", "status", "detail"]
MIN_INTERVAL_MINUTES = 5          # be polite; faster polling just gets you blocked
DELAY_BETWEEN_PRODUCTS = 4        # seconds between requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

IN_STOCK, OUT, PREORDER, BLOCKED, UNKNOWN, ERROR = (
    "in_stock", "out_of_stock", "preorder", "blocked", "unknown", "error")

OUT_WORDS = ["sold out", "out of stock", "currently unavailable", "not available",
             "coming soon", "notify me when available", "temporarily out of stock"]
IN_WORDS = ["add to cart", "add to bag", "add to basket", "buy now", "ship it"]
PREORDER_WORDS = ["pre-order", "preorder"]
BLOCK_WORDS = ["captcha", "access denied", "are you a robot", "verify you are human",
               "request unsuccessful", "you have been blocked", "queue-it"]


def load_config():
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def load_previous():
    if not STATUS_FILE.exists():
        return {}
    text = STATUS_FILE.read_text(encoding="utf-8")
    m = re.search(r"window\.STATUS\s*=\s*(\{.*\});", text, re.S)
    if not m:
        return {}
    try:
        return {p.get("key") or p["url"]: p for p in json.loads(m.group(1)).get("products", [])}
    except (json.JSONDecodeError, KeyError):
        return {}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read(2_000_000).decode("utf-8", errors="replace")


def availability_from_jsonld(html):
    """Look for schema.org availability values in JSON-LD or microdata."""
    found = re.findall(r'schema\.org/(InStock|OutOfStock|PreOrder|BackOrder|SoldOut|'
                       r'LimitedAvailability|Discontinued|OnlineOnly|InStoreOnly)', html, re.I)
    found += re.findall(r'"availability"\s*:\s*"(InStock|OutOfStock|PreOrder|BackOrder|SoldOut)"',
                        html, re.I)
    if not found:
        return None
    values = {v.lower() for v in found}
    if values & {"instock", "limitedavailability", "onlineonly"}:
        return IN_STOCK
    if values & {"preorder", "backorder"}:
        return PREORDER
    if values & {"instoreonly"}:
        return UNKNOWN
    return OUT


def availability_from_text(html):
    # Strip scripts/styles/tags so we only look at visible-ish text.
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).lower()
    if any(w in text for w in BLOCK_WORDS):
        return BLOCKED
    if any(w in text for w in OUT_WORDS):
        return OUT
    if any(w in text for w in PREORDER_WORDS):
        return PREORDER
    if any(w in text for w in IN_WORDS):
        return IN_STOCK
    return UNKNOWN


def classify(html):
    return availability_from_jsonld(html) or availability_from_text(html)


def product_key(product):
    """One watched item = a URL plus, optionally, a variant (two sizes = two items)."""
    v = str(product.get("variant") or "").strip()
    return product["url"] + (f"#variant={v}" if v else "")


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def variant_matches(want, variant):
    """True if the wanted text matches this variant's title or one of its options."""
    w = norm(want)
    title = norm(variant.get("title", ""))
    if w == title:
        return True
    parts = [norm(p) for p in title.split("/")]
    parts += [norm(variant.get(k)) for k in ("option1", "option2", "option3") if variant.get(k)]
    if w in parts:
        return True
    # "Black / 256GB" style: every piece of the wanted text matches some option
    pieces = [norm(p) for p in re.split(r"[/,]", want) if p.strip()]
    return len(pieces) > 1 and all(p in parts for p in pieces)


def check_shopify(url, want):
    """Shopify exposes every product as JSON at <product url>.js. Returns None if not Shopify."""
    m = re.match(r"(https?://[^?#]+/products/[^/?#]+)", url)
    if not m:
        return None
    try:
        _, body = fetch(m.group(1) + ".js")
        data = json.loads(body)
        variants = data.get("variants") or []
    except Exception:
        return None
    if not isinstance(data, dict) or not variants:
        return None
    if not want:
        status = IN_STOCK if data.get("available") else OUT
        n_avail = sum(1 for v in variants if v.get("available"))
        detail = f"Shopify · {n_avail} of {len(variants)} options available" if len(variants) > 1 else "Shopify"
        return status, detail
    hits = [v for v in variants if variant_matches(want, v)]
    if not hits:
        names = ", ".join(v.get("title", "?") for v in variants[:10])
        return UNKNOWN, f"Variant \"{want}\" not found. Options: {names}"
    avail = [v for v in hits if v.get("available")]
    status = IN_STOCK if avail else OUT
    if len(hits) == 1:
        return status, f"Shopify · variant {hits[0].get('title', want)}"
    shown = ", ".join(v.get("title", "?") for v in avail[:4]) or "none"
    return status, f"Shopify · {len(avail)} of {len(hits)} \"{want}\" options available ({shown})"


def check_product(product):
    url = product["url"]
    want = str(product.get("variant") or "").strip()
    shop = check_shopify(url, want)
    if shop:
        return shop
    try:
        code, html = fetch(url)
        status = classify(html)
        detail = f"HTTP {code}"
        if want:
            detail += f" · whole product, variant \"{want}\" can't be checked on this site"
    except urllib.error.HTTPError as e:
        status = BLOCKED if e.code in (401, 403, 429, 503) else ERROR
        detail = f"HTTP {e.code}"
    except Exception as e:  # network errors, timeouts
        status, detail = ERROR, type(e).__name__
    return status, detail


def notify(topic, title, message, url):
    """Free push notifications through ntfy.sh (install the ntfy app, subscribe to your topic)."""
    if not topic:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
        headers={"Title": title, "Click": url, "Priority": "high", "Tags": "rotating_light"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  (notification failed: {e})")


def run_once():
    config = load_config()
    previous = load_previous()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    results = []
    for i, product in enumerate(config.get("products", [])):
        if i:
            time.sleep(DELAY_BETWEEN_PRODUCTS)
        status, detail = check_product(product)
        key = product_key(product)
        prev = previous.get(key, {})
        changed = prev.get("status") != status
        last_change = now if changed else prev.get("last_change", now)
        results.append({**product, "key": key, "status": status, "detail": detail,
                        "checked": now, "last_change": last_change})
        label = product["name"] + (f" ({product['variant']})" if product.get("variant") else "")
        print(f"[{status:>12}] {label}  ({detail})")

        became_available = status in (IN_STOCK, PREORDER) and prev.get("status") not in (IN_STOCK, PREORDER)
        if prev and became_available:
            notify(config.get("ntfy_topic", ""), f"Restock: {label}",
                   f"{product.get('retailer', '')} shows {status.replace('_', ' ')}", product["url"])

    payload = {"updated": now, "products": results}
    STATUS_FILE.write_text("window.STATUS = " + json.dumps(payload, indent=2) + ";\n",
                           encoding="utf-8")
    append_history(results)
    build_history_js(config)


def append_history(results):
    new_file = not HISTORY_CSV.exists()
    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        for r in results:
            w.writerow({**r, "checked_at": r["checked"], "url": r["key"]})


def build_history_js(config):
    """Turn the last 30 days of checks into status segments per product.

    A segment is [start, end, status] in Unix seconds. A new segment starts when
    the status changes, or after a gap longer than the gap limit (the PC was off
    or the checker stopped), so the dashboard can show that time as untracked.
    """
    interval = max(MIN_INTERVAL_MINUTES, config.get("check_every_minutes", 10))
    gap_limit = max(30, 3 * interval) * 60
    cutoff = (datetime.now().astimezone() - timedelta(days=HISTORY_DAYS)).timestamp()
    checks = {}
    try:
        with HISTORY_CSV.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.fromisoformat(row["checked_at"]).timestamp()
                except (KeyError, ValueError):
                    continue
                if t >= cutoff:
                    checks.setdefault(row["url"], []).append((t, row))
    except FileNotFoundError:
        return

    by_key = {product_key(p): p for p in config.get("products", [])}
    products = []
    for url, rows in checks.items():
        rows.sort(key=lambda x: x[0])
        segs = []
        for t, row in rows:
            st = row["status"]
            if segs and t - segs[-1][1] <= gap_limit:
                if segs[-1][2] == st:
                    segs[-1][1] = t
                    continue
                segs[-1][1] = t          # previous status lasted until this check
            segs.append([t, t, st])
        last = rows[-1][1]
        cfg = by_key.get(url, {})
        products.append({"url": url.split("#variant=")[0], "key": url, "name": last["name"],
                         "retailer": last["retailer"], "category": cfg.get("category", ""),
                         "variant": cfg.get("variant", ""), "watching": url in by_key,
                         "segments": [[int(a), int(b), s] for a, b, s in segs]})

    payload = {"generated": int(time.time()), "gap_seconds": gap_limit,
               "interval_minutes": interval, "products": products}
    HISTORY_JS.write_text("window.HISTORY = " + json.dumps(payload, separators=(",", ":")) + ";\n",
                          encoding="utf-8")


def main():
    if "--loop" not in sys.argv:
        run_once()
        return
    while True:
        minutes = max(MIN_INTERVAL_MINUTES, load_config().get("check_every_minutes", 10))
        print(f"\n--- {datetime.now():%H:%M:%S} checking ---")
        run_once()
        print(f"Next check in {minutes} minutes. Press Ctrl+C to stop.")
        time.sleep(minutes * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")

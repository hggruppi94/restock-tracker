# Restock Tracker

A small local tracker for any product (trading cards, sneakers, consoles, anything with a product page):

- **Stock watch**: checks the product pages you choose every few minutes and shows in stock / out of stock (`checker.py`).
- **Stock trends**: a history of every check, with restock patterns.
- **Stores near me**: nearby stores of any type, with GPS coordinates and a restock schedule for each.
- **Upcoming drops**: release dates for anything you're waiting on (`releases.js`).

## Files

| File | What it does |
|---|---|
| `index.html` | The dashboard. Open it through `start-tracker.bat`; it refreshes every minute. |
| `products.json` | The products to watch, the check interval, and an optional notification topic. |
| `products.example.json` | An example showing categories and size/variant watching. |
| `checker.py` | Checks each product and writes `status.js`, `history.csv` and `history.js`. |
| `releases.js` | Upcoming drops. Add any product's release dates. |
| `start-tracker.bat` | Double-click to open the dashboard and start checking. |
| `server.py` | Serves the dashboard at http://localhost:8765 and saves store schedules. Started by the .bat file. |
| `store-notes.json` | Your store restock schedules. Created the first time you save one. Back it up. |

## Watching products

Each product in `products.json`:

```json
{ "name": "Jordan 1 Retro", "retailer": "Some shop", "category": "Sneakers", "variant": "10.5", "url": "https://..." }
```

- `name` and `url` are required.
- `category` is anything you like ("Pokémon TCG", "Sneakers", "Electronics"). The chips at the top of the
  dashboard filter by it. Products without one show under "General".
- `variant` is optional: a size, color or option to watch (for example `"10.5"`, `"Black"`, `"Black / 256GB"`).
  It's checked exactly on Shopify stores (URLs containing `/products/`), which many sneaker and hobby shops use.
  On other sites the whole product is checked and the dashboard says the variant couldn't be checked.
- To watch two sizes of the same item, add it twice with different `variant` values.

## Stock trends

- Every check is appended to `history.csv` (opens in Excel; keep it as your long-term log).
- `history.js` holds the last 30 days, compacted for the dashboard.
- Each product gets a 7- or 30-day timeline plus: % of tracked time in stock, restock count, typical time
  before selling out, last restock, and the most common restock day and time.
- **When restocks happen** is a weekday × time-of-day grid, plus a row for in-store restocks you logged.
- Gaps are times the PC was off. Stores show in stock / out of stock, not unit counts.

## Stores near me and restock schedules

- Click **Use my location** or type a ZIP code, then pick a radius.
- Tick the store types to search: big-box, electronics and games, shoes and sneakers, toys and hobby, books,
  sporting goods, department stores, clothing, beauty, home and hardware.
- Type any store name or shop type (e.g. "Apple", "Lego", "vinyl") and click **Add to search** for anything else.
- Each store shows distance, GPS coordinates (Copy button) and a directions link. Data: OpenStreetMap.
- Click **Add restock schedule** on a store: what restocks there, restock days, usual time, last restock seen,
  where the info came from (staff, your own sightings, community, guess) and notes.
- **Saw a restock today** logs a sighting in one click. Stores likely to restock today are highlighted at the top of **My stores**.

### Finding a store's restock schedule

Stores don't publish restock schedules. What works best, in order:
1. Ask staff once which days trucks arrive or when the vendor stocks your product, and record it.
2. Log every restock you see. After a few weeks the "In store" row of the restock grid shows the real pattern.
3. Use the online trend grid and local Discord/Reddit groups to fill gaps.

## Setup (Windows)

1. Install Python from python.org (tick **Add python.exe to PATH**).
2. Put your products in `products.json` (see `products.example.json`).
3. Double-click `start-tracker.bat`. Leave the windows open; close them to stop.

## Phone alerts (optional, free)

1. Install the **ntfy** app on your phone.
2. Subscribe to a hard-to-guess topic name, e.g. `restock-alerts-7f3k2`.
3. Put that same name in `"ntfy_topic"` in `products.json`.

## What to expect

- **Works best on:** smaller shops and sites that publish standard product data (most Shopify stores do).
- **Often "Blocked":** big retailers (Target, Walmart, Nike, Foot Locker, Pokémon Center) block automated checks.
  Keep them for the link, but rely on alerts communities for those.
- **Interval:** minimum 5 minutes. Faster checking gets you blocked and may break retailer terms.
- **Accuracy:** "In stock" means the page said so at check time. Hyped drops can sell out in under a minute.

# Restock Tracker

A small local tracker for any product (trading cards, sneakers, consoles, anything with a product page):

- **Stock watch**: checks the product pages you choose every few minutes and shows in stock / out of stock (`checker.py`).
- **Stock trends**: a history of every check, with restock patterns.
- **Stores near me**: nearby stores of any type, with GPS coordinates and a restock schedule for each.
- **Upcoming drops**: release dates for anything you're waiting on (`releases.js`), with a countdown,
  prep checklist and phone reminder for timed online drops.
- **One-tap cart**: on Shopify stores, a button (and the phone alert) that opens checkout with the item already in your cart.
- **Raffles & queues**: entry windows for raffles, draws and online queues (`raffles.js`), with reminders until you tick Entered.
- **Flip calculator**: recent eBay *sold* prices and your profit after tax, fees and shipping.

## Files

| File | What it does |
|---|---|
| `index.html` | The dashboard. Open it through `start-tracker.bat`; it refreshes every minute. |
| `products.json` | The products to watch, the check interval, and an optional notification topic. |
| `products.example.json` | An example showing categories and size/variant watching. |
| `checker.py` | Checks each product and writes `status.js`, `history.csv` and `history.js`. |
| `releases.js` | Upcoming drops. Add any product's release dates, plus an optional time and links for online drops. |
| `raffles.js` | Raffles, draws and queues to enter. |
| `state.json` | What you tick on the dashboard (drop checklists, raffles entered, saved flips). Created by `server.py`. |
| `reminders.json` | Reminders already sent, so each one goes out once. Created by `checker.py`. |
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

## Timed drops, raffles and queues

Give a drop in `releases.js` a `time` (24-hour, your PC's time zone), a `retailer` and `links`:

```js
{ name: "ETB restock", category: "Pokémon TCG", date: "2026-12-05", time: "10:00", retailer: "Pokémon Center",
  status: "confirmed", links: [{ label: "Pokémon Center", url: "https://www.pokemoncenter.com/..." }] },
```

It appears under **Next drop** for the week before, with a live countdown and a checklist (signed in, payment
saved, address saved, links open, phone alerts on). Your phone gets a reminder about 30–45 minutes before.

`raffles.js` works the same way with `opens` and `closes` times. You get a phone alert when entry opens and
3 hours before it closes, until you tick **Entered** on the dashboard.

## One-tap cart

On Shopify stores the checker records the exact in-stock option. When it's in stock, the dashboard shows
**⚡ One-tap cart**, and the restock alert on your phone opens checkout with one already in the cart. You still
review and place the order yourself. Set `variant` for anything with sizes or colors; without it the button
only appears for single-option products, so it can never add the wrong size.

## Flip calculator

Type a product (or click **Flip check** on any product, drop or raffle) and click **Look up eBay sold prices**.
It takes the median of recent *sold* listings, skips junk like empty boxes, and shows your profit after sales tax,
eBay fees and shipping, your return, and the break-even sale price. If eBay blocks the lookup, use
**Open sold listings** and type the price. Fees vary by category and change; adjust them to eBay's current rates.

## Phone alerts (optional, free)

1. Install the **ntfy** app on your phone.
2. Subscribe to a hard-to-guess topic name, e.g. `restock-alerts-7f3k2`.
3. Put that same name in `"ntfy_topic"` in `products.json`.

You'll get restock alerts, drop reminders and raffle reminders there. Alerts only go out while `start-tracker.bat` is running.

## What to expect

- **Works best on:** smaller shops and sites that publish standard product data (most Shopify stores do).
- **Often "Blocked":** big retailers (Target, Walmart, Nike, Foot Locker, Pokémon Center) block automated checks.
  Keep them for the link, but rely on alerts communities for those.
- **Interval:** minimum 5 minutes. Faster checking gets you blocked and may break retailer terms.
- **Accuracy:** "In stock" means the page said so at check time. Hyped drops can sell out in under a minute.

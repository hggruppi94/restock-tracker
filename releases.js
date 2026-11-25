// Upcoming drops. Add release dates for any product.
// category: any label ("Pokémon TCG", "Sneakers", ...). The dashboard's category chips filter by it.
// status: "released" | "confirmed" | "reported" | "rumored"
// category: "Pokémon TCG", region: "EN" (English) | "JP" (Japanese)
//
// Timed online drops (optional): add time (24-hour, this PC's time zone), retailer and links.
// The dashboard then shows a countdown with a prep checklist, and your phone gets a
// reminder about 30-45 minutes before it goes live. Example:
//   { name: "Some ETB restock", category: "Pokémon TCG", date: "2026-12-05", time: "10:00", retailer: "Pokémon Center",
//     status: "confirmed", links: [{ label: "Pokémon Center", url: "https://www.pokemoncenter.com/..." }] },
window.RELEASES = [
  { name: "Perfect Order",     category: "Pokémon TCG", region: "EN", date: "2026-03-27", type: "Main expansion",        status: "released" },
  { name: "Chaos Rising",      category: "Pokémon TCG", region: "EN", date: "2026-05-22", type: "Main expansion",        status: "released" },
  { name: "Pitch Black",       category: "Pokémon TCG", region: "EN", date: "2026-07-17", type: "Main expansion",        status: "released", note: "Mega Darkrai ex" },
  { name: "30th Celebration",  category: "Pokémon TCG", region: "EN", date: "2026-09-16", type: "30th anniversary set",  status: "released", note: "First worldwide same-day release" },
  { name: "Delta Reign",       category: "Pokémon TCG", region: "EN", date: "2026-11-06", type: "Main expansion",        status: "released", note: "English version of Storm Emeralda (Mega Rayquaza ex)" },
  { name: "Aura Seeker (M7)",  category: "Pokémon TCG", region: "JP", date: "2026-11-27", type: "Main expansion",        status: "reported", note: "Date reported, not yet official in Japan" },
  { name: "Aura Seeker (English)", category: "Pokémon TCG", region: "EN", date: null,    type: "Main expansion",        status: "rumored", note: "Floated for early 2027, unconfirmed" },
  { name: "MEGA×MEGA Parade",  category: "Pokémon TCG", region: "JP", date: null,         type: "Unknown",               status: "rumored", note: "Trademark only" }
];
window.RELEASES_UPDATED = "2026-11-24";

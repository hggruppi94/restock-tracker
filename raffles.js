// Raffles, draws and online queues for hyped products.
// A weekly scheduled task can send you new lines to paste here.
//
// Fields:
//   name      what it's for
//   type      "raffle" | "queue" | "draw" | "invite"
//   retailer  the store
//   category  any label ("Pokémon TCG", "Sneakers", ...) for the category chips
//   opens     when entry opens: "2026-12-01T10:00" (this PC's time zone) or null if already open
//   closes    when entry closes, same format, or null if unknown
//   url       where to enter
//   product   optional, what to price in the flip calculator (defaults to name)
//   note      optional
//
// Tick "Entered" on the dashboard and the checker stops reminding you about it.
window.RAFFLES = [
];
window.RAFFLES_UPDATED = "2026-11-24";

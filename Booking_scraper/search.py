"""
Booking.com Hotel Search pro Sardinii - Bright Data API
Hledá kombinaci dvou ubytování v zadaném termínu.
"""

import os
import json
import time
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BRIGHTDATA_API_KEY")
DATASET_ID = os.getenv("BRIGHTDATA_DATASET_ID")

# === NASTAVENÍ HLEDÁNÍ ===
CHECKIN_TOTAL = date(2026, 9, 10)
CHECKOUT_TOTAL = date(2026, 9, 22)
ADULTS = 2
CHILDREN = [1]  # seznam věků dětí (v letech)
ROOMS = 1

# Destinace (části ostrova)
DESTINATIONS = [
    {"name": "jihozápad Sardinie", "query": "Southwest Sardinia, Italy"},
    {"name": "severozápad Sardinie", "query": "Northwest Sardinia, Italy"},
]

# Minimální hodnocení (0-10)
MIN_RATING = 8.0

# Budget: max 2800 Kč/noc — převedeno na EUR (kurz ~25 Kč/EUR)
MAX_PRICE_PER_NIGHT_CZK = 2800
CZK_TO_EUR = 25
MAX_PRICE_PER_NIGHT = MAX_PRICE_PER_NIGHT_CZK / CZK_TO_EUR  # ~112 EUR

# === BRIGHT DATA API ===
BASE_URL = "https://api.brightdata.com/datasets/v3"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def trigger_search(destination_query: str, checkin: date, checkout: date) -> str:
    """Spustí vyhledávání přes Bright Data API."""
    children_params = "".join(f"&age={age}" for age in CHILDREN)
    payload = [
        {
            "url": (
                f"https://www.booking.com/searchresults.html"
                f"?ss={destination_query.replace(' ', '+')}"
                f"&checkin={checkin.isoformat()}"
                f"&checkout={checkout.isoformat()}"
                f"&group_adults={ADULTS}"
                f"&group_children={len(CHILDREN)}"
                f"{children_params}"
                f"&no_rooms={ROOMS}"
            )
        }
    ]

    resp = requests.post(
        f"{BASE_URL}/trigger",
        headers=HEADERS,
        params={"dataset_id": DATASET_ID, "include_errors": "true"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    snapshot_id = resp.json().get("snapshot_id")
    print(f"  Snapshot spuštěn: {snapshot_id}")
    return snapshot_id


def wait_for_results(snapshot_id: str, max_wait_seconds: int = 300) -> list:
    """Čeká na dokončení snapshotu a vrátí výsledky."""
    print(f"  Čekám na výsledky (max {max_wait_seconds}s)...", end="", flush=True)
    waited = 0
    while waited < max_wait_seconds:
        time.sleep(10)
        waited += 10
        print(".", end="", flush=True)

        resp = requests.get(
            f"{BASE_URL}/snapshot/{snapshot_id}",
            headers=HEADERS,
            params={"format": "json"},
            timeout=30,
        )
        if resp.status_code == 200:
            print(" hotovo!")
            return resp.json()
        if resp.status_code != 202:
            resp.raise_for_status()

    raise TimeoutError(f"Snapshot {snapshot_id} se nedokončil v čase.")


def filter_hotels(hotels: list, checkin: date, checkout: date) -> list:
    """Filtruje hotely podle hodnocení a ceny."""
    nights = (checkout - checkin).days
    filtered = []
    for h in hotels:
        rating = float(h.get("review_score") or h.get("rating") or 0)
        price_total = float(h.get("price") or h.get("price_per_night") or 0)
        price_per_night = price_total / nights if nights > 0 else price_total

        if rating < MIN_RATING:
            continue
        if MAX_PRICE_PER_NIGHT and price_per_night > MAX_PRICE_PER_NIGHT:
            continue

        filtered.append({
            "name": h.get("name") or h.get("hotel_name", "?"),
            "rating": rating,
            "price_total": round(price_total, 2),
            "price_per_night": round(price_per_night, 2),
            "price_per_night_czk": round(price_per_night * CZK_TO_EUR),
            "nights": nights,
            "checkin": checkin.isoformat(),
            "checkout": checkout.isoformat(),
            "location": h.get("location") or h.get("address") or h.get("city", ""),
            "breakfast": _has_breakfast(h),
            "url": h.get("url") or h.get("link", ""),
        })

    return sorted(filtered, key=lambda x: (-x["rating"], x["price_per_night"]))


def _has_breakfast(hotel: dict) -> bool:
    """Zjistí, zda hotel nabízí snídani."""
    text = json.dumps(hotel).lower()
    return any(k in text for k in ["breakfast", "snídaně", "colazione"])


def find_combinations(results_by_dest: dict, total_nights: int) -> list:
    """Najde nejlepší kombinace dvou ubytování."""
    destinations = list(results_by_dest.keys())
    if len(destinations) < 2:
        return []

    combos = []
    for split in range(3, total_nights - 2):  # min 3 noci na každém místě
        nights_a = split
        nights_b = total_nights - split

        for hotel_a in results_by_dest[destinations[0]][:10]:
            for hotel_b in results_by_dest[destinations[1]][:10]:
                total_price = (
                    hotel_a["price_per_night"] * nights_a
                    + hotel_b["price_per_night"] * nights_b
                )
                avg_rating = (hotel_a["rating"] + hotel_b["rating"]) / 2
                combos.append({
                    "hotel_a": {**hotel_a, "nights_in_combo": nights_a},
                    "hotel_b": {**hotel_b, "nights_in_combo": nights_b},
                    "total_price_eur": round(total_price, 2),
                    "avg_rating": round(avg_rating, 2),
                    "split": f"{nights_a}+{nights_b} nocí",
                })

    return sorted(combos, key=lambda x: (-x["avg_rating"], x["total_price_eur"]))[:20]


def format_for_claude(results: dict, combos: list, total_nights: int) -> str:
    """Vytvoří přehledný text pro vložení do Claude chatu."""
    children_info = f" + {len(CHILDREN)} dítě (věk: {', '.join(str(a) for a in CHILDREN)} r.)"
    lines = [
        "# Výsledky hledání ubytování na Sardinii",
        f"Termín: {CHECKIN_TOTAL} – {CHECKOUT_TOTAL} ({total_nights} nocí)",
        f"Osoby: {ADULTS} dospělí{children_info} | Min. hodnocení: {MIN_RATING}",
        f"Max. cena/noc: {MAX_PRICE_PER_NIGHT_CZK} Kč (~{MAX_PRICE_PER_NIGHT:.0f} EUR, kurz {CZK_TO_EUR} Kč/EUR)",
        "",
    ]

    for dest, hotels in results.items():
        lines.append(f"## {dest} ({len(hotels)} ubytování splňuje kritéria)")
        for i, h in enumerate(hotels[:15], 1):
            snidane = " | ✓ snídaně" if h["breakfast"] else ""
            lines.append(
                f"{i}. **{h['name']}** | ⭐ {h['rating']} | "
                f"{h['price_per_night_czk']} Kč/noc (~{h['price_per_night']} EUR){snidane}"
            )
            if h["location"]:
                lines.append(f"   📍 {h['location']}")
            if h["url"]:
                lines.append(f"   {h['url']}")
        lines.append("")

    if combos:
        lines.append("## TOP kombinace dvou ubytování")
        for i, c in enumerate(combos[:10], 1):
            a, b = c["hotel_a"], c["hotel_b"]
            total_czk = round(c["total_price_eur"] * CZK_TO_EUR)
            lines.append(
                f"\n### Kombinace {i} – {c['split']} | "
                f"Celkem ~{total_czk} Kč (~{c['total_price_eur']} EUR) | ⭐ avg {c['avg_rating']}"
            )
            lines.append(
                f"  1. {a['name']} ({a['nights_in_combo']} nocí | ⭐{a['rating']} | "
                f"{a['price_per_night_czk']} Kč/noc)"
            )
            lines.append(
                f"  2. {b['name']} ({b['nights_in_combo']} nocí | ⭐{b['rating']} | "
                f"{b['price_per_night_czk']} Kč/noc)"
            )

    return "\n".join(lines)


def main():
    if not API_KEY or API_KEY == "your_api_key_here":
        print("CHYBA: Nastav BRIGHTDATA_API_KEY v souboru .env")
        return
    if not DATASET_ID or DATASET_ID == "your_dataset_id_here":
        print("CHYBA: Nastav BRIGHTDATA_DATASET_ID v souboru .env")
        return

    total_nights = (CHECKOUT_TOTAL - CHECKIN_TOTAL).days
    print(f"Hledám ubytování na Sardinii | {CHECKIN_TOTAL} – {CHECKOUT_TOTAL} ({total_nights} nocí)")
    print(f"Osoby: {ADULTS} dospělí + {len(CHILDREN)} dítě | Max {MAX_PRICE_PER_NIGHT_CZK} Kč/noc")
    print()

    results_by_dest = {}

    for dest in DESTINATIONS:
        print(f"[{dest['name']}]")
        try:
            snapshot_id = trigger_search(dest["query"], CHECKIN_TOTAL, CHECKOUT_TOTAL)
            raw_hotels = wait_for_results(snapshot_id)
            filtered = filter_hotels(raw_hotels, CHECKIN_TOTAL, CHECKOUT_TOTAL)
            results_by_dest[dest["name"]] = filtered
            print(f"  Nalezeno: {len(raw_hotels)} celkem, {len(filtered)} splňuje kritéria")
        except Exception as e:
            print(f"  CHYBA: {e}")
            results_by_dest[dest["name"]] = []
        print()

    combos = find_combinations(results_by_dest, total_nights)

    output = format_for_claude(results_by_dest, combos, total_nights)

    output_file = "vysledky_sardinie.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nVýsledky uloženy do: {output_file}")
    print("Obsah pro Claude chat:\n")
    print(output)


if __name__ == "__main__":
    main()

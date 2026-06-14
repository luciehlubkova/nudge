"""
Booking.com scraper pro Sardinii - Bright Data API
Hledá: agriturismo na jihu + B&B/penzion na severozápadě
NEPROVÁDÍ rezervaci — pouze vyhledává a porovnává.
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

# === TERMÍN ===
CHECKIN_TOTAL = date(2026, 9, 10)
CHECKOUT_TOTAL = date(2026, 9, 22)
ADULTS = 2
CHILDREN = [1]   # věk dítěte v letech (Booking.com: age=1)
ROOMS = 1
TOTAL_NIGHTS = (CHECKOUT_TOTAL - CHECKIN_TOTAL).days  # 12

# === SPOLEČNÉ FILTRY ===
MIN_RATING = 8.5
MAX_PRICE_PER_NIGHT_CZK = 2800
CZK_TO_EUR = 25
MAX_PRICE_PER_NIGHT_EUR = MAX_PRICE_PER_NIGHT_CZK / CZK_TO_EUR  # ~112 EUR

# === ROZSAHY ROZDĚLENÍ NOCÍ (min 4, max 8 na každém místě) ===
MIN_NIGHTS_PER_STAY = 4
MAX_NIGHTS_PER_STAY = 8

# === PROFIL 1: AGRITURISMO NA JIHU ===
STAY_1 = {
    "id": "farm_south",
    "label": "Ubytování 1 – Agriturismo / farma (jih)",
    "destinations": [
        {"name": "Teulada", "query": "Teulada, Sardinia, Italy"},
        {"name": "Chia",    "query": "Chia, Sardinia, Italy"},
        {"name": "Pula",    "query": "Pula, Sardinia, Italy"},
        {"name": "Domus de Maria", "query": "Domus de Maria, Sardinia, Italy"},
    ],
    # klíčová slova pro typ ubytování (v názvu nebo popisu)
    "type_keywords": [
        "agriturismo", "agriturismo", "farm", "fattoria",
        "masseria", "podere", "azienda agricola",
    ],
    # musí obsahovat (v amenities/popisu)
    "required_amenities": ["pool", "piscina", "swimming"],
    "required_family": ["family", "bambini", "children", "kids", "crib", "cot"],
    # preferované stravování (alespoň jedno)
    "meal_keywords": [
        "half board", "mezza pensione", "half-board",
        "breakfast", "colazione", "prima colazione",
        "kitchen", "kitchenette", "cucina", "kitchenette",
    ],
    # bonus (zvyšují skóre, ale nejsou povinné)
    "bonus_keywords": [
        "animals", "animali", "horses", "cavalli",
        "playground", "giochi", "playroom",
        "farm animals", "barnyard",
    ],
}

# === PROFIL 2: B&B / PENZION NA SEVEROZÁPADĚ ===
STAY_2 = {
    "id": "city_northwest",
    "label": "Ubytování 2 – B&B / penzion (severozápad)",
    "destinations": [
        {"name": "Bosa",    "query": "Bosa, Sardinia, Italy"},      # primární
        {"name": "Alghero", "query": "Alghero, Sardinia, Italy"},   # sekundární
    ],
    "type_keywords": [
        "b&b", "bed and breakfast", "bed & breakfast",
        "pension", "penzion", "guesthouse", "guest house",
        "boutique", "locanda", "albergo diffuso",
    ],
    "required_amenities": [],
    "required_family": [],
    # snídaně musí být v ceně — tvrdý filtr
    "meal_keywords": [
        "breakfast included", "breakfast", "colazione inclusa",
        "colazione", "prima colazione",
    ],
    "bonus_keywords": ["sea view", "vista mare", "panoramic", "historic center"],
}

# === BRIGHT DATA API ===
BASE_URL = "https://api.brightdata.com/datasets/v3"


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _booking_url(query: str, checkin: date, checkout: date) -> str:
    children_ages = "".join(f"&age={a}" for a in CHILDREN)
    q = query.replace(" ", "+").replace(",", "%2C")
    return (
        f"https://www.booking.com/searchresults.html"
        f"?ss={q}"
        f"&checkin={checkin.isoformat()}"
        f"&checkout={checkout.isoformat()}"
        f"&group_adults={ADULTS}"
        f"&group_children={len(CHILDREN)}{children_ages}"
        f"&no_rooms={ROOMS}"
        f"&nflt=review_score%3D85"   # min. hodnocení 8.5 přímo v URL filtru
    )


def trigger_search(dest_query: str, checkin: date, checkout: date) -> str:
    payload = [{"url": _booking_url(dest_query, checkin, checkout)}]
    resp = requests.post(
        f"{BASE_URL}/trigger",
        headers=_headers(),
        params={"dataset_id": DATASET_ID, "include_errors": "true"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    snapshot_id = resp.json().get("snapshot_id")
    print(f"    snapshot: {snapshot_id}")
    return snapshot_id


def wait_for_snapshot(snapshot_id: str, max_wait: int = 360) -> list:
    print(f"    čekám na výsledky", end="", flush=True)
    waited = 0
    while waited < max_wait:
        time.sleep(15)
        waited += 15
        print(".", end="", flush=True)
        resp = requests.get(
            f"{BASE_URL}/snapshot/{snapshot_id}",
            headers=_headers(),
            params={"format": "json"},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f" OK ({len(data)} záznamů)")
            return data if isinstance(data, list) else []
        if resp.status_code != 202:
            resp.raise_for_status()
    raise TimeoutError(f"Snapshot {snapshot_id} se nedokončil v čase.")


def _text(hotel: dict) -> str:
    """Spojí všechna textová pole hotelu pro prohledávání."""
    return json.dumps(hotel, ensure_ascii=False).lower()


def _has_any(text: str, keywords: list) -> bool:
    return any(kw.lower() in text for kw in keywords)


def _count_bonus(text: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw.lower() in text)


def _detect_meal(text: str) -> str:
    if _has_any(text, ["half board", "mezza pensione", "half-board", "polopenze"]):
        return "polopenze"
    if _has_any(text, ["full board", "pensione completa"]):
        return "plná penze"
    if _has_any(text, ["breakfast included", "breakfast", "colazione inclusa", "colazione"]):
        return "snídaně"
    if _has_any(text, ["kitchen", "kitchenette", "cucina"]):
        return "kuchyňský kout"
    return "bez stravy"


def filter_hotels(raw: list, profile: dict, checkin: date, checkout: date) -> list:
    nights = (checkout - checkin).days
    results = []

    for h in raw:
        text = _text(h)

        # Hodnocení
        rating = 0.0
        for key in ("review_score", "rating", "score"):
            try:
                rating = float(h.get(key) or 0)
                if rating > 0:
                    break
            except (ValueError, TypeError):
                pass
        if rating < MIN_RATING:
            continue

        # Cena
        price_total = 0.0
        for key in ("price", "total_price", "price_per_night"):
            try:
                price_total = float(h.get(key) or 0)
                if price_total > 0:
                    break
            except (ValueError, TypeError):
                pass
        if price_total <= 0:
            continue
        price_per_night = price_total / nights if nights > 1 else price_total
        if price_per_night > MAX_PRICE_PER_NIGHT_EUR:
            continue

        # Typ ubytování
        if profile["type_keywords"] and not _has_any(text, profile["type_keywords"]):
            continue

        # Povinné amenities (pool pro farmu)
        if profile["required_amenities"] and not _has_any(text, profile["required_amenities"]):
            continue

        # Rodinná vhodnost (pro farmu)
        if profile["required_family"] and not _has_any(text, profile["required_family"]):
            continue

        # Stravování — pro severozápad je snídaně tvrdý filtr
        meal = _detect_meal(text)
        if profile["id"] == "city_northwest" and meal == "bez stravy":
            continue

        # Bonus skóre
        bonus = _count_bonus(text, profile.get("bonus_keywords", []))

        results.append({
            "name": (h.get("name") or h.get("hotel_name") or "?").strip(),
            "rating": rating,
            "price_per_night_eur": round(price_per_night, 1),
            "price_per_night_czk": round(price_per_night * CZK_TO_EUR),
            "meal": meal,
            "location": (
                h.get("location") or h.get("address") or
                h.get("city") or h.get("neighborhood") or ""
            ).strip(),
            "bonus": bonus,
            "url": (h.get("url") or h.get("link") or "").strip(),
            # pomocné pro kombinace
            "_checkin": checkin.isoformat(),
            "_checkout": checkout.isoformat(),
            "_nights": nights,
        })

    # seřadit: hodnocení desc, pak cena asc, pak bonus desc
    results.sort(key=lambda x: (-x["rating"], x["price_per_night_eur"], -x["bonus"]))
    return results


def search_profile(profile: dict) -> list:
    """Projde všechny destinace profilu a vrátí sloučené výsledky."""
    all_hotels = []
    seen_names = set()

    for dest in profile["destinations"]:
        print(f"  [{dest['name']}]")
        try:
            sid = trigger_search(dest["query"], CHECKIN_TOTAL, CHECKOUT_TOTAL)
            raw = wait_for_snapshot(sid)
            filtered = filter_hotels(raw, profile, CHECKIN_TOTAL, CHECKOUT_TOTAL)
            for h in filtered:
                key = h["name"].lower()
                if key not in seen_names:
                    seen_names.add(key)
                    h["_dest"] = dest["name"]
                    all_hotels.append(h)
            print(f"    → {len(filtered)} splňuje kritéria")
        except Exception as e:
            print(f"    CHYBA: {e}")

    all_hotels.sort(key=lambda x: (-x["rating"], x["price_per_night_eur"], -x["bonus"]))
    return all_hotels


def build_combinations(hotels_1: list, hotels_2: list) -> list:
    """
    Vygeneruje kombinace dvou ubytování se všemi přijatelnými rozděleními nocí.
    Pořadí: nejdříve farma na jihu, pak severozápad.
    """
    combos = []
    for nights_1 in range(MIN_NIGHTS_PER_STAY, MAX_NIGHTS_PER_STAY + 1):
        nights_2 = TOTAL_NIGHTS - nights_1
        if not (MIN_NIGHTS_PER_STAY <= nights_2 <= MAX_NIGHTS_PER_STAY):
            continue

        checkin_1 = CHECKIN_TOTAL
        checkout_1 = checkin_1 + timedelta(days=nights_1)
        checkin_2 = checkout_1
        checkout_2 = CHECKOUT_TOTAL  # vždy 22.9.

        for h1 in hotels_1[:10]:
            for h2 in hotels_2[:10]:
                cost_1 = h1["price_per_night_eur"] * nights_1
                cost_2 = h2["price_per_night_eur"] * nights_2
                total_eur = round(cost_1 + cost_2, 1)
                total_czk = round(total_eur * CZK_TO_EUR)
                avg_rating = round((h1["rating"] + h2["rating"]) / 2, 2)

                # value score: čím vyšší hodnocení a nižší cena, tím lepší
                value = avg_rating / (total_eur / TOTAL_NIGHTS)

                combos.append({
                    "hotel_1": {
                        **h1,
                        "nights": nights_1,
                        "checkin": checkin_1.isoformat(),
                        "checkout": checkout_1.isoformat(),
                        "subtotal_eur": round(cost_1, 1),
                        "subtotal_czk": round(cost_1 * CZK_TO_EUR),
                    },
                    "hotel_2": {
                        **h2,
                        "nights": nights_2,
                        "checkin": checkin_2.isoformat(),
                        "checkout": checkout_2.isoformat(),
                        "subtotal_eur": round(cost_2, 1),
                        "subtotal_czk": round(cost_2 * CZK_TO_EUR),
                    },
                    "split": f"{nights_1}+{nights_2}",
                    "total_eur": total_eur,
                    "total_czk": total_czk,
                    "avg_rating": avg_rating,
                    "value_score": round(value, 4),
                })

    combos.sort(key=lambda x: -x["value_score"])
    return combos[:25]


def _hotel_block(h: dict, idx: int) -> list[str]:
    bonus_str = f" | +{h['bonus']} bonus" if h.get("bonus") else ""
    lines = [
        f"{idx}. **{h['name']}**",
        f"   📍 {h.get('_dest', '')} {('– ' + h['location']) if h.get('location') else ''}",
        f"   ⭐ {h['rating']} | 💰 {h['price_per_night_czk']} Kč/noc "
        f"(~{h['price_per_night_eur']} EUR) | 🍽 {h['meal']}{bonus_str}",
    ]
    if h.get("url"):
        lines.append(f"   🔗 {h['url']}")
    return lines


def format_output(hotels_1: list, hotels_2: list, combos: list) -> str:
    lines = [
        "# Výsledky hledání ubytování na Sardinii",
        f"Termín: {CHECKIN_TOTAL} – {CHECKOUT_TOTAL} ({TOTAL_NIGHTS} nocí) | "
        f"{ADULTS} dospělí + {len(CHILDREN)} dítě ({CHILDREN[0]} rok)",
        f"Max. cena: {MAX_PRICE_PER_NIGHT_CZK} Kč/noc | Min. hodnocení: {MIN_RATING}",
        f"Kurz: {CZK_TO_EUR} Kč/EUR",
        "",
        "---",
        "",
    ]

    # --- Výpis nalezených ubytování ---
    lines.append(f"## Agriturismo / farmy na jihu ({len(hotels_1)} nalezeno)")
    if hotels_1:
        for i, h in enumerate(hotels_1[:15], 1):
            lines.extend(_hotel_block(h, i))
            lines.append("")
    else:
        lines.append("_Žádné ubytování nesplňuje kritéria._")
        lines.append("")

    lines.append(f"## B&B / penziony na severozápadě ({len(hotels_2)} nalezeno)")
    if hotels_2:
        for i, h in enumerate(hotels_2[:15], 1):
            lines.extend(_hotel_block(h, i))
            lines.append("")
    else:
        lines.append("_Žádné ubytování nesplňuje kritéria._")
        lines.append("")

    lines += ["---", "", "## TOP kombinace (seřazeno podle poměru cena/hodnocení)", ""]

    if not combos:
        lines.append("_Nepodařilo se sestavit žádnou kombinaci._")
    else:
        for i, c in enumerate(combos[:15], 1):
            h1, h2 = c["hotel_1"], c["hotel_2"]
            lines.append(
                f"### Kombinace {i} | {c['split']} nocí | "
                f"Celkem ~{c['total_czk']:,} Kč (~{c['total_eur']} EUR) | "
                f"⭐ průměr {c['avg_rating']}"
            )
            lines.append(
                f"**Farma jih** – {h1['name']} | "
                f"{h1['checkin']} → {h1['checkout']} ({h1['nights']} nocí) | "
                f"⭐{h1['rating']} | {h1['price_per_night_czk']} Kč/noc | "
                f"🍽 {h1['meal']} | Celkem {h1['subtotal_czk']:,} Kč"
            )
            if h1.get("url"):
                lines.append(f"🔗 {h1['url']}")
            lines.append(
                f"**Severozápad** – {h2['name']} | "
                f"{h2['checkin']} → {h2['checkout']} ({h2['nights']} nocí) | "
                f"⭐{h2['rating']} | {h2['price_per_night_czk']} Kč/noc | "
                f"🍽 {h2['meal']} | Celkem {h2['subtotal_czk']:,} Kč"
            )
            if h2.get("url"):
                lines.append(f"🔗 {h2['url']}")
            lines.append("")

    return "\n".join(lines)


def main():
    if not API_KEY or API_KEY == "your_api_key_here":
        print("CHYBA: Nastav BRIGHTDATA_API_KEY v souboru .env")
        return
    if not DATASET_ID or DATASET_ID == "your_dataset_id_here":
        print("CHYBA: Nastav BRIGHTDATA_DATASET_ID v souboru .env")
        return

    print("=" * 60)
    print("Sardinský scraper — Bright Data / Booking.com")
    print(f"Termín: {CHECKIN_TOTAL} – {CHECKOUT_TOTAL} ({TOTAL_NIGHTS} nocí)")
    print(f"Max cena: {MAX_PRICE_PER_NIGHT_CZK} Kč/noc | Min hodnocení: {MIN_RATING}")
    print("POUZE vyhledávání — žádná rezervace se neprovádí.")
    print("=" * 60)
    print()

    print(">>> Hledám agriturismo / farmy na jihu...")
    hotels_1 = search_profile(STAY_1)
    print(f"    Celkem nalezeno: {len(hotels_1)}")
    print()

    print(">>> Hledám B&B / penziony na severozápadě...")
    hotels_2 = search_profile(STAY_2)
    print(f"    Celkem nalezeno: {len(hotels_2)}")
    print()

    print(">>> Sestavuji kombinace...")
    combos = build_combinations(hotels_1, hotels_2)
    print(f"    TOP kombinací: {len(combos)}")
    print()

    output = format_output(hotels_1, hotels_2, combos)

    out_file = "vysledky_sardinie.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Výsledky uloženy do: {out_file}")
    print()
    print(output)


if __name__ == "__main__":
    main()

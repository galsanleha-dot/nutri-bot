import aiohttp
from typing import Optional


async def search_food(query: str) -> list[dict]:
    """Search food products via OpenFoodFacts API"""
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "fields": "product_name,nutriments,serving_size,brands"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return parse_products(data.get("products", []))
    return []


def parse_products(products: list) -> list[dict]:
    result = []
    for p in products:
        nutriments = p.get("nutriments", {})
        cal = nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g", 0)
        protein = nutriments.get("proteins_100g", 0)
        fat = nutriments.get("fat_100g", 0)
        carbs = nutriments.get("carbohydrates_100g", 0)

        if not cal:
            continue

        name = p.get("product_name", "").strip()
        brand = p.get("brands", "").strip()
        if brand and brand not in name:
            name = f"{name} ({brand})" if name else brand

        if name:
            result.append({
                "name": name[:60],
                "calories_per_100g": round(float(cal), 1),
                "protein_per_100g": round(float(protein), 1),
                "fat_per_100g": round(float(fat), 1),
                "carbs_per_100g": round(float(carbs), 1),
            })
    return result[:5]


# Fallback: small local database of common Russian foods (per 100g)
COMMON_FOODS = {
    "гречка": {"calories": 343, "protein": 12.6, "fat": 3.3, "carbs": 62.1},
    "овсянка": {"calories": 352, "protein": 11.9, "fat": 7.2, "carbs": 61.8},
    "рис": {"calories": 344, "protein": 6.7, "fat": 0.7, "carbs": 78.9},
    "куриная грудка": {"calories": 113, "protein": 23.6, "fat": 1.9, "carbs": 0.4},
    "яйцо": {"calories": 157, "protein": 12.7, "fat": 11.5, "carbs": 0.7},
    "творог 5%": {"calories": 121, "protein": 17.2, "fat": 5.0, "carbs": 1.8},
    "молоко": {"calories": 60, "protein": 3.2, "fat": 3.6, "carbs": 4.7},
    "хлеб": {"calories": 233, "protein": 7.9, "fat": 3.2, "carbs": 43.9},
    "картошка": {"calories": 77, "protein": 2.0, "fat": 0.4, "carbs": 16.3},
    "банан": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 22.8},
    "яблоко": {"calories": 47, "protein": 0.4, "fat": 0.4, "carbs": 9.8},
    "говядина": {"calories": 218, "protein": 26.0, "fat": 12.5, "carbs": 0.0},
    "лосось": {"calories": 208, "protein": 20.0, "fat": 13.4, "carbs": 0.0},
    "творог 0%": {"calories": 79, "protein": 18.0, "fat": 0.5, "carbs": 1.8},
    "греческий йогурт": {"calories": 66, "protein": 11.0, "fat": 0.4, "carbs": 3.6},
}


def search_local(query: str) -> Optional[dict]:
    query = query.lower().strip()
    for key, data in COMMON_FOODS.items():
        if query in key or key in query:
            return {"name": key, **data}
    return None

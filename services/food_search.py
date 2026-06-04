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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_products(data.get("products", []))
    except Exception:
        pass
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


COMMON_FOODS = {
    # Крупы и каши
    "гречка": {"calories": 343, "protein": 12.6, "fat": 3.3, "carbs": 62.1},
    "гречневая каша": {"calories": 132, "protein": 4.5, "fat": 2.3, "carbs": 25.0},
    "овсянка": {"calories": 352, "protein": 11.9, "fat": 7.2, "carbs": 61.8},
    "овсяная каша": {"calories": 88, "protein": 3.2, "fat": 1.8, "carbs": 15.0},
    "рис": {"calories": 344, "protein": 6.7, "fat": 0.7, "carbs": 78.9},
    "рисовая каша": {"calories": 97, "protein": 2.4, "fat": 0.4, "carbs": 21.0},
    "перловка": {"calories": 320, "protein": 9.3, "fat": 1.1, "carbs": 66.9},
    "пшённая каша": {"calories": 90, "protein": 3.0, "fat": 1.1, "carbs": 17.0},
    "манная каша": {"calories": 98, "protein": 3.2, "fat": 1.2, "carbs": 18.6},
    "геркулес": {"calories": 352, "protein": 11.9, "fat": 7.2, "carbs": 61.8},

    # Мясо и птица
    "куриная грудка": {"calories": 113, "protein": 23.6, "fat": 1.9, "carbs": 0.4},
    "курица": {"calories": 165, "protein": 20.0, "fat": 9.0, "carbs": 0.0},
    "куриное бедро": {"calories": 185, "protein": 19.0, "fat": 12.0, "carbs": 0.0},
    "говядина": {"calories": 218, "protein": 26.0, "fat": 12.5, "carbs": 0.0},
    "свинина": {"calories": 263, "protein": 16.9, "fat": 21.7, "carbs": 0.0},
    "индейка": {"calories": 117, "protein": 19.2, "fat": 4.1, "carbs": 0.0},
    "котлета": {"calories": 220, "protein": 14.0, "fat": 15.0, "carbs": 8.0},
    "сосиска": {"calories": 256, "protein": 10.1, "fat": 23.0, "carbs": 1.6},
    "колбаса": {"calories": 301, "protein": 11.4, "fat": 28.0, "carbs": 1.5},
    "пельмени": {"calories": 233, "protein": 11.9, "fat": 9.7, "carbs": 25.8},
    "вареники": {"calories": 190, "protein": 6.8, "fat": 3.7, "carbs": 33.5},

    # Рыба
    "лосось": {"calories": 208, "protein": 20.0, "fat": 13.4, "carbs": 0.0},
    "скумбрия": {"calories": 191, "protein": 18.0, "fat": 13.2, "carbs": 0.0},
    "треска": {"calories": 78, "protein": 17.5, "fat": 0.6, "carbs": 0.0},
    "тунец": {"calories": 96, "protein": 23.0, "fat": 1.0, "carbs": 0.0},
    "сельдь": {"calories": 248, "protein": 17.7, "fat": 19.5, "carbs": 0.0},
    "минтай": {"calories": 72, "protein": 16.1, "fat": 0.9, "carbs": 0.0},

    # Молочные продукты
    "яйцо": {"calories": 157, "protein": 12.7, "fat": 11.5, "carbs": 0.7},
    "творог 5%": {"calories": 121, "protein": 17.2, "fat": 5.0, "carbs": 1.8},
    "творог 0%": {"calories": 79, "protein": 18.0, "fat": 0.5, "carbs": 1.8},
    "творог 9%": {"calories": 159, "protein": 16.7, "fat": 9.0, "carbs": 2.0},
    "молоко": {"calories": 60, "protein": 3.2, "fat": 3.6, "carbs": 4.7},
    "кефир": {"calories": 51, "protein": 3.4, "fat": 2.5, "carbs": 4.0},
    "сметана": {"calories": 206, "protein": 2.8, "fat": 20.0, "carbs": 3.2},
    "сыр": {"calories": 355, "protein": 25.0, "fat": 27.5, "carbs": 0.0},
    "греческий йогурт": {"calories": 66, "protein": 11.0, "fat": 0.4, "carbs": 3.6},
    "йогурт": {"calories": 68, "protein": 5.0, "fat": 3.2, "carbs": 3.5},
    "масло сливочное": {"calories": 748, "protein": 0.8, "fat": 82.5, "carbs": 0.8},

    # Хлеб и выпечка
    "хлеб белый": {"calories": 233, "protein": 7.9, "fat": 3.2, "carbs": 43.9},
    "хлеб чёрный": {"calories": 165, "protein": 6.7, "fat": 1.2, "carbs": 34.2},
    "хлеб": {"calories": 233, "protein": 7.9, "fat": 3.2, "carbs": 43.9},
    "батон": {"calories": 262, "protein": 8.2, "fat": 3.3, "carbs": 51.9},
    "макароны": {"calories": 338, "protein": 10.4, "fat": 1.1, "carbs": 69.7},
    "спагетти": {"calories": 338, "protein": 10.4, "fat": 1.1, "carbs": 69.7},
    "блины": {"calories": 206, "protein": 6.1, "fat": 8.2, "carbs": 26.0},

    # Овощи
    "картошка": {"calories": 77, "protein": 2.0, "fat": 0.4, "carbs": 16.3},
    "картофельное пюре": {"calories": 90, "protein": 2.5, "fat": 3.3, "carbs": 14.4},
    "капуста": {"calories": 27, "protein": 1.8, "fat": 0.1, "carbs": 4.7},
    "морковь": {"calories": 35, "protein": 1.3, "fat": 0.1, "carbs": 6.9},
    "огурец": {"calories": 14, "protein": 0.8, "fat": 0.1, "carbs": 2.5},
    "помидор": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.7},
    "лук": {"calories": 41, "protein": 1.4, "fat": 0.2, "carbs": 8.2},
    "свёкла": {"calories": 43, "protein": 1.5, "fat": 0.1, "carbs": 8.8},
    "брокколи": {"calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 6.6},

    # Фрукты
    "банан": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 22.8},
    "яблоко": {"calories": 47, "protein": 0.4, "fat": 0.4, "carbs": 9.8},
    "апельсин": {"calories": 43, "protein": 0.9, "fat": 0.2, "carbs": 8.1},
    "виноград": {"calories": 69, "protein": 0.6, "fat": 0.2, "carbs": 15.4},
    "арбуз": {"calories": 30, "protein": 0.6, "fat": 0.1, "carbs": 7.6},

    # Готовые блюда
    "борщ": {"calories": 50, "protein": 2.5, "fat": 2.0, "carbs": 5.5},
    "щи": {"calories": 36, "protein": 2.2, "fat": 1.5, "carbs": 3.8},
    "суп": {"calories": 45, "protein": 2.5, "fat": 1.8, "carbs": 5.0},
    "солянка": {"calories": 68, "protein": 4.5, "fat": 3.5, "carbs": 4.8},
    "оливье": {"calories": 198, "protein": 5.9, "fat": 15.3, "carbs": 10.5},
    "винегрет": {"calories": 110, "protein": 2.5, "fat": 5.5, "carbs": 14.0},
    "карбонара": {"calories": 290, "protein": 12.0, "fat": 14.0, "carbs": 28.0},
    "паста": {"calories": 270, "protein": 10.0, "fat": 10.0, "carbs": 35.0},
    "пицца": {"calories": 270, "protein": 11.0, "fat": 10.0, "carbs": 33.0},
    "роллы": {"calories": 175, "protein": 7.5, "fat": 5.5, "carbs": 24.0},
    "суши": {"calories": 150, "protein": 8.0, "fat": 3.5, "carbs": 22.0},
    "шаурма": {"calories": 225, "protein": 12.0, "fat": 11.0, "carbs": 20.0},
    "бургер": {"calories": 295, "protein": 14.0, "fat": 14.0, "carbs": 27.0},
    "омлет": {"calories": 154, "protein": 9.5, "fat": 12.0, "carbs": 1.5},
    "яичница": {"calories": 192, "protein": 13.0, "fat": 15.0, "carbs": 1.0},
    "плов": {"calories": 210, "protein": 9.0, "fat": 8.0, "carbs": 26.0},
    "голубцы": {"calories": 130, "protein": 8.0, "fat": 6.5, "carbs": 10.0},

    # Снеки и сладкое
    "шоколад": {"calories": 546, "protein": 6.9, "fat": 35.7, "carbs": 49.5},
    "печенье": {"calories": 417, "protein": 7.5, "fat": 15.4, "carbs": 63.0},
    "торт": {"calories": 400, "protein": 5.5, "fat": 22.0, "carbs": 48.0},
    "мороженое": {"calories": 201, "protein": 3.5, "fat": 10.0, "carbs": 25.0},
    "орехи": {"calories": 607, "protein": 15.0, "fat": 60.0, "carbs": 11.0},
    "мёд": {"calories": 329, "protein": 0.8, "fat": 0.0, "carbs": 81.5},

    # Напитки
    "кофе": {"calories": 2, "protein": 0.3, "fat": 0.0, "carbs": 0.0},
    "чай": {"calories": 1, "protein": 0.0, "fat": 0.0, "carbs": 0.3},
    "сок": {"calories": 45, "protein": 0.5, "fat": 0.0, "carbs": 10.0},
    "молочный коктейль": {"calories": 112, "protein": 3.5, "fat": 3.0, "carbs": 17.5},
}


def search_local(query: str) -> Optional[dict]:
    query = query.lower().strip()
    # Точное совпадение
    if query in COMMON_FOODS:
        data = COMMON_FOODS[query]
        return {"name": query, **data}
    # Частичное совпадение
    for key, data in COMMON_FOODS.items():
        if query in key or key in query:
            return {"name": key, **data}
    return None

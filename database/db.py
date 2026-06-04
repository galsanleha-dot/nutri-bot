import aiohttp
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


async def get_user(user_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{SUPABASE_URL}/rest/v1/nutri_users",
            headers=HEADERS,
            params={"user_id": f"eq.{user_id}", "limit": "1"}
        ) as resp:
            data = await resp.json()
            return data[0] if data else None


async def save_user(user_id: int, username: str, weight: float, height: float,
                    age: int, gender: str, goal: str, activity: str):
    daily_calories = calculate_calories(weight, height, age, gender, goal, activity)
    payload = {
        "user_id": user_id,
        "username": username,
        "weight": weight,
        "height": height,
        "age": age,
        "gender": gender,
        "goal": goal,
        "activity": activity,
        "daily_calories": daily_calories
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SUPABASE_URL}/rest/v1/nutri_users",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload
        ) as resp:
            await resp.json()
    return daily_calories


async def log_food(user_id: int, date: str, meal_type: str, food_name: str,
                   weight_g: float, calories: float, protein: float, fat: float, carbs: float):
    payload = {
        "user_id": user_id,
        "date": date,
        "meal_type": meal_type,
        "food_name": food_name,
        "weight_g": weight_g,
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SUPABASE_URL}/rest/v1/nutri_food_log",
            headers=HEADERS,
            json=payload
        ) as resp:
            await resp.json()


async def get_daily_log(user_id: int, date: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{SUPABASE_URL}/rest/v1/nutri_food_log",
            headers=HEADERS,
            params={"user_id": f"eq.{user_id}", "date": f"eq.{date}", "order": "logged_at"}
        ) as resp:
            return await resp.json()


async def get_daily_totals(user_id: int, date: str):
    logs = await get_daily_log(user_id, date)
    total_calories = sum(r.get("calories", 0) for r in logs)
    total_protein = sum(r.get("protein", 0) for r in logs)
    total_fat = sum(r.get("fat", 0) for r in logs)
    total_carbs = sum(r.get("carbs", 0) for r in logs)
    return (total_calories, total_protein, total_fat, total_carbs)


def calculate_calories(weight: float, height: float, age: int, gender: str,
                        goal: str, activity: str) -> float:
    """Mifflin-St Jeor formula"""
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    tdee = bmr * activity_factors.get(activity, 1.55)

    goal_adjustments = {
        "lose": -500,
        "maintain": 0,
        "gain": 300
    }
    return round(tdee + goal_adjustments.get(goal, 0))

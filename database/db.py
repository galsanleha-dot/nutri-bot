import asyncpg
import os
from config import DATABASE_URL


_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10, statement_cache_size=0)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                weight REAL,
                height REAL,
                age INTEGER,
                gender TEXT,
                goal TEXT,
                activity TEXT,
                daily_calories REAL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                date TEXT,
                meal_type TEXT,
                food_name TEXT,
                weight_g REAL,
                calories REAL,
                protein REAL,
                fat REAL,
                carbs REAL,
                logged_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)


async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def save_user(user_id: int, username: str, weight: float, height: float,
                    age: int, gender: str, goal: str, activity: str):
    daily_calories = calculate_calories(weight, height, age, gender, goal, activity)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, weight, height, age, gender, goal, activity, daily_calories)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT(user_id) DO UPDATE SET
                weight=EXCLUDED.weight,
                height=EXCLUDED.height,
                age=EXCLUDED.age,
                gender=EXCLUDED.gender,
                goal=EXCLUDED.goal,
                activity=EXCLUDED.activity,
                daily_calories=EXCLUDED.daily_calories
        """, user_id, username, weight, height, age, gender, goal, activity, daily_calories)
    return daily_calories


async def log_food(user_id: int, date: str, meal_type: str, food_name: str,
                   weight_g: float, calories: float, protein: float, fat: float, carbs: float):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO food_log (user_id, date, meal_type, food_name, weight_g, calories, protein, fat, carbs)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, user_id, date, meal_type, food_name, weight_g, calories, protein, fat, carbs)


async def get_daily_log(user_id: int, date: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM food_log WHERE user_id = $1 AND date = $2 ORDER BY logged_at",
            user_id, date
        )


async def get_daily_totals(user_id: int, date: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(fat), 0) as total_fat,
                COALESCE(SUM(carbs), 0) as total_carbs
            FROM food_log WHERE user_id = $1 AND date = $2
        """, user_id, date)


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

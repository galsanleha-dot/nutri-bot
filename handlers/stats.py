from aiogram import Router, types, F
from datetime import date, timedelta

from database.db import get_daily_log, get_daily_totals, get_user

router = Router()

MEAL_NAMES = {
    "breakfast": "🌅 Завтрак",
    "lunch": "☀️ Обед",
    "dinner": "🌙 Ужин",
    "snack": "🍎 Перекус"
}


@router.message(F.text == "📅 Дневник")
async def food_diary(message: types.Message):
    today = str(date.today())
    logs = await get_daily_log(message.from_user.id, today)

    if not logs:
        await message.answer("📅 Сегодня ещё ничего не записано.\n\nНажми *🍽 Добавить еду*", parse_mode="Markdown")
        return

    text = f"📅 *Дневник питания — {today}*\n\n"
    by_meal = {}
    for row in logs:
        meal = row["meal_type"]
        if meal not in by_meal:
            by_meal[meal] = []
        by_meal[meal].append(row)

    for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
        if meal_type in by_meal:
            text += f"{MEAL_NAMES[meal_type]}\n"
            for item in by_meal[meal_type]:
                text += f"  • {item['food_name']} — {item['weight_g']}г → {int(item['calories'])} ккал\n"
            text += "\n"

    totals = await get_daily_totals(message.from_user.id, today)
    user = await get_user(message.from_user.id)
    daily_norm = int(user["daily_calories"])
    remaining = daily_norm - int(totals[0])

    text += f"*Итого:* {int(totals[0])} / {daily_norm} ккал\n"
    text += f"{'✅ Осталось: ' + str(remaining) + ' ккал' if remaining > 0 else '⚠️ Превышение на ' + str(abs(remaining)) + ' ккал'}\n\n"
    text += f"Б: {round(totals[1], 1)}г | Ж: {round(totals[2], 1)}г | У: {round(totals[3], 1)}г"

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала заполни профиль")
        return

    daily_norm = int(user["daily_calories"])
    text = f"📊 *Статистика за последние 7 дней*\n\n"
    total_calories = 0
    days_with_data = 0

    for i in range(7):
        day = str(date.today() - timedelta(days=i))
        totals = await get_daily_totals(message.from_user.id, day)
        cal = int(totals[0])
        if cal > 0:
            days_with_data += 1
            total_calories += cal
            bar = "█" * min(int(cal / daily_norm * 10), 10)
            status = "✅" if cal <= daily_norm else "⚠️"
            text += f"{day}: {cal} ккал {status} {bar}\n"

    if days_with_data == 0:
        await message.answer("Пока нет данных. Начни записывать еду! 🍽")
        return

    avg = total_calories // days_with_data
    text += f"\n📈 Среднее за период: *{avg} ккал/день*\n"
    text += f"🎯 Твоя норма: *{daily_norm} ккал/день*"

    await message.answer(text, parse_mode="Markdown")

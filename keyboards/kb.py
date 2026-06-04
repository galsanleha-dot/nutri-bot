from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Добавить еду"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📅 Дневник")],
        ],
        resize_keyboard=True
    )


def goal_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📉 Похудеть", callback_data="goal_lose")],
        [InlineKeyboardButton(text="⚖️ Удержать вес", callback_data="goal_maintain")],
        [InlineKeyboardButton(text="📈 Набрать вес", callback_data="goal_gain")],
    ])


def gender_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender_female"),
        ]
    ])


def activity_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛋 Сидячий (офис, дом)", callback_data="act_sedentary")],
        [InlineKeyboardButton(text="🚶 Лёгкая активность (1-3 раза/нед)", callback_data="act_light")],
        [InlineKeyboardButton(text="🏃 Средняя активность (3-5 раз/нед)", callback_data="act_moderate")],
        [InlineKeyboardButton(text="💪 Высокая активность (6-7 раз/нед)", callback_data="act_active")],
        [InlineKeyboardButton(text="🔥 Очень высокая (2 тренировки/день)", callback_data="act_very_active")],
    ])


def meal_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌅 Завтрак", callback_data="meal_breakfast"),
            InlineKeyboardButton(text="☀️ Обед", callback_data="meal_lunch"),
        ],
        [
            InlineKeyboardButton(text="🌙 Ужин", callback_data="meal_dinner"),
            InlineKeyboardButton(text="🍎 Перекус", callback_data="meal_snack"),
        ],
    ])


def food_results_keyboard(products: list, query: str):
    buttons = []
    for i, p in enumerate(products):
        label = f"{p['name']} — {p['calories_per_100g']} ккал/100г"
        buttons.append([InlineKeyboardButton(text=label[:60], callback_data=f"food_{i}")])
    buttons.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="food_manual")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

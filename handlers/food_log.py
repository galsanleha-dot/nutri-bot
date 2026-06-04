from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date

from database.db import log_food, get_user, get_daily_totals
from services.food_search import search_food, search_local
from keyboards.kb import meal_type_keyboard, food_results_keyboard, main_menu

router = Router()


class FoodLogStates(StatesGroup):
    waiting_meal_type = State()
    waiting_food_name = State()
    waiting_food_select = State()
    waiting_weight = State()
    waiting_manual_calories = State()
    waiting_manual_protein = State()
    waiting_manual_fat = State()
    waiting_manual_carbs = State()


@router.message(F.text == "🍽 Добавить еду")
async def add_food_start(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала заполни профиль — нажми 👤 Профиль")
        return
    await message.answer("Выбери приём пищи:", reply_markup=meal_type_keyboard())
    await state.set_state(FoodLogStates.waiting_meal_type)


@router.callback_query(FoodLogStates.waiting_meal_type, F.data.startswith("meal_"))
async def select_meal_type(callback: types.CallbackQuery, state: FSMContext):
    meal = callback.data.split("_")[1]
    await state.update_data(meal_type=meal)
    await callback.message.edit_text("Введи название продукта или блюда:")
    await state.set_state(FoodLogStates.waiting_food_name)


@router.message(FoodLogStates.waiting_food_name)
async def search_food_handler(message: types.Message, state: FSMContext):
    query = message.text.strip()
    await state.update_data(query=query)
    await message.answer("🔍 Ищу...")

    local = search_local(query)
    if local:
        products = [{
            "name": local["name"],
            "calories_per_100g": local["calories"],
            "protein_per_100g": local["protein"],
            "fat_per_100g": local["fat"],
            "carbs_per_100g": local["carbs"],
        }]
    else:
        products = await search_food(query)

    if products:
        await state.update_data(products=products)
        await message.answer(
            f"Найдено {len(products)} вариантов. Выбери подходящий:",
            reply_markup=food_results_keyboard(products, query)
        )
        await state.set_state(FoodLogStates.waiting_food_select)
    else:
        await message.answer(
            "❌ Не нашёл такой продукт.\n\nВведём вручную — сколько ккал на 100г?"
        )
        await state.set_state(FoodLogStates.waiting_manual_calories)


@router.callback_query(FoodLogStates.waiting_food_select, F.data.startswith("food_"))
async def select_food(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "food_manual":
        await callback.message.edit_text("Введи калорийность на 100г:")
        await state.set_state(FoodLogStates.waiting_manual_calories)
        return

    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    product = data["products"][idx]
    await state.update_data(selected_food=product)

    await callback.message.edit_text(
        f"✅ *{product['name']}*\n"
        f"На 100г: {product['calories_per_100g']} ккал | "
        f"Б: {product['protein_per_100g']}г | "
        f"Ж: {product['fat_per_100g']}г | "
        f"У: {product['carbs_per_100g']}г\n\n"
        "Сколько грамм ты съел(а)?",
        parse_mode="Markdown"
    )
    await state.set_state(FoodLogStates.waiting_weight)


@router.message(FoodLogStates.waiting_weight)
async def get_food_weight(message: types.Message, state: FSMContext):
    try:
        weight_g = float(message.text.replace(",", "."))
        if weight_g <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи вес в граммах, например: 150")
        return

    data = await state.get_data()
    food = data["selected_food"]
    k = weight_g / 100

    calories = round(food["calories_per_100g"] * k, 1)
    protein = round(food["protein_per_100g"] * k, 1)
    fat = round(food["fat_per_100g"] * k, 1)
    carbs = round(food["carbs_per_100g"] * k, 1)

    today = str(date.today())
    await log_food(
        user_id=message.from_user.id,
        date=today,
        meal_type=data["meal_type"],
        food_name=food["name"],
        weight_g=weight_g,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs
    )

    totals = await get_daily_totals(message.from_user.id, today)
    user = await get_user(message.from_user.id)
    daily_norm = int(user["daily_calories"])

    await state.clear()
    await message.answer(
        f"✅ *Записано!*\n\n"
        f"*{food['name']}* — {weight_g}г\n"
        f"🔥 {calories} ккал | Б: {protein}г | Ж: {fat}г | У: {carbs}г\n\n"
        f"📊 *Итого за сегодня:*\n"
        f"Калории: {int(totals[0])} / {daily_norm} ккал "
        f"({'✅' if totals[0] <= daily_norm else '⚠️ Превышение'})\n"
        f"Белки: {round(totals[1], 1)}г | Жиры: {round(totals[2], 1)}г | Углеводы: {round(totals[3], 1)}г",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


@router.message(FoodLogStates.waiting_manual_calories)
async def manual_calories(message: types.Message, state: FSMContext):
    try:
        calories = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число, например: 250")
        return
    await state.update_data(manual_calories=calories)
    await message.answer("Белки на 100г (г)? Если не знаешь — введи 0:")
    await state.set_state(FoodLogStates.waiting_manual_protein)


@router.message(FoodLogStates.waiting_manual_protein)
async def manual_protein(message: types.Message, state: FSMContext):
    try:
        protein = float(message.text.replace(",", "."))
    except ValueError:
        protein = 0
    await state.update_data(manual_protein=protein)
    await message.answer("Жиры на 100г (г)? Если не знаешь — введи 0:")
    await state.set_state(FoodLogStates.waiting_manual_fat)


@router.message(FoodLogStates.waiting_manual_fat)
async def manual_fat(message: types.Message, state: FSMContext):
    try:
        fat = float(message.text.replace(",", "."))
    except ValueError:
        fat = 0
    await state.update_data(manual_fat=fat)
    await message.answer("Углеводы на 100г (г)? Если не знаешь — введи 0:")
    await state.set_state(FoodLogStates.waiting_manual_carbs)


@router.message(FoodLogStates.waiting_manual_carbs)
async def manual_carbs(message: types.Message, state: FSMContext):
    try:
        carbs = float(message.text.replace(",", "."))
    except ValueError:
        carbs = 0

    data = await state.get_data()
    await state.update_data(selected_food={
        "name": data["query"],
        "calories_per_100g": data["manual_calories"],
        "protein_per_100g": data["manual_protein"],
        "fat_per_100g": data["manual_fat"],
        "carbs_per_100g": carbs,
    })
    await message.answer("Сколько грамм ты съел(а)?")
    await state.set_state(FoodLogStates.waiting_weight)

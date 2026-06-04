from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import save_user, get_user
from keyboards.kb import main_menu, goal_keyboard, gender_keyboard, activity_keyboard

router = Router()


class ProfileStates(StatesGroup):
    waiting_weight = State()
    waiting_height = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_goal = State()
    waiting_activity = State()


@router.message(F.text == "👤 Профиль")
async def profile_menu(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user:
        await message.answer(
            f"👤 *Твой профиль*\n\n"
            f"⚖️ Вес: {user['weight']} кг\n"
            f"📏 Рост: {user['height']} см\n"
            f"🎂 Возраст: {user['age']} лет\n"
            f"🎯 Цель: {goal_text(user['goal'])}\n"
            f"🔥 Норма: *{int(user['daily_calories'])} ккал/день*\n\n"
            "Хочешь обновить данные? Введи свой вес (кг):",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Давай заполним профиль!\n\nВведи свой вес в кг (например: 75):")
    await state.set_state(ProfileStates.waiting_weight)


@router.message(ProfileStates.waiting_weight)
async def get_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        if not 30 <= weight <= 300:
            raise ValueError
        await state.update_data(weight=weight)
        await message.answer("Отлично! Теперь введи рост в см (например: 175):")
        await state.set_state(ProfileStates.waiting_height)
    except ValueError:
        await message.answer("❌ Некорректное значение. Введи вес в кг, например: 70")


@router.message(ProfileStates.waiting_height)
async def get_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text.replace(",", "."))
        if not 100 <= height <= 250:
            raise ValueError
        await state.update_data(height=height)
        await message.answer("Введи свой возраст (лет):")
        await state.set_state(ProfileStates.waiting_age)
    except ValueError:
        await message.answer("❌ Некорректное значение. Введи рост в см, например: 175")


@router.message(ProfileStates.waiting_age)
async def get_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if not 10 <= age <= 100:
            raise ValueError
        await state.update_data(age=age)
        await message.answer("Укажи пол:", reply_markup=gender_keyboard())
        await state.set_state(ProfileStates.waiting_gender)
    except ValueError:
        await message.answer("❌ Некорректное значение. Введи возраст числом, например: 25")


@router.callback_query(ProfileStates.waiting_gender, F.data.startswith("gender_"))
async def get_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_text("Какая у тебя цель?", reply_markup=goal_keyboard())
    await state.set_state(ProfileStates.waiting_goal)


@router.callback_query(ProfileStates.waiting_goal, F.data.startswith("goal_"))
async def get_goal(callback: types.CallbackQuery, state: FSMContext):
    goal = callback.data.split("_")[1]
    await state.update_data(goal=goal)
    await callback.message.edit_text("Уровень физической активности:", reply_markup=activity_keyboard())
    await state.set_state(ProfileStates.waiting_activity)


@router.callback_query(ProfileStates.waiting_activity, F.data.startswith("act_"))
async def get_activity(callback: types.CallbackQuery, state: FSMContext):
    activity = callback.data[4:]  # remove "act_"
    data = await state.get_data()

    daily_calories = await save_user(
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        gender=data["gender"],
        goal=data["goal"],
        activity=activity
    )

    await state.clear()
    await callback.message.edit_text(
        f"✅ *Профиль сохранён!*\n\n"
        f"🔥 Твоя дневная норма калорий: *{int(daily_calories)} ккал*\n\n"
        "Теперь можешь записывать еду и следить за питанием! 💪",
        parse_mode="Markdown"
    )
    await callback.message.answer("Главное меню:", reply_markup=main_menu())


def goal_text(goal: str) -> str:
    return {"lose": "📉 Похудеть", "maintain": "⚖️ Удержать вес", "gain": "📈 Набрать"}.get(goal, goal)

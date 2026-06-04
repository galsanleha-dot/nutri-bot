from aiogram import Router, types
from aiogram.filters import CommandStart

from database.db import get_user
from keyboards.kb import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"👋 С возвращением, {message.from_user.first_name}!\n\n"
            f"Твоя дневная норма: *{int(user['daily_calories'])} ккал*\n\n"
            "Что будем делать?",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я бот-нутрициолог 🥗\n\n"
            "Помогу считать калории, белки, жиры и углеводы, "
            "и подберу твою дневную норму питания.\n\n"
            "Для начала давай заполним твой профиль. Нажми *👤 Профиль*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

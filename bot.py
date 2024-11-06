import asyncio
import logging
import os
import re
import sys

from aiogram import Bot, Dispatcher, types, filters
from aiogram.enums import ParseMode
from cachetools import TTLCache

from asilo_getter import get_asylum_options, get_full_information

token = os.getenv("ASILO_BOT")
dp = Dispatcher()

cache = TTLCache(maxsize=262144, ttl=60)

text = """
Бот позволяет найти тебе нужный провинциальный отдел полиции,\nчтобы узнать какой вид получения ситы там есть.\n
Для начала работы нажми на кнопку 'Список провинций'
"""


async def get_cached_data():
    cached_data = cache.get("cached_data")
    if cached_data is None:
        options = get_asylum_options(test=False)
        raw_data = get_full_information(options=options)
        cache["cached_data"] = raw_data
        return raw_data
    else:
        return cached_data


def create_lvl1_kb():
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="Список провинций", callback_data="provinces"),
            # types.InlineKeyboardButton(text="Задонатить на чай", pay=True),
        ]]
    )
    return inline_kb


def create_lvl2_kb(provinces: list) -> list[list[types.InlineKeyboardButton]]:
    chunk_size = 3
    inline_kb = []

    provinces = sorted(provinces)

    for i in range(0, len(provinces), chunk_size):
        tmp = []
        for p in provinces[i:i + chunk_size]:
            tmp.append(types.InlineKeyboardButton(text=p, callback_data=f"action_{p}"))

        inline_kb.append(tmp)

    return inline_kb


@dp.message(filters.CommandStart())
async def command_start_handler(message: types.Message) -> None:
    await message.answer(
        text=text,
        reply_markup=create_lvl1_kb(),
    )


@dp.callback_query(lambda msg: isinstance(msg, types.CallbackQuery))
async def list_of_provinces(callback_query: types.CallbackQuery):
    match_ = re.match(r'^action_(\w+|\w+\s\w+)$', callback_query.data)

    kb = None

    if "provinces" == callback_query.data or callback_query.data == "back1":
        raw_data = await get_cached_data()
        provinces = [data["province"] for data in raw_data]
        inline_kb = create_lvl2_kb(provinces=provinces)
        inline_kb.append([types.InlineKeyboardButton(text="<- Назад", callback_data="back")])
        kb = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)

        await callback_query.message.edit_text(
            text="Список провинций",
            reply_markup=kb,
        )

    elif "back" == callback_query.data:
        await callback_query.message.edit_text(
            text=text,
            reply_markup=create_lvl1_kb(),
        )

    elif match_:
        province_name = match_.group(1)
        raw_data = await get_cached_data()

        for item in raw_data:
            if item["province"] == province_name:
                markup_message = f"Провинция: <b>{province_name}</b>\n"

                for key, value in item["options"].items():
                    if key == "internet":
                        markup_item = f"<b>{key.capitalize().replace('_', ' ')}:</b> <a href='{value}'>Открыть сайт extranjeria</a>\n"
                    elif key == "correo_electrónico":
                        markup_item = f"<b>{key.capitalize().replace('_', ' ')}:</b> <a href='mailto:{value}'>{value}</a>\n"
                    else:
                        markup_item = f"<b>{key.capitalize().replace('_', ' ')}:</b> {value}\n"

                    markup_message += markup_item

                await callback_query.message.edit_text(
                    text=markup_message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="<- Назад", callback_data="back1")]
                    ])
                )

# @dp.pre_checkout_query()
# async def pre_checkout_query_handler(pre_checkout: types.PreCheckoutQuery):
#     await dp.pre_checkout_query(pre_checkout.id, ok=True)


async def main() -> None:
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

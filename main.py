import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import BasicAuth
import database as db
import utils

# логи для pycharm
logging.basicConfig(level=logging.INFO)

# Конфиг
API_TOKEN = ""
PROXY_URL = "http://193.58.109.9:8000"
PROXY_AUTH = BasicAuth("FurzTb", "Zn1oQT")

# класс для главного меню (состояния вкладок)
class SearchSteps(StatesGroup):
    brand = State()
    model = State()
    color = State()
    price = State()

dp = Dispatcher()


# главный интерфейс

# ui вывода производителей
async def ui_show_brands(message: types.Message, state: FSMContext, edit=False):
    brands = db.get_brands("brand")
    builder = InlineKeyboardBuilder()
    for b in brands:
        builder.add(types.InlineKeyboardButton(text=b, callback_data=f"set_brand:{b}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Меню", callback_data="nav_menu"))

    text = "Производитель:"
    if edit:
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(SearchSteps.brand)

# ui вывода моделей
async def ui_show_models(message: types.Message, state: FSMContext, brand: str):
    models = db.get_brands("model", {"brand": brand})
    builder = InlineKeyboardBuilder()
    for m in models:
        builder.add(types.InlineKeyboardButton(text=m, callback_data=f"set_model:{m}"))
    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_brand"),
        types.InlineKeyboardButton(text="Меню", callback_data="nav_menu")
    )

    await message.edit_text(f"Производитель: **{brand}**\n Модель:", parse_mode="Markdown", reply_markup=builder.as_markup())
    await state.set_state(SearchSteps.model)


# Команды боту
## старт
@dp.message(F.text == "/start")
@dp.message(F.text == "Начать!")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await ui_show_brands(message, state)

## меню
@dp.callback_query(F.data == "nav_menu")
async def nav_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()  # Удаляем интерфейс поиска
    await callback.message.answer("Меню", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Начать")]], resize_keyboard=True))

## назад к производителю
@dp.callback_query(F.data == "back_to_brand")
async def nav_back_brand(callback: types.CallbackQuery, state: FSMContext):
    await ui_show_brands(callback.message, state, edit=True)

## выбор производителя
@dp.callback_query(SearchSteps.brand, F.data.startswith("set_brand:"))
async def select_brand(callback: types.CallbackQuery, state: FSMContext):
    brand = callback.data.split(":")[1]
    await state.update_data(brand=brand)
    await ui_show_models(callback.message, state, brand)

## выбор модели
@dp.callback_query(SearchSteps.model, F.data.startswith("set_model:"))
async def select_model(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.split(":")[1]
    await state.update_data(model=model)
    data = await state.get_data()

    # удаляем сообщение с моделями, так как дальше пойдут фото (их нельзя впихнуть в edit_text)
    await callback.message.delete()

    colors = db.get_colors_with_hex(data['brand'], model)
    await callback.message.answer(f"Модель: **{model}**\nЦвет:", parse_mode="Markdown")

    for c in colors:
        photo_path = utils.create_color_preview(c['hex'], c['name'])
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text=f"Выбрать {c['name']}", callback_data=f"set_color:{c['name']}"))
        await callback.message.answer_photo(FSInputFile(photo_path), caption=f"Цвет: {c['name']}", reply_markup=builder.as_markup())

    # Кнопка назад в отдельном сообщении
    nav = InlineKeyboardBuilder()
    nav.row(types.InlineKeyboardButton(text="⬅ Назад",
                                       callback_data="back_to_brand"))  # Назад к брендам, чтобы перерисовать всё
    await callback.message.answer("Это все доступные цвета", reply_markup=nav.as_markup())
    await state.set_state(SearchSteps.color)

## выбор цвета
@dp.callback_query(SearchSteps.color, F.data.startswith("set_color:"))
async def select_color(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    await state.update_data(color=color)

    # "Испаряем" сообщение с фото и вопросом
    await callback.message.delete()

    builder = InlineKeyboardBuilder()
    for p in [50000, 100000, 150000, 250000]:
        builder.add(types.InlineKeyboardButton(text=f"До {p} руб.", callback_data=f"set_price:{p}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="Другая цена (своя)", callback_data="nav_custom"))
    builder.row(types.InlineKeyboardButton(text="Меню", callback_data="nav_menu"))

    await callback.message.answer(f"Цвет: **{color}**\n Стоимость:", parse_mode="Markdown", reply_markup=builder.as_markup())
    await state.set_state(SearchSteps.price)

## выбор цены
@dp.callback_query(SearchSteps.price, F.data.startswith("set_price:"))
async def price_button(callback: types.CallbackQuery, state: FSMContext):
    price = int(callback.data.split(":")[1])
    await callback.message.delete()
    await process_search(callback.message, state, price)


@dp.message(SearchSteps.price)
async def price_text(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        try:
            await message.delete()
        except:
            pass
        await process_search(message, state, int(message.text))

## Главный поиск
async def process_search(message, state, price):
    data = await state.get_data()
    results = db.final_search(data['brand'], data['model'], data['color'], price)

    header = f"Результаты поиска ({data['brand']} {data['model']}, до {price} руб.):"
    await message.answer(header)

    if not results:
        await message.answer("К сожалению, ничего не нашлось (")
    else:
        for r in results:
            await message.answer(f"Производитель: {r['brand']} \nМодель: {r['model']}\nЦена: {r['price']} руб.\n [Ссылка]({r['url']})", parse_mode="Markdown")

    await state.clear()
    await message.answer("Поиск завершен", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Начать")]],resize_keyboard=True))


async def main():
    db.init_db()
    session = AiohttpSession(proxy=(PROXY_URL, PROXY_AUTH))
    bot = Bot(token=API_TOKEN, session=session)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import json
import asyncio
import os
from datetime import datetime

# Настройки
TOKEN = "7809565448:AAFsfuInMk7bjzIGQ52nZTjjFgaFzYP5AA4"
ADMIN_ID = 359505266  # Ваш ID администратора
USER_DATA_FILE = "user.json"

# Загружаем данные о пользователях из файла (если файл существует)
def load_user_data():
    if os.path.exists(USER_DATA_FILE) and os.path.getsize(USER_DATA_FILE) > 0:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохраняем данные о пользователях в файл
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

# Список каналов
CHANNELS = [
    {"name": "Канал #1", "id": "@testprikolbot123", "is_private": False},  
    {"name": "Канал #2", "link": "https://t.me/+Nan6BOsZLTs3ZmVi", "is_private": True},  
]

# Загружаем коды фильмов из JSON
with open("films.json", "r", encoding="utf-8") as f:
    FILMS = json.load(f)

# Логирование
logging.basicConfig(level=logging.INFO)

# Бот и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция проверки подписки
async def is_subscribed(user_id: int) -> bool:
    for channel in CHANNELS:
        if not channel["is_private"]:
            try:
                member = await bot.get_chat_member(channel["id"], user_id)
                if member.status in ["left", "kicked"]:
                    return False
            except Exception as e:
                logging.error(f"Ошибка проверки {channel['id']}: {e}")
                return False
    return True

# Функция создания клавиатуры подписки
def get_subscription_keyboard():
    keyboard = []
    row = []
    
    for channel in CHANNELS:
        btn_text = f"{channel['name']}"
        btn_url = channel["link"] if channel["is_private"] else f"https://t.me/{channel['id'].lstrip('@')}"
        button = InlineKeyboardButton(text=btn_text, url=btn_url)
        
        row.append(button)
        if len(row) == 2:  # Добавляем кнопки в ряд по 2
            keyboard.append(row)
            row = []
    
    if row:  # Если осталась одна кнопка (например, при 3 каналах)
        keyboard.append(row)
    
    # Добавляем кнопку "Продолжить" отдельной строкой
    keyboard.append([InlineKeyboardButton(text="Продолжить", callback_data="continue")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Команда /start
async def start(message: types.Message):
    user_data = load_user_data()
    user_id = str(message.from_user.id)

    if user_id not in user_data:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data[user_id] = {
            "id": message.from_user.id,
            "full_name": message.from_user.full_name,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "language_code": message.from_user.language_code,
            "join_date": current_datetime,
        }
        save_user_data(user_data)
        
        await bot.send_message(
				ADMIN_ID,
				f"🆕 Новый пользователь:\n"
				f"ID: {user_data[user_id]['id']}\n"
				f"full_name: {user_data[user_id]['full_name']}\n"
				f"username: @{user_data[user_id]['username']}\n"
				f"First Name: {user_data[user_id]['first_name']}\n"
				f"Last Name: {user_data[user_id]['last_name']}\n"
				f"language: {user_data[user_id]['language_code']}\n"
				f"Дата регистрации: {user_data[user_id]['join_date']}",
)

        
				
    if await is_subscribed(message.from_user.id):
        await message.answer("✅ Спасибо за подписку! Введите код фильма:")
    else:
        await message.answer(
            "✋ Чтобы продолжить пользоваться ботом, вы должны подписаться на наши каналы.\n\n"
            "_Подпишись и нажми «Продолжить»!_",
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard(),
        )

# Обработка кнопки "Продолжить"
async def button_handler(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    user_data = load_user_data()

    if await is_subscribed(callback_query.from_user.id):
        await bot.edit_message_text("✅ Спасибо за подписку! Введите код фильма:",
                                    chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id)
    else:
        await bot.answer_callback_query(callback_query.id, "⛔️ Вы не подписались, попробуйте ещё раз.", show_alert=True)

# Обработка кода фильма
async def handle_code(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return  # Просто игнорируем сообщение, если нет подписки

    film_data = FILMS.get(message.text.strip())
    if film_data:
        await message.answer(f"🎬 Название фильма: {film_data['title']}")
    else:
        await message.answer("❌ Код не найден.")

# Функция для получения следующего кода
def get_next_code():
    if FILMS:
        # Находим максимальный код и увеличиваем его на 1
        max_code = max(int(k) for k in FILMS.keys())
        return f"{max_code + 1:03d}"  # Форматируем как трёхзначный код (001, 002 и т.д.)
    else:
        return "001"  # Если словарь пуст, начинаем с 001

# Команда /addfilm (только для администратора)
async def add_film(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        next_code = get_next_code()
        await message.answer(
            f"📝 Чтобы добавить новый фильм, отправьте сообщение в формате:\n\n"
            f"`/addfilm КОД:НАЗВАНИЕ`\n\n"
            f"Пример:\n"
            f"`/addfilm {next_code}:Новый фильм`\n\n"
            f"Следующий доступный код: `{next_code}`",
            parse_mode="Markdown",
        )
    else:
        await message.answer("⛔️ Вы не администратор!")

# Обработка добавления фильма
async def add_film_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return  # Игнорируем, если это не администратор

    try:
        # Разделяем текст на код и название
        _, film_data = message.text.split(" ", 1)
        code, name = film_data.split(":", 1)

        # Проверяем, существует ли уже такой код
        if code.strip() in FILMS:
            await message.answer(f"❌ Код `{code}` уже существует. Используйте другой код.", parse_mode="Markdown")
            return

        # Добавляем фильм в словарь
        FILMS[code.strip()] = {"title": name.strip()}

        # Сохраняем обновлённый словарь в файл
        with open("films.json", "w", encoding="utf-8") as f:
            json.dump(FILMS, f, ensure_ascii=False, indent=4)

        await message.answer(f"✅ Фильм добавлен:\nКод: `{code}`\nНазвание: `{name}`", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте:\n`/addfilm КОД:НАЗВАНИЕ`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", parse_mode="Markdown")

# Регистрация обработчиков
dp.message.register(start, Command("start"))
dp.callback_query.register(button_handler)
dp.message.register(handle_code, lambda message: not message.text.startswith("/"))
dp.message.register(add_film_handler, lambda message: message.text.startswith("/addfilm ") and ":" in message.text)
dp.message.register(add_film, Command("addfilm"))

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
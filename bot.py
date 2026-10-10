import asyncio
import random
import sqlite3
import os
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

# ==================== КОНФИГ ====================
TOKEN = "8898707307:AAFNqsLvnD_VllH4GLXB5s7ixOcsH7N0L-A"
ALLOWED_USER_IDS = [5765002871, 779295626]  # первый ID — ты, второй — она
IMAGE_FOLDER = "bot_images"
FREE_COOLDOWN = 60  # секунд между бесплатными сообщениями
# Дата начала ваших отношений (с точным временем)
RELATIONSHIP_START = datetime(2025, 1, 20, 15, 3)  # 20 января 2025, 15:03

# Дата, когда вы официально стали парой
OFFICIAL_START = datetime(2025, 10, 31, 15, 3)  # 31 октября 2025, 15:03

# Файлы для пасхалки (положи рядом с bot.py)
SECRET_VOICE_FILE = "secret_voice.ogg"  # твой голос
SECRET_GIF_FILE = "sparkle.gif"         # твоя гифка

# Папка с картинками Пушин
PUSHEEN_FOLDER = "bot_images/pusheen"
PUSHEEN_STEP = 10  # сколько процентов за одно поглаживание

# ---------- КУЛИНАРНАЯ ИГРА ----------
PUSHEEN_DOLLARS_DAILY = 100  # сколько Пушин-Долларов в день
INGREDIENTS_IMG_FOLDER = "bot_images/ingredients"
DISHES_IMG_FOLDER = "bot_images/dishes"

# Основные ингредиенты (верхний ряд)
MAIN_INGREDIENTS = [
    {"id": "cream",     "name": "Сливки",     "emoji": "🥛", "price": 25},
    {"id": "ketchup",   "name": "Кетчуп",     "emoji": "🥫", "price": 15},
    {"id": "chocolate", "name": "Шоколад",    "emoji": "🍫", "price": 30},
    {"id": "egg",       "name": "Яйцо",       "emoji": "🥚", "price": 10},
    {"id": "flour",     "name": "Мука",       "emoji": "🌾", "price": 10},
    {"id": "potato",    "name": "Картофель",  "emoji": "🥔", "price": 10},
]

# Дополнительные ингредиенты (левый столбец)
EXTRA_INGREDIENTS = [
    {"id": "sugar",   "name": "Сахар",  "emoji": "🧂", "price": 10},
    {"id": "milk",    "name": "Молоко", "emoji": "🥛", "price": 10},
    {"id": "sausage", "name": "Колбаса","emoji": "🥩", "price": 25},
    {"id": "apple",   "name": "Яблоко", "emoji": "🍎", "price": 15},
    {"id": "cheese",  "name": "Сыр",    "emoji": "🧀", "price": 20},
    {"id": "bread",   "name": "Хлеб",   "emoji": "🍞", "price": 10},
]

# Все ингредиенты в одном словаре (для быстрого поиска по id)
ALL_INGREDIENTS = {ing["id"]: ing for ing in MAIN_INGREDIENTS + EXTRA_INGREDIENTS}

# Рецепты (ключ — пара id ингредиентов, отсортированная)
# quality: 3 = легендарное, 2 = хорошо, 1 = средне, 0 = плохо
RECIPES = {
    ("cream", "sugar"):     {"name": "Праздничный торт",         "quality": 3},
    ("cream", "milk"):      {"name": "Кремовое мороженое",       "quality": 3},
    ("cream", "sausage"):   {"name": "Сливочный хот-дог",        "quality": 2},
    ("cream", "apple"):     {"name": "Яблочный крем-десерт",     "quality": 2},
    ("cream", "cheese"):    {"name": "Сырный крем-суп",          "quality": 2},
    ("cream", "bread"):     {"name": "Французские тосты",        "quality": 2},
    
    ("ketchup", "sugar"):   {"name": "Острые крылышки",          "quality": 2},
    ("ketchup", "milk"):    {"name": "Томатно-сливочная паста",  "quality": 2},
    ("ketchup", "sausage"): {"name": "Загруженный хот-дог",      "quality": 2},
    ("ketchup", "apple"):   {"name": "Курица в кисло-сладком",   "quality": 2},
    ("ketchup", "cheese"):  {"name": "Домашняя пицца",           "quality": 3},
    ("ketchup", "bread"):   {"name": "Горячий сэндвич",          "quality": 2},
    
    ("chocolate", "sugar"): {"name": "Шоколадный торт",          "quality": 3},
    ("chocolate", "milk"):  {"name": "Горячий шоколад",          "quality": 2},
    ("chocolate", "sausage"):{"name": "Шоколадный барбекю",      "quality": 0},
    ("chocolate", "apple"): {"name": "Шоколадное яблоко",        "quality": 1},
    ("chocolate", "cheese"):{"name": "Шоколадно-сырная запеканка","quality": 0},
    ("chocolate", "bread"): {"name": "Шоколадные тосты",         "quality": 0},
    
    ("egg", "sugar"):       {"name": "Яичный крем-десерт",       "quality": 2},
    ("egg", "milk"):        {"name": "Молочный омлет",           "quality": 2},
    ("egg", "sausage"):     {"name": "Охотничий завтрак",        "quality": 2},
    ("egg", "apple"):       {"name": "Яблочный омлет",           "quality": 0},
    ("egg", "cheese"):      {"name": "Сырный омлет",             "quality": 2},
    ("egg", "bread"):       {"name": "Яичный сэндвич",           "quality": 2},
    
    ("flour", "sugar"):     {"name": "Пышные блинчики",          "quality": 2},
    ("flour", "milk"):      {"name": "Домашние блинчики",        "quality": 2},
    ("flour", "sausage"):   {"name": "Мясной пирог",             "quality": 2},
    ("flour", "apple"):     {"name": "Яблочный пирог",           "quality": 2},
    ("flour", "cheese"):    {"name": "Сырная выпечка",           "quality": 2},
    ("flour", "bread"):     {"name": "Хлебная запеканка",        "quality": 0},
    
    ("potato", "sugar"):    {"name": "Сладкий картофель",        "quality": 0},
    ("potato", "milk"):     {"name": "Картофельное пюре",        "quality": 2},
    ("potato", "sausage"):  {"name": "Сытное жаркое",            "quality": 1},
    ("potato", "apple"):    {"name": "Яблочный ростбиф",         "quality": 0},
    ("potato", "cheese"):   {"name": "Картофельная запеканка",   "quality": 2},
    ("potato", "bread"):    {"name": "Картофельный сэндвич",     "quality": 2},
}

# Время готовки в минутах (по качеству)
COOKING_TIME = {
    3: 5,  # легендарное — 5 мин
    2: 3,  # хорошо — 3 мин
    1: 1,  # средне — 1 мин
    0: 1,  # плохо — 1 мин
}

# Названия качеств
QUALITY_NAMES = {
    3: "⭐⭐⭐ Легендарное",
    2: "⭐⭐ Хорошо",
    1: "⭐ Средне",
    0: "⚠️ Плохо",
}

# Счастье от кормления (по качеству)
FEED_HAPPINESS = {
    3: 20,
    2: 15,
    1: 10,
    0: 0,
}
# ================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для отслеживания времени последнего бесплатного сообщения
last_free_time = {}

# Для отслеживания двойного нажатия на баланс
last_balance_click = {}

# Черновик готовки: {user_id: {"first": ing_id, "second": ing_id}}
cooking_draft = {}

# Активные таймеры готовки: {user_id: asyncio.Task}
cooking_tasks = {}

# Черновик продажи: {user_id: {"dish_name": ..., "quality": ...}}
selling_draft = {}

# Ожидание ввода цены: {user_id: True/False}
waiting_for_price = {}

# Ожидание комментария от тебя: {sale_id: {"user_id": ..., "dish_name": ..., "quality": ..., "price": ..., "decision": "accept"/"reject"}}
waiting_for_comment = {}

# ---------- КЛАВИАТУРА ----------
def get_keyboard(tokens, user_id=None):
    """Клавиатура меняется в зависимости от баланса и пользователя"""
    buttons = [
        [KeyboardButton(text="💖Милашка, нажми сюда (10 токенов)")]
    ]
    if tokens < 10:
        buttons.append([KeyboardButton(text="🔄 Бесконечные нежности (раз в минуту)")])
    buttons.append([
        KeyboardButton(text="💋 Поцеловать"),
        KeyboardButton(text="🤗 Обнять")
    ])
    
    # Пасхалка: появляется при 100+ токенов
    if tokens >= 100:
        buttons.append([KeyboardButton(text="✨ Пасхалка")])
    
    buttons.append([KeyboardButton(text="🐱 Погладить Пушин")])
    buttons.append([KeyboardButton(text="🛒 Магазин")])
    buttons.append([KeyboardButton(text="🎒 Инвентарь")])
    buttons.append([KeyboardButton(text="🍳 Готовка")])
    buttons.append([KeyboardButton(text="🍽️ Покормить Пушин")])
    buttons.append([KeyboardButton(text="💞 Сколько мы вместе?")])
    buttons.append([KeyboardButton(text="📊 Мой прогресс")])
    buttons.append([KeyboardButton(text="➕ Добавить картинку")])
    buttons.append([KeyboardButton(text="💰 Мой баланс")])
    
    # 👇 КНОПКА ТОЛЬКО ДЛЯ ТЕБЯ (первый ID в списке)
    if user_id == ALLOWED_USER_IDS[0]:
        buttons.append([KeyboardButton(text="🎁 Выдать 100 токенов Милашке")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ---------- БАЗА ДАННЫХ (токены) ----------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            tokens INTEGER DEFAULT 50,
            last_reset TEXT,
            pusheen_happiness INTEGER DEFAULT 0,
            pusheen_reset TEXT
        )
    """)
    # Безопасно добавляем новые колонки (для старых баз)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN pusheen_happiness INTEGER DEFAULT 0")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN pusheen_reset TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN pusheen_dollars INTEGER DEFAULT 100")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN pd_reset TEXT")
    except:
        pass
    
    # ---------- ИНВЕНТАРЬ ИНГРЕДИЕНТОВ ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_ingredients (
            user_id INTEGER,
            ingredient_id TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, ingredient_id)
        )
    """)
    
    # ---------- ИНВЕНТАРЬ БЛЮД ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_dishes (
            user_id INTEGER,
            dish_name TEXT,
            quality INTEGER,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, dish_name, quality)
        )
    """)
    
    # ---------- АКТИВНАЯ ГОТОВКА ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_cooking (
            user_id INTEGER PRIMARY KEY,
            dish_name TEXT,
            quality INTEGER,
            finish_time REAL
        )
    """)
    
    # ---------- ОЖИДАЮЩИЕ ПРОДАЖИ ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dish_name TEXT,
            quality INTEGER,
            price INTEGER,
            status TEXT DEFAULT 'pending'
        )
    """)
    # 👇 Таблица просмотренных фраз
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_messages (
            user_id INTEGER,
            message_hash TEXT,
            PRIMARY KEY (user_id, message_hash)
        )
    """)
    # 👇 Таблица просмотренных картинок
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_images (
            user_id INTEGER,
            image_name TEXT,
            PRIMARY KEY (user_id, image_name)
        )
    """)
    conn.commit()
    conn.close()

def check_and_reset(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT tokens, last_reset FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if row is None:
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("INSERT INTO users (user_id, tokens, last_reset) VALUES (?, 50, ?)", (user_id, today))
        conn.commit()
        conn.close()
        return 50
    
    tokens, last_reset = row
    today = datetime.now().date()
    last_date = datetime.strptime(last_reset, "%Y-%m-%d").date()
    
    if today > last_date:
        cur.execute("UPDATE users SET tokens = 50, last_reset = ? WHERE user_id = ?", (today.strftime("%Y-%m-%d"), user_id))
        conn.commit()
        conn.close()
        return 50
    
    conn.close()
    return tokens

def spend_tokens(user_id, amount):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET tokens = tokens - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_tokens(user_id, new_tokens):
    """Обновляет количество токенов у пользователя"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET tokens = ? WHERE user_id = ?", (new_tokens, user_id))
    conn.commit()
    conn.close()

# ---------- ЗАЩИТА: проверка доступа ----------
def is_allowed(user_id):
    return user_id in ALLOWED_USER_IDS

# ---------- ПУШИН ----------
# ---------- МАГАЗИН ----------
def get_ingredient_image_path(ingredient_id):
    """Возвращает путь к картинке ингредиента"""
    for ext in ("png", "jpg", "jpeg"):
        path = os.path.join(INGREDIENTS_IMG_FOLDER, f"{ingredient_id}.{ext}")
        if os.path.exists(path):
            return path
    return None

def get_dish_image_path(dish_name):
    """Возвращает путь к картинке блюда по названию (транслит)"""
    # Карта: русское название → имя файла
    dish_files = {
        "Праздничный торт": "holiday_cake",
        "Кремовое мороженое": "cream_icecream",
        "Домашняя пицца": "homemade_pizza",
        "Шоколадный торт": "chocolate_cake",
        "Сливочный хот-дог": "creamy_hotdog",
        "Яблочный крем-десерт": "apple_cream_dessert",
        "Сырный крем-суп": "cheese_cream_soup",
        "Французские тосты": "french_toast",
        "Острые крылышки": "spicy_wings",
        "Томатно-сливочная паста": "tomato_cream_pasta",
        "Загруженный хот-дог": "loaded_hotdog",
        "Курица в кисло-сладком": "sweet_sour_chicken",
        "Горячий сэндвич": "hot_sandwich",
        "Горячий шоколад": "hot_chocolate",
        "Яичный крем-десерт": "egg_cream_dessert",
        "Молочный омлет": "milk_omelette",
        "Охотничий завтрак": "hunter_breakfast",
        "Сырный омлет": "cheese_omelette",
        "Яичный сэндвич": "egg_sandwich",
        "Пышные блинчики": "fluffy_pancakes",
        "Домашние блинчики": "homemade_pancakes",
        "Мясной пирог": "meat_pie",
        "Яблочный пирог": "apple_pie",
        "Сырная выпечка": "cheese_pastry",
        "Картофельное пюре": "mashed_potato",
        "Картофельная запеканка": "potato_casserole",
        "Картофельный сэндвич": "potato_sandwich",
        "Шоколадное яблоко": "chocolate_apple",
        "Сытное жаркое": "hearty_stew",
        "Шоколадный барбекю": "chocolate_bbq",
        "Шоколадно-сырная запеканка": "chocolate_cheese_casserole",
        "Шоколадные тосты": "chocolate_toast",
        "Яблочный омлет": "apple_omelette",
        "Хлебная запеканка": "bread_casserole",
        "Сладкий картофель": "sweet_potato",
        "Яблочный роstбиф": "apple_roastbeef",
    }
    filename = dish_files.get(dish_name)
    if not filename:
        return None
    for ext in ("png", "jpg", "jpeg"):
        path = os.path.join(DISHES_IMG_FOLDER, f"{filename}.{ext}")
        if os.path.exists(path):
            return path
    return None

def build_shop_carousel(category, index, user_id):
    """Строит инлайн-клавиатуру для карусели магазина.
    category: 'main' или 'extra'
    index: текущий индекс ингредиента
    """
    ingredients = MAIN_INGREDIENTS if category == "main" else EXTRA_INGREDIENTS
    total = len(ingredients)
    index = index % total  # зацикливаем
    ing = ingredients[index]
    
    # Получаем остаток у пользователя
    inv = get_ingredients(user_id)
    owned = inv.get(ing["id"], 0)
    
    # Кнопки: ◀️ | Купить за N | ▶️
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"shop_{category}_{(index - 1) % total}"),
            InlineKeyboardButton(text=f"Купить за {ing['price']}", callback_data=f"buy_{ing['id']}_{category}_{index}"),
            InlineKeyboardButton(text="▶️", callback_data=f"shop_{category}_{(index + 1) % total}"),
        ],
        [
            InlineKeyboardButton(text="🥗 Основные", callback_data="shop_main_0"),
            InlineKeyboardButton(text="🍖 Дополнительные", callback_data="shop_extra_0"),
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть", callback_data="shop_close"),
        ],
    ])
    
    caption = (
        f"{ing['emoji']} <b>{ing['name']}</b>\n\n"
        f"💰 Цена: {ing['price']} Пушин-Долларов\n"
        f"📦 У тебя: {owned} шт.\n\n"
        f"<i>Мотай стрелками и покупай, что хочешь!</i>"
    )
    return caption, keyboard

# ---------- ПРОДАЖА БЛЮД ----------
def build_selling_carousel(index, user_id):
    """Строит карусель блюд для продажи"""
    dishes = get_dishes(user_id)
    
    if not dishes:
        caption = (
            "😔 У тебя нет блюд, чтобы продать.\n\n"
            "Приготовь что-нибудь! 🍳"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Готовка", callback_data="cook_main_0")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="sell_close")],
        ])
        return caption, keyboard, None
    
    index = index % len(dishes)
    dish_name, quality, qty = dishes[index]
    
    stars = QUALITY_NAMES.get(quality, "?")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"sell_{(index - 1) % len(dishes)}"),
            InlineKeyboardButton(text="💸 Продать", callback_data=f"sell_pick_{index}"),
            InlineKeyboardButton(text="▶️", callback_data=f"sell_{(index + 1) % len(dishes)}"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="sell_close"),
        ],
    ])
    
    caption = (
        f"🍽️ <b>{dish_name}</b>\n"
        f"{stars}\n\n"
        f"📦 В наличии: {qty} шт.\n\n"
        f"<i>Продать это блюдо?</i>"
    )
    return caption, keyboard, (dish_name, quality)

def create_pending_sale(user_id, dish_name, quality, price):
    """Создаёт запись о продаже и возвращает sale_id"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pending_sales (user_id, dish_name, quality, price)
        VALUES (?, ?, ?, ?)
    """, (user_id, dish_name, quality, price))
    sale_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sale_id

def get_pending_sale(sale_id):
    """Возвращает данные о продаже"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, dish_name, quality, price, status FROM pending_sales WHERE sale_id = ?", (sale_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_sale_status(sale_id, status):
    """Обновляет статус продажи"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE pending_sales SET status = ? WHERE sale_id = ?", (status, sale_id))
    conn.commit()
    conn.close()

# ---------- КОРМЛЕНИЕ ПУШИН ----------
def build_feeding_carousel(index, user_id):
    """Строит карусель блюд для кормления (без повторов, одинаковые группируются)"""
    dishes = get_dishes(user_id)
    
    if not dishes:
        caption = (
            "😔 У тебя нет блюд, чтобы покормить Пушин.\n\n"
            "Приготовь что-нибудь! 🍳"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Готовка", callback_data="cook_main_0")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="feed_close")],
        ])
        return caption, keyboard, None
    
    index = index % len(dishes)
    dish_name, quality, qty = dishes[index]
    
    stars = QUALITY_NAMES.get(quality, "?")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"feed_{(index - 1) % len(dishes)}"),
            InlineKeyboardButton(text="🍽️ Покормить", callback_data=f"feed_give_{index}"),
            InlineKeyboardButton(text="▶️", callback_data=f"feed_{(index + 1) % len(dishes)}"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="feed_close"),
        ],
    ])
    
    caption = (
        f"🍽️ <b>{dish_name}</b>\n"
        f"{stars}\n\n"
        f"📦 В наличии: {qty} шт.\n\n"
        f"<i>Покормить Пушин?</i>"
    )
    return caption, keyboard, (dish_name, quality)

# ---------- ГОТОВКА ----------
def get_active_cooking(user_id):
    """Возвращает активную готовку или None"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT dish_name, quality, finish_time FROM active_cooking WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row  # (dish_name, quality, finish_time)

def start_cooking(user_id, dish_name, quality):
    """Запускает готовку"""
    cooking_time = COOKING_TIME.get(quality, 1) * 60  # в секундах
    finish_time = time.time() + cooking_time
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO active_cooking (user_id, dish_name, quality, finish_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, dish_name, quality, finish_time))
    conn.commit()
    conn.close()
    return cooking_time

def finish_cooking(user_id):
    """Завершает готовку: добавляет блюдо в инвентарь, удаляет активную"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT dish_name, quality FROM active_cooking WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    dish_name, quality = row
    add_dish(user_id, dish_name, quality, 1)
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM active_cooking WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return dish_name, quality

def build_cooking_carousel(category, index, user_id):
    """Строит инлайн-клавиатуру для выбора ингредиентов в готовке.
    Показывает ТОЛЬКО те ингредиенты, что есть в инвентаре."""
    ingredients = MAIN_INGREDIENTS if category == "main" else EXTRA_INGREDIENTS
    inv = get_ingredients(user_id)
    
    # Оставляем только те, что есть в наличии
    available = [ing for ing in ingredients if inv.get(ing["id"], 0) > 0]
    
    if not available:
        caption = (
            f"😔 У тебя нет ингредиентов из категории "
            f"{'🥗 Основные' if category == 'main' else '🍖 Дополнительные'}.\n\n"
            f"Купи их в магазине! 🛒"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 В магазин", callback_data="shop_main_0")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="cook_close")],
        ])
        return caption, keyboard, None
    
    index = index % len(available)
    ing = available[index]
    qty = inv.get(ing["id"], 0)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"cook_{category}_{(index - 1) % len(available)}"),
            InlineKeyboardButton(text="Выбрать", callback_data=f"cook_pick_{ing['id']}_{category}"),
            InlineKeyboardButton(text="▶️", callback_data=f"cook_{category}_{(index + 1) % len(available)}"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cook_close"),
        ],
    ])
    
    caption = (
        f"{ing['emoji']} <b>{ing['name']}</b>\n\n"
        f"📦 В наличии: {qty} шт.\n\n"
        f"<i>Выбери этот ингредиент или мотай дальше</i>"
    )
    return caption, keyboard, ing

# ---------- ИНВЕНТАРЬ: ТЕКСТ ----------
def build_inventory_text(user_id):
    """Строит текст инвентаря: ингредиенты + блюда"""
    inv_ing = get_ingredients(user_id)
    dishes = get_dishes(user_id)
    
    # Ингредиенты
    if inv_ing:
        ing_lines = []
        for ing in MAIN_INGREDIENTS + EXTRA_INGREDIENTS:
            qty = inv_ing.get(ing["id"], 0)
            if qty > 0:
                ing_lines.append(f"{ing['emoji']} {ing['name']} — {qty} шт.")
        ing_text = "\n".join(ing_lines)
    else:
        ing_text = "<i>Пока пусто. Купи что-нибудь в магазине! 🛒</i>"
    
    # Блюда
    if dishes:
        dish_lines = []
        for dish_name, quality, qty in dishes:
            stars = QUALITY_NAMES.get(quality, "?")
            dish_lines.append(f"🍽️ {dish_name} {stars} — {qty} шт.")
        dish_text = "\n".join(dish_lines)
    else:
        dish_text = "<i>Пока пусто. Приготовь что-нибудь! 🍳</i>"
    
    text = (
        "🎒 <b>Твой инвентарь</b>\n\n"
        "🥗 <b>Ингредиенты:</b>\n"
        f"{ing_text}\n\n"
        "🍰 <b>Блюда:</b>\n"
        f"{dish_text}\n\n"
        f"💵 Пушин-Долларов: <b>{get_pusheen_dollars(user_id)}</b>"
    )
    return text

# ---------- ПУШИН-ДОЛЛАРЫ ----------
def get_pusheen_dollars(user_id):
    """Возвращает баланс Пушин-Долларов, начисляя 100 в день"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT pusheen_dollars, pd_reset FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if row is None:
        conn.close()
        return 0
    
    dollars, last_reset = row
    today = datetime.now().date()
    
    if last_reset is None:
        last_reset_date = today - timedelta(days=1)
    else:
        try:
            last_reset_date = datetime.strptime(last_reset, "%Y-%m-%d").date()
        except:
            last_reset_date = today - timedelta(days=1)
    
    # Новый день — начисляем 100
    if today > last_reset_date:
        new_balance = (dollars or 0) + PUSHEEN_DOLLARS_DAILY
        cur.execute("UPDATE users SET pusheen_dollars = ?, pd_reset = ? WHERE user_id = ?",
                    (new_balance, today.strftime("%Y-%m-%d"), user_id))
        conn.commit()
        conn.close()
        return new_balance
    
    conn.close()
    return dollars or 0

def add_pusheen_dollars(user_id, amount):
    """Добавляет Пушин-Доллары"""
    current = get_pusheen_dollars(user_id)
    new_balance = current + amount
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET pusheen_dollars = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    return new_balance

def spend_pusheen_dollars(user_id, amount):
    """Списывает Пушин-Доллары. Возвращает True, если хватило"""
    current = get_pusheen_dollars(user_id)
    if current < amount:
        return False
    new_balance = current - amount
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET pusheen_dollars = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    return True

# ---------- ИНВЕНТАРЬ ----------
def add_ingredient(user_id, ingredient_id, quantity=1):
    """Добавляет ингредиент в инвентарь (до 99)"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM inventory_ingredients WHERE user_id = ? AND ingredient_id = ?",
                (user_id, ingredient_id))
    row = cur.fetchone()
    
    if row is None:
        cur.execute("INSERT INTO inventory_ingredients (user_id, ingredient_id, quantity) VALUES (?, ?, ?)",
                    (user_id, ingredient_id, min(quantity, 99)))
    else:
        new_qty = min(row[0] + quantity, 99)
        cur.execute("UPDATE inventory_ingredients SET quantity = ? WHERE user_id = ? AND ingredient_id = ?",
                    (new_qty, user_id, ingredient_id))
    conn.commit()
    conn.close()

def remove_ingredient(user_id, ingredient_id, quantity=1):
    """Убирает ингредиент из инвентаря"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM inventory_ingredients WHERE user_id = ? AND ingredient_id = ?",
                (user_id, ingredient_id))
    row = cur.fetchone()
    if row is None or row[0] < quantity:
        conn.close()
        return False
    new_qty = row[0] - quantity
    if new_qty <= 0:
        cur.execute("DELETE FROM inventory_ingredients WHERE user_id = ? AND ingredient_id = ?",
                    (user_id, ingredient_id))
    else:
        cur.execute("UPDATE inventory_ingredients SET quantity = ? WHERE user_id = ? AND ingredient_id = ?",
                    (new_qty, user_id, ingredient_id))
    conn.commit()
    conn.close()
    return True

def get_ingredients(user_id):
    """Возвращает {ingredient_id: quantity}"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT ingredient_id, quantity FROM inventory_ingredients WHERE user_id = ? AND quantity > 0",
                (user_id,))
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def add_dish(user_id, dish_name, quality, quantity=1):
    """Добавляет блюдо в инвентарь (до 99)"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM inventory_dishes WHERE user_id = ? AND dish_name = ? AND quality = ?",
                (user_id, dish_name, quality))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO inventory_dishes (user_id, dish_name, quality, quantity) VALUES (?, ?, ?, ?)",
                    (user_id, dish_name, quality, min(quantity, 99)))
    else:
        new_qty = min(row[0] + quantity, 99)
        cur.execute("UPDATE inventory_dishes SET quantity = ? WHERE user_id = ? AND dish_name = ? AND quality = ?",
                    (new_qty, user_id, dish_name, quality))
    conn.commit()
    conn.close()

def remove_dish(user_id, dish_name, quality, quantity=1):
    """Убирает блюдо из инвентаря"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM inventory_dishes WHERE user_id = ? AND dish_name = ? AND quality = ?",
                (user_id, dish_name, quality))
    row = cur.fetchone()
    if row is None or row[0] < quantity:
        conn.close()
        return False
    new_qty = row[0] - quantity
    if new_qty <= 0:
        cur.execute("DELETE FROM inventory_dishes WHERE user_id = ? AND dish_name = ? AND quality = ?",
                    (user_id, dish_name, quality))
    else:
        cur.execute("UPDATE inventory_dishes SET quantity = ? WHERE user_id = ? AND dish_name = ? AND quality = ?",
                    (new_qty, user_id, dish_name, quality))
    conn.commit()
    conn.close()
    return True

def get_dishes(user_id):
    """Возвращает список блюд с количеством"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT dish_name, quality, quantity FROM inventory_dishes WHERE user_id = ? AND quantity > 0",
                (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows  # [(dish_name, quality, quantity), ...]

# ---------- ПУШИН ----------
def get_pusheen_happiness(user_id):
    """Возвращает уровень счастья Пушин (0-100), сбрасывая каждый день"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT pusheen_happiness, pusheen_reset FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if row is None:
        conn.close()
        return 0
    
    happiness, last_reset = row
    today = datetime.now().date()
    
    if last_reset is None:
        last_reset_date = today - timedelta(days=1)
    else:
        try:
            last_reset_date = datetime.strptime(last_reset, "%Y-%m-%d").date()
        except:
            last_reset_date = today - timedelta(days=1)
    
    # Если наступил новый день — сбрасываем
    if today > last_reset_date:
        cur.execute("UPDATE users SET pusheen_happiness = 0, pusheen_reset = ? WHERE user_id = ?", 
                    (today.strftime("%Y-%m-%d"), user_id))
        conn.commit()
        conn.close()
        return 0
    
    conn.close()
    return happiness

def add_pusheen_happiness(user_id):
    """Добавляет +PUSHEEN_STEP к счастью, но не больше 100"""
    current = get_pusheen_happiness(user_id)
    new_value = min(current + PUSHEEN_STEP, 100)
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("UPDATE users SET pusheen_happiness = ?, pusheen_reset = ? WHERE user_id = ?", 
                (new_value, today, user_id))
    conn.commit()
    conn.close()
    return new_value

def get_pusheen_image(happiness):
    """Возвращает путь к картинке Пушин по уровню счастья"""
    if happiness >= 100:
        img = "star.jpg"
    elif happiness >= 70:
        img = "happy.jpg"
    elif happiness >= 30:
        img = "smile.jpg"
    else:
        img = "sad.jpg"
    return os.path.join(PUSHEEN_FOLDER, img)

def get_pusheen_mood_emoji(happiness):
    """Возвращает только эмодзи настроения"""
    if happiness >= 100:
        return "😻😻😻😻😻😻😻😻😻😻"
    elif happiness >= 70:
        return "😻"
    elif happiness >= 30:
        return "😺"
    else:
        return "😴"

def get_pusheen_mood_text(happiness):
    """Возвращает только текст настроения"""
    if happiness >= 100:
        return "Пушин счастлива!"
    elif happiness >= 70:
        return "Пушин сияет от счастья!"
    elif happiness >= 30:
        return "Пушин мурлычет"
    else:
        return "Пушин только просыпается..."

def get_pusheen_mood(happiness):
    """Возвращает полную строку настроения (для совместимости)"""
    return f"🐾 Настроение: {get_pusheen_mood_emoji(happiness)}\n{get_pusheen_mood_text(happiness)}"

# ---------- ПРОГРЕСС: отслеживание просмотренного ----------
def mark_message_seen(user_id, message_text):
    """Записывает, что пользователь увидел эту фразу (использует текст как ключ)"""
    key = message_text[:500]  # обрезаем на всякий случай
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO seen_messages (user_id, message_hash) VALUES (?, ?)", (user_id, key))
        conn.commit()
    except:
        pass
    conn.close()

def mark_image_seen(user_id, image_name):
    """Записывает, что пользователь увидел эту картинку"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO seen_images (user_id, image_name) VALUES (?, ?)", (user_id, image_name))
        conn.commit()
    except:
        pass
    conn.close()

def get_progress(user_id):
    """Возвращает процент просмотренного контента (считает свежие данные каждый раз)"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    
    # Сколько фраз она видела (только те, что ещё существуют в пуле)
    cur.execute("SELECT message_hash FROM seen_messages WHERE user_id = ?", (user_id,))
    all_seen_msgs = cur.fetchall()
    
    # Сколько картинок она видела (только те, что ещё существуют на диске)
    cur.execute("SELECT image_name FROM seen_images WHERE user_id = ?", (user_id,))
    all_seen = cur.fetchall()
    
    conn.close()
    
    # Собираем все существующие картинки на диске
    existing_images = set()
    try:
        for root, dirs, files in os.walk(IMAGE_FOLDER):
            for f in files:
                if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                    full_path = os.path.join(root, f)
                    rel_name = os.path.relpath(full_path, IMAGE_FOLDER)
                    existing_images.add(rel_name)
    except Exception as e:
        print(f"⚠️ Ошибка чтения папки: {e}")
    
    # Считаем только те просмотренные, что ещё существуют
    seen_imgs = sum(1 for (name,) in all_seen if name in existing_images)
    
    # Всего фраз в пуле (обычные + поцелуи + объятия + Пушин)
    all_messages = MESSAGES + KISS_REPLIES + HUG_REPLIES + PUSHEEN_PHRASES
    total_msgs = len(all_messages)
    
    # Собираем ВСЕ актуальные фразы (обрезанные так же, как записывали)
    existing_keys = set(m[:500] for m in all_messages)
    
    # Считаем только те просмотренные, что ещё есть в пуле
    seen_msgs = sum(1 for (h,) in all_seen_msgs if h in existing_keys)
    
    # Всего картинок в папке = количество существующих (уже посчитано выше)
    total_imgs = len(existing_images)
    
    # Считаем общий процент
    total_seen = seen_msgs + seen_imgs
    total_all = total_msgs + total_imgs
    
    if total_all == 0:
        return 0, 0, total_msgs, 0, total_imgs
    
    percent = int((total_seen / total_all) * 100)
    
    print(f"📊 Прогресс: {seen_msgs}/{total_msgs} фраз, {seen_imgs}/{total_imgs} картинок, {percent}%")
    
    return percent, seen_msgs, total_msgs, seen_imgs, total_imgs

# ---------- СКОЛЬКО МЫ ВМЕСТЕ ----------
def get_time_since(start_date):
    """Возвращает полную разбивку от указанной даты:
    дни, недели, месяцы, часы, минуты, секунды, общие часы, общие минуты"""
    now = datetime.now()
    delta = now - start_date
    days = delta.days
    months = days // 30
    weeks = days // 7
    
    total_seconds = int(delta.total_seconds())
    hours = (total_seconds // 3600) % 24
    minutes = (total_seconds // 60) % 60
    seconds = total_seconds % 60
    
    total_hours = total_seconds // 3600
    total_minutes = total_seconds // 60
    
    return days, weeks, months, hours, minutes, seconds, total_hours, total_minutes
    

# ---------- БАЗА ТЕКСТОВ (ДОБАВЛЯЙ СВОИ) ----------
MESSAGES = [
    "Бабочки не могут видеть свои крылья, но все остальные ими восхищаются. Даже если ты сама этого не видишь, я вижу.",
    "Ты - моё любимое произведение искусства. Даже когда ты устала, я вижу в тебе сияние.",
    "Я знаю, что сегодня серо. Но даже сквозь тучи солнце пробивается. Ты - моё солнце.",
    "Ты не обязана быть продуктивной. Ты обязана просто дышать. А я буду любить тебя даже просто за то, что ты есть.",
    "Если твоя голова говорит гадости - не верь ей. Верь мне. Ты справляешься уже одним тем, что встала.",
    "Напомни-ка мне, ты пила воду сегодня? Сходи, выпей стаканчик, я подожду.",
    "Представь, что я обнимаю тебя так крепко, чтобы все тревоги вышли наружу. Я здесь.",
    "Ты не одна. Даже если кажется, что темнота сжимается - я держу фонарик и никуда не уйду.",
    "Я горжусь тобой. Не за результат, а за то, что ты продолжаешь идти, даже когда ноги тяжелые.",
    "Если бы ты видела себя моими глазами, ты бы влюбилась в себя без памяти.",
    "Милашик, никогда не думай что ты одна, я всегда к тебе приду и полюблю и понежню!",
    "Ты имеешь право чувствовать всё, что чувствуешь. Я буду рядом, чтобы держать тебя за руку в любой темноте.",
    "Твои чувства реальны. Они важны. И я принимаю их все - даже те, которые я не понимаю.",
    "Ты ценна, ты нужна, и ты любима. Без всяких условий.",
    "Ты - лучшая часть моего дня.",
    "Если твоя забота обо мне - это артефакты в геншине, а мои мысли о тебе — это билд, то каждый день у меня самый сильный билд в мире.",
    "Ты — как мой личный спаниель-терапевт. Никаких слов, просто присутствие, и мне уже легче.",
    "Знаешь, почему спаниели такие счастливые? Потому что они знают, что их любят. Ты делаешь меня таким же счастливым.",
    "Если бы ты была спаниелем, ты бы вечно путалась в своих длинных ушах. И я бы каждый день распутывал их и целовал в макушку.",
    "Если бы я был собакой, я бы выбрал тебя своим хозяином. Потому что ты - та, кто кормит вкусняшками, гладит по голове и никогда не бросает.",
    "Спаниель - порода, которая не умеет предавать. Мы с тобой как спаниели. Мы выбираем друг друга навсегда.",
    "Если бы ты была спаниелем, ты бы вечно искала вкусняшки в моих карманах. И я бы вечно клал их туда специально для тебя.",
    "Ты делаешь меня добрее. Я смотрю на тебя и понимаю: быть добрым - это круто. Это сильно. Это быть как ты.",
    "Ты всегда находишь хорошие слова для других. Найди их для себя тоже. Ты этого достойна.",
    "Если бы ты относилась к себе с той же добротой, с которой относишься к другим, ты бы поняла, как ты прекрасна.",
    "Ты в жизни как и в Роблоксе. Мы проходим квесты вместе, и даже когда сложно - ты не выходишь из игры. Спасибо.",
    "у Сесилиона и Кармиллы, есть такие слова: Time devours all but you — Время пожирает всё, кроме тебя . Это идеально описывает и мои чувства к тебе. Для меня тоже есть только одно вечно - и это ты.»",
    "Ты даришь мне не просто подарки. Ты даришь мне частичку своего сердца, упакованную в красивую бумагу. И каждый раз, когда я открываю твой подарок, я чувствую, как ты думала обо мне. И это - самый ценный подарок.",
    "Ценность твоих подарков не простая. Она в том, что ты помнишь каждую мою мелочь. Ты помнишь, что я люблю, что я хочу, что я даже не сказал вслух. И я каждый раз ашалеваю когда получаю такой приз. Милаша, ты самая лучшая!",
    "Твои подарки - как твои глаза. Они всегда говорят мне правду: что ты любишь меня, что ты думаешь обо мне, что ты хочешь сделать меня счастливым. И у тебя это отлично получается.",
    "Ты - единственный человек, чьи подарки я открываю с детским восторгом. Потому что я знаю: внутри не просто вещь, а твоя любовь. И эта любовь упакована в красивую обёртку.",
    "Ты первое о чем я думаю с утра и последнее перед сном",
    "Когда ты садишься ко мне когда я на Джонсоне, я чувствую себя самым счастливым водителем в мире.",
    "Когда ты рядом, я чувствую себя как собака, которую наконец-то погладили. Тепло, уютно, и хочется мурлыкать (да, собаки наверно тоже так умеют и их ты любишь больше чем кошек ведь).",
    "Ты  как лосось. Плывёшь против течения, не сдаёшься, и всегда идёшь к своей цели. Я восхищаюсь твоей силой.",
    "Ты мой самый любимый лосось. Да, это звучит канешна странно, но ты честно самая лучшая рыбка-лососька в моём океане.",
    "Ты как лосось на гриле. Тёплая, аппетитная, и я хочу тебя... съесть, но не прям скушать, ну может укусить просто, понимаешь?",
    "Ты моя креветка. Маленькая, но самая важная. Без тебя мой ролл был бы просто рисом.",
    "Милаша, когда я катаю тебя на Джонсоне, а ты Кадита, как будто бы я добыл самого большого и ценного лосося.",
    "https://vt.tiktok.com/ZSbdeWfWT/ - специальный тикток для тебя, невидный ни для кого больше.",
    "Если бы ты была в параллельной вселенной One True Pusheenкой, то я бы даже не обалдел, потому что в этой вселенной ты в сто раз замечательнее.","Если бы ты была в параллельной вселенной One True Pusheenкой, то я бы даже не обалдел, потому что в этой вселенной ты в сто раз замечательнее.",
    "https://music.yandex.ru/album/35698905/track/136837204?ref_id=D3F31C1B-5030-4685-9887-6D0B1F824A13&utm_medium=share_link_tg&utm_source=mobile_ios",
    
    

]
KISS_REPLIES = [
    "💋 Я чувствую твой поцелуй. Мне стало тепло.",
    "💋 Твой поцелуй — лучшее лекарство в мире.",
    "💋 Поцеловал тебя в ответ. Но ты не увидишь, потому что я далеко. Но я правда поцеловал экран.",
    "💋 Ты знаешь, что после твоего поцелуя я улыбаюсь как дурак?",
    "💋 Сохранил твой поцелуй в сердечко. Открою, когда будет грустно.",
    "💋 Ого! А ты сегодня смелая. Я ценю.",
    "💋 Милашкискис, я за тобой слежу.",
    "💋 Люблюю тебя, моя хорошечка.",
]

# Фразы Пушин при кормлении (по качеству)
FEED_PHRASES = {
    3: [  # Легендарное
        "😻 Пушин на седьмом небе от счастья! Это было божественно!",
        "😻 Пушин танцует от восторга! Ты — лучший повар на свете!",
        "😻 Пушин смотрит на тебя влюблёнными глазами. Это было великолепно!",
        "✨ Пушин проглотила всё за секунду и просит ещё! Это шедевр!",
    ],
    2: [  # Хорошо
        "😺 Пушин довольна! Она облизывается и мурлычет.",
        "😺 Пушин съела всё до крошки и просит добавки!",
        "😺 Пушин трётся о твою руку. Спасибо, вкусно!",
        "😺 Пушин жмурится от удовольствия. Ей понравилось!",
        "😺 Пушин благодарно смотрит на тебя. Вкуснятина!",
    ],
    1: [  # Средне
        "😐 Пушин съела, но не впечатлилась. Может, добавишь что-то ещё?",
        "😐 Пушин жуёт, поглядывая на тебя. Ей норм.",
        "😐 Пушин скушала, но не облизнулась. Значит, на троечку.",
        "😐 Пушин проглотила, но посмотрела с лёгким укором.",
        "😐 Пушин съела, но как будто из вежливости.",
    ],
    0: [  # Плохо
        "🙀 Пушин понюхала, поморщилась и спряталась под диван...",
        "😾 Пушин съела, но посмотрела на тебя с укором...",
        "😿 Пушин сделала вид, что не заметила это блюдо...",
        "🙀 Пушин вежливо отказалась, сославшись на занятость...",
        "🙀 Пушин закопала это блюдо в невидимый песок...",
        "😿 Пушин посмотрела на тебя так, будто ты её предала...",
    ],
}

PUSHEEN_PHRASES = [
    "🐱 Пушин мурлычет...",
    "🐾 Пушин мурлычет так громко, что слышно на весь дом",
    "😺 Пушин довольно урчит",
    "🎵 Пушин мурлычет свою кошачью песенку",
    "💤 Пушин тихо сопит от счастья",
    "🔊 Пушин урчит как маленький трактор",
    "🎶 Пушин мурлычет в такт твоему сердцу",
    "🐱 Пушин издаёт самое уютное «мррр» на свете",
    "😻 Пушин думает, что ты самая лучшая девочка на свете",
    "🤍 Пушин никогда не забудет какая ты хорошка",
    "🐾 Пушин трётся о твою руку",
    "😽 Пушин жмурится от удовольствия",
    "💖 Пушин мягко бодает тебя головой",
    "🤍 Пушин тянется к тебе всем тельцем",
    "🌸 Пушин щурится и улыбается",
    "✨ Пушин вытягивает лапки от счастья",
    "🐱 Пушин прижимается к тебе и не отпускает",
    "💕 Пушин нежно касается тебя лапкой",
    "💤 Пушин сворачивается клубочком у тебя на коленях",
    "😴 Пушин засыпает, чувствуя твоё тепло",
    "🛌 Пушин устраивается поудобнее и зевает",
    "🌙 Пушин дремлет, тихо посапывая",
    "🐾 Пушин прячет носик в свои лапки",
    "✨ Пушин видит кошачьи сны рядом с тобой",
    "💤 Пушин потягивается и снова сворачивается",
    "🐱 Пушин зевает и жмурится",
    "🎾 Пушин ловит твою руку лапками",
    "🧶 Пушин играет с невидимым клубком",
    "🐭 Пушин делает вид, что охотится",
    "😹 Пушин прыгает и кувыркается от радости",
    "🎀 Пушин грациозно потягивается",
    "🪶 Пушин ловит солнечного зайчика",
    "😺 Пушин показывает тебе свой животик",
    "🐱 Пушин машет хвостиком от восторга",
    "💖 Пушин благодарит тебя за ласку",
    "🤍 Пушин смотрит на тебя влюблёнными глазами",
    "💕 Пушин обнимает тебя хвостиком",
    "✨ Пушин светится от счастья рядом с тобой",
    "💗 Пушин чувствует себя самой любимой кошкой",
    "🌸 Пушин доверяет тебе самое сокровенное",
    "🐾 Пушин выбрала тебя своей хозяйкой",
    "💝 Пушин дарит тебе всю свою нежность",
    "🌸 Пушин наслаждается твоим присутствием",
    "🌿 Пушин уютно устроилась рядом",
    "🍃 Пушин вдыхает твой запах и улыбается",
    "🌺 Пушин чувствует себя в безопасности",
    "🍀 Пушин приносит тебе удачу своим мурчанием",
    "🌷 Пушин делает мир вокруг тебя добрее",
    "🌻 Пушин согревает тебя своим теплом",
    "🌼 Пушин наполняет дом уютом",
    "😻 Пушин на седьмом небе от счастья",
    "😽 Пушин посылает тебе воздушный поцелуй",
    "💫 Пушин сияет как маленькая звезда",
    "🌟 Пушин — самая счастливая кошка в мире",
    "👑 Пушин чувствует себя королевой рядом с тобой",
    "🏆 Пушин признаёт тебя лучшей хозяйкой на свете",
    "🐱 Пушин мурчит",
    "🐾 Пушин рядом",
    "😺 Пушин довольна",
    "💖 Пушин тебя любит",
    "✨ Пушин счастлива",
    "🌸 Пушин улыбается",
    "💤 Пушин спит",
    "🤍 Пушин твоя",
    
]

HUG_REPLIES = [
    "🤗 Я обнимаю тебя так крепко, что ты чувствуешь? Даже через экран.",
    "🤗 Обнимаю тебя и не отпускаю. Хочешь, постоим так пару минут?",
    "🤗 Ты только что сделала мой день лучше. Спасибо за объятия.",
    "🤗 Я закрыл глаза и представил, что ты рядом. Тепло разлилось по всему телу. Спасибо.",
    "🤗 Обнимаю тебя в ответ. Представь, что это самый уютный плед и горячий чай одновременно.",
    "🤗 Я бы обнимал тебя вечно, но тогда бы мы ничего не успели. Поэтому обнимаю сильно-сильно и отпускаю. До следующего раза.",
    "🤗 Мяу мряу мяу мяу мяу мяу, сладкий котек.",
    "🤗 Обнял няху, по секрету, в картинках есть новая пасхалка, пасхалочка.",
]

# ---------- ФУНКЦИЯ ОТПРАВКИ С КАРТИНКОЙ ----------
async def send_with_image(message: types.Message, text: str):
    """Отправляет текст с картинкой из всех подпапок. И записывает просмотр."""
    user_id = message.from_user.id
    
    # Записываем просмотр фразы
    mark_message_seen(user_id, text)
    
    try:
        # Собираем ВСЕ картинки из корня и всех подпапок
        images = []
        for root, dirs, files in os.walk(IMAGE_FOLDER):
            for f in files:
                if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                    # Сохраняем полный путь и имя для записи в БД
                    full_path = os.path.join(root, f)
                    # Уникальное имя для БД — относительный путь
                    rel_name = os.path.relpath(full_path, IMAGE_FOLDER)
                    images.append((full_path, rel_name))
        
        if images:
            img_path, img_name = random.choice(images)
            photo = FSInputFile(img_path)
            
            # Записываем просмотр картинки
            mark_image_seen(user_id, img_name)
            
            await message.answer_photo(photo=photo, caption=text, reply_markup=get_keyboard_for_user(user_id))
        else:
            await message.answer(text, reply_markup=get_keyboard_for_user(user_id))
    except Exception as e:
        print(f"⚠️ Ошибка отправки картинки: {e}")
        await message.answer(text + "\n\n(Картинка не загрузилась, но слова от души)", reply_markup=get_keyboard_for_user(user_id))

def get_keyboard_for_user(user_id):
    """Возвращает клавиатуру в зависимости от баланса пользователя"""
    tokens = check_and_reset(user_id)
    return get_keyboard(tokens, user_id)

# ---------- УВЕДОМЛЕНИЕ ТЕБЕ ----------
async def notify_you(chat_id: int, text: str):
    """Отправляет уведомление тебе в личные сообщения"""
    try:
        await bot.send_message(chat_id=ALLOWED_USER_IDS[0], text=text)
    except Exception as e:
        print(f"⚠️ Не удалось отправить уведомление: {e}")

# ---------- ОПОВЕЩЕНИЕ ВСЕХ О ЗАПУСКЕ ----------
# Файл для хранения времени последнего запуска
LAST_START_FILE = "last_start.txt"

async def notify_all_started():
    """Отправляет оповещение о запуске, но не чаще, чем раз в 30 минут"""
    # Проверяем, когда бот запускался последний раз
    try:
        if os.path.exists(LAST_START_FILE):
            with open(LAST_START_FILE, "r") as f:
                last_start = float(f.read().strip())
            if time.time() - last_start < 1800:  # 1800 секунд = 30 минут
                print("⏭️ Оповещение пропущено (бот запускался недавно)")
                return
    except:
        pass
    
    # Отправляем оповещение
    for user_id in ALLOWED_USER_IDS:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "🌸 Я снова в сети!\n\n"
                    "Бот включён и готов дарить тебе тепло. 🤍\n"
                    "Загляни — у меня есть для тебя что-то приятное!"
                ),
                reply_markup=get_keyboard(check_and_reset(user_id), user_id)
            )
        except Exception as e:
            print(f"⚠️ Не удалось оповестить {user_id}: {e}")
    
    # Сохраняем время запуска
    with open(LAST_START_FILE, "w") as f:
        f.write(str(time.time()))

# ---------- КОМАНДЫ БОТА ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        await message.answer("🚫 Этот бот не для тебя. Извини.")
        return
    
    tokens = check_and_reset(user_id)
    await message.answer(
        "🌸 Привет, моя хорошая!\n"
        "У тебя есть 50 токенов в день.\n"
        "За 10 токенов ты можешь получить тёплое сообщение с картинкой.\n"
        "Я всегда рядом. 🤍\n\n"
        "💫 Иногда я прячу сюрпризы. Особенно когда ты особенно добра ко мне.\n\n"
        "🌙 Если я вдруг замолчу — я просто ушёл на перерыв. Напиши мне позже, и я отвечу!",
        reply_markup=get_keyboard(tokens, user_id)
    )

@dp.message(lambda msg: msg.text == "💖Милашка, нажми сюда (10 токенов)")
async def get_support(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    tokens = check_and_reset(user_id)
    
    if tokens < 10:
        await message.answer(
            f"У тебя осталось всего {tokens} токенов.\n"
            "Используй кнопку «🔄 Бесконечные нежности (раз в минуту)» — я всё равно буду с тобой.",
        reply_markup=get_keyboard(tokens, user_id)
        )
        return
    
    spend_tokens(user_id, 10)
    new_tokens = tokens - 10
    text = random.choice(MESSAGES)
    await send_with_image(message, text)
    await message.answer(f"✨ Осталось токенов: {new_tokens} из 50", reply_markup=get_keyboard(new_tokens, user_id))

@dp.message(lambda msg: msg.text == "🔄 Бесконечные нежности (раз в минуту)")
async def free_support(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    tokens = check_and_reset(user_id)
    
    current_time = time.time()
    if user_id in last_free_time:
        elapsed = current_time - last_free_time[user_id]
        if elapsed < FREE_COOLDOWN:
            remaining = int(FREE_COOLDOWN - elapsed)
            await message.answer(
                f"⏳ Подожди {remaining} секунд, чтобы получить ещё одну порцию нежностей.\n"
                f"А пока знай: ты важна для меня. 🤍",
                reply_markup=get_keyboard(tokens, user_id)
            )
            return
    
    last_free_time[user_id] = current_time
    text = random.choice(MESSAGES)
    await send_with_image(message, text)

@dp.message(lambda msg: msg.text == "💋 Поцеловать")
async def kiss(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    tokens = check_and_reset(user_id)
    
    reply = random.choice(KISS_REPLIES)
    new_tokens = tokens + 5
    update_tokens(user_id, new_tokens)
    
    await send_with_image(message, reply)
    await message.answer(f"✨ Ты получила +5 токенов за поцелуй! Теперь у тебя {new_tokens} токенов.", reply_markup=get_keyboard(new_tokens, user_id))
    await notify_you(ALLOWED_USER_IDS[0], f"💋 Твоя девочка прислала тебе поцелуйчик! +5 токенов. Теперь у неё {new_tokens} токенов.")

@dp.message(lambda msg: msg.text == "🤗 Обнять")
async def hug(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    tokens = check_and_reset(user_id)
    
    reply = random.choice(HUG_REPLIES)
    new_tokens = tokens + 5
    update_tokens(user_id, new_tokens)
    
    await send_with_image(message, reply)
    await message.answer(f"✨ Ты получила +5 токенов за объятие! Теперь у тебя {new_tokens} токенов.", reply_markup=get_keyboard(new_tokens, user_id))
    await notify_you(ALLOWED_USER_IDS[0], f"🤗 Твоя девочка хочет обняться! +5 токенов. Теперь у неё {new_tokens} токенов.")

@dp.message(lambda msg: msg.text == "✨ Пасхалка")
async def secret_message(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    tokens = check_and_reset(user_id)
    if tokens < 100:
        await message.answer(
            "✨ Ой! Похоже, эта кнопка пропала. Попробуй накопить 100 токенов!",
            reply_markup=get_keyboard(tokens, user_id)
        )
        return
    
    # 1. Отправляем гифку
    try:
        gif_file = FSInputFile(SECRET_GIF_FILE)
        await message.answer_animation(animation=gif_file)
    except Exception as e:
        print(f"⚠️ Не удалось отправить гифку: {e}")
    
    # 2. Отправляем голосовое
    try:
        voice = FSInputFile(SECRET_VOICE_FILE)
        await message.answer_voice(voice=voice)
    except Exception as e:
        await message.answer(
            "✨ У меня для тебя секретное послание, но оно временно недоступно.\nНо я люблю тебя! 🤍",
            reply_markup=get_keyboard(tokens, user_id)
        )
        return
    
    # 3. Текст
    await message.answer(
        "✨ Ты нашла пасхалку!\n"
        "Ты супер молодеч, Милашик.\n\n"
        "Хапи хапи хапи. 🤍",
        reply_markup=get_keyboard(tokens, user_id)
    )
    
    # 4. Уведомление тебе
    await notify_you(ALLOWED_USER_IDS[0], f"✨ Она нашла пасхалку и услышала твой голос! 🥹")

@dp.message(lambda msg: msg.text == "➕ Добавить картинку")
async def add_image_prompt(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    await message.answer(
        "📸 Отправь мне фото, и я добавлю его в нашу общую коллекцию!\n\n"
        "Оно будет появляться в случайных сообщениях вместе с другими картинками.\n"
        "(Можешь отправить одно фото за раз)",
        reply_markup=get_keyboard(check_and_reset(user_id), user_id)
    )

@dp.message(lambda msg: msg.photo is not None)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_{timestamp}.jpg"
        full_path = os.path.join(IMAGE_FOLDER, filename)
        
        await bot.download_file(file_path, full_path)
        
        await message.answer(
            f"✅ Картинка добавлена! Теперь она в общем пуле.",
            reply_markup=get_keyboard(check_and_reset(user_id), user_id)
        )
        
        await notify_you(ALLOWED_USER_IDS[0], f"🖼️ Она добавила новую картинку: {filename}")
        
    except Exception as e:
        await message.answer(
            "⚠️ Не удалось сохранить картинку. Попробуй ещё раз.",
            reply_markup=get_keyboard(check_and_reset(user_id))
        )
        print(f"Ошибка сохранения фото: {e}")

@dp.message(lambda msg: msg.text == "🎁 Выдать 100 токенов Милашке")
async def give_tokens_to_her(message: types.Message):
    user_id = message.from_user.id
    
    # Только ты можешь использовать эту кнопку
    if user_id != ALLOWED_USER_IDS[0]:
        return
    
    her_id = ALLOWED_USER_IDS[1]
    
    # Получаем её текущий баланс
    her_tokens = check_and_reset(her_id)
    new_tokens = her_tokens + 100
    update_tokens(her_id, new_tokens)
    
    # 🎉 Отправляем ей хлопушки и сообщение
    try:
        await bot.send_message(
            chat_id=her_id,
            text=(
                "🎉🎊✨🎉🎊✨🎉\n\n"
                "Вот тебе токены, ни в чём себе не отказывай, милаш! 💖\n\n"
                f"💰 Теперь у тебя {new_tokens} токенов.\n\n"
                "🎉🎊✨🎉🎊✨🎉"
            ),
            reply_markup=get_keyboard(new_tokens, her_id)
        )
    except Exception as e:
        print(f"⚠️ Не удалось отправить ей: {e}")
    
    # Тебе подтверждение
    await message.answer(
        f"✅ Ты выдал 100 токенов Милашке!\n"
        f"Было: {her_tokens}\n"
        f"Стало: {new_tokens}",
        reply_markup=get_keyboard(check_and_reset(user_id), user_id)
    )

# ---------- CALLBACK'И ПРОДАЖИ ----------
@dp.callback_query(lambda c: c.data.startswith("sell_"))
async def selling_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_allowed(user_id):
        await callback.answer("Не для тебя", show_alert=False)
        return
    
    data = callback.data.split("_")
    
    # Закрыть
    if data[1] == "close":
        await callback.message.delete()
        await callback.answer()
        return
    
    # Переключение карусели: sell_{index}
    if len(data) == 2:
        index = int(data[1])
        caption, keyboard, dish = build_selling_carousel(index, user_id)
        
        if dish:
            img_path = get_dish_image_path(dish[0])
        else:
            img_path = None
        
        try:
            await callback.message.delete()
            if img_path:
                photo = FSInputFile(img_path)
                await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await callback.message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        except:
            pass
        await callback.answer()
        return
    
    # Выбор блюда для продажи: sell_pick_{index}
    if data[1] == "pick":
        index = int(data[2])
        dishes = get_dishes(user_id)
        
        if index >= len(dishes):
            await callback.answer("Блюдо не найдено", show_alert=True)
            return
        
        dish_name, quality, qty = dishes[index]
        
        # Сохраняем черновик
        selling_draft[user_id] = {"dish_name": dish_name, "quality": quality}
        waiting_for_price[user_id] = True
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="sell_cancel_price")],
        ])
        
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            f"💸 Ты продаёшь: <b>{dish_name}</b> {QUALITY_NAMES[quality]}\n\n"
            f"Напиши цену в Пушин-Долларах (просто число в чат).\n"
            f"<i>Например: 150</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    # Отмена ввода цены
    if data[1] == "cancel" and data[2] == "price":
        selling_draft.pop(user_id, None)
        waiting_for_price[user_id] = False
        await callback.message.delete()
        await callback.answer("Отменено")
        return

# ---------- ОБРАБОТКА ВВОДА ЦЕНЫ ----------
@dp.message(lambda msg: msg.from_user.id in waiting_for_price and waiting_for_price[msg.from_user.id] is True)
async def handle_price_input(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    text = message.text.strip()
    
    if not text.isdigit():
        await message.answer("⚠️ Напиши просто число, без букв и символов. Например: 150")
        return
    
    price = int(text)
    
    if price <= 0:
        await message.answer("⚠️ Цена должна быть больше 0.")
        return
    
    if price > 999999:
        await message.answer("⚠️ Слишком много! Попробуй поменьше.")
        return
    
    draft = selling_draft.get(user_id)
    if not draft:
        waiting_for_price[user_id] = False
        await message.answer("⚠️ Что-то пошло не так. Попробуй ещё раз через инвентарь.")
        return
    
    dish_name = draft["dish_name"]
    quality = draft["quality"]
    
    # Проверяем, что блюдо ещё в инвентаре
    dishes = get_dishes(user_id)
    exists = any(d[0] == dish_name and d[1] == quality and d[2] > 0 for d in dishes)
    if not exists:
        waiting_for_price[user_id] = False
        selling_draft.pop(user_id, None)
        await message.answer("⚠️ Этого блюда больше нет в инвентаре.")
        return
    
    # Создаём запись о продаже
    sale_id = create_pending_sale(user_id, dish_name, quality, price)
    
    waiting_for_price[user_id] = False
    selling_draft.pop(user_id, None)
    
    # Отправляем тебе запрос
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"sale_accept_{sale_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"sale_reject_{sale_id}"),
        ],
    ])
    
    try:
        await bot.send_message(
            chat_id=ALLOWED_USER_IDS[0],
            text=(
                f"💸 <b>Запрос на продажу</b>\n\n"
                f"👤 От: Милашки\n"
                f"🍽️ Блюдо: <b>{dish_name}</b> {QUALITY_NAMES[quality]}\n"
                f"💰 Цена: <b>{price}</b> Пушин-Долларов\n\n"
                f"<i>Принять или отклонить?</i>"
            ),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await message.answer(
            f"✅ Запрос на продажу отправлен!\n\n"
            f"🍽️ {dish_name} {QUALITY_NAMES[quality]}\n"
            f"💰 Цена: {price} Пушин-Долларов\n\n"
            f"<i>Жди ответа.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Ошибка отправки запроса: {e}")
        await message.answer("⚠️ Не удалось отправить запрос. Попробуй позже.")

# ---------- CALLBACK'И ПРИНЯТИЯ/ОТКЛОНЕНИЯ (ТОЛЬКО ДЛЯ ТЕБЯ) ----------
@dp.callback_query(lambda c: c.data.startswith("sale_accept_") or c.data.startswith("sale_reject_"))
async def sale_decision(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Только ты можешь принимать/отклонять
    if user_id != ALLOWED_USER_IDS[0]:
        await callback.answer("Это только для админа", show_alert=True)
        return
    
    parts = callback.data.split("_")
    action = parts[1]  # accept / reject
    sale_id = int(parts[2])
    
    sale = get_pending_sale(sale_id)
    if not sale:
        await callback.answer("Запрос не найден", show_alert=True)
        return
    
    seller_id, dish_name, quality, price, status = sale
    
    if status != "pending":
        await callback.answer("Уже обработано", show_alert=True)
        return
    
    # Запоминаем решение и ждём комментарий
    waiting_for_comment[user_id] = {
        "sale_id": sale_id,
        "seller_id": seller_id,
        "dish_name": dish_name,
        "quality": quality,
        "price": price,
        "decision": action,
    }
    
    # Обновляем сообщение
    try:
        await callback.message.edit_text(
            f"💸 <b>Запрос на продажу</b>\n\n"
            f"👤 От: Милашки\n"
            f"🍽️ Блюдо: <b>{dish_name}</b> {QUALITY_NAMES[quality]}\n"
            f"💰 Цена: <b>{price}</b> Пушин-Долларов\n\n"
            f"📝 Решение: <b>{'Принять' if action == 'accept' else 'Отклонить'}</b>\n\n"
            f"<i>Напиши комментарий (или отправь «-», чтобы пропустить)</i>",
            parse_mode="HTML"
        )
    except:
        pass
    
    await callback.answer()

# ---------- ОБРАБОТКА КОММЕНТАРИЯ ОТ ТЕБЯ ----------
@dp.message(lambda msg: msg.from_user.id in waiting_for_comment)
async def handle_comment(message: types.Message):
    user_id = message.from_user.id
    
    if user_id != ALLOWED_USER_IDS[0]:
        return
    
    data = waiting_for_comment.pop(user_id)
    sale_id = data["sale_id"]
    seller_id = data["seller_id"]
    dish_name = data["dish_name"]
    quality = data["quality"]
    price = data["price"]
    decision = data["decision"]
    
    comment = message.text.strip()
    if comment == "-":
        comment = None
    
    if decision == "accept":
        # Проверяем, что блюдо ещё есть у неё
        dishes = get_dishes(seller_id)
        exists = any(d[0] == dish_name and d[1] == quality and d[2] > 0 for d in dishes)
        
        if not exists:
            await message.answer("⚠️ У неё уже нет этого блюда. Продажа отменена.")
            update_sale_status(sale_id, "cancelled")
            return
        
        # Убираем блюдо и начисляем Пушин-Доллары
        remove_dish(seller_id, dish_name, quality, 1)
        add_pusheen_dollars(seller_id, price)
        
        update_sale_status(sale_id, "accepted")
        
        # Сообщение ей
        comment_text = f"\n\n💬 Комментарий: <i>{comment}</i>" if comment else ""
        try:
            await bot.send_message(
                chat_id=seller_id,
                text=(
                    f"🎉 <b>Продажа одобрена!</b>\n\n"
                    f"🍽️ {dish_name} {QUALITY_NAMES[quality]}\n"
                    f"💰 Ты получила: <b>{price}</b> Пушин-Долларов{comment_text}\n\n"
                    f"Спасибо! 💖"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить ей: {e}")
        
        await message.answer(
            f"✅ Продажа одобрена!\n\n"
            f"🍽️ {dish_name}\n"
            f"💰 {price} Пушин-Долларов отправлено ей."
        )
    
    else:  # reject
        update_sale_status(sale_id, "rejected")
        
        comment_text = f"\n\n💬 Комментарий: <i>{comment}</i>" if comment else ""
        try:
            await bot.send_message(
                chat_id=seller_id,
                text=(
                    f"😔 <b>Продажа отклонена.</b>\n\n"
                    f"🍽️ {dish_name} {QUALITY_NAMES[quality]}\n"
                    f"💰 Цена: {price} Пушин-Долларов\n\n"
                    f"<i>Блюдо остаётся у тебя. Может, попробуешь позже?</i>{comment_text}"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить ей: {e}")
        
        await message.answer(
            f"❌ Продажа отклонена.\n\n"
            f"🍽️ {dish_name}\n"
            f"<i>Блюдо осталось у неё.</i>"
        )

# ---------- CALLBACK'И КОРМЛЕНИЯ ----------
@dp.callback_query(lambda c: c.data.startswith("feed_"))
async def feeding_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_allowed(user_id):
        await callback.answer("Не для тебя", show_alert=False)
        return
    
    data = callback.data.split("_")
    
    # Закрыть
    if data[1] == "close":
        await callback.message.delete()
        await callback.answer()
        return
    
    # Переключение карусели: feed_{index}
    if len(data) == 2:
        index = int(data[1])
        caption, keyboard, dish = build_feeding_carousel(index, user_id)
        
        if dish:
            img_path = get_dish_image_path(dish[0])
        else:
            img_path = None
        
        try:
            await callback.message.delete()
            if img_path:
                photo = FSInputFile(img_path)
                await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await callback.message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        except:
            pass
        await callback.answer()
        return
    
    # Кормление: feed_give_{index}
    if data[1] == "give":
        index = int(data[2])
        dishes = get_dishes(user_id)
        
        if index >= len(dishes):
            await callback.answer("Блюдо не найдено", show_alert=True)
            return
        
        dish_name, quality, qty = dishes[index]
        
        # Убираем блюдо из инвентаря
        remove_dish(user_id, dish_name, quality, 1)
        
        # Добавляем счастье
        happiness_bonus = FEED_HAPPINESS.get(quality, 0)
        current_happiness = get_pusheen_happiness(user_id)
        new_happiness = min(current_happiness + happiness_bonus, 100)
        
        # Обновляем счастье в БД
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("UPDATE users SET pusheen_happiness = ?, pusheen_reset = ? WHERE user_id = ?",
                    (new_happiness, today, user_id))
        conn.commit()
        conn.close()
        
        # Выбираем фразу по качеству
        phrase = random.choice(FEED_PHRASES.get(quality, ["🐱 Пушин поела"]))
        
        # Картинка Пушин по текущему настроению
        img_path = get_pusheen_image(new_happiness)
        
        # Формируем сообщение
        caption = (
            f"{phrase}\n\n"
            f"🍽️ {dish_name} {QUALITY_NAMES[quality]}"
        )
        
        try:
            await callback.message.delete()
        except:
            pass
        
        if os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=get_keyboard(check_and_reset(user_id), user_id)
            )
        else:
            await callback.message.answer(caption, reply_markup=get_keyboard(check_and_reset(user_id), user_id))
        
        # Уведомление тебе
        await notify_you(
            ALLOWED_USER_IDS[0],
            f"🍽️ Она покормила Пушин: {dish_name} {QUALITY_NAMES[quality]}\n"
            f"🐾 Настроение Пушин: {new_happiness}%"
        )
        
        await callback.answer("Пушин покормлена! 🐱")

# ---------- CALLBACK'И ГОТОВКИ ----------
@dp.callback_query(lambda c: c.data.startswith("cook_"))
async def cooking_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_allowed(user_id):
        await callback.answer("Не для тебя", show_alert=False)
        return
    
    data = callback.data.split("_")
    
    # Закрыть
    if data[1] == "close":
        if user_id in cooking_draft:
            del cooking_draft[user_id]
        await callback.message.delete()
        await callback.answer()
        return
    
    # Переключение карусели: cook_{category}_{index}
    if data[1] in ("main", "extra") and len(data) == 3:
        category = data[1]
        index = int(data[2])
        caption, keyboard, ing = build_cooking_carousel(category, index, user_id)
        
        if ing:
            img_path = get_ingredient_image_path(ing["id"])
        else:
            img_path = None
        
        try:
            await callback.message.delete()
            if img_path:
                photo = FSInputFile(img_path)
                await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await callback.message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        except:
            pass
        await callback.answer()
        return
    
    # Выбор ингредиента: cook_pick_{ing_id}_{category}
    if data[1] == "pick":
        ing_id = data[2]
        category = data[3]
        ing = ALL_INGREDIENTS.get(ing_id)
        
        if not ing:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        draft = cooking_draft.get(user_id, {"first": None, "second": None})
        
        if category == "main":
            # Первый ингредиент
            draft["first"] = ing_id
            draft["second"] = None
            cooking_draft[user_id] = draft
            
            # Показываем вторую карусель (extra)
            caption, keyboard, ing2 = build_cooking_carousel("extra", 0, user_id)
            
            # Добавляем контекст
            first_ing = ALL_INGREDIENTS[draft["first"]]
            prefix = f"✅ Выбран: {first_ing['emoji']} {first_ing['name']}\n\nТеперь выбери второй ингредиент:\n\n"
            
            if ing2:
                img_path = get_ingredient_image_path(ing2["id"])
            else:
                img_path = None
            
            try:
                await callback.message.delete()
                if img_path:
                    photo = FSInputFile(img_path)
                    await callback.message.answer_photo(photo=photo, caption=prefix + caption, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await callback.message.answer(prefix + caption, parse_mode="HTML", reply_markup=keyboard)
            except:
                pass
            await callback.answer()
            return
        
        else:
            # Второй ингредиент (extra)
            if draft.get("first") is None:
                await callback.answer("Сначала выбери первый ингредиент!", show_alert=True)
                return
            
            draft["second"] = ing_id
            cooking_draft[user_id] = draft
            
            first_ing = ALL_INGREDIENTS[draft["first"]]
            second_ing = ALL_INGREDIENTS[draft["second"]]
            
            # Ищем рецепт (проверяем оба порядка — для надёжности)
            key1 = (draft["first"], draft["second"])
            key2 = (draft["second"], draft["first"])
            recipe = RECIPES.get(key1) or RECIPES.get(key2)
            
            if not recipe:
                await callback.answer("Такое блюдо не получится!", show_alert=True)
                return
            
            caption = (
                f"🍳 <b>Готовим:</b>\n\n"
                f"{first_ing['emoji']} {first_ing['name']}\n"
                f"+ {second_ing['emoji']} {second_ing['name']}\n"
                f"= <b>{recipe['name']}</b>\n\n"
                f"Качество: {QUALITY_NAMES[recipe['quality']]}\n"
                f"⏳ Время готовки: {COOKING_TIME[recipe['quality']]} мин.\n\n"
                f"<i>Начинаем?</i>"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Готовить", callback_data="cook_start")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cook_close")],
            ])
            
            img_path = get_dish_image_path(recipe["name"])
            try:
                await callback.message.delete()
                if img_path:
                    photo = FSInputFile(img_path)
                    await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await callback.message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
            except:
                pass
            await callback.answer()
            return
    
    # Запуск готовки: cook_start
    if data[1] == "start":
        draft = cooking_draft.get(user_id)
        if not draft or not draft.get("first") or not draft.get("second"):
            await callback.answer("Ошибка: ингредиенты не выбраны", show_alert=True)
            return
        
        key1 = (draft["first"], draft["second"])
        key2 = (draft["second"], draft["first"])
        recipe = RECIPES.get(key1) or RECIPES.get(key2)
        if not recipe:
            await callback.answer("Ошибка рецепта", show_alert=True)
            return
        
        # Проверяем наличие ингредиентов
        inv = get_ingredients(user_id)
        if inv.get(draft["first"], 0) < 1 or inv.get(draft["second"], 0) < 1:
            await callback.answer("Не хватает ингредиентов!", show_alert=True)
            return
        
        # Списываем ингредиенты
        remove_ingredient(user_id, draft["first"], 1)
        remove_ingredient(user_id, draft["second"], 1)
        
        # Запускаем готовку
        cooking_time_sec = start_cooking(user_id, recipe["name"], recipe["quality"])
        
        # Убираем черновик
        del cooking_draft[user_id]
        
        await callback.message.delete()
        msg = await callback.message.answer(
            f"🍳 Готовится: <b>{recipe['name']}</b> {QUALITY_NAMES[recipe['quality']]}\n\n"
            f"⏳ Осталось: {cooking_time_sec // 60} мин.",
            parse_mode="HTML"
        )
        
        # Запускаем фоновую задачу обновления таймера
        task = asyncio.create_task(cooking_timer_update(msg, user_id, recipe["name"], recipe["quality"], cooking_time_sec))
        cooking_tasks[user_id] = task
        
        await callback.answer("Готовка началась! 🍳")

# ---------- ФОНОВАЯ ЗАДАЧА ТАЙМЕРА ----------
async def cooking_timer_update(msg, user_id, dish_name, quality, total_seconds):
    """Обновляет сообщение с таймером каждую минуту и завершает готовку"""
    try:
        remaining = total_seconds
        while remaining > 0:
            await asyncio.sleep(60)
            remaining -= 60
            if remaining > 0:
                minutes = (remaining + 59) // 60
                try:
                    await msg.edit_text(
                        f"🍳 Готовится: <b>{dish_name}</b> {QUALITY_NAMES[quality]}\n\n"
                        f"⏳ Осталось: {minutes} мин.",
                        parse_mode="HTML"
                    )
                except:
                    pass
        
        # Готово
        result = finish_cooking(user_id)
        if result:
            dish, q = result
            try:
                await msg.edit_text(
                    f"✅ <b>Готово!</b>\n\n"
                    f"🍽️ {dish} {QUALITY_NAMES[q]}\n\n"
                    f"Добавлено в инвентарь! 🎒",
                    parse_mode="HTML"
                )
            except:
                pass
    except asyncio.CancelledError:
        pass
    finally:
        if user_id in cooking_tasks:
            del cooking_tasks[user_id]

# ---------- CALLBACK'И МАГАЗИНА ----------
@dp.callback_query(lambda c: c.data.startswith("shop_"))
async def shop_carousel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_allowed(user_id):
        await callback.answer("Не для тебя", show_alert=False)
        return
    
    data = callback.data.split("_")
    
    if data[1] == "close":
        await callback.message.delete()
        await callback.answer()
        return
    
    category = data[1]  # main или extra
    index = int(data[2])
    
    caption, keyboard = build_shop_carousel(category, index, user_id)
    
    ingredients = MAIN_INGREDIENTS if category == "main" else EXTRA_INGREDIENTS
    ing = ingredients[index % len(ingredients)]
    img_path = get_ingredient_image_path(ing["id"])
    
    try:
        if img_path:
            photo = FSInputFile(img_path)
            await callback.message.delete()
            await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_caption(caption=caption, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        # Если сообщение без фото — редактируем текст
        try:
            await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=keyboard)
        except:
            pass
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_ingredient(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_allowed(user_id):
        await callback.answer("Не для тебя", show_alert=False)
        return
    
    # data: buy_{id}_{category}_{index}
    parts = callback.data.split("_")
    ing_id = parts[1]
    category = parts[2]
    index = int(parts[3])
    
    ing = ALL_INGREDIENTS.get(ing_id)
    if not ing:
        await callback.answer("Ингредиент не найден", show_alert=True)
        return
    
    # Проверяем остаток в инвентаре
    inv = get_ingredients(user_id)
    owned = inv.get(ing_id, 0)
    if owned >= 99:
        await callback.answer("У тебя уже 99 штук — больше не поместится!", show_alert=True)
        return
    
    # Проверяем баланс
    balance = get_pusheen_dollars(user_id)
    if balance < ing["price"]:
        await callback.answer(f"Не хватает Пушин-Долларов! У тебя {balance}, нужно {ing['price']}.", show_alert=True)
        return
    
    # Списываем и добавляем
    spend_pusheen_dollars(user_id, ing["price"])
    add_ingredient(user_id, ing_id, 1)
    
    new_balance = get_pusheen_dollars(user_id)
    
    await callback.answer(f"✅ Куплено! {ing['emoji']} {ing['name']} — {ing['price']} 💵", show_alert=False)
    
    # Обновляем карусель
    caption, keyboard = build_shop_carousel(category, index, user_id)
    img_path = get_ingredient_image_path(ing_id)
    
    caption += f"\n\n💵 Осталось: {new_balance} Пушин-Долларов"
    
    try:
        await callback.message.delete()
        if img_path:
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
    except:
        pass

@dp.message(Command("stop"))
async def stop_bot(message: types.Message):
    """Команда для выключения бота с уведомлением всех"""
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    # Отправляем прощание всем разрешённым пользователям
    for uid in ALLOWED_USER_IDS:
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "🌙 Бот уходит на перерыв.\n\n"
                    "Скоро вернусь и снова буду рядом. 🤍\n"
                    "А пока — помни, что я тебя люблю."
                )
            )
        except Exception as e:
            print(f"⚠️ Не удалось оповестить {uid}: {e}")
    
    print("🛑 Бот выключается по команде /stop")
    await bot.session.close()
    exit(0)

@dp.message(lambda msg: msg.text == "💰 Мой баланс")
async def balance(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    tokens = check_and_reset(user_id)
    
    # Проверяем, нажимала ли она баланс в прошлый раз
    was_last_action_balance = last_balance_click.get(user_id, False)
    
    if was_last_action_balance:
        # Второе нажатие подряд — показываем "из 100"
        text = f"💰 У тебя {tokens} токенов из 100.\n"
        if tokens < 10:
            text += "Но ты всегда можешь получить бесплатные нежности. 🔄"
        else:
            text += "Можешь тратить! 💖"
        last_balance_click[user_id] = False
    else:
        # Первое нажатие — показываем "из 50"
        text = f"💰 У тебя {tokens} токенов из 50.\n"
        if tokens < 10:
            text += "Но ты всегда можешь получить бесплатные нежности. 🔄"
        else:
            text += "Можешь тратить! 💖"
        last_balance_click[user_id] = True
    
    await message.answer(text, reply_markup=get_keyboard(tokens, user_id))

@dp.message(lambda msg: msg.text == "🍽️ Покормить Пушин")
async def feed_open(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    caption, keyboard, dish = build_feeding_carousel(0, user_id)
    
    if dish:
        img_path = get_dish_image_path(dish[0])
    else:
        img_path = None
    
    if img_path:
        photo = FSInputFile(img_path)
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "🍳 Готовка")
async def cooking_open(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    # Проверяем, не готовится ли уже что-то
    active = get_active_cooking(user_id)
    if active:
        dish_name, quality, finish_time = active
        left = int(finish_time - time.time())
        if left > 0:
            minutes = (left + 59) // 60
            await message.answer(
                f"🍳 У тебя уже готовится <b>{dish_name}</b> {QUALITY_NAMES[quality]}.\n\n"
                f"⏳ Осталось примерно: {minutes} мин.\n\n"
                f"<i>Подожди, пока закончится, или проверь позже.</i>",
                parse_mode="HTML",
                reply_markup=get_keyboard(check_and_reset(user_id), user_id)
            )
            return
        else:
            # Готовка уже завершилась — завершаем
            result = finish_cooking(user_id)
            if result:
                dish_name, quality = result
                await message.answer(
                    f"✅ <b>Готово!</b> {dish_name} {QUALITY_NAMES[quality]} добавлено в инвентарь!\n\n"
                    f"🍳 Что будем готовить теперь?",
                    parse_mode="HTML",
                    reply_markup=get_keyboard(check_and_reset(user_id), user_id)
                )
    
    # Начинаем новую готовку: показываем первую карусель
    # Инициализируем "черновик" готовки в памяти
    cooking_draft[user_id] = {"first": None, "second": None}
    
    caption, keyboard, ing = build_cooking_carousel("main", 0, user_id)
    if ing:
        img_path = get_ingredient_image_path(ing["id"])
        if img_path:
            photo = FSInputFile(img_path)
            await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "🎒 Инвентарь")
async def inventory_open(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    text = build_inventory_text(user_id)
    
    # Инлайн-кнопка «Продать блюдо», если есть блюда
    dishes = get_dishes(user_id)
    if dishes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Продать блюдо", callback_data="sell_0")],
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=get_keyboard(check_and_reset(user_id), user_id))

@dp.message(lambda msg: msg.text == "🛒 Магазин")
async def shop_open(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    caption, keyboard = build_shop_carousel("main", 0, user_id)
    img_path = get_ingredient_image_path(MAIN_INGREDIENTS[0]["id"])
    
    if img_path:
        photo = FSInputFile(img_path)
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "💵 Мой баланс Пушин-Долларов")
async def pd_balance(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    pd = get_pusheen_dollars(user_id)
    
    await message.answer(
        f"💵 У тебя {pd} Пушин-Долларов.\n\n"
        f"Каждый день ты получаешь ещё 100. Трать их в магазине на ингредиенты для Пушин! 🐾",
        reply_markup=get_keyboard(check_and_reset(user_id), user_id)
    )

@dp.message(lambda msg: msg.text == "📊 Мой прогресс")
async def progress(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    percent, seen_msgs, total_msgs, seen_imgs, total_imgs = get_progress(user_id)
    
    # Строим прогресс-бар
    bar_length = 20
    filled = int((percent / 100) * bar_length)
    bar = "▓" * filled + "░" * (bar_length - filled)
    
    # Сообщение с прогрессом
    text = (
        f"📊 Твой прогресс в нашей коллекции:\n\n"
        f"{bar} {percent}%\n\n"
        f"💬 Фразы: {seen_msgs} из {total_msgs}\n"
        f"🖼️ Картинки: {seen_imgs} из {total_imgs}\n\n"
    )
    
    # Мотивация в зависимости от процента
    if percent == 100:
        text += "🏆 Ты видела ВСЁ! Ты — настоящий коллекционер нашей истории. Я горжусь тобой!"
    elif percent >= 75:
        text += "🌟 Ты почти всё собрала! Осталось совсем чуть-чуть."
    elif percent >= 50:
        text += "💖 Половина пути пройдена! Ты отлично справляешься."
    elif percent >= 25:
        text += "✨ Ты уже много увидела. Но впереди ещё столько интересного!"
    else:
        text += "🌱 Только начало пути. Впереди — целая коллекция наших моментов."
    
    await message.answer(text, reply_markup=get_keyboard(check_and_reset(user_id), user_id))

@dp.message(lambda msg: msg.text == "🐱 Погладить Пушин")
async def pet_pusheen(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    # Добавляем счастье
    new_happiness = add_pusheen_happiness(user_id)
    
    # Выбираем картинку и настроение
    img_path = get_pusheen_image(new_happiness)
    mood_text = get_pusheen_mood(new_happiness)
    
    # Выбираем фразу Пушин
    pusheen_phrase = random.choice(PUSHEEN_PHRASES)
    
    # Записываем просмотр фразы Пушин
    mark_message_seen(user_id, pusheen_phrase)
    
    try:
        photo = FSInputFile(img_path)
        
        # Если 100% — особое сообщение
        if new_happiness >= 100:
            caption = (
                f"{mood_text}\n\n"
                "🎉✨ Пушин самая счастливая кошка на свете! ✨🎉\n\n"
                "Спасибо тебе! 💖"
            )
        else:
            # Обычное поглаживание
            caption = f"{mood_text}\n\n{pusheen_phrase}"
        
        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=get_keyboard_for_user(user_id)
        )
    except Exception as e:
        print(f"⚠️ Ошибка с Пушин: {e}")
        await message.answer(
            "🐱 Пушин куда-то убежала... Попробуй ещё раз!",
            reply_markup=get_keyboard_for_user(user_id)
        )

@dp.message(lambda msg: msg.text == "💞 Сколько мы вместе?")
async def days_together(message: types.Message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    
    last_balance_click[user_id] = False
    
    # ---------- ПЕРВЫЙ ОТЧЁТ: с 20.01.2025 ----------
    d1, w1, m1, h1, min1, s1, th1, tm1 = get_time_since(RELATIONSHIP_START)
    
    # ---------- ВТОРОЙ ОТЧЁТ: с 31.10.2025 ----------
    d2, w2, m2, h2, min2, s2, th2, tm2 = get_time_since(OFFICIAL_START)
    
    text = (
        "💞 Мы вместе уже:\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"📅 {d1} дней • {w1} недель • {m1} месяцев\n"
        f"⏰ Точнее: {d1} д. {h1} ч. {min1} мин. {s1} сек.\n"
        f"🕐 Это {th1} часов или {tm1} минут\n\n"
        "💍 Официально мы пара:\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"📅 {d2} дней • {w2} недель • {m2} месяцев\n"
        f"⏰ Точнее: {d2} д. {h2} ч. {min2} мин. {s2} сек.\n"
        f"🕐 Это {th2} часов или {tm2} минут\n\n"
    )
    
    # Поздравления для первой даты
    if d1 == 100:
        text += "🎉 СТО ДНЕЙ ВМЕСТЕ! 💖\n"
    elif d1 == 365:
        text += "🎉 ЦЕЛЫЙ ГОД ВМЕСТЕ! 🥂\n"
    elif d1 % 100 == 0 and d1 > 0:
        text += f"🎉 {d1} дней! Круглая дата! 💝\n"
    elif d1 % 50 == 0 and d1 > 0:
        text += f"🎉 {d1} дней вместе! 💕\n"
    
    # Поздравления для второй даты
    if d2 == 100:
        text += "💍 СТО ДНЕЙ КАК МЫ ПАРА! 💖\n"
    elif d2 == 365:
        text += "💍 ГОД КАК МЫ ПАРА! 🥂\n"
    elif d2 % 100 == 0 and d2 > 0:
        text += f"💍 {d2} дней как мы пара! 💝\n"
    elif d2 % 50 == 0 and d2 > 0:
        text += f"💍 {d2} дней как мы пара! 💕\n"
    
    text += "\nКаждый день с тобой — это подарок. 🤍"
    
    await message.answer(text, reply_markup=get_keyboard(check_and_reset(user_id), user_id))

# ---------- ОДНОРАЗОВАЯ ФУНКЦИЯ: отметить все текущие фразы как просмотренные ----------
def mark_all_current_as_seen():
    """Отмечает ВСЕ текущие фразы как просмотренные (запускать ОДИН раз)"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        all_messages = MESSAGES + KISS_REPLIES + HUG_REPLIES + PUSHEEN_PHRASES
        for user_id in ALLOWED_USER_IDS:
            for msg in all_messages:
                key = msg[:500]
                cur.execute("INSERT OR IGNORE INTO seen_messages (user_id, message_hash) VALUES (?, ?)", (user_id, key))
        conn.commit()
        print(f"✅ Все {len(all_messages)} фраз отмечены как просмотренные для {len(ALLOWED_USER_IDS)} пользователей")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    conn.close()

# ---------- ОЧИСТКА СТАРЫХ ХЕШЕЙ ----------
def cleanup_broken_hashes():
    """Удаляет старые записи с нестабильными хешами (одноразовая очистка)"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        all_messages = MESSAGES + KISS_REPLIES + HUG_REPLIES + PUSHEEN_PHRASES
        existing_keys = set(m[:500] for m in all_messages)
        
        cur.execute("SELECT rowid, message_hash FROM seen_messages")
        rows = cur.fetchall()
        deleted = 0
        for rowid, msg_hash in rows:
            if msg_hash not in existing_keys:
                cur.execute("DELETE FROM seen_messages WHERE rowid = ?", (rowid,))
                deleted += 1
        
        conn.commit()
        if deleted > 0:
            print(f"🧹 Удалено {deleted} устаревших записей из seen_messages")
        else:
            print("🧹 Устаревших записей не найдено")
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")
    conn.close()

# ---------- ВОССТАНОВЛЕНИЕ ТАЙМЕРОВ ПОСЛЕ ПЕРЕЗАПУСКА ----------
async def restore_cooking_timers():
    """Проверяет все активные готовки и восстанавливает таймеры"""
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, dish_name, quality, finish_time FROM active_cooking")
    rows = cur.fetchall()
    conn.close()
    
    for user_id, dish_name, quality, finish_time in rows:
        left = int(finish_time - time.time())
        if left <= 0:
            # Уже готово — завершаем
            result = finish_cooking(user_id)
            if result:
                try:
                    await bot.send_message(
                        user_id,
                        f"✅ <b>Пока тебя не было, всё приготовилось!</b>\n\n"
                        f"🍽️ {dish_name} {QUALITY_NAMES[quality]}\n\n"
                        f"Добавлено в инвентарь! 🎒",
                        parse_mode="HTML"
                    )
                except:
                    pass
        else:
            # Ещё готовится — восстанавливаем таймер
            msg = await bot.send_message(
                user_id,
                f"🍳 Готовится: <b>{dish_name}</b> {QUALITY_NAMES[quality]}\n\n"
                f"⏳ Осталось: {(left + 59) // 60} мин.",
                parse_mode="HTML"
            )
            task = asyncio.create_task(cooking_timer_update(msg, user_id, dish_name, quality, left))
            cooking_tasks[user_id] = task

# ---------- ЗАПУСК ----------
async def main():
    init_db()
    
    # 👇 ОДНОРАЗОВО: отметить все текущие фразы как просмотренные
    #mark_all_current_as_seen()
    
    print("✅ Бот с бесплатными утешениями и картинками запущен!")
    
    # Восстанавливаем таймеры готовки
    await restore_cooking_timers()
    
    # 👇 Оповещаем всех, что бот включился
    await notify_all_started()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import html
import json
import os
import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand

BOT_TOKEN = "8826988522:AAGz9EZjjhcEhjjlOCSKEBjb6cPRc6QRw2U"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

messages_cache = {}
connections_cache = {}

# Файлы для сохранения данных
RP_FILE = "rp_commands.json"
STATS_FILE = "chat_stats.json"

# Базовые команды в фембойском/няшном стиле (с рандомными вариантами)
RP_ACTIONS = {
    "обнять": [
        [
            "🌸",
            "крепко-крепко обнял(а)",
            "и уткнулся(ась) носиком в плечо (づ｡◕‿‿◕｡)づ",
        ],
        ["🎀", "тепло обнял(а)", "и не хочет отпускать~ (⁄ ⁄•⁄ω⁄•⁄ ⁄)"],
        ["💞", "заключил(а) в нежные объятия", "прижавшись всем телом uwu"],
    ],
    "поцеловать": [
        ["💋", "нежно поцеловал(а)", "и смущённо отвёл(а) взгляд 👉👈"],
        [
            "💖",
            "сладко поцеловал(а) в губки",
            "покраснев до кончиков ушек (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)",
        ],
    ],
    "чмок": [
        ["😚", "мило чмокнул(а) в щёчку", "оставив блестящий след~ ✨"],
        ["🍓", "быстро чмокнул(а) в носик", "и тихонько хихикнул(а) :3"],
    ],
    "укусить": [
        ["🐾", "игриво укусил(а)", "за плечико rawr~ (>_<)"],
        ["😈", "легонько цапнул(а) острыми зубками", "и облизнулся(ась) :3"],
    ],
    "кусь": [
        ["🦷", "сделал(а) нежный кусь", "за ушко и мило засопел(а)~ 🌸"],
        ["🐱", "по-кошачьи кусьнул(а)", "за пальчик ня~ (=^･ω･^=)"],
        ["🐾", "сделал(а) внезапный кусь", "виляя хвостиком uwu"],
    ],
    "погладить": [
        [
            "🌷",
            "ласково погладил(а) по головке",
            "перебирая мягкие волосы ( ´ ∀ `)ノ～ ♡",
        ],
        ["🐾", "нежно почесал(а) за ушком", "вызывая довольное мурчание~ uwu"],
    ],
    "ударить": [
        ["🎀", "обиженно стукнул(а) мягкой лапкой", "надув щёчки ( ` ω ´ )"],
        ["💥", "плюхнул(а) пушистой розовой подушкой", "прямо по лицу! >_<"],
        ["🐾", "провёл(а) серию сокрушительных кошачьих лапок по", "ня-пауч! 🥊"],
    ],
    "шлёп": [
        ["🍑", "звонко и игриво шлёпнул(а)", "по попке~ (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)"],
        ["👋", "хитро шлёпнул(а)", "и спрятал(а) ручки за спину :3"],
    ],
    "пнуть": [
        ["🧦", "слегка пнул(а) ножкой в полосатом чулочке", "под столом 👉👈"],
        ["👟", "дал(а) милого волшебного пенделя", "для ускорения~ ✨"],
    ],
    "похвалить": [
        ["🌟", "похвалил(а)", "и назвал(а) самым сладким котиком на свете (◕‿◕)♡"],
        ["🍬", "восхитился(ась) успехами", "и подарил(а) блестящую наклеечку~ ✨"],
    ],
    "пожать руку": [
        ["🤝", "аккуратно пожал(а) ручку", "своими мягкими лапками uwu"],
        ["🤍", "переплёл(а) пальчики с", "и мило улыбнулся(ась) (´• ω •`)"],
    ],
    "покормить": [
        [
            "🍓",
            "покормил(а) клубничкой с ложечки",
            "сказав «открывай ротик, ам~» ( ˘▽˘)っ♨",
        ],
        ["🧋", "угостил(а) сладким клубничным бабл-ти", "и вкусняшкой~ 🧁"],
        ["🍰", "поделился(ась) нежным тортиком с", "uwu 💕"],
    ],
    "щекотать": [
        ["🪶", "защекотал(а) до милого писка", "и звонкого смеха~ (≧◡≦)"],
        ["🐾", "устроил(а) пушистую атаку щекоткой на", "ня~ :3"],
    ],
    "лизнуть": [
        ["👅", "внезапно лизнул(а) прямо в носик", "как маленький котёнок (=^･ｪ･^=)"],
        ["🍦", "сладко лизнул(а) в щёчку", "и жутко засмущался(ась) (⁄ ⁄•⁄ω⁄•⁄ ⁄)"],
    ],
    "выстрелить": [
        [
            "💘",
            "пустил(а) розовую стрелу Амура прямо в сердечко",
            "пиу-пиу~ ( ´ ▽ ` )b",
        ],
        ["🔫", "обрызгал(а) из милого водяного пистолетика", "хихикая >w<"],
    ],
    "мур": [
        ["🐱", "прижался(ась) к", "и сладко замурчал(а) на ушко мур-мур~ (=^･ω･^=)"],
        ["🐾", "потёрся(ась) носиком о", "тихонько мурлыкая uwu"],
    ],
    "прижаться": [
        ["🥺", "смущённо прижался(ась) к", "ища тепла и ласки 👉👈"],
        ["🎀", "уютно свернулся(ась) калачиком рядом с", "(づ◡﹏◡)づ"],
    ],
    "монстр": [
        [
            "🥫",
            "протянул(а) холодную баночку белого Monster Energy для",
            "и мило подмигнул(а) uwu 🤍",
        ],
        [
            "⚡",
            "поделился(ась) глоточком розового Monster Pipeline Punch с",
            "для заряда бодрости~ 🌸",
        ],
    ],
    "наручки": [
        ["🥺", "тянет лапки вверх и просится на ручки к", "ну возьмиии~ 👉👈"],
        [
            "🐾",
            "запрыгнул(а) прямо на ручки к",
            "и довольно болтает ножками в чулочках (◕‿◕)♡",
        ],
    ],
    "чокер": [
        [
            "🔔",
            "аккуратно застегнул(а) бархатный чокер с бубенчиком на шейке",
            "дзынь-дзынь~ 🎀",
        ],
        [
            "🖤",
            "поправил(а) милый чокер с сердечком на",
            "и восхищённо улыбнулся(ась) uwu",
        ],
    ],
    "смутиться": [
        [
            "😳",
            "закрыл(а) раскрасневшееся личико рукавами оверсайз-худи из-за",
            "(⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)",
        ],
        ["👉👈", "сильно засмущался(ась) перед", "и спрятал(а) глазки под чёлкой~ 🌸"],
    ],
    "обидеться": [
        [
            "💢",
            "надул(а) щёчки, отвернулся(ась) от",
            "и тихонько фыркнул(а) ( ` ω ´ )💨",
        ],
        ["🥺", "обиженно сложил(а) лапки на груди и ждёт извинений от", "хмпф!"],
    ],
    "одеялко": [
        [
            "🛌",
            "укутал(а) в тёплое пушистое одеялко",
            "как маленькую шаурму и лёг(ла) рядышком~ 🌸",
        ],
        ["☁️", "накрыл(а) мягким пледиком", "чтобы точно не замёрз(ла) uwu 💕"],
    ],
    "хвостик": [
        ["🐾", "радостно завилял(а) пушистым хвостиком при виде", "ура-ура~ ✨"],
        ["🦊", "обвил(а) пушистым хвостиком вокруг", "нежно прижимая к себе :3"],
    ],
}

# Английские алиасы для команд со слэшем (/hug, /kiss и т.д.)
SLASH_RP_ALIASES = {
    "hug": "обнять",
    "kiss": "поцеловать",
    "chmok": "чмок",
    "bite": "укусить",
    "kus": "кусь",
    "pat": "погладить",
    "slap": "ударить",
    "spank": "шлёп",
    "kick": "пнуть",
    "praise": "похвалить",
    "handshake": "пожать руку",
    "feed": "покормить",
    "tickle": "щекотать",
    "lick": "лизнуть",
    "shoot": "выстрелить",
    "purr": "мур",
    "cuddle": "прижаться",
    "monster": "монстр",
    "upp": "наручки",
    "choker": "чокер",
    "blush": "смутиться",
    "pout": "обидеться",
    "blanket": "одеялко",
    "tail": "хвостик",
}


# ==================== РАБОТА С ФАЙЛАМИ И БАЗОЙ ====================


def save_rp_commands(commands_dict: dict):
    with open(RP_FILE, "w", encoding="utf-8") as f:
        json.dump(commands_dict, f, ensure_ascii=False, indent=4)


def load_rp_commands() -> dict:
    data = RP_ACTIONS.copy()
    if os.path.exists(RP_FILE):
        try:
            with open(RP_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    if k not in RP_ACTIONS:
                        data[k] = v
        except Exception as err:
            print(f"[!] Ошибка чтения {RP_FILE}: {err}")
    save_rp_commands(data)
    return data


def load_stats() -> dict:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            print(f"[!] Ошибка чтения {STATS_FILE}: {err}")
    return {}


def save_stats(stats_dict: dict):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats_dict, f, ensure_ascii=False, indent=4)


RP_COMMANDS = load_rp_commands()
CHAT_STATS = load_stats()


def get_chat_stat(chat_id: int, partner_name: str = "Собеседник") -> dict:
    cid = str(chat_id)
    if cid not in CHAT_STATS:
        CHAT_STATS[cid] = {
            "partner_name": partner_name,
            "messages": 0,
            "rp_total": 0,
            "rp_breakdown": {},
            "deleted_caught": 0,
            "edited_caught": 0,
            "married_since": None,
        }
    elif partner_name and partner_name != "Собеседник":
        CHAT_STATS[cid]["partner_name"] = partner_name
    return CHAT_STATS[cid]


def format_rp_action(action_data) -> tuple[str, str, str]:
    if isinstance(action_data, list) and action_data:
        chosen = random.choice(action_data)
        if isinstance(chosen, (list, tuple)) and len(chosen) == 3:
            return chosen[0], chosen[1], chosen[2]
        return "🎀", str(chosen), "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"
    return "🎀", str(action_data), "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"


def uwuify_text(text: str) -> str:
    """Переводит обычный текст на няшно-картавый uwu-язык."""
    replacements = [
        ("р", "в"),
        ("л", "в"),
        ("Р", "В"),
        ("Л", "В"),
        ("на", "ня"),
        ("На", "Ня"),
        ("но", "ньо"),
        ("Но", "Ньо"),
        ("привет", "пвиветик"),
        ("Привет", "Пвиветик"),
    ]
    res = text
    for old, new in replacements:
        res = res.replace(old, new)
    kaomojis = ["uwu~", "(⁄ ⁄•⁄ω⁄•⁄ ⁄)", "👉👈", ":3", "nya~ 🐾", "(◕‿◕)♡"]
    return f"{res} {random.choice(kaomojis)}"


def format_duration(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days > 0:
        parts.append(f"{days} дн.")
    if hours > 0 or days > 0:
        parts.append(f"{hours} ч.")
    parts.append(f"{minutes} мин.")
    return " ".join(parts)


async def get_owner_chat_id(business_connection_id: str) -> int:
    if business_connection_id not in connections_cache:
        conn = await bot.get_business_connection(business_connection_id)
        connections_cache[business_connection_id] = conn.user_chat_id
    return connections_cache[business_connection_id]


async def send_business_reply(
    chat_id: int, text: str, conn_id: str, chat_name: str = ""
):
    """Безопасная отправка сообщения в бизнес-чат с защитой от ошибок."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            business_connection_id=conn_id,
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "BUSINESS_PEER_INVALID" in str(e):
            print(f"[!] Собеседник ({chat_name}) ещё ничего не написал в чат!")
        else:
            print(f"[!] Ошибка Telegram при отправке в чат: {e}")


async def setup_bot_commands():
    commands = [
        BotCommand(command="start", description="🌸 Запустить бота и краткая инфа"),
        BotCommand(command="help", description="🎀 Полная шпаргалка по всем командам"),
        BotCommand(command="rp", description="🐾 Список всех РП-команд"),
        BotCommand(command="add_rp", description="➕ Добавить свою РП-команду"),
        BotCommand(command="del_rp", description="🗑 Удалить РП-команду"),
    ]
    await bot.set_my_commands(commands)


# ==================== КОМАНДЫ В ЛИЧКЕ С САМИМ БОТОМ ====================


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "🌸 <b>Приветик! Няшный бизнес-бот активен и готов к работе~ (◕‿◕)♡</b>\n\n"
        "🎀 <b>Меню управления ботом:</b>\n"
        "• /help — полный список мини-игр, браков и команд\n"
        "• /rp — посмотреть все доступные РП-действия\n"
        "• /add_rp — создать свою собственную РП-команду\n"
        "• /del_rp — удалить ненужную команду\n\n"
        "<i>🐾 Сюда автоматически прилетают все удалённые и изменённые сообщения твоих собеседников!</i>",
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🎀 <b>Полная инструкция по боту (⁄ ⁄•⁄ω⁄•⁄ ⁄):</b>\n\n"
        "<b>1. 🎭 РП-команды (в личке с друзьями):</b>\n"
        "Пиши с точкой, со слэшем или просто словом: <code>.обнять</code>, <code>.монстр</code>, "
        "<code>.наручки</code>, <code>.чокер</code>, <code>.кусь за ушко</code> (полный список: /rp).\n\n"
        "<b>2. 🎲 Мини-игры и рандомайзеры:</b>\n"
        "• <code>.инфа [текст]</code> или <code>.шар [текст]</code> — вероятность события в %\n"
        "• <code>.шип</code> или <code>.любовь</code> — ваша совместимость с собеседником\n"
        "• <code>.милота</code> или <code>.фембойтест</code> — тест на % няшности\n"
        "• <code>.выбор А или Б</code> — поможет выбрать между двумя вариантами\n"
        "• <code>.uwu</code> (ответом на сообщение) — переведёт текст друга на няшный язык\n\n"
        "<b>3. 💍 Отношения и статистика чата:</b>\n"
        "• <code>.брак</code> — пожениться с собеседником в личке\n"
        "• <code>.мы</code> — сколько времени вы уже в браке\n"
        "• <code>.развод</code> — расторгнуть брак 💔\n"
        "• <code>.стата</code> — статистика сообщений и обнимашек в чате\n"
        "• <code>.инфо</code> — карточка собеседника (ID, юзернейм, сколько удалёнок поймано)\n\n"
        "<b>4. ➕ Свои РП-команды без кода:</b>\n"
        "Добавить: <code>/add_rp боньк = сделал(а) мягкий боньк 🐾</code>\n"
        "Удалить: <code>/del_rp боньк</code>",
        parse_mode="HTML",
    )


@dp.message(Command("rp"))
async def cmd_rp_list(message: types.Message):
    if not RP_COMMANDS:
        await message.answer(
            "Список РП-команд пока пуст 🥺 Добавь первую через /add_rp!"
        )
        return

    reverse_aliases = {v: f" (<code>/{k}</code>)" for k, v in SLASH_RP_ALIASES.items()}

    lines = []
    for cmd, act_data in RP_COMMANDS.items():
        emoji, verb, _ = format_rp_action(act_data)
        alias_str = reverse_aliases.get(cmd, "")
        lines.append(
            f"🌸 {emoji} <code>.{cmd}</code>{alias_str} — <i>{html.escape(verb)}~</i>"
        )

    text = (
        "🎀 <b>Няшный список РП-команд (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄):</b>\n\n"
        + "\n".join(lines)
        + "\n\n➕ <b>Добавить свою команду:</b>\n<code>/add_rp слово = действие</code> ✨"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("add_rp"))
async def cmd_add_rp(message: types.Message):
    raw = message.text.partition(" ")[2].strip()
    if "=" not in raw:
        await message.answer(
            "🎀 <b>Чтобы добавить команду, напиши её через знак <code>=</code>:</b>\n\n"
            "Пример:\n<code>/add_rp боньк = сделал(а) мягкий боньк по головке 🐾</code>",
            parse_mode="HTML",
        )
        return

    cmd_name, action_text = raw.split("=", maxsplit=1)
    cmd_name = cmd_name.strip().lower().lstrip(".!/")
    action_text = action_text.strip()

    if not cmd_name or not action_text:
        await message.answer("🥺 Укажи и название команды, и текст действия 👉👈")
        return

    RP_COMMANDS[cmd_name] = [["🎀", action_text, "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"]]
    save_rp_commands(RP_COMMANDS)

    await message.answer(
        f"🌸 <b>Ура! Новая РП-команда сохранена~ (◕‿◕)♡</b>\n\n"
        f"Теперь в чатах можно писать <code>.{html.escape(cmd_name)}</code>:\n"
        f"🎀 <b>Ты</b> {html.escape(action_text)} <b>Собеседника</b> (⁄ ⁄•⁄ω⁄•⁄ ⁄)~",
        parse_mode="HTML",
    )


@dp.message(Command("del_rp"))
async def cmd_del_rp(message: types.Message):
    cmd_name = message.text.partition(" ")[2].strip().lower().lstrip(".!/")
    if not cmd_name:
        await message.answer(
            "🎀 Укажи название команды, которую нужно удалить.\n"
            "Пример: <code>/del_rp кусь</code>",
            parse_mode="HTML",
        )
        return

    if cmd_name in RP_COMMANDS:
        del RP_COMMANDS[cmd_name]
        save_rp_commands(RP_COMMANDS)
        await message.answer(
            f"🗑 Команда <code>.{html.escape(cmd_name)}</code> удалена из списка~ 🌸",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"🥺 Команды <code>{html.escape(cmd_name)}</code> нет в списке 👉👈",
            parse_mode="HTML",
        )


# ==================== РАБОТА В ЛИЧНЫХ ЧАТАХ (BUSINESS) ====================


@dp.business_message()
async def handle_business_message(message: types.Message):
    conn_id = message.business_connection_id
    owner_chat_id = await get_owner_chat_id(conn_id)

    partner_title = message.chat.full_name or "Милашка"
    chat_stat = get_chat_stat(message.chat.id, partner_title)
    chat_stat["messages"] += 1
    save_stats(CHAT_STATS)

    if message.text:
        text_stripped = message.text.strip()
        lower_stripped = text_stripped.lower()

        # Определяем имена участников для интерактивных команд
        sender_name = html.escape(message.from_user.full_name)
        if message.reply_to_message and message.reply_to_message.from_user:
            target_name = html.escape(message.reply_to_message.from_user.full_name)
        elif message.from_user.id == owner_chat_id:
            target_name = html.escape(partner_title)
        else:
            target_name = "тебя"

        # 1. Управление пользовательскими командами прямо из лички (.дерп / .удрп)
        if message.from_user.id == owner_chat_id and lower_stripped.startswith(
            (".дерп ", "/add_rp ")
        ):
            raw = text_stripped.partition(" ")[2].strip()
            if "=" in raw:
                cmd_name, action_text = raw.split("=", maxsplit=1)
                cmd_name = cmd_name.strip().lower().lstrip(".!/")
                action_text = action_text.strip()
                if cmd_name and action_text:
                    RP_COMMANDS[cmd_name] = [["🎀", action_text, "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"]]
                    save_rp_commands(RP_COMMANDS)
                    await bot.send_message(
                        owner_chat_id,
                        f"🌸 Команда <code>.{html.escape(cmd_name)}</code> добавлена~!",
                        parse_mode="HTML",
                    )
            return

        if message.from_user.id == owner_chat_id and lower_stripped.startswith(
            (".удрп ", "/del_rp ")
        ):
            cmd_name = text_stripped.partition(" ")[2].strip().lower().lstrip(".!/")
            if cmd_name in RP_COMMANDS:
                del RP_COMMANDS[cmd_name]
                save_rp_commands(RP_COMMANDS)
                await bot.send_message(
                    owner_chat_id,
                    f"🗑 Команда <code>.{html.escape(cmd_name)}</code> удалена~!",
                    parse_mode="HTML",
                )
            return

        # 2. МИНИ-ИГРЫ И СТАТИСТИКА (срабатывают с точкой, слэшем или !)
        if text_stripped.startswith((".", "/", "!")):
            cmd_parts = text_stripped[1:].strip().split(maxsplit=1)
            cmd_word = cmd_parts[0].lower() if cmd_parts else ""
            cmd_arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

            # --- .инфа / .шар ---
            if cmd_word in ("инфа", "шар", "infa", "ball"):
                if not cmd_arg:
                    await send_business_reply(
                        message.chat.id,
                        "🔮 Напиши вопрос после команды, например: <code>.инфа мы пойдём гулять</code> 👉👈",
                        conn_id,
                        partner_title,
                    )
                    return
                pct = random.randint(0, 100)
                verdict = (
                    "Ура-ура, почти наверняка! (◕‿◕)♡"
                    if pct >= 50
                    else "Кажется, шансов маловато... 🥺👉👈"
                )
                await send_business_reply(
                    message.chat.id,
                    f"🔮 <b>Шар судьбы мурлычет:</b>\n"
                    f"Вероятность того, что <i>«{html.escape(cmd_arg)}»</i> — <b>{pct}%</b>!\n"
                    f"╰┈➤ {verdict}",
                    conn_id,
                    partner_title,
                )
                return

            # --- .шип / .любовь ---
            if cmd_word in ("шип", "любовь", "ship", "love"):
                pct = random.randint(0, 100)
                if pct >= 85:
                    comment = "Идеальная парочка котиков! Срочно обниматься~ 🐾💞"
                elif pct >= 50:
                    comment = "Очень милый вайб, у вас всё получится~ (⁄ ⁄•⁄ω⁄•⁄ ⁄)"
                elif pct >= 20:
                    comment = "Нужно больше вкусняшек и белых Монстров для укрепления связи! 🥫🌸"
                else:
                    comment = "Кто-то сегодня вредничает и кусается! >_<"
                await send_business_reply(
                    message.chat.id,
                    f"💘 <b>Проверка любви:</b>\n"
                    f"Совместимость <b>{sender_name}</b> и <b>{html.escape(partner_title)}</b> сегодня — <b>{pct}%</b>!\n"
                    f"╰┈➤ <i>{comment}</i>",
                    conn_id,
                    partner_title,
                )
                return

            # --- .милота / .фембойтест ---
            if cmd_word in ("милота", "фембойтест", "няшность", "cute", "femboy"):
                tested_user = (
                    html.escape(message.reply_to_message.from_user.full_name)
                    if (message.reply_to_message and message.reply_to_message.from_user)
                    else sender_name
                )
                pct = random.randint(0, 100)
                if pct <= 20:
                    rank = "Суровый гигачад, ни одного чулочка в шкафу 🗿"
                elif pct <= 55:
                    rank = "Начинающий котик, уже засматривается на розовые оверсайз-худи 👉👈"
                elif pct <= 85:
                    rank = (
                        "Сертифицированная милашка, кошачьи ушки сидят как влитые! 🐾🌸"
                    )
                else:
                    rank = "Ультра-фембойчик 1000 lvl в полосатых чулочках и с баночкой белого Монстра! 🧦🥫💖"
                await send_business_reply(
                    message.chat.id,
                    f"🌸 <b>Сканер милоты завершил проверку!</b>\n"
                    f"Уровень няшности <b>{tested_user}</b> — <b>{pct}%</b>!\n"
                    f"╰┈➤ 🎀 <i>Вердикт: {rank}</i>",
                    conn_id,
                    partner_title,
                )
                return

            # --- .выбор ---
            if cmd_word in ("выбор", "choose", "или"):
                if " или " not in cmd_arg.lower():
                    await send_business_reply(
                        message.chat.id,
                        "🎀 Напиши два варианта через «или», например:\n<code>.выбор пойти спать или пить монстр</code>",
                        conn_id,
                        partner_title,
                    )
                    return
                idx = cmd_arg.lower().find(" или ")
                opt1 = cmd_arg[:idx].strip()
                opt2 = cmd_arg[idx + 5 :].strip()
                chosen = random.choice([opt1, opt2]) if (opt1 and opt2) else cmd_arg
                await send_business_reply(
                    message.chat.id,
                    f"🐾 <b>Лапки сделали выбор:</b>\n"
                    f"Конечно же <b>«{html.escape(chosen)}»</b>! uwu~ ✨",
                    conn_id,
                    partner_title,
                )
                return

            # --- .uwu ---
            if cmd_word == "uwu":
                source_text = cmd_arg
                if not source_text and message.reply_to_message:
                    source_text = (
                        message.reply_to_message.text
                        or message.reply_to_message.caption
                        or ""
                    )
                if not source_text:
                    await send_business_reply(
                        message.chat.id,
                        "🥺 Ответь командой <code>.uwu</code> на текстовое сообщение или напиши <code>.uwu свой текст</code>!",
                        conn_id,
                        partner_title,
                    )
                    return
                await send_business_reply(
                    message.chat.id,
                    f"🌸 <b>UwU-переводчик:</b>\n<blockquote>{html.escape(uwuify_text(source_text))}</blockquote>",
                    conn_id,
                    partner_title,
                )
                return

            # --- .брак / .развод / .мы ---
            if cmd_word in ("брак", "marry"):
                if chat_stat.get("married_since"):
                    dur = format_duration(int(time.time() - chat_stat["married_since"]))
                    await send_business_reply(
                        message.chat.id,
                        f"💍 Вы с <b>{html.escape(partner_title)}</b> уже в счастливом браке целых <b>{dur}</b>! (◕‿◕)♡",
                        conn_id,
                        partner_title,
                    )
                else:
                    chat_stat["married_since"] = time.time()
                    save_stats(CHAT_STATS)
                    await send_business_reply(
                        message.chat.id,
                        f"💍🌸 <b>Горько!</b>\n"
                        f"<b>{sender_name}</b> и <b>{html.escape(partner_title)}</b> теперь официально в няшном браке! "
                        f"Обменялись чокерами и кольцами~ 🎀💞\n"
                        f"╰┈➤ <i>Проверить стаж: <code>.мы</code></i>",
                        conn_id,
                        partner_title,
                    )
                return

            if cmd_word in ("развод", "divorce"):
                if not chat_stat.get("married_since"):
                    await send_business_reply(
                        message.chat.id,
                        "🥺 Вы и так пока не состоите в браке 👉👈 (заключить: <code>.брак</code>)",
                        conn_id,
                        partner_title,
                    )
                else:
                    dur = format_duration(int(time.time() - chat_stat["married_since"]))
                    chat_stat["married_since"] = None
                    save_stats(CHAT_STATS)
                    await send_business_reply(
                        message.chat.id,
                        f"💔🥺 <b>Брак расторгнут...</b>\n"
                        f"Вы пробыли вместе <b>{dur}</b>, но котики решили пойти разными дорожками.",
                        conn_id,
                        partner_title,
                    )
                return

            if cmd_word in ("мы", "we"):
                if not chat_stat.get("married_since"):
                    await send_business_reply(
                        message.chat.id,
                        f"🐾 Вы с <b>{html.escape(partner_title)}</b> пока не в браке! Чтобы пожениться, напиши <code>.брак</code> 💍",
                        conn_id,
                        partner_title,
                    )
                else:
                    dur = format_duration(int(time.time() - chat_stat["married_since"]))
                    await send_business_reply(
                        message.chat.id,
                        f"💞 <b>Ваш любовный уголок с {html.escape(partner_title)}:</b>\n\n"
                        f"💍 <b>Вместе уже:</b> {dur}\n"
                        f"🌸 <b>Всего РП-нежностей:</b> {chat_stat['rp_total']}\n"
                        f"💬 <b>Сообщений в чате:</b> {chat_stat['messages']}",
                        conn_id,
                        partner_title,
                    )
                return

            # --- .стата / /stats ---
            if cmd_word in ("стата", "stats"):
                married_str = (
                    f"💍 В браке ({format_duration(int(time.time() - chat_stat['married_since']))})"
                    if chat_stat.get("married_since")
                    else "Свободны котики 🐾"
                )
                breakdown = chat_stat.get("rp_breakdown", {})
                top_rp = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
                top_lines = (
                    "\n".join(
                        [f"  • <code>.{k}</code> — {v} раз(а)" for k, v in top_rp]
                    )
                    if top_rp
                    else "  Пока ни одной команды 🥺"
                )
                await send_business_reply(
                    message.chat.id,
                    f"📊 <b>Няшная статистика чата с {html.escape(partner_title)}:</b>\n\n"
                    f"💬 <b>Сообщений записано:</b> {chat_stat['messages']}\n"
                    f"🎭 <b>Всего РП-действий:</b> {chat_stat['rp_total']}\n"
                    f"💖 <b>Статус:</b> {married_str}\n\n"
                    f"🏆 <b>Топ ваших действий:</b>\n{top_lines}",
                    conn_id,
                    partner_title,
                )
                return

            # --- .инфо / /info ---
            if cmd_word in ("инфо", "info"):
                uname = (
                    f"@{message.chat.username}" if message.chat.username else "скрыт"
                )
                await send_business_reply(
                    message.chat.id,
                    f"🪪 <b>Карточка котика {html.escape(partner_title)}:</b>\n\n"
                    f"🆔 <b>Telegram ID:</b> <code>{message.chat.id}</code>\n"
                    f"🔗 <b>Юзернейм:</b> {uname}\n"
                    f"💬 <b>Сообщений в базе:</b> {chat_stat['messages']}\n"
                    f"✏️ <b>Изменено сообщений:</b> {chat_stat['edited_caught']}\n"
                    f"🐾 <b>Удалено сообщений:</b> {chat_stat['deleted_caught']}",
                    conn_id,
                    partner_title,
                )
                return

        # 3. Проверяем срабатывание RP-команд (русские, двухсловные и английские алиасы)
        clean_text = text_stripped.lstrip(".!/").strip()
        clean_lower = clean_text.lower()
        first_word = clean_lower.split()[0] if clean_lower else ""

        matched_cmd = None
        extra_text = ""

        if first_word in SLASH_RP_ALIASES:
            target_rp = SLASH_RP_ALIASES[first_word]
            if target_rp in RP_COMMANDS:
                matched_cmd = target_rp
                parts = clean_text.split(maxsplit=1)
                extra_text = parts[1] if len(parts) > 1 else ""
        else:
            for cmd_key in sorted(RP_COMMANDS.keys(), key=len, reverse=True):
                if clean_lower == cmd_key or clean_lower.startswith(cmd_key + " "):
                    matched_cmd = cmd_key
                    extra_text = clean_text[len(cmd_key) :].strip()
                    break

        if matched_cmd:
            emoji, verb, suffix = format_rp_action(RP_COMMANDS[matched_cmd])
            suffix_part = f" {html.escape(suffix)}" if suffix else ""
            extra_comment = (
                f"\n╰┈➤ 💭 <i>Реплика: {html.escape(extra_text)}</i> 🎀"
                if extra_text
                else ""
            )

            # Обновляем счётчик РП-действий в статистике
            chat_stat["rp_total"] += 1
            chat_stat["rp_breakdown"][matched_cmd] = (
                chat_stat["rp_breakdown"].get(matched_cmd, 0) + 1
            )
            save_stats(CHAT_STATS)

            await send_business_reply(
                message.chat.id,
                f"{emoji} <b>{sender_name}</b> {html.escape(verb)} <b>{target_name}</b>{suffix_part}~{extra_comment}",
                conn_id,
                partner_title,
            )
            print(f"[RP] Отправлена команда '{matched_cmd}' в чат с {partner_title}")
            return

    # 4. Сохраняем сообщение в кэш на случай удаления или редактирования
    media_type = None
    file_id = None

    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
    elif message.video_note:
        media_type = "video_note"
        file_id = message.video_note.file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id

    messages_cache[(message.chat.id, message.message_id)] = {
        "sender_id": message.from_user.id,
        "sender_name": message.from_user.full_name,
        "text": message.text or message.caption or "",
        "media_type": media_type,
        "file_id": file_id,
    }
    print(
        f"[КЭШ] Запомнил сообщение от {message.from_user.full_name}: {message.text or f'[{media_type}]'}"
    )


@dp.edited_business_message()
async def handle_edited_business_message(message: types.Message):
    conn_id = message.business_connection_id
    owner_chat_id = await get_owner_chat_id(conn_id)

    if message.from_user.id == owner_chat_id:
        return

    chat_stat = get_chat_stat(message.chat.id, message.chat.full_name or "Собеседник")
    chat_stat["edited_caught"] += 1
    save_stats(CHAT_STATS)

    key = (message.chat.id, message.message_id)
    old_data = messages_cache.get(key)
    old_text = (
        html.escape(old_data["text"])
        if old_data and old_data["text"]
        else "[не сохранено в кэше]"
    )
    new_text = html.escape(message.text or message.caption or "[без текста]")
    sender = html.escape(message.from_user.full_name)

    if old_data:
        old_data["text"] = message.text or message.caption or ""

    try:
        await bot.send_message(
            chat_id=owner_chat_id,
            text=(
                f"🌸 <b>Изменено сообщение</b> от <b>{sender}</b> (👀):\n\n"
                f"🎀 <b>Было:</b>\n<blockquote>{old_text}</blockquote>\n"
                f"✨ <b>Стало:</b>\n<blockquote>{new_text}</blockquote>"
            ),
            parse_mode="HTML",
        )
        print(f"[ЛОГ] Переслано изменённое сообщение от {sender}")
    except Exception as e:
        print(f"[!] Не удалось отправить лог в личку бота: {e}")


@dp.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    conn_id = event.business_connection_id
    owner_chat_id = await get_owner_chat_id(conn_id)

    chat_stat = get_chat_stat(event.chat.id, event.chat.full_name or "Собеседник")

    for msg_id in event.message_ids:
        key = (event.chat.id, msg_id)
        data = messages_cache.pop(key, None)

        if not data or data["sender_id"] == owner_chat_id:
            continue

        chat_stat["deleted_caught"] += 1
        save_stats(CHAT_STATS)

        sender = html.escape(data["sender_name"])
        saved_text = html.escape(data["text"]) if data["text"] else "[без текста]"
        header = f"🐾 <b>Удалено сообщение</b> от <b>{sender}</b> (не спрячешься~ :3):\n\n<blockquote>{saved_text}</blockquote>"

        m_type = data["media_type"]
        f_id = data["file_id"]

        try:
            if m_type == "photo":
                await bot.send_photo(
                    owner_chat_id, f_id, caption=header, parse_mode="HTML"
                )
            elif m_type == "voice":
                await bot.send_voice(
                    owner_chat_id, f_id, caption=header, parse_mode="HTML"
                )
            elif m_type == "video":
                await bot.send_video(
                    owner_chat_id, f_id, caption=header, parse_mode="HTML"
                )
            elif m_type == "document":
                await bot.send_document(
                    owner_chat_id, f_id, caption=header, parse_mode="HTML"
                )
            elif m_type == "video_note":
                await bot.send_message(
                    owner_chat_id,
                    f"🐾 <b>Удалён кружочек</b> от <b>{sender}</b>:",
                    parse_mode="HTML",
                )
                await bot.send_video_note(owner_chat_id, f_id)
            else:
                await bot.send_message(owner_chat_id, header, parse_mode="HTML")
            print(f"[ЛОГ] Переслано удалённое сообщение от {sender}")
        except Exception as e:
            print(f"[!] Не удалось отправить удалённое сообщение: {e}")


async def main():
    await setup_bot_commands()
    print("🌸 Бот успешно запущен со всеми мини-играми и статистикой!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

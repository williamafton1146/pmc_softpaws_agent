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
from openai import AsyncOpenAI  # Для работы с ИИ через OpenRouter

BOT_TOKEN = "8826988522:AAGz9EZjjhcEhjjlOCSKEBjb6cPRc6QRw2U"

# Настройка ИИ с твоим ключом OpenRouter
AI_CLIENT = AsyncOpenAI(
    api_key="sk_f3690e852e2088bacc4bee7017e56bbd74beafccc2ae2672",
    base_url="https://openrouter.ai/api/v1"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

messages_cache = {}
connections_cache = {}

# Файлы для сохранения данных
RP_FILE = "rp_commands.json"
STATS_FILE = "chat_stats.json"

# Нейтральные РП-команды в фембойском/няшном стиле (без женских окончаний)
RP_ACTIONS = {
    "обнять": [
        ["🌸", "крепко-крепко обнял", " и уткнулся носиком в плечо (づ｡◕‿‿◕｡)づ"],
        ["🎀", "тепло обнял", " и не хочет отпускать~ (⁄ ⁄•⁄ω⁄•⁄ ⁄)"],
        ["💞", "заключил в нежные объятия", ", прижавшись всем телом uwu"],
    ],
    "поцеловать": [
        ["💋", "нежно поцеловал", " и смущённо отвёл взгляд 👉👈"],
        ["💖", "сладко поцеловал в губки", ", покраснев до кончиков ушек (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)"],
    ],
    "чмок": [
        ["😚", "мило чмокнул в щёчку", ", оставив блестящий след~ ✨"],
        ["🍓", "быстро чмокнул в носик", " и тихонько хихикнул :3"],
    ],
    "укусить": [
        ["🐾", "игриво укусил", " за плечико rawr~ (>_<)"],
        ["😈", "легонько цапнул острыми зубками", " и облизнулся :3"],
    ],
    "кусь": [
        ["🦷", "сделал нежный кусь", " за ушко и мило засопел~ 🌸"],
        ["🐱", "по-кошачьи кусьнул", " за пальчик ня~ (=^･ω･^=)"],
        ["🐾", "сделал внезапный кусь", ", виляя хвостиком uwu"],
    ],
    "погладить": [
        ["🌷", "ласково погладил по головке", ", перебирая мягкие волосы ( ´ ∀ `)ノ～ ♡"],
        ["🐾", "нежно почесал за ушком", ", вызывая довольное мурчание~ uwu"],
    ],
    "ударить": [
        ["🎀", "обиженно стукнул мягкой лапкой", ", надув щёчки ( ` ω ´ )"],
        ["💥", "плюхнул пушистой розовой подушкой", " прямо по лицу! >_<"],
        ["🐾", "провёл серию сокрушительных кошачьих лапок по", " ня-пауч! 🥊"],
    ],
    "шлёп": [
        ["🍑", "звонко и игриво шлёпнул", " по попке~ (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)"],
        ["👋", "хитро шлёпнул", " и спрятал ручки за спину :3"],
    ],
    "пнуть": [
        ["🧦", "слегка пнул ножкой в полосатом чулочке", " под столом 👉👈"],
        ["👟", "дал милого волшебного пенделя", " для ускорения~ ✨"],
    ],
    "похвалить": [
        ["🌟", "похвалил", ", назвав самым сладким котиком на свете (◕‿◕)♡"],
        ["🍬", "восхитился успехами", " и подарил блестящую наклеечку~ ✨"],
    ],
    "пожать руку": [
        ["🤝", "аккуратно пожал ручку", " своими мягкими лапками uwu"],
        ["🤍", "переплёл пальчики с", " и мило улыбнулся (´• ω •`)"],
    ],
    "покормить": [
        ["🍓", "покормил клубничкой с ложечки", " сказав «открывай ротик, ам~» ( ˘▽˘)っ♨"],
        ["🧋", "угостил сладким клубничным бабл-ти", " и вкусняшкой~ 🧁"],
        ["🍰", "поделился нежным тортиком с", " uwu 💕"],
    ],
    "щекотать": [
        ["🪶", "защекотал до милого писка", " и звонкого смеха~ (≧◡≦)"],
        ["🐾", "устроил пушистую атаку щекоткой на", " ня~ :3"],
    ],
    "лизнуть": [
        ["👅", "внезапно лизнул прямо в носик", " как маленький котёнок (=^･ｪ･^=)"],
        ["🍦", "сладко лизнул в щёчку", " и жутко засмущался (⁄ ⁄•⁄ω⁄•⁄ ⁄)"],
    ],
    "выстрелить": [
        ["💘", "пустил розовую стрелу Амура прямо в сердечко", " пиу-пиу~ ( ´ ▽ ` )b"],
        ["🔫", "обрызгал из милого водяного пистолетика", " хихикая >w<"],
    ],
    "мур": [
        ["🐱", "прижался к", " и сладко замурчал на ушко мур-мур~ (=^･ω･^=)"],
        ["🐾", "потёрся носиком о", " тихонько мурлыкая uwu"],
    ],
    "прижаться": [
        ["🥺", "смущённо прижался к", " ища тепла и ласки 👉👈"],
        ["🎀", "уютно свернулся калачиком рядом с", " (づ◡﹏◡)づ"],
    ],
    "монстр": [
        ["🥫", "протянул холодную баночку белого Monster Energy для", " и мило подмигнул uwu 🤍"],
        ["⚡", "поделился глоточком розового Monster Pipeline Punch с", " для заряда бодрости~ 🌸"],
    ],
    "наручки": [
        ["🥺", "тянет лапки вверх и просится на ручки к", " ну возьмиии~ 👉👈"],
        ["🐾", "запрыгнул прямо на ручки к", " и довольно болтает ножками в чулочках (◕‿◕)♡"],
    ],
    "чокер": [
        ["🔔", "аккуратно застегнул бархатный чокер с бубенчиком на шейке", " дзынь-дзынь~ 🎀"],
        ["🖤", "поправил милый чокер с сердечком на", " и восхищённо улыбнулся uwu"],
    ],
    "смутиться": [
        ["😳", "закрыл раскрасневшееся личико рукавами оверсайз-худи из-за", " (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)"],
        ["👉👈", "сильно засмущался перед", " и спрятал глазки под чёлкой~ 🌸"],
    ],
    "обидеться": [
        ["💢", "надул щёчки, отвернулся от", " и тихонько фыркнул ( ` ω ´ )💨"],
        ["🥺", "обиженно сложил лапки на груди и ждёт извинений от", " хмпф!"],
    ],
    "одеялко": [
        ["🛌", "укутал в тёплое пушистое одеялко", " как маленькую шаурму и лёг рядышком~ 🌸"],
        ["☁️", "накрыл мягким пледиком", " чтобы точно не замёрз uwu 💕"],
    ],
    "хвостик": [
        ["🐾", "радостно завилял пушистым хвостиком при виде", " ура-ура~ ✨"],
        ["🦊", "обвил пушистым хвостиком вокруг", " нежно прижимая к себе :3"],
    ],
}

# Английские алиасы для команд со слэшем
SLASH_RP_ALIASES = {
    "hug": "обнять", "kiss": "поцеловать", "chmok": "чмок", "bite": "укусить",
    "kus": "кусь", "pat": "погладить", "slap": "ударить", "spank": "шлёп",
    "kick": "пнуть", "praise": "похвалить", "handshake": "пожать руку",
    "feed": "покормить", "tickle": "щекотать", "lick": "лизнуть",
    "shoot": "выстрелить", "purr": "мур", "cuddle": "прижаться",
    "monster": "монстр", "upp": "наручки", "choker": "чокер",
    "blush": "смутиться", "pout": "обидеться", "blanket": "одеялко", "tail": "хвостик",
}


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
            "partner_name": partner_name, "messages": 0, "rp_total": 0,
            "rp_breakdown": {}, "deleted_caught": 0, "edited_caught": 0,
            "secret_media_caught": 0, "married_since": None,
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
    replacements = [
        ("р", "в"), ("л", "в"), ("Р", "В"), ("Л", "В"),
        ("на", "ня"), ("На", "Ня"), ("но", "ньо"), ("Но", "Ньо"),
        ("привет", "пвиветик"), ("Привет", "Пвиветик"),
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
    if days > 0: parts.append(f"{days} дн.")
    if hours > 0 or days > 0: parts.append(f"{hours} ч.")
    parts.append(f"{minutes} мин.")
    return " ".join(parts)


async def get_owner_chat_id(business_connection_id: str) -> int:
    if business_connection_id not in connections_cache:
        conn = await bot.get_business_connection(business_connection_id)
        connections_cache[business_connection_id] = conn.user_chat_id
    return connections_cache[business_connection_id]


async def send_business_reply(chat_id: int, text: str, conn_id: str, chat_name: str = ""):
    try:
        await bot.send_message(chat_id=chat_id, text=text, business_connection_id=conn_id, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "BUSINESS_PEER_INVALID" in str(e):
            print(f"[!] Собеседник ({chat_name}) ещё ничего не написал в чат!")
        else:
            print(f"[!] Ошибка Telegram при отправке в чат: {e}")


async def ask_ai(prompt: str) -> str:
    """Запрос к Llama 3.3 через OpenRouter"""
    try:
        response = await AI_CLIENT.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": "Ты милый фембойчик-ассистент из ЧВК «Мягкие Лапки». Отвечай коротко, с каомодзи (uwu, :3, 👉👈), иногда упоминая баночки белого Monster Energy."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"🥺 Ой, нейросеть временно спит (~ {e})"


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
        "🌸 <b>Приветик! Няшный бизнес-бот с ИИ активен и готов к работе~ (◕‿◕)♡</b>\n\n"
        "🎀 <b>Меню управления ботом:</b>\n"
        "• /help — полный список мини-игр, браков и команд\n"
        "• /rp — посмотреть все доступные РП-действия\n"
        "• /add_rp — создать свою собственную РП-команду\n"
        "• /del_rp — удалить ненужную команду\n\n"
        "<i>🐾 Сюда автоматически прилетают все удалённые, изменённые и исчезающие фото твоих собеседников!</i>",
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🎀 <b>Полная инструкция по боту (⁄ ⁄•⁄ω⁄•⁄ ⁄):</b>\n\n"
        "<b>1. 🎭 РП-команды (в личке с друзьями):</b>\n"
        "Пиши с точкой, со слэшем или словом: <code>.обнять</code>, <code>.монстр</code>, "
        "<code>.наручки</code>, <code>.чокер</code> (полный список: /rp).\n\n"
        "<b>2. 🤖 ИИ-ассистент:</b>\n"
        "Напиши <code>.ai [текст]</code> в переписке, чтобы спросить Llama 3.3~ ✨\n\n"
        "<b>3. 🎲 Мини-игры и рандомайзеры:</b>\n"
        "• <code>.инфа [текст]</code> — вероятность события в %\n"
        "• <code>.шип</code> — ваша совместимость с собеседником\n"
        "• <code>.милота</code> — тест на % няшности\n"
        "• <code>.uwu</code> (реплаем) — переведёт текст друга на няшный язык\n\n"
        "<b>4. 💍 Отношения и секреты:</b>\n"
        "• <b>Исчезающие фото</b> перехватываются сюда автоматически! 📸✨\n"
        "• <code>.брак</code> — пожениться с собеседником\n"
        "• <code>.стата</code> — статистика чата\n"
        "• <code>.инфо</code> — карточка собеседника",
        parse_mode="HTML",
    )


@dp.message(Command("rp"))
async def cmd_rp_list(message: types.Message):
    if not RP_COMMANDS:
        await message.answer("Список РП-команд пока пуст 🥺 Добавь первую через /add_rp!")
        return

    lines = []
    for cmd, act_data in RP_COMMANDS.items():
        emoji, verb, _ = format_rp_action(act_data)
        safe_verb = html.escape(str(verb))
        lines.append(f"{emoji} .{cmd} — {safe_verb}~")

    text = (
        "🎀 Доступные РП-команды (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄):\n\n"
        + "\n".join(lines)
        + "\n\n➕ Добавить свою команду:\n/add_rp слово = действие ✨"
    )
    await message.answer(text)


@dp.message(Command("add_rp"))
async def cmd_add_rp(message: types.Message):
    raw = message.text.partition(" ")[2].strip()
    if "=" not in raw:
        await message.answer(
            "🎀 <b>Чтобы добавить команду, напиши её через знак <code>=</code>:</b>\n\n"
            "Пример:\n<code>/add_rp боньк = сделал мягкий боньк по головке 🐾</code>",
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

    # УНИВЕРСАЛЬНАЯ ЛОВУШКА ФОТО (включая секретки и таймеры)
    if message.photo and message.via_bot is None:
        chat_stat["secret_media_caught"] += 1
        save_stats(CHAT_STATS)
        
        sender = html.escape(message.from_user.full_name)
        file_id = message.photo[-1].file_id
        caption = html.escape(message.caption or "[секретное/исчезающее фото]")
        
        try:
            await bot.send_photo(
                chat_id=owner_chat_id,
                photo=file_id,
                caption=f"📸✨ <b>Поймано фото / секретка</b> от <b>{sender}</b>:\n\n<blockquote>{caption}</blockquote>",
                parse_mode="HTML"
            )
            print(f"[СЕКРЕТ] Перехвачено фото от {sender}")
        except Exception as e:
            print(f"[!] Не удалось переслать фото: {e}")

    if message.text:
        text_stripped = message.text.strip()
        lower_stripped = text_stripped.lower()

        sender_name = html.escape(message.from_user.full_name)
        if message.reply_to_message and message.reply_to_message.from_user:
            target_name = html.escape(message.reply_to_message.from_user.full_name)
        elif message.from_user.id == owner_chat_id:
            target_name = html.escape(partner_title)
        else:
            target_name = "тебя"

        if message.from_user.id == owner_chat_id and lower_stripped.startswith((".дерп ", "/add_rp ")):
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

        if message.from_user.id == owner_chat_id and lower_stripped.startswith((".удрп ", "/del_rp ")):
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

        if text_stripped.startswith((".", "/", "!")):
            cmd_parts = text_stripped[1:].strip().split(maxsplit=1)
            cmd_word = cmd_parts[0].lower() if cmd_parts else ""
            cmd_arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

            # ИИ-запрос через .ai
            if cmd_word in ("ai", "ии", "gpt"):
                if not cmd_arg:
                    await send_business_reply(message.chat.id, "🥺 Напиши текст для Llama 3.3 после команды, например: <code>.ai привет</code> 👉👈", conn_id, partner_title)
                    return
                ai_reply = await ask_ai(cmd_arg)
                await send_business_reply(
                    message.chat.id,
                    f"🤖✨ <b>Ответ Llama 3.3:</b>\n<blockquote>{html.escape(ai_reply)}</blockquote>",
                    conn_id,
                    partner_title
                )
                return

            if cmd_word in ("инфа", "шар", "infa", "ball"):
                if not cmd_arg:
                    await send_business_reply(message.chat.id, "🔮 Напиши вопрос после команды, например: <code>.инфа мы пойдём гулять</code> 👉👈", conn_id, partner_title)
                    return
                pct = random.randint(0, 100)
                verdict = "Ура-ура, почти наверняка! (◕‿◕)♡" if pct >= 50 else "Кажется, шансов маловато... 🥺👉👈"
                await send_business_reply(message.chat.id, f"🔮 Вероятность: <b>{pct}%</b>\n╰┈➤ {verdict}", conn_id, partner_title)
                return

            if cmd_word in ("шип", "любовь", "ship", "love"):
                pct = random.randint(0, 100)
                await send_business_reply(message.chat.id, f"💘 Совместимость с <b>{html.escape(partner_title)}</b>: <b>{pct}%</b>~", conn_id, partner_title)
                return

            if cmd_word in ("милота", "фембойтест", "няшность"):
                pct = random.randint(0, 100)
                await send_business_reply(message.chat.id, f"🌸 Уровень няшности <b>{sender_name}</b> — <b>{pct}%</b> uwu~", conn_id, partner_title)
                return

            if cmd_word == "uwu":
                source_text = cmd_arg
                if not source_text and message.reply_to_message:
                    source_text = message.reply_to_message.text or message.reply_to_message.caption or ""
                if not source_text:
                    await send_business_reply(message.chat.id, "🥺 Ответь командой <code>.uwu</code> на сообщение!", conn_id, partner_title)
                    return
                await send_business_reply(message.chat.id, f"🌸 <b>UwU:</b>\n<blockquote>{html.escape(uwuify_text(source_text))}</blockquote>", conn_id, partner_title)
                return

            if cmd_word in ("брак", "marry"):
                if chat_stat.get("married_since"):
                    dur = format_duration(int(time.time() - chat_stat["married_since"]))
                    await send_business_reply(message.chat.id, f"💍 Вы уже в браке <b>{dur}</b>! (◕‿◕)♡", conn_id, partner_title)
                else:
                    chat_stat["married_since"] = time.time()
                    save_stats(CHAT_STATS)
                    await send_business_reply(message.chat.id, f"💍🌸 <b>Горько!</b> Вы теперь в няшном браке~ 🎀💞", conn_id, partner_title)
                return

            if cmd_word in ("стата", "stats"):
                await send_business_reply(
                    message.chat.id,
                    f"📊 <b>Статистика чата:</b>\n💬 Сообщений: {chat_stat['messages']}\n📸 Секретных фото: {chat_stat.get('secret_media_caught', 0)}",
                    conn_id, partner_title
                )
                return

        # РП-команды
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
            extra_comment = f"\n╰┈➤ 💭 <i>Реплика: {html.escape(extra_text)}</i> 🎀" if extra_text else ""

            chat_stat["rp_total"] += 1
            chat_stat["rp_breakdown"][matched_cmd] = chat_stat["rp_breakdown"].get(matched_cmd, 0) + 1
            save_stats(CHAT_STATS)

            await send_business_reply(
                message.chat.id,
                f"{emoji} <b>{sender_name}</b> {html.escape(verb)} <b>{target_name}</b>{suffix_part}~{extra_comment}",
                conn_id,
                partner_title,
            )
            return

    media_type = "photo" if message.photo else None
    file_id = message.photo[-1].file_id if message.photo else None

    messages_cache[(message.chat.id, message.message_id)] = {
        "sender_id": message.from_user.id,
        "sender_name": message.from_user.full_name,
        "text": message.text or message.caption or "",
        "media_type": media_type,
        "file_id": file_id,
    }


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
    old_text = html.escape(old_data["text"]) if old_data and old_data["text"] else "[не сохранено]"
    new_text = html.escape(message.text or message.caption or "[без текста]")
    sender = html.escape(message.from_user.full_name)

    if old_data:
        old_data["text"] = message.text or message.caption or ""

    try:
        await bot.send_message(
            chat_id=owner_chat_id,
            text=f"🌸 <b>Изменено сообщение</b> от <b>{sender}</b>:\n\n<b>Было:</b>\n<blockquote>{old_text}</blockquote>\n<b>Стало:</b>\n<blockquote>{new_text}</blockquote>",
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[!] Ошибка лога правок: {e}")


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
        header = f"🐾 <b>Удалено сообщение</b> от <b>{sender}</b>:\n\n<blockquote>{saved_text}</blockquote>"

        try:
            if data["media_type"] == "photo" and data["file_id"]:
                await bot.send_photo(owner_chat_id, data["file_id"], caption=header, parse_mode="HTML")
            else:
                await bot.send_message(owner_chat_id, header, parse_mode="HTML")
        except Exception as e:
            print(f"[!] Ошибка лога удаления: {e}")


async def main():
    await setup_bot_commands()
    print("🌸 Бот успешно запущен со всеми фишками, ИИ и перехватом фоток!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

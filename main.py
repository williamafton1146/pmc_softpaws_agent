import asyncio
import html
import io
import json
import os
import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BufferedInputFile
from openai import AsyncOpenAI

BOT_TOKEN = "8826988522:AAGz9EZjjhcEhjjlOCSKEBjb6cPRc6QRw2U"

AI_CLIENT = AsyncOpenAI(
    api_key="sk_f3690e852e2088bacc4bee7017e56bbd74beafccc2ae2672",
    base_url="https://api.provod.ai/v1",
)
ACTIVE_AI_MODEL = None
AVAILABLE_AI_MODELS = []

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

messages_cache = {}
connections_cache = {}
ai_history = {}

# Настройки режима «Не в сети» (AFK)
AFK_TIMEOUT = 600  # 10 минут (600 секунд) без твоих сообщений = режим «не в сети»
last_owner_activity = time.time()
manual_afk = False
afk_last_reply_time = {}

RP_FILE = "rp_commands.json"
STATS_FILE = "chat_stats.json"

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
            "partner_name": partner_name,
            "messages": 0,
            "rp_total": 0,
            "rp_breakdown": {},
            "deleted_caught": 0,
            "edited_caught": 0,
            "secret_media_caught": 0,
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
    if days > 0:
        parts.append(f"{days} дн.")
    if hours > 0 or days > 0:
        parts.append(f"{hours} ч.")
    parts.append(f"{minutes} мин.")
    return " ".join(parts)


def is_owner_offline() -> bool:
    if manual_afk:
        return True
    return (time.time() - last_owner_activity) >= AFK_TIMEOUT


async def resolve_ai_model() -> str:
    global ACTIVE_AI_MODEL, AVAILABLE_AI_MODELS
    if ACTIVE_AI_MODEL:
        return ACTIVE_AI_MODEL

    preferred = [
        "deepseek-v4-flash",
        "gemini-3.1-flash-lite",
        "qwen3-max-preview",
        "qwen3.7-max",
        "glm-5.3-flash",
        "glm-5.3",
        "glm-5.2",
        "claude-fable-5.1",
        "claude-fable-5",
        "deepseek-v4-flash-0731",
    ]
    try:
        models_page = await AI_CLIENT.models.list()
        AVAILABLE_AI_MODELS = [m.id for m in models_page.data]
        for pref in preferred:
            if pref in AVAILABLE_AI_MODELS:
                ACTIVE_AI_MODEL = pref
                return ACTIVE_AI_MODEL
        if AVAILABLE_AI_MODELS:
            ACTIVE_AI_MODEL = AVAILABLE_AI_MODELS[0]
            return ACTIVE_AI_MODEL
    except Exception as e:
        print(f"[!] Не удалось получить список моделей: {e}")

    ACTIVE_AI_MODEL = "deepseek-v4-flash"
    return ACTIVE_AI_MODEL


async def ask_ai(chat_id: int, user_text: str, mode: str = "normal", partner_name: str = "Собеседник") -> str:
    global ACTIVE_AI_MODEL
    model_name = await resolve_ai_model()

    if mode == "afk":
        system_prompt = (
            f"Ты милый, ласковый фембойчик-ассистент из ЧВК «Мягкие Лапки». "
            f"Владелец аккаунта сейчас не в сети (отдыхает или занят), поэтому ты временно отвечаешь его собеседнику по имени {partner_name}. "
            f"Отвечай дружелюбно, коротко, в няшном стиле с каомодзи (uwu, :3, 👉👈, (◕‿◕)♡), "
            f"иногда упоминай пушистые чулочки, обнимашки или баночку белого Monster Energy. "
            f"Используй только мужской род по отношению к себе (например: «я увидел», «я передал», «я решил»)."
        )
    else:
        system_prompt = (
            "Ты милый, умный и ласковый фембойчик-ассистент из ЧВК «Мягкие Лапки». "
            "Отвечай полезно, понятно и с душой, добавляя милые каомодзи (uwu, :3, 👉👈, (⁄ ⁄•⁄ω⁄•⁄ ⁄)). "
            "Используй только мужской род по отношению к себе (например: «я подумал», «я нашёл», «я сделал»)."
        )

    history = ai_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    if len(history) > 8:
        history[:] = history[-8:]

    messages_payload = [{"role": "system", "content": system_prompt}] + history
    candidates = [model_name] + AVAILABLE_AI_MODELS + [
        "deepseek-v4-flash", "gemini-3.1-flash-lite", "qwen3-max-preview", "glm-5.3-flash", "claude-fable-5.1"
    ]

    last_err = None
    for m in dict.fromkeys(candidates):
        if not m:
            continue
        try:
            resp = await AI_CLIENT.chat.completions.create(
                model=m, messages=messages_payload, max_tokens=400, temperature=0.8
            )
            reply_text = resp.choices[0].message.content.strip()
            ACTIVE_AI_MODEL = m
            history.append({"role": "assistant", "content": reply_text})
            return reply_text
        except Exception as err:
            last_err = err
            continue

    history.pop()
    return f"🥺 Ой, лапки запутались в проводах нейросети... ({last_err})"


async def get_owner_chat_id(business_connection_id: str) -> int:
    if business_connection_id not in connections_cache:
        conn = await bot.get_business_connection(business_connection_id)
        connections_cache[business_connection_id] = conn.user_chat_id
    return connections_cache[business_connection_id]


async def send_business_reply(chat_id: int, text: str, conn_id: str, chat_name: str = ""):
    try:
        await bot.send_message(
            chat_id=chat_id, text=text, business_connection_id=conn_id, parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        print(f"[!] Ошибка Telegram при отправке в чат ({chat_name}): {e}")


def is_secret_or_timer_media(message: types.Message) -> bool:
    if getattr(message, "has_protected_content", None) or getattr(message, "has_media_spoiler", None):
        return True
    if getattr(message, "ttl_seconds", None) or getattr(message, "self_destruct_period", None):
        return True
    extra = getattr(message, "model_extra", None) or {}
    for k, v in extra.items():
        if ("ttl" in k.lower() or "destruct" in k.lower() or "once" in k.lower() or "secret" in k.lower()) and v:
            return True
    return False


async def download_media_bytes(file_id: str) -> bytes | None:
    try:
        buf = io.BytesIO()
        await bot.download(file_id, destination=buf)
        return buf.getvalue()
    except Exception as e:
        print(f"[!] Не удалось скачать медиа: {e}")
        return None


async def send_cached_media_to_owner(
    owner_chat_id: int, m_type: str, f_id: str | None, raw_bytes: bytes | None, header: str
):
    filename_map = {
        "photo": "secret_photo.jpg",
        "video": "secret_video.mp4",
        "voice": "secret_voice.ogg",
        "video_note": "secret_circle.mp4",
        "document": "secret_file.bin",
    }
    fname = filename_map.get(m_type, "secret.bin")

    if raw_bytes:
        input_file = BufferedInputFile(raw_bytes, filename=fname)
        if m_type == "photo":
            await bot.send_photo(owner_chat_id, input_file, caption=header, parse_mode="HTML")
            return
        elif m_type == "voice":
            await bot.send_voice(owner_chat_id, input_file, caption=header, parse_mode="HTML")
            return
        elif m_type == "video":
            await bot.send_video(owner_chat_id, input_file, caption=header, parse_mode="HTML")
            return
        elif m_type == "video_note":
            await bot.send_message(owner_chat_id, header, parse_mode="HTML")
            await bot.send_video_note(owner_chat_id, input_file)
            return
        elif m_type == "document":
            await bot.send_document(owner_chat_id, input_file, caption=header, parse_mode="HTML")
            return

    if f_id:
        if m_type == "photo":
            await bot.send_photo(owner_chat_id, f_id, caption=header, parse_mode="HTML")
        elif m_type == "voice":
            await bot.send_voice(owner_chat_id, f_id, caption=header, parse_mode="HTML")
        elif m_type == "video":
            await bot.send_video(owner_chat_id, f_id, caption=header, parse_mode="HTML")
        elif m_type == "video_note":
            await bot.send_message(owner_chat_id, header, parse_mode="HTML")
            await bot.send_video_note(owner_chat_id, f_id)
        elif m_type == "document":
            await bot.send_document(owner_chat_id, f_id, caption=header, parse_mode="HTML")
        else:
            await bot.send_message(owner_chat_id, header, parse_mode="HTML")
    else:
        await bot.send_message(owner_chat_id, header, parse_mode="HTML")


async def setup_bot_commands():
    commands = [
        BotCommand(command="start", description="🌸 Запустить бота и краткая инфа"),
        BotCommand(command="help", description="🎀 Полная шпаргалка по всем командам"),
        BotCommand(command="afk", description="🌙 Вкл/выкл режим «Не в сети» для ИИ"),
        BotCommand(command="rp", description="🐾 Список всех РП-команд"),
        BotCommand(command="add_rp", description="➕ Добавить свою РП-команду"),
        BotCommand(command="del_rp", description="🗑 Удалить РП-команду"),
        BotCommand(command="clear", description="🧹 Очистить память диалога с ИИ"),
    ]
    await bot.set_my_commands(commands)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    global last_owner_activity
    last_owner_activity = time.time()
    status_str = "🌙 Включён принудительно (/afk)" if manual_afk else "☀️ Автоматический (через 5 мин тишины)"
    await message.answer(
        "🌸 <b>Приветик! Няшный бизнес-бот с ИИ активен и готов к работе~ (◕‿◕)♡</b>\n\n"
        "💬 <b>Общение с ИИ:</b>\n"
        "Пиши мне сюда <b>любое сообщение</b> без команд — я отвечу как твой личный фембой-ассистент!\n\n"
        f"🤖 <b>Режим автоответчика в чатах:</b> {status_str}\n\n"
        "🎀 <b>Меню управления ботом:</b>\n"
        "• /help — полный список мини-игр, ИИ, браков и команд\n"
        "• /afk — переключить режим «Не в сети» вручную\n"
        "• /rp — посмотреть все доступные РП-действия\n"
        "• /add_rp — создать свою собственную РП-команду\n"
        "• /del_rp — удалить ненужную команду\n"
        "• /clear — очистить память ИИ\n\n"
        "<i>🐾 Сюда также автоматически прилетают все удалённые, изменённые и секретные медиа твоих собеседников!</i>",
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🎀 <b>Полная инструкция по боту (⁄ ⁄•⁄ω⁄•⁄ ⁄):</b>\n\n"
        "<b>1. 🤖 ИИ-ассистент (3 режима):</b>\n"
        "• <b>В личке со мной:</b> просто пиши любой текст, я отвечу на всё!\n"
        "• <b>В чатах с друзьями по команде:</b> напиши <code>.ии [вопрос]</code> или <code>.ai [вопрос]</code>\n"
        "• <b>Когда ты не в сети:</b> если ты не писал ничего 5 минут (или включил <code>/afk</code> / <code>.афк</code>), я сам вежливо отвечу собеседнику за тебя!\n\n"
        "<b>2. 🎭 РП-команды (в личке с друзьями):</b>\n"
        "Пиши с точкой, со слэшем или словом: <code>.обнять</code>, <code>.монстр</code>, "
        "<code>.наручки</code>, <code>.чокер</code> (полный список: /rp).\n\n"
        "<b>3. 🎲 Мини-игры и рандомайзеры:</b>\n"
        "• <code>.инфа [текст]</code> или <code>.шар [текст]</code> — вероятность события в %\n"
        "• <code>.шип</code> или <code>.любовь</code> — ваша совместимость с собеседником\n"
        "• <code>.милота</code> или <code>.фембойтест</code> — тест на % няшности\n"
        "• <code>.выбор А или Б</code> — поможет выбрать между двумя вариантами\n"
        "• <code>.uwu</code> (ответом на сообщение) — переведёт текст друга на няшный язык\n\n"
        "<b>4. 💍 Отношения, статистика и секреты:</b>\n"
        "• <b>Секретные и удалённые фото/кружочки/ГС</b> сохраняются сюда автоматически! 📸✨\n"
        "• <code>.брак</code> — пожениться с собеседником\n"
        "• <code>.мы</code> — сколько времени в браке\n"
        "• <code>.развод</code> — расторгнуть брак 💔\n"
        "• <code>.стата</code> — статистика сообщений и обнимашек\n"
        "• <code>.инфо</code> — карточка собеседника (ID, пойманные секреты)\n\n"
        "<b>5. ➕ Свои РП-команды без кода:</b>\n"
        "Добавить: <code>/add_rp боньк = сделал мягкий боньк 🐾</code>\n"
        "Удалить: <code>/del_rp боньк</code>",
        parse_mode="HTML",
    )


@dp.message(Command("afk"))
async def cmd_afk(message: types.Message):
    global manual_afk, last_owner_activity
    manual_afk = not manual_afk
    if not manual_afk:
        last_owner_activity = time.time()
    state_text = (
        "🌙 <b>Режим «Не в сети» ВКЛЮЧЁН!</b>\nТеперь я буду сам отвечать твоим собеседникам в личных чатах~ 🐾"
        if manual_afk
        else "☀️ <b>Режим «Не в сети» ВЫКЛЮЧЕН!</b>\nЯ буду включаться только если ты не пишешь больше 10 минут uwu~"
    )
    await message.answer(state_text, parse_mode="HTML")


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    ai_history.pop(message.chat.id, None)
    await message.answer("🧹✨ Память диалога со мной очищена! Начинаем с чистого листа uwu~")


@dp.message(Command("rp"))
async def cmd_rp_list(message: types.Message):
    if not RP_COMMANDS:
        await message.answer("Список РП-команд пока пуст 🥺 Добавь первую через /add_rp!")
        return
    lines = [f"{format_rp_action(v)[0]} .{k} — {html.escape(str(format_rp_action(v)[1]))}~" for k, v in RP_COMMANDS.items()]
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
        await message.answer("🎀 Укажи название команды: <code>/del_rp кусь</code>", parse_mode="HTML")
        return
    if cmd_name in RP_COMMANDS:
        del RP_COMMANDS[cmd_name]
        save_rp_commands(RP_COMMANDS)
        await message.answer(f"🗑 Команда <code>.{html.escape(cmd_name)}</code> удалена из списка~ 🌸", parse_mode="HTML")
    else:
        await message.answer(f"🥺 Команды <code>{html.escape(cmd_name)}</code> нет в списке 👉👈", parse_mode="HTML")


@dp.message()
async def handle_bot_dm_ai(message: types.Message):
    global last_owner_activity
    last_owner_activity = time.time()

    user_prompt = (message.text or message.caption or "").strip()
    if not user_prompt:
        await message.answer("🐾 Мур? Напиши мне что-нибудь текстом, и я с радостью отвечу uwu~")
        return

    for prefix in (".ai ", ".ии ", "/ai ", "/ии ", "!ai ", "!ии "):
        if user_prompt.lower().startswith(prefix):
            user_prompt = user_prompt[len(prefix):].strip()
            break

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    reply = await ask_ai(message.chat.id, user_prompt, mode="normal")
    await message.answer(reply)


@dp.business_message()
async def handle_business_message(message: types.Message):
    global last_owner_activity, manual_afk

    conn_id = message.business_connection_id
    owner_chat_id = await get_owner_chat_id(conn_id)

    if message.from_user.id == owner_chat_id:
        last_owner_activity = time.time()

    partner_title = message.chat.full_name or "Милашка"
    chat_stat = get_chat_stat(message.chat.id, partner_title)
    chat_stat["messages"] += 1
    save_stats(CHAT_STATS)

    media_type = None
    file_id = None
    if message.photo:
        media_type, file_id = "photo", message.photo[-1].file_id
    elif message.voice:
        media_type, file_id = "voice", message.voice.file_id
    elif message.video_note:
        media_type, file_id = "video_note", message.video_note.file_id
    elif message.video:
        media_type, file_id = "video", message.video.file_id
    elif message.document:
        media_type, file_id = "document", message.document.file_id

    # Сохраняем в кэш и скачиваем медиа ТОЛЬКО от собеседника (свои фото не кэшируем)
    if message.from_user.id != owner_chat_id:
        raw_bytes = None
        if media_type and file_id:
            raw_bytes = await download_media_bytes(file_id)
            if is_secret_or_timer_media(message):
                chat_stat["secret_media_caught"] += 1
                save_stats(CHAT_STATS)
                sender = html.escape(message.from_user.full_name)
                caption = html.escape(message.caption or "[без подписи]")
                header = f"📸🔥 <b>Поймана секретка / медиа с таймером</b> от <b>{sender}</b>:\n\n<blockquote>{caption}</blockquote>"
                try:
                    await send_cached_media_to_owner(owner_chat_id, media_type, file_id, raw_bytes, header)
                except Exception as e:
                    print(f"[!] Не удалось отправить секретное медиа: {e}")

        if len(messages_cache) > 30:
            messages_cache.pop(next(iter(messages_cache)), None)

        messages_cache[(message.chat.id, message.message_id)] = {
            "sender_id": message.from_user.id,
            "sender_name": message.from_user.full_name,
            "text": message.text or message.caption or "",
            "media_type": media_type,
            "file_id": file_id,
            "raw_bytes": raw_bytes,
        }

    if not message.text:
        return

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
            cmd_name, action_text = [x.strip() for x in raw.split("=", 1)]
            cmd_name = cmd_name.lower().lstrip(".!/")
            if cmd_name and action_text:
                RP_COMMANDS[cmd_name] = [["🎀", action_text, "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"]]
                save_rp_commands(RP_COMMANDS)
                await bot.send_message(owner_chat_id, f"🌸 Команда <code>.{html.escape(cmd_name)}</code> добавлена~!", parse_mode="HTML")
        return

    if message.from_user.id == owner_chat_id and lower_stripped.startswith((".удрп ", "/del_rp ")):
        cmd_name = text_stripped.partition(" ")[2].strip().lower().lstrip(".!/")
        if cmd_name in RP_COMMANDS:
            del RP_COMMANDS[cmd_name]
            save_rp_commands(RP_COMMANDS)
            await bot.send_message(owner_chat_id, f"🗑 Команда <code>.{html.escape(cmd_name)}</code> удалена~!", parse_mode="HTML")
        return

    if text_stripped.startswith((".", "/", "!")):
        cmd_parts = text_stripped[1:].strip().split(maxsplit=1)
        cmd_word = cmd_parts[0].lower() if cmd_parts else ""
        cmd_arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

        if cmd_word in ("афк", "afk") and message.from_user.id == owner_chat_id:
            manual_afk = not manual_afk
            if not manual_afk:
                last_owner_activity = time.time()
            await bot.send_message(
                owner_chat_id,
                "🌙 Режим «Не в сети» ВКЛЮЧЁН!" if manual_afk else "☀️ Режим «Не в сети» ВЫКЛЮЧЕН!",
            )
            return

        if cmd_word in ("ии", "ai", "gpt", "нейро"):
            prompt_text = cmd_arg or ((message.reply_to_message.text or message.reply_to_message.caption or "") if message.reply_to_message else "")
            if not prompt_text:
                await send_business_reply(message.chat.id, "🥺 Напиши вопрос после команды <code>.ии</code> 👉👈", conn_id, partner_title)
                return
            ai_reply = await ask_ai(message.chat.id, prompt_text, mode="normal", partner_name=partner_title)
            await send_business_reply(message.chat.id, f"🤖🐾 <b>Ответ ИИ:</b>\n<blockquote>{html.escape(ai_reply)}</blockquote>", conn_id, partner_title)
            return

        if cmd_word in ("инфа", "шар", "infa", "ball"):
            if not cmd_arg:
                await send_business_reply(message.chat.id, "🔮 Напиши вопрос после команды, например: <code>.инфа мы пойдём гулять</code> 👉👈", conn_id, partner_title)
                return
            pct = random.randint(0, 100)
            verdict = "Ура-ура, почти наверняка! (◕‿◕)♡" if pct >= 50 else "Кажется, шансов маловато... 🥺👉👈"
            await send_business_reply(
                message.chat.id,
                f"🔮 <b>Шар судьбы мурлычет:</b>\nВероятность того, что <i>«{html.escape(cmd_arg)}»</i> — <b>{pct}%</b>!\n╰┈➤ {verdict}",
                conn_id, partner_title,
            )
            return

        if cmd_word in ("шип", "любовь", "ship", "love"):
            pct = random.randint(0, 100)
            comment = (
                "Идеальная парочка котиков! Срочно обниматься~ 🐾💞" if pct >= 85 else
                "Очень милый вайб, у вас всё получится~ (⁄ ⁄•⁄ω⁄•⁄ ⁄)" if pct >= 50 else
                "Нужно больше вкусняшек и белых Монстров для укрепления связи! 🥫🌸" if pct >= 20 else
                "Кто-то сегодня вредничает и кусается! >_<"
            )
            await send_business_reply(
                message.chat.id,
                f"💘 <b>Проверка любви:</b>\nСовместимость <b>{sender_name}</b> и <b>{html.escape(partner_title)}</b> сегодня — <b>{pct}%</b>!\n╰┈➤ <i>{comment}</i>",
                conn_id, partner_title,
            )
            return

        if cmd_word in ("милота", "фембойтест", "няшность", "cute", "femboy"):
            tested_user = html.escape(message.reply_to_message.from_user.full_name) if (message.reply_to_message and message.reply_to_message.from_user) else sender_name
            pct = random.randint(0, 100)
            rank = (
                "Суровый гигачад, ни одного чулочка в шкафу 🗿" if pct <= 20 else
                "Начинающий котик, уже засматривается на розовые оверсайз-худи 👉👈" if pct <= 55 else
                "Сертифицированная милашка, кошачьи ушки сидят как влитые! 🐾🌸" if pct <= 85 else
                "Ультра-фембойчик 1000 lvl в полосатых чулочках и с баночкой белого Монстра! 🧦🥫💖"
            )
            await send_business_reply(
                message.chat.id,
                f"🌸 <b>Сканер милоты завершил проверку!</b>\nУровень няшности <b>{tested_user}</b> — <b>{pct}%</b>!\n╰┈➤ 🎀 <i>Вердикт: {rank}</i>",
                conn_id, partner_title,
            )
            return

        if cmd_word in ("выбор", "choose", "или"):
            if " или " not in cmd_arg.lower():
                await send_business_reply(message.chat.id, "🎀 Напиши два варианта через «или», например:\n<code>.выбор пойти спать или пить монстр</code>", conn_id, partner_title)
                return
            idx = cmd_arg.lower().find(" или ")
            chosen = random.choice([cmd_arg[:idx].strip(), cmd_arg[idx + 5 :].strip()])
            await send_business_reply(message.chat.id, f"🐾 <b>Лапки сделали выбор:</b>\nКонечно же <b>«{html.escape(chosen)}»</b>! uwu~ ✨", conn_id, partner_title)
            return

        if cmd_word == "uwu":
            source_text = cmd_arg or ((message.reply_to_message.text or message.reply_to_message.caption or "") if message.reply_to_message else "")
            if not source_text:
                await send_business_reply(message.chat.id, "🥺 Ответь командой <code>.uwu</code> на сообщение или напиши <code>.uwu свой текст</code>!", conn_id, partner_title)
                return
            await send_business_reply(message.chat.id, f"🌸 <b>UwU-переводчик:</b>\n<blockquote>{html.escape(uwuify_text(source_text))}</blockquote>", conn_id, partner_title)
            return

        if cmd_word in ("брак", "marry"):
            if chat_stat.get("married_since"):
                dur = format_duration(int(time.time() - chat_stat["married_since"]))
                await send_business_reply(message.chat.id, f"💍 Вы с <b>{html.escape(partner_title)}</b> уже в счастливом браке целых <b>{dur}</b>! (◕‿◕)♡", conn_id, partner_title)
            else:
                chat_stat["married_since"] = time.time()
                save_stats(CHAT_STATS)
                await send_business_reply(
                    message.chat.id,
                    f"💍🌸 <b>Горько!</b>\n<b>{sender_name}</b> и <b>{html.escape(partner_title)}</b> теперь официально в няшном браке! Обменялись чокерами и кольцами~ 🎀💞\n╰┈➤ <i>Проверить стаж: <code>.мы</code></i>",
                    conn_id, partner_title,
                )
            return

        if cmd_word in ("развод", "divorce"):
            if not chat_stat.get("married_since"):
                await send_business_reply(message.chat.id, "🥺 Вы и так пока не состоите в браке 👉👈 (заключить: <code>.брак</code>)", conn_id, partner_title)
            else:
                dur = format_duration(int(time.time() - chat_stat["married_since"]))
                chat_stat["married_since"] = None
                save_stats(CHAT_STATS)
                await send_business_reply(message.chat.id, f"💔🥺 <b>Брак расторгнут...</b>\nВы пробыли вместе <b>{dur}</b>, но котики решили пойти разными дорожками.", conn_id, partner_title)
            return

        if cmd_word in ("мы", "we"):
            if not chat_stat.get("married_since"):
                await send_business_reply(message.chat.id, f"🐾 Вы с <b>{html.escape(partner_title)}</b> пока не в браке! Чтобы пожениться, напиши <code>.брак</code> 💍", conn_id, partner_title)
            else:
                dur = format_duration(int(time.time() - chat_stat["married_since"]))
                await send_business_reply(
                    message.chat.id,
                    f"💞 <b>Ваш любовный уголок с {html.escape(partner_title)}:</b>\n\n💍 <b>Вместе уже:</b> {dur}\n🌸 <b>Всего РП-нежностей:</b> {chat_stat['rp_total']}\n💬 <b>Сообщений в чате:</b> {chat_stat['messages']}",
                    conn_id, partner_title,
                )
            return

        if cmd_word in ("стата", "stats"):
            married_str = f"💍 В браке ({format_duration(int(time.time() - chat_stat['married_since']))})" if chat_stat.get("married_since") else "Свободны котики 🐾"
            top_rp = sorted(chat_stat.get("rp_breakdown", {}).items(), key=lambda x: x[1], reverse=True)[:5]
            top_lines = "\n".join([f"  • <code>.{k}</code> — {v} раз(а)" for k, v in top_rp]) if top_rp else "  Пока ни одной команды 🥺"
            await send_business_reply(
                message.chat.id,
                f"📊 <b>Няшная статистика чата с {html.escape(partner_title)}:</b>\n\n💬 <b>Сообщений записано:</b> {chat_stat['messages']}\n🎭 <b>Всего РП-действий:</b> {chat_stat['rp_total']}\n📸 <b>Секретных фото поймано:</b> {chat_stat.get('secret_media_caught', 0)}\n💖 <b>Статус:</b> {married_str}\n\n🏆 <b>Топ ваших действий:</b>\n{top_lines}",
                conn_id, partner_title,
            )
            return

        if cmd_word in ("инфо", "info"):
            uname = f"@{message.chat.username}" if message.chat.username else "скрыт"
            await send_business_reply(
                message.chat.id,
                f"🪪 <b>Карточка котика {html.escape(partner_title)}:</b>\n\n🆔 <b>Telegram ID:</b> <code>{message.chat.id}</code>\n🔗 <b>Юзернейм:</b> {uname}\n💬 <b>Сообщений в базе:</b> {chat_stat['messages']}\n✏️ <b>Изменено сообщений:</b> {chat_stat['edited_caught']}\n🐾 <b>Удалено сообщений:</b> {chat_stat['deleted_caught']}\n📸 <b>Секретных фоток сохранено:</b> {chat_stat.get('secret_media_caught', 0)}",
                conn_id, partner_title,
            )
            return

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
            conn_id, partner_title,
        )
        return

    if message.from_user.id != owner_chat_id and is_owner_offline():
        now = time.time()
        if now - afk_last_reply_time.get(message.chat.id, 0) >= 15:
            afk_last_reply_time[message.chat.id] = now
            ai_reply = await ask_ai(message.chat.id, text_stripped, mode="afk", partner_name=partner_title)
            await send_business_reply(
                message.chat.id,
                f"🌙🐾 <b>[Автоответчик ЧВК «Мягкие Лапки»]:</b>\n<blockquote>{html.escape(ai_reply)}</blockquote>",
                conn_id, partner_title,
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

    old_data = messages_cache.get((message.chat.id, message.message_id))
    old_text = html.escape(old_data["text"]) if old_data and old_data["text"] else "[не сохранено в кэше]"
    new_text = html.escape(message.text or message.caption or "[без текста]")
    sender = html.escape(message.from_user.full_name)
    if old_data:
        old_data["text"] = message.text or message.caption or ""

    await bot.send_message(
        chat_id=owner_chat_id,
        text=(
            f"🌸 <b>Изменено сообщение</b> от <b>{sender}</b> (👀):\n\n"
            f"🎀 <b>Было:</b>\n<blockquote>{old_text}</blockquote>\n"
            f"✨ <b>Стало:</b>\n<blockquote>{new_text}</blockquote>"
        ),
        parse_mode="HTML",
    )


@dp.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    conn_id = event.business_connection_id
    owner_chat_id = await get_owner_chat_id(conn_id)
    chat_stat = get_chat_stat(event.chat.id, event.chat.full_name or "Собеседник")

    for msg_id in event.message_ids:
        data = messages_cache.pop((event.chat.id, msg_id), None)
        if not data or data["sender_id"] == owner_chat_id:
            continue

        chat_stat["deleted_caught"] += 1
        if data["media_type"] in ("photo", "video", "video_note", "voice"):
            chat_stat["secret_media_caught"] = chat_stat.get("secret_media_caught", 0) + 1
        save_stats(CHAT_STATS)

        sender = html.escape(data["sender_name"])
        saved_text = html.escape(data["text"]) if data["text"] else "[без текста]"
        header = f"🐾 <b>Удалено / исчезло сообщение</b> от <b>{sender}</b> (не спрячешься~ :3):\n\n<blockquote>{saved_text}</blockquote>"

        await send_cached_media_to_owner(
            owner_chat_id=owner_chat_id,
            m_type=data["media_type"],
            f_id=data["file_id"],
            raw_bytes=data.get("raw_bytes"),
            header=header,
        )


async def main():
    await setup_bot_commands()
    model = await resolve_ai_model()
    print(f"🌸 Бот успешно запущен! ИИ-модель: {model} | Защита секреток и AFK-режим активны!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🐾 Бот спокойно остановлен, лапки отдыхают~")
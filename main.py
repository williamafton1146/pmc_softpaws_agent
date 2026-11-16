import asyncio
import html
import io
import json
import os
import random
import time
from openai import AsyncOpenAI
from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline

# ==================== НАСТРОЙКИ ====================
# Данные от my.telegram.org (ОБЯЗАТЕЛЬНО ЗАПОЛНИ СВОИ)
TG_API_ID = 611335
TG_API_HASH = "d524b414d21f4d37f08684c1df41ac9d"

# Настройка ИИ (provod.ai)
AI_CLIENT = AsyncOpenAI(
    api_key="sk_f3690e852e2088bacc4bee7017e56bbd74beafccc2ae2672",
    base_url="https://api.provod.ai/v1",
)
ACTIVE_AI_MODEL = None
AVAILABLE_AI_MODELS = []

client = TelegramClient("softpaws_pure_telethon", TG_API_ID, TG_API_HASH)
OWNER_ID = None

messages_cache = {}  # msg_id -> dict
ai_history = {}
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
        except Exception:
            pass
    save_rp_commands(data)
    return data


def load_stats() -> dict:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
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


async def is_owner_offline_real() -> bool:
    if manual_afk:
        return True
    try:
        me = await client.get_entity("me")
        return not isinstance(me.status, UserStatusOnline)
    except Exception:
        return False


async def resolve_ai_model() -> str:
    global ACTIVE_AI_MODEL, AVAILABLE_AI_MODELS
    if ACTIVE_AI_MODEL:
        return ACTIVE_AI_MODEL
    preferred = [
        "deepseek-v4-flash", "gemini-3.1-flash-lite", "qwen3-max-preview",
        "qwen3.7-max", "glm-5.3-flash", "claude-fable-5.1",
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
    except Exception:
        pass
    ACTIVE_AI_MODEL = "deepseek-v4-flash"
    return ACTIVE_AI_MODEL


async def ask_ai(chat_id: int, user_text: str, mode: str = "normal", partner_name: str = "Собеседник") -> str:
    global ACTIVE_AI_MODEL
    model_name = await resolve_ai_model()

    if mode == "afk":
        system_prompt = (
            f"Ты милый фембойчик-ассистент из ЧВК «Мягкие Лапки». "
            f"Хозяин аккаунта сейчас не в сети, поэтому ты отвечаешь его собеседнику по имени {partner_name}. "
            f"Отвечай коротко, с каомодзи (uwu, :3, 👉👈) и в мужском роде."
        )
    else:
        system_prompt = (
            "Ты милый, умный фембойчик-ассистент из ЧВК «Мягкие Лапки». "
            "Отвечай полезно, с каомодзи (uwu, :3, 👉👈) и в мужском роде."
        )

    history = ai_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    if len(history) > 8:
        history[:] = history[-8:]

    messages_payload = [{"role": "system", "content": system_prompt}] + history
    candidates = [model_name] + AVAILABLE_AI_MODELS + ["deepseek-v4-flash", "gemini-3.1-flash-lite"]

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


async def send_or_edit(event: events.NewMessage.Event, text: str):
    """Если команду написал владелец — редактирует сообщение, если собеседник — отвечает"""
    if event.out:
        await event.edit(text, parse_mode="html")
    else:
        await event.reply(text, parse_mode="html")


# ==================== ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ TELETHON ====================

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_private_message(event: events.NewMessage.Event):
    global manual_afk
    msg = event.message
    chat = await event.get_chat()
    sender = await event.get_sender()

    partner_title = f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip() or "Милашка"
    sender_name = html.escape(
        f"{getattr(sender, 'first_name', '')} {getattr(sender, 'last_name', '')}".strip() or "Котик"
    )

    # Если пишем сами себе в «Избранное» — там работает прямой чат с ИИ и команды управления
    if event.chat_id == OWNER_ID:
        txt = (msg.message or "").strip()
        if txt == ".афк" or txt == "/afk":
            manual_afk = not manual_afk
            await event.reply(
                "🌙 Режим «Не в сети» ВКЛЮЧЁН!" if manual_afk else "☀️ Режим ВЫКЛЮЧЕН (смотрю по реальному онлайну)!"
            )
            return
        if txt == ".рп" or txt == "/rp":
            lines = [f"{format_rp_action(v)[0]} .{k} — {format_rp_action(v)[1]}~" for k, v in RP_COMMANDS.items()]
            await event.reply("🎀 Доступные РП-команды:\n\n" + "\n".join(lines))
            return
        if txt.startswith((".ai ", ".ии ")):
            reply = await ask_ai(OWNER_ID, txt[4:].strip(), mode="normal")
            await event.reply(f"🤖🐾 <b>ИИ:</b>\n<blockquote>{html.escape(reply)}</blockquote>", parse_mode="html")
        return

    chat_stat = get_chat_stat(event.chat_id, partner_title)
    chat_stat["messages"] += 1
    save_stats(CHAT_STATS)

    # 1. ПЕРЕХВАТ МЕДИА И ТАЙМЕРОВ ОТ СОБЕСЕДНИКА
    if not event.out:
        raw_bytes = None
        ext = ".bin"
        if msg.media:
            if msg.photo:
                ext = ".jpg"
            elif msg.voice:
                ext = ".ogg"
            elif msg.video or msg.video_note:
                ext = ".mp4"
            buf = io.BytesIO()
            await client.download_media(msg, file=buf)
            raw_bytes = buf.getvalue()

            ttl = getattr(msg.media, "ttl_seconds", None)
            if ttl:
                chat_stat["secret_media_caught"] += 1
                save_stats(CHAT_STATS)
                file_obj = io.BytesIO(raw_bytes)
                file_obj.name = f"timer_secret{ext}"
                caption = html.escape(msg.message or "[без подписи]")
                await client.send_file(
                    "me",
                    file=file_obj,
                    caption=(
                        f"📸🔥 <b>Поймано медиа с таймером ({ttl} сек)</b> от <b>{sender_name}</b>:\n\n"
                        f"<blockquote>{caption}</blockquote>"
                    ),
                    parse_mode="html",
                )
                print(f"[СЕКРЕТ] Сохранено медиа с таймером от {sender_name} в Избранное!")

        if len(messages_cache) > 40:
            messages_cache.pop(next(iter(messages_cache)), None)
        messages_cache[msg.id] = {
            "chat_id": event.chat_id,
            "sender_name": sender_name,
            "text": msg.message or "",
            "raw_bytes": raw_bytes,
            "ext": ext,
        }

    if not msg.message:
        return

    text_stripped = msg.message.strip()
    lower_stripped = text_stripped.lower()
    target_name = html.escape(partner_title) if event.out else "тебя"

    # Добавление/удаление своих РП-команд
    if event.out and lower_stripped.startswith((".дерп ", "/add_rp ")):
        raw = text_stripped.partition(" ")[2].strip()
        if "=" in raw:
            cmd_name, action_text = [x.strip() for x in raw.split("=", 1)]
            cmd_name = cmd_name.lower().lstrip(".!/")
            RP_COMMANDS[cmd_name] = [["🎀", action_text, "(⁄ ⁄•⁄ω⁄•⁄ ⁄)"]]
            save_rp_commands(RP_COMMANDS)
            await event.edit(f"🌸 Команда <code>.{html.escape(cmd_name)}</code> добавлена~!", parse_mode="html")
        return

    if event.out and lower_stripped.startswith((".удрп ", "/del_rp ")):
        cmd_name = text_stripped.partition(" ")[2].strip().lower().lstrip(".!/")
        if cmd_name in RP_COMMANDS:
            del RP_COMMANDS[cmd_name]
            save_rp_commands(RP_COMMANDS)
            await event.edit(f"🗑 Команда <code>.{html.escape(cmd_name)}</code> удалена~!", parse_mode="html")
        return

    # 2. МИНИ-ИГРЫ, СТАТИСТИКА И ВЫЗОВ ИИ
    if text_stripped.startswith((".", "/", "!")):
        cmd_parts = text_stripped[1:].strip().split(maxsplit=1)
        cmd_word = cmd_parts[0].lower() if cmd_parts else ""
        cmd_arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

        if cmd_word in ("афк", "afk") and event.out:
            manual_afk = not manual_afk
            await event.edit(
                "🌙 Режим «Не в сети» ВКЛЮЧЁН!" if manual_afk else "☀️ Режим «Не в сети» ВЫКЛЮЧЕН!",
                parse_mode="html",
            )
            return

        if cmd_word in ("ии", "ai", "gpt", "нейро") and cmd_arg:
            ai_reply = await ask_ai(event.chat_id, cmd_arg, mode="normal", partner_name=partner_title)
            await send_or_edit(
                event, f"🤖🐾 <b>Ответ ИИ:</b>\n<blockquote>{html.escape(ai_reply)}</blockquote>"
            )
            return

        if cmd_word in ("инфа", "шар", "infa", "ball") and cmd_arg:
            pct = random.randint(0, 100)
            verdict = "Ура-ура, почти наверняка! (◕‿◕)♡" if pct >= 50 else "Кажется, шансов маловато... 🥺👉👈"
            await send_or_edit(
                event,
                f"🔮 <b>Шар судьбы мурлычет:</b>\nВероятность того, что <i>«{html.escape(cmd_arg)}»</i> — <b>{pct}%</b>!\n╰┈➤ {verdict}",
            )
            return

        if cmd_word in ("шип", "любовь", "ship", "love"):
            pct = random.randint(0, 100)
            await send_or_edit(
                event,
                f"💘 <b>Проверка любви:</b>\nСовместимость с <b>{html.escape(partner_title)}</b> сегодня — <b>{pct}%</b>! 🐾💞",
            )
            return

        if cmd_word in ("милота", "фембойтест", "няшность", "cute", "femboy"):
            pct = random.randint(0, 100)
            await send_or_edit(
                event,
                f"🌸 <b>Сканер милоты:</b>\nУровень няшности <b>{sender_name}</b> — <b>{pct}%</b>! 🧦🥫💖",
            )
            return

        if cmd_word in ("выбор", "choose", "или") and " или " in cmd_arg.lower():
            idx = cmd_arg.lower().find(" или ")
            chosen = random.choice([cmd_arg[:idx].strip(), cmd_arg[idx + 5:].strip()])
            await send_or_edit(event, f"🐾 <b>Лапки выбрали:</b> <b>«{html.escape(chosen)}»</b>! uwu~ ✨")
            return

        if cmd_word == "uwu" and cmd_arg:
            await send_or_edit(
                event, f"🌸 <b>UwU-переводчик:</b>\n<blockquote>{html.escape(uwuify_text(cmd_arg))}</blockquote>"
            )
            return

        if cmd_word in ("брак", "marry"):
            if not chat_stat.get("married_since"):
                chat_stat["married_since"] = time.time()
                save_stats(CHAT_STATS)
            dur = format_duration(int(time.time() - chat_stat["married_since"]))
            await send_or_edit(
                event, f"💍🌸 Вы с <b>{html.escape(partner_title)}</b> в счастливом браке уже <b>{dur}</b>! (◕‿◕)♡"
            )
            return

        if cmd_word in ("развод", "divorce"):
            chat_stat["married_since"] = None
            save_stats(CHAT_STATS)
            await send_or_edit(event, "💔🥺 Брак расторгнут...")
            return

        if cmd_word in ("мы", "we", "стата", "stats", "инфо", "info"):
            await send_or_edit(
                event,
                f"📊 <b>Няшная статистика с {html.escape(partner_title)}:</b>\n\n"
                f"💬 Сообщений: {chat_stat['messages']} | 🎭 РП: {chat_stat['rp_total']}\n"
                f"✏️ Изменено: {chat_stat['edited_caught']} | 🐾 Удалено: {chat_stat['deleted_caught']}\n"
                f"📸 Секреток сохранено: {chat_stat.get('secret_media_caught', 0)}",
            )
            return

    # 3. РП-КОМАНДЫ
    clean_text = text_stripped.lstrip(".!/").strip()
    clean_lower = clean_text.lower()
    first_word = clean_lower.split()[0] if clean_lower else ""

    matched_cmd = SLASH_RP_ALIASES.get(first_word) if first_word in SLASH_RP_ALIASES else None
    extra_text = clean_text.split(maxsplit=1)[1] if (matched_cmd and len(clean_text.split(maxsplit=1)) > 1) else ""

    if not matched_cmd:
        for cmd_key in sorted(RP_COMMANDS.keys(), key=len, reverse=True):
            if clean_lower == cmd_key or clean_lower.startswith(cmd_key + " "):
                matched_cmd = cmd_key
                extra_text = clean_text[len(cmd_key):].strip()
                break

    if matched_cmd:
        emoji, verb, suffix = format_rp_action(RP_COMMANDS[matched_cmd])
        extra_comment = f"\n╰┈➤ 💭 <i>Реплика: {html.escape(extra_text)}</i> 🎀" if extra_text else ""
        chat_stat["rp_total"] += 1
        save_stats(CHAT_STATS)
        await send_or_edit(
            event,
            f"{emoji} <b>{sender_name}</b> {html.escape(verb)} <b>{target_name}</b> {html.escape(suffix)}~{extra_comment}",
        )
        return

    # 4. АВТООТВЕТЧИК ИИ ПО РЕАЛЬНОМУ ОФЛАЙНУ
    if not event.out and await is_owner_offline_real():
        now = time.time()
        if now - afk_last_reply_time.get(event.chat_id, 0) >= 15:
            afk_last_reply_time[event.chat_id] = now
            ai_reply = await ask_ai(event.chat_id, text_stripped, mode="afk", partner_name=partner_title)
            await event.reply(
                f"🌙🐾 <b>[Автоответчик ЧВК «Мягкие Лапки»]:</b>\n<blockquote>{html.escape(ai_reply)}</blockquote>",
                parse_mode="html",
            )


# ==================== ЛОГГЕР ИЗМЕНЕНИЙ И УДАЛЕНИЙ В «ИЗБРАННОЕ» ====================

@client.on(events.MessageEdited(func=lambda e: e.is_private))
async def handle_edited(event: events.MessageEdited.Event):
    if event.out or event.chat_id == OWNER_ID:
        return
    old_data = messages_cache.get(event.message.id)
    old_text = html.escape(old_data["text"]) if old_data and old_data["text"] else "[не сохранено]"
    new_text = html.escape(event.message.message or "[без текста]")
    if old_text == new_text:
        return

    sender = await event.get_sender()
    sender_name = html.escape(getattr(sender, "first_name", "Собеседник"))
    if old_data:
        old_data["text"] = event.message.message or ""

    chat_stat = get_chat_stat(event.chat_id, sender_name)
    chat_stat["edited_caught"] += 1
    save_stats(CHAT_STATS)

    await client.send_message(
        "me",
        f"🌸 <b>Изменено сообщение</b> от <b>{sender_name}</b>:\n\n"
        f"🎀 <b>Было:</b>\n<blockquote>{old_text}</blockquote>\n"
        f"✨ <b>Стало:</b>\n<blockquote>{new_text}</blockquote>",
        parse_mode="html",
    )


@client.on(events.MessageDeleted())
async def handle_deleted(event: events.MessageDeleted.Event):
    for msg_id in event.deleted_ids:
        data = messages_cache.pop(msg_id, None)
        if not data:
            continue
        chat_stat = get_chat_stat(data["chat_id"], data["sender_name"])
        chat_stat["deleted_caught"] += 1
        save_stats(CHAT_STATS)

        saved_text = html.escape(data["text"]) if data["text"] else "[без текста]"
        header = (
            f"🐾 <b>Удалено сообщение</b> от <b>{data['sender_name']}</b> (не спрячешься~ :3):\n\n"
            f"<blockquote>{saved_text}</blockquote>"
        )
        if data["raw_bytes"]:
            file_obj = io.BytesIO(data["raw_bytes"])
            file_obj.name = f"deleted_media{data['ext']}"
            await client.send_file("me", file=file_obj, caption=header, parse_mode="html")
        else:
            await client.send_message("me", header, parse_mode="html")


async def main():
    global OWNER_ID
    print("🐾 Запуск чистого Telethon-юзербота...")
    await client.start()
    me = await client.get_me()
    OWNER_ID = me.id
    model = await resolve_ai_model()
    print(f"🌸 Юзербот ЧВК «Мягкие Лапки» запущен на аккаунте {me.first_name}! ИИ: {model}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
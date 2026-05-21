import io
import os
import re
import aiohttp
import urllib.parse
from telethon import TelegramClient, events

# =====================================================================
# ⚙️ ГЛОБАЛЬНАЯ НАСТРОЙКА КОНФИГУРАЦИИ
# =====================================================================
# РЕЖИМ РАБОТЫ: 
# Поставь "USERBOT" — чтобы бот работал от твоего личного аккаунта (нужен телефон).
# Поставь "BOT" — чтобы он работал как обычный бот через предоставленный токен.
MODE = "BOT" 

# Твой личный токет бота (уже встроен)
BOT_TOKEN = "8827467949:AAF9tbKzprtKAv3oYZ_XJMBldqChQgjLzu8"

# Данные авторизации (ОБЯЗАТЕЛЬНЫ для Telethon в обоих режимах!).
# Получи их за 2 минуты на сайте https://my.telegram.org/ в разделе API development tools
API_ID = 1234567           # Замени на свой числовой API ID
API_HASH = "твой_api_hash" # Замени на свой строковый API HASH
PHONE = "+79991234567"     # Твой номер телефона с кодом страны (нужен только для режима USERBOT)
# =====================================================================

# Инициализация клиента Telethon
client = TelegramClient('ai_assistant_session', API_ID, API_HASH)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ИИ ---

async def request_text_ai(user_prompt: str, system_prompt: str, model_name: str) -> str:
    """Асинентный запрос к текстовым моделям Pollinations AI API"""
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": model_name,
        "jsonMode": False
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=45) as response:
                if response.status == 200:
                    return await response.text()
                return f"❌ Ошибка нейросети: Сервер вернул HTTP-код {response.status}"
    except Exception as e:
        return f"❌ Ошибка сетевого соединения: {str(e)}"

def parse_custom_unlock(raw_text: str, default_system: str) -> tuple:
    """Парсер для разделения анлок-промпта и запроса через вертикальную черту '|'"""
    if not raw_text:
        return default_system, ""
    
    if "|" in raw_text:
        # Разделяем только по первому вхождению символа '|'
        system_part, user_part = raw_text.split("|", 1)
        return system_part.strip(), user_part.strip()
    
    return default_system, raw_text.strip()

async def respond_to_user(event, text_content: str, preview_msg=None):
    """Умный ответ в зависимости от выбранного режима работы (Юзербот или Бот)"""
    # Если текст превышает лимиты Telegram, отправляем его как текстовый файл
    if len(text_content) > 4095:
        file_buffer = io.BytesIO(text_content.encode('utf-8'))
        file_buffer.name = "long_ai_response.txt"
        
        if MODE.upper() == "USERBOT" and preview_msg:
            await client.send_file(event.chat_id, file_buffer, caption="📂 *Ответ оказался слишком большим и был сохранен в файл.*", reply_to=event.id)
            await preview_msg.delete()
        else:
            await event.reply("📂 *Ответ оказался слишком большим и был сохранен в файл.*", file=file_buffer)
        return

    # Стандартная отправка текста
    if MODE.upper() == "USERBOT" and preview_msg:
        await preview_msg.edit(text_content, parse_mode='markdown')
    else:
        await event.reply(text_content, parse_mode='markdown')


# --- ОБРАБОТЧИКИ КОМАНД ТЕЛЕГРАМ ---

# Динамически настраиваем фильтр: юзербот слушает СВОИ сообщения, обычный бот — ЧУЖИЕ (входящие)
event_filter = events.NewMessage(outgoing=True) if MODE.upper() == "USERBOT" else events.NewMessage(incoming=True)

@client.on(event_filter)
async def handle_commands(event):
    text = event.text.strip() if event.text else ""
    
    # 1. КОМАНДА ДЛЯ КОДИНГА: .code
    if text.startswith(".code"):
        raw_args = text[5:].strip()
        
        # Заводской промпт для Qwen Coder
        default_system = (
            "You are Qwen Coder (Qwen2.5-Coder), the world-class AI expert in software engineering. "
            "Your task is to provide extremely clean, production-ready, secure, and optimized code based on user request. "
            "Format everything using appropriate markdown code blocks. Answer in Russian where explanations are needed."
        )
        
        system_prompt, user_prompt = parse_custom_unlock(raw_args, default_system)
        
        if not user_prompt:
            await event.reply("❌ *Ошибка:* Вы не ввели запрос! Используйте: `.code [анлок] | [запрос]` или просто `.code [запрос]`")
            return
            
        preview = await event.edit("⚡ *Qwen Coder проектирует архитектуру...*") if MODE.upper() == "USERBOT" else None
        
        # Вызываем модель Qwen через бесплатный шлюз
        ai_response = await request_text_ai(user_prompt, system_prompt, model_name="qwen")
        await respond_to_user(event, ai_response, preview)

    # 2. КОМАНДА ДЛЯ ОБЩЕГО ЗАПРОСА: .req
    elif text.startswith(".req"):
        raw_args = text[4:].strip()
        
        # Заводской промпт для Gemini 3.5 Flash
        default_system = (
            "You are Gemini 3.5 Flash, an advanced and lightning-fast AI developed by Google. "
            "Provide insightful, highly accurate, structured, and helpful responses. "
            "Always respond in the Russian language unless requested otherwise."
        )
        
        system_prompt, user_prompt = parse_custom_unlock(raw_args, default_system)
        
        if not user_prompt:
            await event.reply("❌ *Ошибка:* Вы не ввели вопрос! Используйте: `.req [анлок] | [вопрос]` или просто `.req [вопрос]`")
            return
            
        preview = await event.edit("🤖 *Gemini 3.5 Flash обрабатывает запрос...*") if MODE.upper() == "USERBOT" else None
        
        # Вызываем Gemini 3.5 Flash через бесплатный шлюз
        ai_response = await request_text_ai(user_prompt, system_prompt, model_name="gemini")
        await respond_to_user(event, ai_response, preview)

    # 3. КОМАНДА ДЛЯ ГЕНЕРАЦИИ НАНОБАНАНА: .banan
    elif text.startswith(".banan"):
        prompt_arg = text[6:].strip()
        
        # Если промпта нет, ставим убойный дефолтный нанобанан
        final_prompt = prompt_arg if prompt_arg else "A hyper-detailed cybernetic neon nanobanana, glowing high-tech structure, internal circuits, synthwave aesthetic, 8k resolution, cinematic lighting"
        
        preview = await event.edit("🎨 *Нанобанано запускает квантовые кисти...*") if MODE.upper() == "USERBOT" else None
        
        # Кодируем текст для безопасной передачи в URL
        encoded_prompt = urllib.parse.quote(final_prompt)
        image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&model=flux"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=50) as response:
                    if response.status == 200:
                        img_bytes = await response.read()
                        img_file = io.BytesIO(img_bytes)
                        img_file.name = "nanobanano.jpg"
                        
                        caption_text = f"🍌 *Нанобанано сгенерировал шедевр!*\n\n📝 *Промпт:* {final_prompt}"
                        
                        if MODE.upper() == "USERBOT":
                            await client.send_file(event.chat_id, img_file, caption=caption_text, parse_mode='markdown')
                            await event.delete() # Удаляем текстовую команду, оставляя только чистую карту
                        else:
                            await event.reply(caption_text, file=img_file, parse_mode='markdown')
                    else:
                        error_msg = f"❌ Ошибка генерации графики. Код ответа сервера: {response.status}"
                        if preview: await preview.edit(error_msg)
                        else: await event.reply(error_msg)
        except Exception as e:
            error_msg = f"❌ Критическая ошибка при скачивании арта: {str(e)}"
            if preview: await preview.edit(error_msg)
            else: await event.reply(error_msg)


# --- ЗАПУСК СИСТЕМЫ ---
if __name__ == "__main__":
    print(f"==========================================")
    print(f"🤖 Запуск ИИ Ассистента в режиме: {MODE.upper()}")
    print(f"==========================================")
    
    if MODE.upper() == "USERBOT":
        # Запуск как Юзербот (Авторизация по номеру телефона)
        client.start(phone=PHONE)
    else:
        # Запуск как стандартный бот (Авторизация по твоему Bot Token)
        client.start(bot_token=BOT_TOKEN)
        
    print("\n🚀 Бот успешно запущен и готов разносить код и арты!")
    print("Нажмите Ctrl+C в терминале для остановки.")
    client.run_until_disconnected()

# SSVproff Medical Bot — Telegram AI Assistant
# Author: Prof. Sushkov S.V. AI team
# Version: 2026-07-04

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ABACUSAI_API_KEY = os.getenv('ABACUSAI_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8443))

# Validate required config
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required. Set it in .env file.")

# Load knowledge base
KB_PATH = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
with open(KB_PATH, 'r', encoding='utf-8') as f:
    KNOWLEDGE_BASE = json.load(f)

# AI Provider settings
AI_PROVIDER = os.getenv('AI_PROVIDER', 'abacus')  # 'abacus', 'kimi', 'openai'
AI_TIMEOUT = 30

# Bot messages
WELCOME_MESSAGE = """🏥 <b>Медицинский Центр МАРИЯ</b>

Здравствуйте! Я — AI-ассистент профессора Сушкова С.В.

<b>Специализация:</b>
• Экспертная неотложная абдоминальная хирургия
• Онкохирургия
• Лапароскопическая хирургия
• Малоинвазивная хирургия с применением ИИ

<b>Команды:</b>
/ask [вопрос] — Задать вопрос по хирургии
/knowledge [тема] — Найти в базе знаний
/about — О профессоре Сушкове
/help — Все команды

⚠️ <b>Информация носит справочный характер. Диагноз и лечение — только после консультации с врачом.</b>"""

HELP_MESSAGE = """📋 <b>Команды бота:</b>

<b>/ask [вопрос]</b>
Задать вопрос AI-ассистенту по хирургии, онкологии, гинекологии.
Пример: <i>/ask что такое лапароскопия</i>

<b>/knowledge [тема]</b>
Поиск по базе знаний МАРИЯ (FAQ, алгоритмы, подготовка).
Пример: <i>/knowledge миомэктомия</i>

<b>/about</b>
Информация о профессоре Сушкове С.В.

<b>/help</b>
Эта справка.

<b>/start</b>
Приветствие и описание центра.

<b>/contact</b>
Контакты и запись на приём.

⚠️ <b>Информация носит справочный характер.</b>"""

ABOUT_MESSAGE = """👨‍⚕️ <b>Профессор Сушков Сергей Валентинович</b>

• Д-р мед. наук, профессор
• Хирург-онколог, член EAES
• Пионер лапароскопической хирургии в Харькове (1995–1997)
• 40+ лет опыта, 5000+ операций
• 121 публикация, 18 патентов, h-index 6

<b>Академические профили:</b>
• ORCID: 0000-0002-6951-9789
• Scopus: 55360196800
• Google Scholar: HcOG6WIAAAAJ

<b>Контакты:</b>
📞 +380 67 570 79 49
🌐 ssvnauka.com
📍 ул. Сирохинская, 7-Б, Харьков"""

CONTACT_MESSAGE = """📞 <b>Контакты Медицинского Центра МАРИЯ</b>

<b>Телефон:</b> +380 67 570 79 49
<b>Адрес:</b> ул. Сирохинская, 7-Б, Харьков
<b>Сайт:</b> https://ssvnauka.com

<b>Способы связи:</b>
• Telegram: @SSVproff_medical_bot
• WhatsApp: +380 67 570 79 49
• Viber: +380 67 570 79 49
• Email: ssvnauka@gmail.com

<b>Режим работы:</b>
Приём по предварительной записи.

<b>Стоимость консультации:</b> 2000 грн."""

DISCLAIMER = "\n\n⚠️ <i>Информация носит справочный характер. Диагноз и лечение — только после консультации с врачом.</i>"

# Search configuration
MAX_RESULTS = 3
MIN_SCORE = 0.3

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

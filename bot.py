"""
SSVproff Medical Bot — Telegram AI Assistant for Medical Center MARIA
Author: Prof. Sushkov S.V. AI team
Version: 2026-07-04

Commands:
/start — Welcome message
/ask [question] — Ask medical AI assistant
/knowledge [topic] — Search knowledge base
/about — About Prof. Sushkov
/help — Command list
/contact — Contact info
"""

import logging
import re
import requests
import json
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from config import (
    TELEGRAM_BOT_TOKEN,
    ABACUSAI_API_KEY,
    KIMI_API_KEY,
    AI_PROVIDER,
    AI_TIMEOUT,
    KNOWLEDGE_BASE,
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    ABOUT_MESSAGE,
    CONTACT_MESSAGE,
    DISCLAIMER,
    MAX_RESULTS,
    MIN_SCORE,
    ADMIN_CHAT_ID,
    logger,
)


# ─────────────────────────── Knowledge Base Search ───────────────────────────

def normalize_text(text: str) -> str:
    """Normalize text for search: lowercase, remove extra spaces."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def score_entry(entry: dict, query: str) -> float:
    """Score how relevant an FAQ entry is to a query."""
    query_words = set(normalize_text(query).split())
    if not query_words:
        return 0.0

    # Score question match
    question_words = set(normalize_text(entry['question']).split())
    question_score = len(query_words & question_words) / len(query_words)

    # Score keyword match
    keywords = set(normalize_text(' '.join(entry.get('keywords', []))).split())
    keyword_score = len(query_words & keywords) / len(query_words) if keywords else 0

    # Score answer content match
    answer_words = set(normalize_text(entry['answer']).split())
    answer_score = len(query_words & answer_words) / len(query_words) if answer_words else 0

    # Weighted combination
    return question_score * 0.5 + keyword_score * 0.35 + answer_score * 0.15


def search_knowledge_base(query: str, max_results: int = MAX_RESULTS) -> list:
    """Search the FAQ knowledge base for relevant entries."""
    if not query or len(query) < 2:
        return []

    entries = KNOWLEDGE_BASE.get('entries', [])
    scored = []
    for entry in entries:
        score = score_entry(entry, query)
        if score >= MIN_SCORE:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


def get_algorithm_by_keyword(query: str) -> Optional[dict]:
    """Find a matching algorithm from the knowledge base."""
    query_norm = normalize_text(query)
    algorithms = KNOWLEDGE_BASE.get('algorithms', [])
    for alg in algorithms:
        title_norm = normalize_text(alg.get('title', ''))
        if any(word in title_norm for word in query_norm.split() if len(word) > 3):
            return alg
    return None


# ─────────────────────────── AI API Integration ───────────────────────────

def ask_ai_abacus(question: str) -> str:
    """Ask Abacus AI (GPT-4.1-mini) for a medical answer."""
    system_prompt = """Вы — профессиональный хирург-консультант, специализирующийся на абдоминальной хирургии, онкохирургии, лапароскопии и гинекологии. 
Вы отвечаете на вопросы пациентов и медицинских работников. 
Отвечайте профессионально, точно, с осторожностью, на русском языке. 
Если вопрос требует осмотра или может быть опасным — настоятельно рекомендуйте обратиться к врачу.
В конце каждого ответа добавьте: 'Информация носит справочный характер. Диагноз и лечение — только после консультации с врачом.'"""

    try:
        response = requests.post(
            'https://apps.abacus.ai/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {ABACUSAI_API_KEY}'
            },
            json={
                'model': 'gpt-4.1-mini',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                'max_tokens': 1500,
                'temperature': 0.7
            },
            timeout=AI_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Abacus AI error: {e}")
        raise


def ask_ai_kimi(question: str) -> str:
    """Ask Kimi API (Moonshot AI) for a medical answer."""
    system_prompt = """Вы — профессиональный хирург-консультант, специализирующийся на абдоминальной хирургии, онкохирургии, лапароскопии и гинекологии. 
Отвечайте профессионально, точно, на русском языке. 
В конце каждого ответа добавьте: 'Информация носит справочный характер. Диагноз и лечение — только после консультации с врачом.'"""

    try:
        response = requests.post(
            'https://api.moonshot.cn/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {KIMI_API_KEY}'
            },
            json={
                'model': 'moonshot-v1-8k',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                'temperature': 0.7
            },
            timeout=AI_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Kimi AI error: {e}")
        raise


def ask_ai(question: str) -> str:
    """Route to available AI provider."""
    providers = []
    if AI_PROVIDER == 'abacus' and ABACUSAI_API_KEY:
        providers.append(ask_ai_abacus)
    elif AI_PROVIDER == 'kimi' and KIMI_API_KEY:
        providers.append(ask_ai_kimi)
    else:
        # Try all available
        if ABACUSAI_API_KEY:
            providers.append(ask_ai_abacus)
        if KIMI_API_KEY:
            providers.append(ask_ai_kimi)

    if not providers:
        raise RuntimeError("No AI provider configured. Set ABACUSAI_API_KEY or KIMI_API_KEY.")

    last_error = None
    for provider_func in providers:
        try:
            return provider_func(question)
        except Exception as e:
            last_error = e
            continue

    raise last_error


# ─────────────────────────── Telegram Handlers ───────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    keyboard = [
        [InlineKeyboardButton("❓ Задать вопрос", callback_data='faq_menu')],
        [InlineKeyboardButton("📋 База знаний", callback_data='knowledge_menu')],
        [InlineKeyboardButton("👨‍⚕️ О профессоре", callback_data='about')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        WELCOME_MESSAGE,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_html(HELP_MESSAGE, disable_web_page_preview=True)


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command."""
    await update.message.reply_html(ABOUT_MESSAGE, disable_web_page_preview=True)


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contact command."""
    await update.message.reply_html(CONTACT_MESSAGE, disable_web_page_preview=True)


async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ask [question] command."""
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_html(
            "❓ Укажите вопрос после команды.\n"
            "Пример: <code>/ask что такое лапароскопия</code>\n\n"
            "Или выберите тему из базы знаний:",
            reply_markup=build_faq_keyboard()
        )
        return

    # Typing indicator
    await update.message.chat.send_action(action='typing')

    try:
        # 1. Try AI
        answer = ask_ai(question)
        await update.message.reply_html(answer, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"AI error for /ask: {e}")
        # 2. Fallback to knowledge base
        kb_results = search_knowledge_base(question)
        if kb_results:
            text = "🔍 <b>Найдено в базе знаний:</b>\n\n"
            for i, (score, entry) in enumerate(kb_results, 1):
                text += f"<b>{i}. {entry['question']}</b>\n{entry['answer'][:400]}"
                if len(entry['answer']) > 400:
                    text += "..."
                text += "\n\n"
            text += "⚠️ <i>AI-консультант временно недоступен. Ответ из базы знаний.</i>"
            await update.message.reply_html(text, disable_web_page_preview=True)
        else:
            await update.message.reply_html(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Пожалуйста, попробуйте позже или используйте /knowledge для поиска по базе знаний.\n\n"
                "📞 Для срочных вопросов: +380 67 570 79 49"
            )

        # Notify admin about error
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🚨 Bot Error\nUser: {update.effective_user.id}\nQuestion: {question}\nError: {e}"
                )
            except Exception:
                pass


async def knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /knowledge [topic] command."""
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_html(
            "🔍 Укажите тему для поиска.\n"
            "Пример: <code>/knowledge миомэктомия</code>\n\n"
            "Популярные темы:",
            reply_markup=build_faq_keyboard()
        )
        return

    await update.message.chat.send_action(action='typing')

    # Search FAQ
    results = search_knowledge_base(query)
    algorithm = get_algorithm_by_keyword(query)

    text = f"🔍 <b>Результаты поиска по теме:</b> <i>{query}</i>\n\n"

    if results:
        for i, (score, entry) in enumerate(results, 1):
            text += f"<b>{i}. {entry['question']}</b>\n{entry['answer'][:500]}"
            if len(entry['answer']) > 500:
                text += "..."
            text += "\n\n"
    else:
        text += "❌ По вашему запросу ничего не найдено в базе знаний.\n\n"
        text += "💡 Попробуйте другие слова или задайте вопрос через /ask.\n\n"

    if algorithm:
        text += f"📋 <b>Найден алгоритм:</b> {algorithm['title']}\n"
        text += "\n".join(f"  {i+1}. {step}" for i, step in enumerate(algorithm['steps']))
        text += "\n\n"

    text += DISCLAIMER
    await update.message.reply_html(text, disable_web_page_preview=True)


# ─────────────────────────── Inline Keyboard Builders ───────────────────────────

def build_faq_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for popular FAQ topics."""
    keyboard = [
        [InlineKeyboardButton("🩺 Лапароскопия", callback_data='topic_laparoscopy')],
        [InlineKeyboardButton("🎗️ Онкология", callback_data='topic_oncology')],
        [InlineKeyboardButton("🌸 Гинекология / Миома", callback_data='topic_gynecology')],
        [InlineKeyboardButton("💰 Цены и запись", callback_data='topic_prices')],
        [InlineKeyboardButton("🆘 Экстренные случаи", callback_data='topic_emergency')],
        [InlineKeyboardButton("📝 Подготовка к операции", callback_data='topic_preparation')],
    ]
    return InlineKeyboardMarkup(keyboard)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'faq_menu':
        await query.edit_message_text(
            "📋 <b>Выберите тему:</b>",
            reply_markup=build_faq_keyboard(),
            parse_mode='HTML'
        )
        return

    if data == 'knowledge_menu':
        await query.edit_message_text(
            "🔍 <b>База знаний МАРИЯ</b>\n\n"
            "Введите /knowledge [тема] или выберите раздел:",
            reply_markup=build_faq_keyboard(),
            parse_mode='HTML'
        )
        return

    if data == 'about':
        await query.edit_message_text(ABOUT_MESSAGE, parse_mode='HTML', disable_web_page_preview=True)
        return

    if data == 'contact':
        await query.edit_message_text(CONTACT_MESSAGE, parse_mode='HTML', disable_web_page_preview=True)
        return

    # Topic callbacks
    topic_map = {
        'topic_laparoscopy': 'лапароскопия',
        'topic_oncology': 'онкология рак',
        'topic_gynecology': 'миомэктомия гинекология',
        'topic_prices': 'цена консультация',
        'topic_emergency': 'экстренно острый живот',
        'topic_preparation': 'подготовка операция',
    }

    if data in topic_map:
        search_query = topic_map[data]
        results = search_knowledge_base(search_query, max_results=5)
        text = f"📋 <b>Результаты по теме:</b>\n\n"
        if results:
            for i, (score, entry) in enumerate(results, 1):
                text += f"<b>{i}. {entry['question']}</b>\n{entry['answer'][:500]}"
                if len(entry['answer']) > 500:
                    text += "..."
                text += "\n\n"
        else:
            text += "Нет результатов в базе.\n"
        text += "\n❓ Задать вопрос: /ask [вопрос]"
        await query.edit_message_text(text, parse_mode='HTML', disable_web_page_preview=True)
        return

    # Default: echo
    await query.edit_message_text(f"⚠️ Неизвестная команда: {data}", parse_mode='HTML')


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown text messages."""
    await update.message.reply_html(
        "❓ Я не понял ваше сообщение.\n\n"
        "Используйте команды:\n"
        "• /ask [вопрос] — вопрос AI-ассистенту\n"
        "• /knowledge [тема] — поиск в базе знаний\n"
        "• /about — о профессоре\n"
        "• /contact — контакты\n"
        "• /help — все команды\n\n"
        "Или выберите тему:",
        reply_markup=build_faq_keyboard()
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_html(
            "⚠️ Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.\n"
            "Если ошибка повторяется — обратитесь по телефону +380 67 570 79 49"
        )
    if ADMIN_CHAT_ID and update and update.effective_user:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🚨 Bot Error\nUser: {update.effective_user.id}\nError: {context.error}"
            )
        except Exception:
            pass


# ─────────────────────────── Main Application ───────────────────────────

def main() -> None:
    """Start the bot."""
    logger.info("Starting SSVproff Medical Bot...")
    logger.info(f"Knowledge base entries: {len(KNOWLEDGE_BASE.get('entries', []))}")
    logger.info(f"AI provider: {AI_PROVIDER}")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('about', about_handler))
    application.add_handler(CommandHandler('contact', contact_handler))
    application.add_handler(CommandHandler('ask', ask_handler))
    application.add_handler(CommandHandler('knowledge', knowledge_handler))

    # Callback handler for inline keyboards
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Fallback for unknown text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

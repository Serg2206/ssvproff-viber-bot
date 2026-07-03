# SSVproff Medical Bot — Telegram AI Assistant

Telegram-бот для Медицинского Центра МАРИЯ (Харьков) — AI-ассистент профессора Сушкова С.В.

## Возможности

- **/start** — Приветствие и меню
- **/ask [вопрос]** — Задать вопрос AI-ассистенту (интеграция с Abacus AI / Kimi AI)
- **/knowledge [тема]** — Поиск по базе знаний (FAQ, алгоритмы, подготовка)
- **/about** — Информация о профессоре Сушкове С.В.
- **/contact** — Контакты и запись на приём
- **/help** — Справка по командам
- **Inline keyboards** — Быстрый доступ к популярным темам

## Структура проекта

```
SSVproff_medical_bot/
├── bot.py              # Основной бот (python-telegram-bot v20+)
├── config.py           # Конфигурация и сообщения
├── knowledge_base.json # База знаний (FAQ + алгоритмы)
├── requirements.txt    # Зависимости Python
├── .env.example        # Шаблон переменных окружения
└── README.md           # Этот файл
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Serg2206/ssvproff-viber-bot.git
cd ssvproff-viber-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте `.env` файл:
```bash
cp .env.example .env
# Отредактируйте .env, добавьте TELEGRAM_BOT_TOKEN и API ключи
```

5. Запустите бота:
```bash
python bot.py
```

## Переменные окружения

| Переменная | Описание | Обязательно |
|-----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | ✅ Да |
| `ABACUSAI_API_KEY` | API ключ Abacus AI | ⚠️ Один из AI ключей |
| `KIMI_API_KEY` | API ключ Kimi (Moonshot AI) | ⚠️ Один из AI ключей |
| `ADMIN_CHAT_ID` | Telegram ID админа для уведомлений | ❌ Нет |
| `AI_PROVIDER` | `abacus`, `kimi`, или `auto` | ❌ Нет (default: auto) |

## База знаний

База знаний содержит 28 FAQ-записей и 2 медицинских алгоритма:
- Лапароскопия
- Онкохирургия
- Гинекология / миомэктомия
- Подготовка к операции
- Послеоперационный период
- Цены и консультации
- Экстренные случаи
- Общие вопросы

## Деплой

### Heroku
```bash
heroku create ssvproff-bot
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set ABACUSAI_API_KEY=your_key
heroku config:set KIMI_API_KEY=your_key
```

### PythonAnywhere
1. Загрузите файлы
2. Создайте `.env` через Files
3. Запустите: `python bot.py` в Console

### Локальный сервер (webhook)
```bash
export TELEGRAM_BOT_TOKEN=your_token
export WEBHOOK_URL=https://yourdomain.com/webhook
python bot.py
```

## Лицензия

Медицинский справочник. Не является медицинской консультацией.

---
**Контакты:** Медицинский Центр МАРИЯ, Харьков  
📞 +380 67 570 79 49 | 🌐 https://ssvnauka.com

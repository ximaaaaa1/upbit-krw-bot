# UPBIT KRW Bot Control Panel

Live control panel для запуска Upbit KRW V5.3 бота через веб интерфейс.

## Frontend (Surge)
URL: https://upbit-krw-bot.surge.sh

## Backend Deployment Options

### Option 1: Railway (Рекомендуется - бесплатно)

1. Зайди на https://railway.app
2. Нажми "Deploy Now"
3. Выбери "GitHub" или "Docker"
4. Подключи этот репо
5. Railway автоматически развернет Node.js приложение

Получишь URL типа: `https://upbit-krw-bot.railway.app`

### Option 2: Heroku

```bash
heroku login
heroku create upbit-krw-bot
git push heroku main
```

### Option 3: Local + ngrok (для тестирования)

```bash
cd upbit-krw-site
npm install express
node server.js
# В другой терминал:
ngrok http 5000
```

## Configuration

1. Открой `config.js`
2. Обнови `API_BASE_URL` на твой бэкенд URL:

```javascript
const API_BASE_URL = 'https://upbit-krw-bot.railway.app';
```

3. Обнови фронтенд на Surge:
```bash
surge --project . --domain upbit-krw-bot.surge.sh
```

## How It Works

1. Нажимаешь "START BOT" на сайте
2. Фронтенд отправляет запрос на бэкенд
3. Бэкенд запускает Python скрипт `upbit_mega_fast.py`
4. Результаты появляются в логах реал-тайм
5. Боту отправляются результаты в Telegram

## Requirements

- Node.js 18+
- Python 3.8+
- Telegram Bot Token (в переменных окружения: `BOT_TOKEN`)
- Upbit API доступ

## Environment Variables

```
BOT_TOKEN=your_telegram_bot_token
PYTHON_PATH=/usr/bin/python3  # или путь к Python
```

## Files

- `index.html` - Frontend (Surge)
- `server.js` - Backend API (Node.js)
- `config.js` - Configuration
- `package.json` - Dependencies

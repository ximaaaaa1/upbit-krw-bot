# Деплой на Railway через GitHub

## Шаг 1️⃣: Создай GitHub Репо

1. Зайди на https://github.com/new
2. Назови его `upbit-krw-bot`
3. Выбери "Public" (чтобы Railway мог прочитать)
4. Нажми "Create repository"

## Шаг 2️⃣: Залей код в GitHub

Выполни эти команды в PowerShell:

```powershell
# Перейди в папку проекта
cd C:\Users\Administrator\.openclaw\workspace\upbit-krw-site

# Инициализируй Git
git init

# Добавь все файлы
git add .

# Создай первый коммит
git commit -m "Initial commit: Upbit KRW Bot Control Panel"

# Добавь GitHub как удаленный репо (замени USERNAME на свой GitHub юзер)
git branch -M main
git remote add origin https://github.com/USERNAME/upbit-krw-bot.git

# Загрузи код в GitHub
git push -u origin main
```

**Когда попросит пароль:**
- Юзернейм: `USERNAME` (твой GitHub юзер)
- Пароль: используй **Personal Access Token** (не обычный пароль!)

### Как получить GitHub Token:

1. На GitHub: Settings → Developer settings → Personal access tokens
2. Нажми "Generate new token"
3. Выбери scope: `repo`
4. Скопируй токен
5. Используй его как пароль при `git push`

---

## Шаг 3️⃣: Подключи Railroad (Деплой)

1. Зайди на https://railway.app
2. Нажми **"New Project"**
3. Выбери **"Deploy from GitHub"**
4. Авторизуй GitHub (первый раз)
5. Выбери репо `upbit-krw-bot`
6. Railway автоматически:
   - Обнаружит `package.json`
   - Установит зависимости
   - Запустит `npm start` (= `node server.js`)
   - Создаст публичный URL

---

## Шаг 4️⃣: Получи Backend URL

После деплоя:

1. Зайди в Railway Dashboard
2. Нажми на твой проект
3. Вкладка "Settings"
4. Найди "Domains" → скопируй URL типа:
   ```
   https://upbit-krw-bot-xxx.railway.app
   ```

---

## Шаг 5️⃣: Обнови Frontend

1. Открой https://upbit-krw-bot.surge.sh
2. В поле **"Backend URL"** вставь:
   ```
   https://upbit-krw-bot-xxx.railway.app
   ```
3. Нажми **"START BOT"**

---

## Troubleshooting

### ❌ Railway пишет ошибку при деплое?

Проверь что есть эти файлы:
- ✅ `package.json` (зависимости)
- ✅ `server.js` (основной файл)
- ✅ `index.html` (фронтенд)
- ✅ `Procfile` (команда запуска)

### ❌ Backend URL не работает?

1. Проверь что Railway деплой finished (зелёный статус)
2. Скопируй правильный URL с Railway Dashboard
3. Убедись что нет опечаток

### ❌ Боту не хватает зависимостей?

Добавь в `package.json` в секцию `dependencies`:
```json
"express": "^4.18.2"
```

Потом:
```bash
npm install
git add package-lock.json
git commit -m "Update dependencies"
git push
```

Railway автоматически перезапустится.

---

## Как обновлять код

Когда будешь менять код:

```bash
git add .
git commit -m "Description of changes"
git push
```

Railway автоматически перезадеплоит через 1-2 минуты.

---

**Готово! Теперь люди смогут использовать твой бот через Интернет! 🚀**

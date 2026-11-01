# 🕐 Telegram-бот для обліку робочого часу

Telegram-бот для фіксації та аналізу робочого часу невеликої команди (1–5 працівників).

## ✨ Можливості

- 🟢 **Початок роботи** — фіксація часу початку робочої зміни
- 🔴 **Завершення роботи** — фіксація часу завершення з автоматичним розрахунком тривалості
- ⏱ **Поточна зміна** — перегляд статусу активної зміни в реальному часі
- 📅 **Історія роботи** — перегляд минулих змін з пагінацією
- 📊 **Статистика** — аналітика за сьогодні, тиждень, місяць та весь час
- 👥 **Багатокористувацький режим** — кожен працівник працює зі свого Telegram-акаунта
- 🔒 **Захист даних** — користувач бачить тільки свої записи
- 🕐 **Часовий пояс** — Europe/Kyiv (автоматична конвертація)

## 📋 Вимоги

- Python 3.12 або новіший
- Telegram Bot Token (від [@BotFather](https://t.me/BotFather))

## 🤖 Створення бота через @BotFather

1. Відкрийте Telegram і знайдіть [@BotFather](https://t.me/BotFather).
2. Надішліть команду `/newbot`.
3. Введіть **назву** бота (наприклад, `Облік Робочого Часу`).
4. Введіть **username** бота (має закінчуватися на `bot`, наприклад: `my_work_time_bot`).
5. BotFather надішле вам **токен** — рядок виду:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. Збережіть цей токен — він потрібен для запуску.

### Рекомендовані налаштування BotFather

Надішліть BotFather наступні команди для налаштування меню:

```
/setcommands
```

Виберіть вашого бота та надішліть:

```
start - Запустити бота
help - Допомога
```

## 🚀 Локальний запуск

### 1. Клонування або завантаження проєкту

```bash
git clone <url-репозиторію>
cd JobHours
```

### 2. Створення віртуального середовища

**З використанням uv (рекомендовано):**

```bash
uv venv --python 3.12 .venv
```

**Або стандартний Python:**

```bash
python -m venv .venv
```

### 3. Активація середовища

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Встановлення залежностей

**З uv:**
```bash
uv pip install -r requirements.txt
```

**Або стандартний pip:**
```bash
pip install -r requirements.txt
```

### 5. Налаштування

Створіть файл `.env` на основі прикладу:

```bash
cp .env.example .env
```

Відредагуйте `.env` та вставте ваш токен:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 6. Запуск бота

```bash
python bot.py
```

Ви побачите:
```
2026-11-01 11:00:00 | INFO     | __main__ | Ініціалізація бота...
2026-11-01 11:00:00 | INFO     | database | База даних ініціалізована.
2026-11-01 11:00:00 | INFO     | __main__ | Бот запущено. Очікування повідомлень...
```

## 🧪 Тестування

```bash
python -m pytest tests/test_bot.py -v
```

Тести перевіряють:
1. ✅ Реєстрацію нового користувача
2. ✅ Початок робочої зміни
3. ✅ Повторний початок зміни (захист від дублювання)
4. ✅ Завершення робочої зміни
5. ✅ Завершення зміни без початку
6. ✅ Перегляд активної зміни
7. ✅ Перегляд історії з пагінацією
8. ✅ Розрахунок статистики
9. ✅ Роботу декількох користувачів одночасно
10. ✅ Збереження зміни після перезапуску
11. ✅ Коректну роботу з часовим поясом Europe/Kyiv
12. ✅ Захист особистих даних

## 📁 Структура проєкту

```
JobHours/
├── bot.py                  # Точка входу — запуск бота
├── config.py               # Конфігурація (токен, шляхи, параметри)
├── database.py             # Робота з БД (CRUD операції)
├── models.py               # SQLAlchemy моделі (User, WorkSession)
├── requirements.txt        # Залежності Python
├── .env.example            # Приклад файлу конфігурації
├── .gitignore              # Ігноровані файли Git
├── README.md               # Документація
│
├── handlers/               # Обробники Telegram-повідомлень
│   ├── start.py            # /start — привітання та реєстрація
│   ├── work.py             # Початок/завершення роботи, поточна зміна
│   ├── history.py          # Історія змін з пагінацією
│   ├── statistics.py       # Статистика за періоди
│   └── help.py             # Допомога
│
├── keyboards/              # Клавіатури Telegram
│   ├── main_menu.py        # Головне меню (ReplyKeyboard)
│   └── inline.py           # Inline-кнопки (пагінація)
│
├── services/               # Бізнес-логіка
│   ├── time_calculator.py  # Розрахунок тривалості
│   └── statistics_service.py # Статистика за періоди
│
├── utils/                  # Допоміжні утиліти
│   ├── formatting.py       # Форматування дат, часу, тривалості
│   └── timezone.py         # Робота з часовими поясами
│
├── data/                   # Директорія для БД (створюється автоматично)
│   └── .gitkeep
│
└── tests/                  # Тести
    └── test_bot.py         # 17 тестів
```

## 🖥 Розгортання на сервері (24/7)

### Варіант 1: systemd (Ubuntu/Debian)

#### 1. Підготовка сервера

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

#### 2. Завантаження проєкту

```bash
cd /opt
sudo git clone <url> work-time-bot
sudo chown -R $USER:$USER /opt/work-time-bot
cd /opt/work-time-bot
```

#### 3. Налаштування

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Вставте BOT_TOKEN
```

#### 4. Створення systemd-сервісу

```bash
sudo nano /etc/systemd/system/work-time-bot.service
```

Вміст файлу:

```ini
[Unit]
Description=Work Time Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/work-time-bot
ExecStart=/opt/work-time-bot/.venv/bin/python bot.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/work-time-bot/.env

[Install]
WantedBy=multi-user.target
```

#### 5. Запуск

```bash
sudo systemctl daemon-reload
sudo systemctl enable work-time-bot
sudo systemctl start work-time-bot
```

#### 6. Перевірка стану

```bash
sudo systemctl status work-time-bot
sudo journalctl -u work-time-bot -f
```

### Варіант 2: Docker

Створіть `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

CMD ["python", "bot.py"]
```

Запуск:

```bash
docker build -t work-time-bot .
docker run -d \
  --name work-time-bot \
  --restart always \
  -v work_time_data:/app/data \
  --env-file .env \
  work-time-bot
```

### Варіант 3: VPS з screen/tmux

```bash
# Встановлення tmux
sudo apt install tmux

# Створення сесії
tmux new -s bot

# Запуск бота
cd /opt/work-time-bot
source .venv/bin/activate
python bot.py

# Від'єднатися: Ctrl+B, потім D
# Повернутися: tmux attach -t bot
```

## 🔧 Технології

| Технологія | Версія | Призначення |
|---|---|---|
| Python | 3.12+ | Мова програмування |
| aiogram | 3.x | Telegram Bot API framework |
| SQLAlchemy | 2.x | ORM для бази даних |
| aiosqlite | 0.20+ | Async-драйвер SQLite |
| SQLite | — | Локальна база даних |
| python-dotenv | 1.x | Завантаження .env |
| pytz | 2024+ | Часові пояси |

## ❓ FAQ

**Що буде, якщо бот перезапуститься під час робочої зміни?**
Активна зміна збережеться в базі даних. Після перезапуску ви зможете завершити її як зазвичай.

**Чи можуть інші бачити мої записи?**
Ні. Кожен користувач бачить тільки власні дані.

**Який часовий пояс використовується?**
Час зберігається в UTC, але відображається за часовим поясом Europe/Kyiv.

**Скільки працівників може використовувати бота?**
Бот розрахований на невелику команду до 5 осіб, але технічних обмежень немає.

## 📄 Ліцензія

MIT License

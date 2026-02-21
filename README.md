# LinkedIn Jobs Scraper

Скрапер вакансий с LinkedIn с сохранением в PostgreSQL. Другие разработчики могут запустить БД через Docker, запустить скрапер и получать данные из базы.

## Требования

- Python 3.10+
- Docker и Docker Compose (для БД) или установленный PostgreSQL
- Аккаунт LinkedIn (для входа при первом запуске)

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/YOUR_USERNAME/Scrapper_LinkedIn.git
cd Scrapper_LinkedIn
```

### 2. Запустить PostgreSQL

**Вариант A — через Docker (рекомендуется):**

```bash
docker-compose up -d
```

Будет создана БД `talimjob`, пользователь `talimjob`, пароль `talimjob_pass`, порт 5432.

**Вариант B — свой PostgreSQL:**  
Создайте базу и пользователя, затем укажите `DATABASE_URL` в `.env`.

### 3. Настроить окружение

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Для Docker оставьте в `.env`:

```
DATABASE_URL=postgresql://talimjob:talimjob_pass@localhost:5432/talimjob
SAVE_TO_JSON=false
```

Если используете свой PostgreSQL — измените `DATABASE_URL` в `.env`.

### 4. Установить зависимости

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 5. Запустить скрапер

```bash
python -m app.main
```

При первом запуске откроется браузер — войдите в LinkedIn. Таблица `vacancies` создаётся автоматически при первом подключении к БД.

---

## Получение данных из БД

### Скрипт просмотра (из корня проекта)

```bash
python scripts/view_vacancies.py
```

Показывает количество записей и последние 20 вакансий.

### Через psql

```bash
# Подключение (логин/пароль из .env или docker-compose)
psql postgresql://talimjob:talimjob_pass@localhost:5432/talimjob
```

В psql:

```sql
\dt                    -- список таблиц
SELECT * FROM vacancies LIMIT 10;
SELECT id, title, location, created_at FROM vacancies ORDER BY id DESC;
```

### Из своего кода (Python)

```python
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("SELECT id, title, location, url FROM vacancies ORDER BY id DESC LIMIT 100")
rows = cur.fetchall()
# ...
cur.close()
conn.close()
```

Или использовать уже существующий модуль (только чтение нужно реализовать отдельно, т.к. сейчас там только запись):

```python
from app.storage.postgres import get_storage
storage = get_storage()
# storage.save_or_update(...) — для записи
# для чтения — использовать storage.conn и storage.cursor (осторожно с транзакциями)
```

### Через GUI

- **pgAdmin** или **DBeaver**: новое подключение → host `localhost`, port `5432`, database `talimjob`, user `talimjob`, password `talimjob_pass`.

---

## Структура таблицы `vacancies`

| Поле         | Тип          | Описание                    |
|-------------|---------------|-----------------------------|
| id          | SERIAL        | Первичный ключ             |
| source      | VARCHAR(64)   | Источник (например LinkedIn) |
| title       | TEXT          | Название вакансии           |
| company     | TEXT          | Компания                    |
| location    | TEXT          | Локация                     |
| url         | TEXT          | Ссылка на вакансию          |
| description | TEXT          | Описание                    |
| salary      | TEXT          | Зарплата (если есть)        |
| contact     | TEXT          | Контакт                     |
| desc200     | VARCHAR(200)  | Хеш для дедупликации        |
| contact_norm| VARCHAR(512)  | Нормализованный контакт     |
| created_at  | TIMESTAMPTZ   | Дата создания               |
| updated_at  | TIMESTAMPTZ   | Дата обновления             |

Уникальность: `(source, desc200, contact_norm)` — повторные вакансии обновляют только `updated_at`.

---

## Остановка БД (Docker)

```bash
docker-compose down
```

Данные сохраняются в volume `postgres_data`. Чтобы удалить и их:

```bash
docker-compose down -v
```

---

## Публикация на GitHub

Если репозиторий ещё не под Git:

```bash
git init
git add .
git commit -m "Initial commit: LinkedIn scraper + PostgreSQL"
```

На [GitHub](https://github.com/new) создайте новый репозиторий (без README/gitignore). Затем:

```bash
git remote add origin https://github.com/YOUR_USERNAME/Scrapper_LinkedIn.git
git branch -M main
git push -u origin main
```

Файл `.env` в `.gitignore` не попадёт в репозиторий — другие копируют `.env.example` в `.env` и подставляют свои данные.

---

## Лицензия

MIT (или укажите свою).

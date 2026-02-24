"""
Просмотр таблицы table_1_linkedin_parser в PostgreSQL.
Запуск из корня проекта: python -m scripts.view_vacancies
Или: python scripts/view_vacancies.py (из корня проекта)
"""
import os
import sys

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Ошибка: в .env нет DATABASE_URL")
    sys.exit(1)


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Количество записей
    cur.execute("SELECT COUNT(*) FROM table_1_linkedin_parser")
    total = cur.fetchone()[0]
    print(f"Всего записей в vacancies: {total}\n")

    # Последние 20 вакансий (id, title, location, created_at)
    cur.execute("""
        SELECT id, title, location, created_at
        FROM table_1_linkedin_parser
        ORDER BY id DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    print("Последние 20 записей (id | title | location | created_at):")
    print("-" * 80)
    for r in rows:
        id_, title, location, created = r
        title_short = (title or "")[:50] + ("..." if len(title or "") > 50 else "")
        loc = (location or "")[:25]
        print(f"  {id_:5} | {title_short:53} | {loc:25} | {created}")

    cur.close()
    conn.close()
    print("\n[+] Готово. Подключение к БД закрыто.")


if __name__ == "__main__":
    main()

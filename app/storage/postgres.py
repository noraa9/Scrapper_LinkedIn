import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv

from app.dedupe.key import dedup_key
from app.models import Job

# Загружаем переменные окружения из .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в переменных окружения. Создайте файл .env с DATABASE_URL=...")


class PostgresStorage:
    """Класс для работы с PostgreSQL. Управляет одним соединением."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self.batch_size = 10  # Размер пачки для коммита
        self.batch_count = 0

    def connect(self) -> None:
        """Открывает соединение с базой данных и создаёт таблицу при необходимости."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.database_url)
            self.cursor = self.conn.cursor()
            self._init_table()
            print("[+] Подключено к PostgreSQL")

    def _init_table(self) -> None:
        """Создаёт таблицу table_1_linkedin_parser, если её ещё нет."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_1_linkedin_parser (
                id SERIAL PRIMARY KEY,
                source VARCHAR(64) NOT NULL DEFAULT 'LinkedIn',
                title TEXT,
                company TEXT,
                location TEXT,
                url TEXT,
                description TEXT,
                salary TEXT,
                contact TEXT,
                desc200 VARCHAR(200) NOT NULL,
                contact_norm VARCHAR(512) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (source, desc200, contact_norm)
            )
        """)
        self.conn.commit()

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("[+] Соединение с PostgreSQL закрыто")

    def commit(self) -> None:
        """Делает commit транзакции."""
        if self.conn:
            self.conn.commit()
            self.batch_count = 0

    def _ensure_connected(self) -> None:
        """Проверяет соединение и переподключается при необходимости."""
        if self.conn is None or self.conn.closed:
            self.connect()

    def save_or_update(self, job: Job, job_url: str) -> None:
        """
        Сохраняет или обновляет вакансию в базе данных.

        При конфликте по уникальному индексу (source, desc200, contact_norm)
        обновляет только updated_at.

        Args:
            job: Объект Job с данными вакансии
            job_url: URL вакансии (используется для поля url)
        """
        self._ensure_connected()

        # Вычисляем контакт для дедупликации (email → linkedin → job_url)
        key_contact = job.hr_email or job.hr_linkedin or job.job_url
        desc200, contact_norm = dedup_key(job.description, key_contact)

        # Извлекаем company из contact или оставляем пустым
        company = ""  # Можно расширить логику извлечения компании позже

        # Человекочитаемый контакт: email | linkedin | url (то, что увидим в БД)
        contact = " | ".join(
            [c for c in [job.hr_email, job.hr_linkedin, job.job_url] if c]
        )

        # SQL для INSERT с ON CONFLICT UPDATE
        insert_sql = """
            INSERT INTO table_1_linkedin_parser (
                source, title, company, location, url, description, 
                salary, contact, desc200, contact_norm
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, desc200, contact_norm)
            DO UPDATE SET updated_at = NOW()
        """

        try:
            self.cursor.execute(
                insert_sql,
                (
                    job.source,
                    job.title,
                    company,
                    job.location,
                    job_url,
                    job.description,
                    job.salary,
                    contact,
                    desc200,
                    contact_norm,
                ),
            )

            self.batch_count += 1

            # Делаем commit после каждой пачки
            if self.batch_count >= self.batch_size:
                self.commit()
                print(f"[+] Сохранено {self.batch_size} вакансий в БД (commit)")

        except psycopg2.Error as e:
            print(f"[-] Ошибка при сохранении вакансии: {e}")
            self.conn.rollback()
            raise

    def finalize(self) -> None:
        """Финализирует работу: делает финальный commit и закрывает соединение."""
        if self.batch_count > 0:
            self.commit()
            print(f"[+] Финальный commit: {self.batch_count} вакансий")
        self.close()


# Глобальный экземпляр хранилища
_storage_instance: Optional[PostgresStorage] = None


def get_storage() -> PostgresStorage:
    """Возвращает глобальный экземпляр PostgresStorage."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = PostgresStorage(DATABASE_URL)
        _storage_instance.connect()
    return _storage_instance


def save_or_update(job: Job, job_url: str) -> None:
    """
    Удобная функция для сохранения или обновления вакансии.

    Использует глобальный экземпляр хранилища.

    Args:
        job: Объект Job с данными вакансии
        job_url: URL вакансии
    """
    storage = get_storage()
    storage.save_or_update(job, job_url)


def close_storage() -> None:
    """Закрывает глобальное соединение с БД."""
    global _storage_instance
    if _storage_instance:
        _storage_instance.finalize()
        _storage_instance = None


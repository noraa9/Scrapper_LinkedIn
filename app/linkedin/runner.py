import random
import time
from typing import List, Set, Tuple

from playwright.sync_api import sync_playwright

from app.config import ROLES, ROLE_KEYWORDS, RETRY_ATTEMPTS, RETRY_DELAYS_SEC
from app.dedupe.key import dedup_key
from app.linkedin.browser import create_context_and_page
from app.linkedin.collect import collect_job_links
from app.linkedin.extract import extract_job_from_view
from app.linkedin.urls import build_search_url
from app.linkedin.utils import safe_goto, is_bad_redirect, is_logged_in, sleep_jitter
from app.models import Job
from app.storage.postgres import get_storage, save_or_update, close_storage


def run() -> List[Job]:
    all_jobs: List[Job] = []
    seen_keys: Set[Tuple[str, str]] = set()
    processed_urls: Set[str] = set()

    # Подключаемся к БД в начале, чтобы таблица была создана и соединение открыто
    get_storage()

    with sync_playwright() as p:
        context, page = create_context_and_page(p)

        for idx, current_role in enumerate(ROLES):
            search_url = build_search_url(current_role)

            print(f"\n[+] Role: {current_role}")
            print(f"[+] Open search: {search_url}")

            safe_goto(page, search_url)
            try:
                print("SEARCH page title:", page.title())
            except Exception:
                pass

            sleep_jitter()

            if not is_logged_in(page):
                print("\n[!] LinkedIn просит логин.")
                print("    Залогинься вручную в открывшемся окне, затем нажми Enter в консоли.")
                input("Press Enter after login...")
                safe_goto(page, search_url)

                sleep_jitter()

            links = collect_job_links(page)
            links = list(dict.fromkeys(links))
            print(f"[+] Collected links: {len(links)} (unique)")

            role_keywords = ROLE_KEYWORDS.get(current_role, [])

            for i, job_url in enumerate(links, start=1):
                if job_url in processed_urls:
                    continue
                processed_urls.add(job_url)

                if i % 5 == 0:
                    print("[+] Cooling pause...")
                    time.sleep(random.uniform(6, 10))

                job = None
                last_err = None

                for attempt in range(RETRY_ATTEMPTS):
                    try:
                        sleep_jitter()
                        job = extract_job_from_view(page, job_url)
                        break
                    except Exception as e:
                        last_err = e
                        time.sleep(RETRY_DELAYS_SEC[min(attempt, len(RETRY_DELAYS_SEC) - 1)])

                if not job:
                    if is_bad_redirect(page.url):
                        print(f"[-] Skip (redirected): {job_url} -> {page.url}")
                    else:
                        print(f"[-] Skip (failed/empty): {job_url} ({last_err})")
                    continue

                text_for_role = f"{job.title}\n{job.description}".lower()
                if role_keywords and not any(k in text_for_role for k in role_keywords):
                    print(f"[-] Filtered out by role: {job.title}")
                    continue

                key = dedup_key(job.description, job.contact)
                if key in seen_keys:
                    print(f"[=] Duplicate: {job.title}")
                    continue

                seen_keys.add(key)
                all_jobs.append(job)
                print(f"[+] Added: {job.title} | {job.location}")

                # Сохраняем в PostgreSQL после успешного дедупа
                try:
                    save_or_update(job, job_url)
                except Exception as e:
                    print(f"[-] Ошибка при сохранении в БД: {e}")

        context.close()

    # Финализируем работу с БД (финальный commit и закрытие соединения)
    close_storage()

    return all_jobs



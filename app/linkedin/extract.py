import random
import time
from typing import Optional

from playwright.sync_api import Page

from app.linkedin.utils import safe_goto, is_bad_redirect, sleep_jitter
from app.models import Job
from app.normalize import clean_description, extract_email


def _expand_description(page: Page) -> None:
    for btn_sel in [
        'button:has-text("Показать еще")',
        'button:has-text("Показать ещё")',
        'button:has-text("Развернуть")',
        'button:has-text("See more")',
        'button:has-text("Show more")',
    ]:
        try:
            b = page.locator(btn_sel).first
            if b.count():
                b.scroll_into_view_if_needed(timeout=1000)
                page.wait_for_timeout(150)
                b.click(timeout=1200, force=True)
                page.wait_for_timeout(500)
        except Exception:
            pass


def _extract_title(page: Page) -> str:
    title = ""
    try:
        h1 = page.locator("h1").first
        title = (h1.text_content() or "").strip()
    except Exception:
        pass

    if not title:
        try:
            pt = (page.title() or "").strip()
            if pt:
                title = pt.split("|")[0].strip()
        except Exception:
            pass

    return title


def _extract_description(page: Page) -> str:
    description = ""
    section_locators = [
        'xpath=//h2[contains(normalize-space(.),"Об этой вакансии")]/ancestor::*[self::section or self::div][1]',
        'xpath=//h2[contains(normalize-space(.),"About this job")]/ancestor::*[self::section or self::div][1]',
    ]
    for sec_sel in section_locators:
        try:
            sec = page.locator(sec_sel).first
            if sec.count():
                inner = sec.locator(
                    'div.show-more-less-html__markup, div.jobs-description__content, div.jobs-box__html-content'
                ).first
                if inner.count():
                    description = (inner.inner_text() or "").strip()
                else:
                    description = (sec.inner_text() or "").strip()
                if description and len(description) > 40:
                    break
        except Exception:
            pass

    if not description:
        for sel in [
            'div.show-more-less-html__markup',
            'div.jobs-description__content',
            'div.jobs-box__html-content',
            'div#job-details',
        ]:
            try:
                d = page.locator(sel).first
                if d.count():
                    description = (d.inner_text() or "").strip()
                    if description and len(description) > 40:
                        break
            except Exception:
                pass

    return description


def extract_job_from_view(page: Page, job_url: str) -> Optional[Job]:
    safe_goto(page, job_url)
    page.wait_for_timeout(1200)

    if is_bad_redirect(page.url):
        print(f"[!] Redirected: {page.url} — cooling down...")
        time.sleep(random.uniform(8, 15))
        return None

    if "/jobs/view/" not in (page.url or ""):
        return None

    page.wait_for_timeout(1200)
    sleep_jitter()

    _expand_description(page)

    title = _extract_title(page)

    if (title or "").strip().lower() in ["управляйте своими уведомлениями", "manage your notifications"]:
        return None

    description = _extract_description(page)

    if not title or not description:
        return None

    description = clean_description(description)

    email = extract_email(description)
    contact = job_url if not email else f"{job_url} | {email}"

    return Job(
        title=title,
        description=description,
        salary="не указана",
        location="Казахстан",
        contact=contact,
        source="LinkedIn",
    )

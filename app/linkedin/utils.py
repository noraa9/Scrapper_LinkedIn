import random
import time
from typing import Any, Optional

from playwright.sync_api import TimeoutError as PwTimeoutError, Page

from app.config import RETRY_ATTEMPTS, RETRY_DELAYS_SEC, MIN_DELAY_SEC, MAX_DELAY_SEC, NAV_TIMEOUT_MS


def sleep_jitter() -> None:
    time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))


def is_logged_in(page: Page) -> bool:
    u = (page.url or "").lower()
    if any(x in u for x in ["/login", "/checkpoint", "/authwall"]):
        return False

    for sel in [
        "img.global-nav__me-photo",
        "button.global-nav__primary-link-me-menu-trigger",
        'a.global-nav__primary-link[href*="/in/"]',
    ]:
        try:
            if page.locator(sel).first.count():
                return True
        except Exception:
            pass

    try:
        if page.locator("text=Sign in").first.is_visible(timeout=1200):
            return False
    except Exception:
        pass

    return True


def safe_goto(page: Page, url: str) -> None:
    last_err: Optional[Exception] = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            return
        except PwTimeoutError as e:
            last_err = e
        except Exception as e:
            last_err = e
        time.sleep(RETRY_DELAYS_SEC[min(attempt, len(RETRY_DELAYS_SEC) - 1)])
    raise last_err  # type: ignore[misc]


def is_bad_redirect(url: str) -> bool:
    u = (url or "").lower()
    return any(
        x in u
        for x in [
            "/notifications",
            "/checkpoint",
            "/authwall",
            "/login",
        ]
    )



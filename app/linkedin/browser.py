from typing import Tuple

from playwright.sync_api import BrowserContext, Page, Playwright

from app.config import HEADLESS, PAGE_TIMEOUT_MS, USER_DATA_DIR, PROXY_SERVER, PROXY_USERNAME, PROXY_PASSWORD


def create_context_and_page(playwright: Playwright) -> Tuple[BrowserContext, Page]:
    proxy_cfg = None
    if PROXY_SERVER:
        proxy_cfg = {"server": PROXY_SERVER}
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy_cfg["username"] = PROXY_USERNAME
            proxy_cfg["password"] = PROXY_PASSWORD

    context = playwright.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=HEADLESS,
        proxy=proxy_cfg,
    )
    context.set_default_timeout(PAGE_TIMEOUT_MS)
    page = context.new_page()
    return context, page
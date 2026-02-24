from typing import List, Set

from playwright.sync_api import Page

from app.config import MAX_JOBS_PER_ROLE


def collect_job_links(page: Page) -> List[str]:
    # Даем результатам поискa прогрузиться, но без лишней задержки
    page.wait_for_timeout(800)

    for sel in [
        "div.jobs-search-results-list",
        "div.scaffold-layout__list-container",
        "div.jobs-search__left-rail",
        "div.scaffold-layout__list",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count():
                loc.click(timeout=800, force=True)
                break
        except Exception:
            pass

    try:
        page.wait_for_selector('a[href*="/jobs/view/"]', timeout=15_000)
    except Exception:
        return []

    list_container = None
    for sel in [
        "div.jobs-search-results-list",
        "div.scaffold-layout__list-container",
        "div.jobs-search__left-rail",
        "div.scaffold-layout__list",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count():
                can_scroll = loc.evaluate("(el) => el.scrollHeight > el.clientHeight")
                if can_scroll:
                    list_container = loc
                    break
        except Exception:
            pass

    selectors = [
        'a.job-card-container__link',
        'a[data-control-name="job_card_click"]',
        'a[href*="/jobs/view/"]',
    ]

    links: List[str] = []
    seen: Set[str] = set()

    def grab():
        for sel in selectors:
            loc = page.locator(sel)
            n = min(loc.count(), 300)
            for j in range(n):
                href = loc.nth(j).get_attribute("href")
                if not href:
                    continue
                href = href.split("?")[0]
                if href.startswith("/"):
                    href = "https://www.linkedin.com" + href
                if "/jobs/view/" in href and href not in seen:
                    seen.add(href)
                    links.append(href)

    for _ in range(30):
        grab()
        if len(links) >= MAX_JOBS_PER_ROLE:
            break

        try:
            if list_container:
                list_container.evaluate("(el) => { el.scrollBy(0, 1400); }")
            else:
                page.mouse.wheel(0, 1600)
        except Exception:
            page.mouse.wheel(0, 1600)

        page.wait_for_timeout(500)

    return links[:MAX_JOBS_PER_ROLE]
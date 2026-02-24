
def human_scroll(page, steps=6, px=800, delay_ms=450):
    for _ in range(steps):
        page.mouse.wheel(0, px)
        page.wait_for_timeout(delay_ms)


def click_expandable_text_button(page) -> bool:
    btn = page.locator('button[data-testid="expandable-text-button"]').first
    if btn.count() == 0:
        return False

    try:
        btn.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass

    inner = btn.locator('span[style*="pointer-events: auto"]').first
    if inner.count() > 0:
        try:
            inner.click(timeout=3000)
            page.wait_for_timeout(800)
            return True
        except Exception:
            pass

    try:
        handle = btn.element_handle()
        if handle:
            page.evaluate(
                """(b) => {
                    b.removeAttribute('aria-hidden');
                    b.style.pointerEvents = 'auto';
                    const s = b.querySelector('span[style*="pointer-events: auto"]') || b.querySelector('span');
                    if (s) s.click();
                    else b.click();
                }""",
                handle
            )
            page.wait_for_timeout(800)
            return True
    except Exception:
        pass

    return False


def extract_between(text: str, start_markers: List[str], end_markers: List[str]) -> str:
    if not text:
        return ""

    start_pos = -1
    for sm in start_markers:
        i = text.find(sm)
        if i != -1:
            start_pos = i + len(sm)
            break
    if start_pos == -1:
        return ""

    tail = text[start_pos:]

    end_pos = None
    for em in end_markers:
        j = tail.find(em)
        if j != -1:
            end_pos = j
            break

    chunk = tail if end_pos is None else tail[:end_pos]
    return normalize_spaces(chunk)


def parse_email(text: str) -> str:
    return extract_email(text)


def scrape_job_description(page) -> str:
    page.wait_for_timeout(1500)
    human_scroll(page, steps=3, px=700, delay_ms=400)
    click_expandable_text_button(page)

    main_txt = ""
    try:
        main_txt = page.locator("main").first.inner_text(timeout=4000)
    except Exception:
        try:
            main_txt = page.locator("body").inner_text(timeout=4000)
        except Exception:
            return ""

    main_txt = normalize_spaces(main_txt)

    desc = extract_between(
        main_txt,
        start_markers=["Об этой вакансии", "About this job"],
        end_markers=["О компании", "About the company", "© LinkedIn", "Похожие вакансии", "Similar jobs"]
    )

    if not desc:
        desc = extract_between(
            main_txt,
            start_markers=["Об этой вакансии", "About this job"],
            end_markers=["Отправлять оповещения", "Send me alerts", "© LinkedIn"]
        )

    return desc


def scrape_recruiter(page) -> Tuple[str, str]:
    human_scroll(page, steps=6, px=850, delay_ms=450)

    recruiter_profile = ""
    recruiter_name = ""

    links = page.locator('a[href*="/in/"], a[href*="linkedin.com/in/"]')
    for i in range(min(links.count(), 60)):
        href = links.nth(i).get_attribute("href") or ""
        if "/in/" in href:
            recruiter_profile = normalize_profile_url(href)
            try:
                recruiter_name = normalize_spaces(links.nth(i).inner_text(timeout=1500))
            except Exception:
                recruiter_name = ""
            break

    return recruiter_name, recruiter_profile


def try_contact_info_via_overlay(page, recruiter_profile: str) -> Optional[dict]:
    overlay_url = recruiter_profile.rstrip("/") + "/overlay/contact-info/"
    safe_goto(page, overlay_url)
    page.wait_for_timeout(1200)

    cur = (page.url or "").lower()
    if "login" in cur or "checkpoint" in cur or "authwall" in cur:
        return None

    try:
        page.wait_for_selector("section.pv-contact-info", timeout=8000)
    except Exception:
        return None

    section = page.locator("section.pv-contact-info").first
    try:
        raw = section.inner_text(timeout=4000)
    except Exception:
        raw = ""

    raw = normalize_spaces(raw)
    if not raw:
        return None

    return {
        "public_profile_url": recruiter_profile,
        "email": parse_email(raw),
        "raw": raw,
    }


def click_contact_info_and_read_modal(page, recruiter_profile: str) -> Optional[dict]:
    safe_goto(page, recruiter_profile)
    page.wait_for_timeout(1500)

    page.mouse.wheel(0, 500)
    page.wait_for_timeout(600)

    selectors = [
        'a#top-card-text-details-contact-info',
        'a[data-control-name="topcard_contact_info"]',
        'a:has-text("Контактные сведения")',
        'a:has-text("Contact info")',
        'button:has-text("Контактные сведения")',
        'button:has-text("Contact info")',
    ]

    clicked = False
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() == 0:
            continue
        try:
            loc.click(timeout=3500)
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        return None

    try:
        page.wait_for_selector("section.pv-contact-info", timeout=8000)
    except Exception:
        return None

    section = page.locator("section.pv-contact-info").first
    try:
        raw = section.inner_text(timeout=4000)
    except Exception:
        raw = ""

    raw = normalize_spaces(raw)
    if not raw:
        return None

    info = {
        "public_profile_url": recruiter_profile,
        "email": parse_email(raw),
        "raw": raw,
    }

    for close_sel in ['button[aria-label="Dismiss"]', 'button[aria-label="Закрыть"]']:
        try:
            page.locator(close_sel).first.click(timeout=1500)
            break
        except Exception:
            pass

    return info


def scrape_contact_info(page, recruiter_profile: str) -> dict:
    info = try_contact_info_via_overlay(page, recruiter_profile)
    if info:
        return info

    info = click_contact_info_and_read_modal(page, recruiter_profile)
    if info:
        return info

    return {"public_profile_url": recruiter_profile, "email": "", "raw": ""}


# =========================
# MAIN EXTRACTOR (replaced)
# =========================

def extract_job_from_view(page, job_url: str, city: str) -> Optional[Job]:
    safe_goto(page, job_url)
    page.wait_for_timeout(1200)

    # LinkedIn anti-bot
    if is_bad_redirect(page.url):
        print(f"[!] Redirected: {page.url} — cooling down...")
        time.sleep(random.uniform(8, 15))
        return None

    if "/jobs/view/" not in (page.url or ""):
        return None

    page.wait_for_timeout(900)
    sleep_jitter()

    # Title
    title = ""
    try:
        h1 = page.locator("h1").first
        title = ((h1.text_content() or "").strip())
    except Exception:
        pass

    if not title:
        try:
            pt = (page.title() or "").strip()
            if pt:
                title = pt.split("|")[0].strip()
        except Exception:
            pass

    if (title or "").strip().lower() in ["управляйте своими уведомлениями", "manage your notifications"]:
        return None

    # Better description
    description = scrape_job_description(page)
    description = clean_description(description)

    if not title or not description or len(description) < 40:
        return None

    # Recruiter + contact info
    recruiter_name, recruiter_profile = scrape_recruiter(page)
    contact_info = {"public_profile_url": "", "email": "", "raw": ""}

    if recruiter_profile:
        contact_info = scrape_contact_info(page, recruiter_profile)

    # email HR
    hr_email = (contact_info.get("email") or "").strip()
    if not hr_email:
        hr_email = extract_email(description)

    # linkedin HR
    hr_linkedin = recruiter_profile or ""

    return Job(
        job_url=job_url,
        title=title,
        description=description,
        salary="не указана",
        location=city,
        hr_email=hr_email,
        hr_linkedin=hr_linkedin,
        source="LinkedIn",
    )

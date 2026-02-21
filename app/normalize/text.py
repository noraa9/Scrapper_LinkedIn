import re


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s@+.$₸-]", "", s, flags=re.UNICODE)
    return s


def extract_email(text: str) -> str:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text or "")
    return m.group(0) if m else ""


def clean_description(text: str) -> str:
    if not text:
        return ""
    for r in [
        "Об этой вакансии",
        "About this job",
        "…Показать еще",
        "...Показать еще",
        "Показать еще",
        "Показать ещё",
        "Show more",
        "See more",
    ]:
        text = text.replace(r, "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()



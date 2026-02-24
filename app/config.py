

ROLES = [
    "QA Engineer",
    "Frontend Developer",
    "Product Manager",
    "Project Manager",
    "UX UI Designer",
]

ROLE_KEYWORDS = {
    "QA Engineer": ["qa", "test", "tester", "quality", "automation", "aqa", "sdet"],
    "Frontend Developer": ["frontend", "front-end", "react", "javascript", "typescript", "vue", "angular"],
    "Product Manager": ["product manager", "product owner", "product lead", "head of product"],
    "Project Manager": ["project manager", "руководитель проекта", "проектный менеджер", "delivery manager"],
    "UX UI Designer": ["ux", "ui", "designer", "product designer", "ux/ui", "ux designer", "ui designer"],
}
GEO_IDS = {
"Алматы": 105526356,
"Астана": 100184048,
"Караганда": 106399239,
}


USER_DATA_DIR = "linkedin_profile"
HEADLESS = False
MAX_JOBS_PER_ROLE = 30
PAGE_TIMEOUT_MS = 20_000
NAV_TIMEOUT_MS = 20_000
RETRY_ATTEMPTS = 3
RETRY_DELAYS_SEC = [1, 5, 15]
MIN_DELAY_SEC = 2
MAX_DELAY_SEC = 5

PROXY_SERVER = None
PROXY_USERNAME = None
PROXY_PASSWORD = None
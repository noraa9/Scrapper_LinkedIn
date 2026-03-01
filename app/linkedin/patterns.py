import re

# Work format

# 1. HYBRID: Высокий приоритет. 
# Lookahead исключает случаи, когда flexible относится к часам/графику.
_HYBRID_PATTERNS = [
    re.compile(r"hybrid", re.I),
    re.compile(r"гибрид", re.I),
    re.compile(r"смешанный формат", re.I),
    re.compile(r"flexible work(?!ing\s+hours|ing\s+schedule|\s+time)", re.I),
    re.compile(r"partially remote", re.I),
]

# 2. REMOTE: Средний приоритет.
_REMOTE_PATTERNS = [
    re.compile(r"100% remote", re.I),
    re.compile(r"fully remote", re.I),
    re.compile(r"work from (anywhere|home)", re.I),
    re.compile(r"удаленка|удалёнка|удаленный формат", re.I),
    re.compile(r"wfh|remote-first", re.I),
    # Проверка: слово remote есть, но перед ним нет "not/no"
    re.compile(r"(?<!not\s)(?<!no\s)remote", re.I), 
]

# 3. OFFICE: Низкий приоритет.
_OFFICE_PATTERNS = [
    re.compile(r"on-site|onsite|in-office|office based", re.I),
    re.compile(r"работа в офисе|на месте работодателя", re.I),
]
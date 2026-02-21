def build_search_url(role: str) -> str:
    query = role.replace(" ", "%20")
    return f"https://www.linkedin.com/jobs/search/?geoId=105526356&keywords={query}"

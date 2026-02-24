def build_search_url(role: str, geo_id: int) -> str:
    query = role.replace(" ", "%20")
    return f"https://www.linkedin.com/jobs/search/?geoId={geo_id}&keywords={query}"
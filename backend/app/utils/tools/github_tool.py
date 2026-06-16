import re

import requests
from bs4 import BeautifulSoup


def fetch_github_profile_text(github_url: str) -> str:
    if not github_url:
        return ""

    try:
        response = requests.get(github_url, timeout=8, headers={"User-Agent": "CareerPilotAI/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ").split())
        readme_links = [
            link.get("href", "")
            for link in soup.find_all("a")
            if "README" in link.get_text(" ").upper()
        ][:3]
        return re.sub(r"\s+", " ", text + " " + " ".join(readme_links)).strip()[:8000]
    except Exception:
        return ""

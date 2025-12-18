import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_article(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("meta", property="og:title")
    title = title["content"] if title else soup.title.text.strip()

    summary = soup.find("meta", property="og:description")
    summary = summary["content"] if summary else ""

    image = soup.find("meta", property="og:image")
    image = image["content"] if image else None

    date = soup.find("meta", property="article:published_time")
    date = date["content"][:10] if date else datetime.now().date().isoformat()

    site = soup.find("meta", property="og:site_name")
    site = site["content"] if site else url.split("/")[2]

    return title, summary[:400], image, date, site

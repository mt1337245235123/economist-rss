from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import os

URL = "https://www.economist.com/"


def fetch_items():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-GB",
        )
        page = context.new_page()
        page.goto(URL, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "html.parser")
    items = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)

        if not title or len(title) < 10:
            continue

        # Economist article URLs contain a date slug like /2026/05/17/
        import re
        if not re.search(r'/\d{4}/\d{2}/\d{2}/', href):
            continue

        if not href.startswith("http"):
            href = "https://www.economist.com" + href

        if href in seen:
            continue
        seen.add(href)

        items.append({"title": title, "link": href})

    return items[:30]


def build_rss(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "The Economist"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "Latest articles from The Economist"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    for item in items:
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "guid", isPermaLink="true").text = item["link"]

    return ET.tostring(rss, encoding="unicode", xml_declaration=False)


def main():
    print("Fetching Economist...")
    items = fetch_items()
    print(f"Found {len(items)} items")

    rss_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_rss(items)

    os.makedirs("docs", exist_ok=True)
    with open("docs/feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("Written to docs/feed.xml")


if __name__ == "__main__":
    main()

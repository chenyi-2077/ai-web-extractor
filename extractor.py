"""AI Web Extractor — URL in, clean Markdown/JSON out.

Anti-block fetching + readability parsing + Telegram channel mode.
Built from real production scraping code.
"""
import re
import json
import time
import html
import argparse
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url, timeout=20, retries=2):
    """Fetch with retry + anti-block headers."""
    last_err = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            time.sleep(1 + i)
    raise last_err


# Elements that are noise in article extraction
NOISE = ["script", "style", "noscript", "iframe", "svg", "nav",
         "header", "footer", "aside", "form", "button", "select"]


def readability(html_text):
    """Strip nav/ads/scripts, return main content HTML."""
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup.find_all(NOISE):
        tag.decompose()
    # Common article containers
    for container in soup.find_all(["article", "main", "[role=main]"]):
        return container
    return soup.body or soup


def html_to_markdown(soup):
    """Convert cleaned HTML to basic markdown."""
    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre",
                             "blockquote", "table", "img", "a"]):
        tag = el.name
        if tag == "img":
            src = el.get("src") or ""
            alt = el.get("alt") or ""
            lines.append(f"![{alt}]({src})")
        elif tag == "a":
            txt = el.get_text(" ", strip=True)
            href = el.get("href") or ""
            if txt and href and not href.startswith("#"):
                lines.append(f"[{txt}]({href})")
        elif tag in ("h1", "h2", "h3", "h4"):
            level = int(tag[1])
            txt = el.get_text(" ", strip=True)
            if txt:
                lines.append(f"{'#' * level} {txt}")
        elif tag == "li":
            txt = el.get_text(" ", strip=True)
            if txt:
                lines.append(f"- {txt}")
        elif tag == "pre":
            lines.append("```\n" + el.get_text() + "\n```")
        elif tag == "blockquote":
            txt = el.get_text(" ", strip=True)
            if txt:
                lines.append(f"> {txt}")
        elif tag == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append("| " + " | ".join(cells) + " |")
            if rows:
                lines.append("\n".join(rows))
        else:
            txt = el.get_text(" ", strip=True)
            if txt:
                lines.append(txt)
    # Dedupe consecutive blanks
    out = []
    for line in lines:
        if line.strip() or (out and out[-1].strip()):
            out.append(line)
    return "\n\n".join(out)


def extract_links(soup, base_url):
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = a.get_text(" ", strip=True)
        if href and not href.startswith(("javascript:", "mailto:", "#")):
            links.append({"text": txt[:100], "url": urljoin(base_url, href)})
    return links[:50]


@dataclass
class Extracted:
    url: str = ""
    title: str = ""
    markdown: str = ""
    links: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def json(self):
        return asdict(self)


def extract(url):
    r = fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    main = readability(r.text)
    md = html_to_markdown(main)
    links = extract_links(soup, url)
    return Extracted(url=url, title=title, markdown=md, links=links)


def extract_telegram(channel, limit=10):
    """Parse t.me/s/<channel> public page into posts."""
    r = fetch(f"https://t.me/s/{channel}")
    raw = re.split(r'<div class="tgme_widget_message_wrap', r.text)
    posts = []
    for blk in raw[1:]:
        m = re.search(r'data-post="[^"]*/(\d+)"', blk)
        if not m:
            continue
        mid = int(m.group(1))
        tm = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            blk, re.S)
        if not tm:
            continue
        txt = re.sub(r"<[^>]+>", " ", tm.group(1))
        posts.append({"id": mid, "text": html.unescape(txt).strip()})
        if len(posts) >= limit:
            break
    return posts


def extract_selectors(url, selectors):
    """Extract specific elements by CSS selectors."""
    r = fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")
    out = {}
    for name, sel in selectors.items():
        els = soup.select(sel)
        out[name] = [el.get_text(" ", strip=True) for el in els]
    return out


def main():
    ap = argparse.ArgumentParser(description="AI Web Extractor")
    ap.add_argument("url", nargs="?", help="URL to extract")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("-o", "--output", help="Write to file")
    ap.add_argument("--telegram", help="Telegram channel name")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--selectors", help='JSON selectors, e.g. '{"titles": "h2"}'')
    args = ap.parse_args()

    if args.telegram:
        posts = extract_telegram(args.telegram, args.limit)
        print(json.dumps(posts, ensure_ascii=False, indent=2))
        return

    if args.selectors:
        data = extract_selectors(args.url, json.loads(args.selectors))
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    res = extract(args.url)
    out = res.json() if args.json else res.markdown
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out if isinstance(out, str) else json.dumps(out, indent=2))
        print(f"Saved to {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()

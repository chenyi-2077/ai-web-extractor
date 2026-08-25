<div align="center">

# 🕸️ AI Web Extractor

**URL in → clean Markdown/JSON out.** A lightweight, AI-friendly web
extractor with anti-block headers and readability parsing.

Built from **real production scraping code** (Telegram channel pages, job
boards, crypto dashboards) — not a toy.

---

</div>

## Why

LLMs need **clean text**, not HTML soup. AI Web Extractor fetches a page,
strips the noise (nav, ads, scripts), and returns content an LLM can actually
consume — as Markdown or structured JSON.

## Features

- [x] 🔍 **Anti-block fetching** — realistic browser UA, retry, timeout handling
- [x] 📄 **Readability parsing** — main content extraction (no nav/ads/scripts)
- [x] 📝 **Markdown output** — clean, LLM-ready text
- [x] 🧱 **JSON output** — title, meta, content, links, tables
- [x] 📡 **Telegram channel mode** — parse `t.me/s/` public pages into posts
- [x] 🎯 **Selector mode** — extract specific elements (CSS selectors)
- [x] ⏱️ **Rate limiting** — polite default (1 req/sec)

## Install

```bash
pip install -r requirements.txt
```

## Usage

### Basic extraction

```python
from extractor import extract

# Markdown
result = extract("https://example.com/article")
print(result.markdown)  # clean markdown text

# JSON
print(result.json())    # {title, meta, content, links, tables}
```

### Telegram channel mode

```python
from extractor import extract_telegram

posts = extract_telegram("cryptojobslist", limit=10)
for post in posts:
    print(post.id, post.text[:100])
```

### Selector mode

```python
from extractor import extract_selectors

data = extract_selectors("https://laborx.com/jobs", {
    "job_titles": "h2.job-title",
    "prices": ".price"
})
print(data)
```

## CLI

```bash
# Markdown to file
python -m extractor https://example.com -o output.md

# JSON output
python -m extractor https://example.com --json

# Telegram channel
python -m extractor --telegram cryptojobslist --limit 5
```

## How it's different

| | firecrawl (72k⭐) | **AI Web Extractor** |
|---|---|---|
| Hosting | Cloud API (paid) | **Local, free** |
| Setup | API key + account | `pip install` |
| Use case | Enterprise scale | **Freelancer / AI-agent workflows** |
| Extensibility | SDK | **Readable source, easy to fork** |

## Real-world origin

This tool evolved from production scrapers that ran 24/7:

- Telegram crypto job channels (`t.me/s/` pages) — parsed into structured posts
- Freelance job boards — extracted job titles, budgets, deadlines
- Crypto exchange dashboards — captured live orderbook/price data

## Disclaimer

Respect robots.txt and site ToS. For educational and personal automation use.

## License

MIT

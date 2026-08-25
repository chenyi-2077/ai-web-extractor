"""Smoke tests — run with pytest or directly."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from extractor import extract, extract_telegram, html_to_markdown, readability
from bs4 import BeautifulSoup


def test_readability_strips_noise():
    html = "<html><body><nav>menu</nav><article><h1>Hi</h1><p>World</p></article><script>bad()</script></body></html>"
    main = readability(html)
    md = html_to_markdown(main)
    assert "menu" not in md
    assert "Hi" in md
    assert "World" in md


def test_telegram_parse():
    # offline test with fixture
    posts = extract_telegram("cryptojobslist", limit=1)
    assert isinstance(posts, list)
    if posts:
        assert "id" in posts[0]
        assert "text" in posts[0]


if __name__ == "__main__":
    test_readability_strips_noise()
    print("readability test passed")
    test_telegram_parse()
    print("telegram parse test passed")

"""Text normalization helpers for RedditFetcher."""

from __future__ import annotations

import re
from typing import Final

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt


_MARKDOWN: Final[MarkdownIt] = MarkdownIt()


def clean_text(text: str | None) -> str:
    """Normalize Reddit markdown into clean ASCII text for scoring and storage."""
    if not text:
        return ""

    html = _MARKDOWN.render(text)
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.find_all("a"):
        anchor.attrs.pop("href", None)

    plain_text = soup.get_text(" ")
    plain_text = re.sub(r"https?://\S+", "", plain_text)
    plain_text = re.sub(r"\s+", " ", plain_text).strip()
    plain_text = re.sub(r"[^\x00-\x7F]+", "", plain_text)

    return plain_text

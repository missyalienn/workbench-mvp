"""Unit tests for text cleaning helpers."""

import pytest

from scripts.ingest_pipeline import clean_text


def test_clean_text_removes_urls() -> None:
    result = clean_text("check this out https://example.com and http://foo.bar/page")
    assert result == "check this out and"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("**bold** _italic_", "bold italic"),
        ("[link](https://example.com)", "link"),
        ("# Heading\n\nSome text", "Heading Some text"),
    ],
)
def test_clean_text_strips_markdown(raw: str, expected: str) -> None:
    assert clean_text(raw) == expected


def test_clean_text_normalizes_whitespace() -> None:
    messy = "line1\n\n   line2\tline3  "
    assert clean_text(messy) == "line1 line2 line3"


def test_clean_text_handles_empty_input() -> None:
    assert clean_text("") == ""
    assert clean_text(None) == ""

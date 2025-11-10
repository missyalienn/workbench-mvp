

## Design for clean_text helper 

**Purpose:**  Clean and normalize incoming post and comment text returned from Reddit API so it is usable by for downstream serices (keyword filtering, synthesis, etc.)

**Actions:** Remove markdown, extract plaintext, remove urls, normalize whitespace, require ASCII charcters. 

## Location & signature
- Create services/fetch/text_utils.py with a single clean_text(text: str | None) -> str. 

- Keeping it in services/fetch makes reuse easy for both posts and comments without touching legacy code.

## Processing steps (in order)

- Null/empty guard: return "" immediately when text is falsy, so callers don’t worry about None.
- Markdown → HTML: run the string through markdown_it.MarkdownIt().render() just like the old pipeline. Reddit mixes markdown and inline HTML; this translation gives us consistent structure for the next step.
- Plain-text extraction: feed the HTML to BeautifulSoup and call get_text(" "). That strips tags, keeps link text once, and inserts spaces so lists/headings don’t jam together. Before extraction, drop anchor href attributes to prevent duplicate URLs.
- URL removal: run a regex (r"https?://\S+") on the text to strip leftover naked links so the scorer isn’t triggered by random domains.
- Whitespace normalization: collapse multiple spaces/newlines into single spaces and strip edges. Keeps comparisons stable and helps avoid accidental partial matches.
- ASCII cleanup: remove non-ASCII characters (emoji, odd punctuation) with r"[^\x00-\x7F]+". This mirrors our scoring expectations; everything headed into matching is lowercase ASCII.

## Design Reasoning

- Minimal dependencies (same ones we already rely on) and very clear flow—no extra classes or utilities.
- Produces deterministic lowercase text perfect for keyword matching, with URLs and markdown noise gone.
- Easily unit-testable later with tiny fixtures (markdown bullets, links, emoji, random whitespace).
- Encapsulated helper mirrors the rest of the repo’s style (plain function, explicit steps, readable structure).

This gives the fetcher a single, predictable cleaning pass that both the scoring helper and comment retriever can call without duplicating logic.
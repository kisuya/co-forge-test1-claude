"""Input sanitization utilities."""
from __future__ import annotations

import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from input text."""
    return _HTML_TAG_RE.sub("", text)

#!/usr/bin/env python3
"""Validate generated HTML and local links without third-party packages."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "dist"


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.canonical = False
        self.description = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src"):
            if values.get(key):
                self.links.append(values[key] or "")
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = True
        if tag == "meta" and values.get("name") == "description":
            self.description = True


def main() -> None:
    errors: list[str] = []
    pages = list(ROOT.rglob("*.html"))
    for page in pages:
        parser = Parser()
        parser.feed(page.read_text(encoding="utf-8"))
        if not parser.canonical:
            errors.append(f"{page}: missing canonical")
        if not parser.description:
            errors.append(f"{page}: missing description")
        for link in parser.links:
            if link.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            target = (page.parent / urlsplit(link).path).resolve()
            if not target.exists():
                errors.append(f"{page}: broken link {link}")

    required = ["sitemap.xml", "rss.xml", "robots.txt", "404.html", "_headers", "_redirects"]
    for filename in required:
        if not (ROOT / filename).exists():
            errors.append(f"missing {filename}")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Validated {len(pages)} pages; no broken local links.")


if __name__ == "__main__":
    main()

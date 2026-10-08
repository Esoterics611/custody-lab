"""Every relative link in the repository's Markdown leads to a file that exists, and to a heading
that exists when it names one.

The manual's GitHub pages (``manual/chapters/*.md``), the glossary and the atlas link into each
other by section. Rewriting a chapter renames headings, and this test is what catches a link left
pointing at the old name. Anchors are the explicit ``<a id>`` that ``manual/links.py`` writes
before each heading, or GitHub's slug of a heading's text.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {".venv", "node_modules", "target", "dist", "var", ".pytest_cache", ".quarto"}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def markdown_files() -> list[Path]:
    return [p for p in ROOT.rglob("*.md") if not EXCLUDED & set(p.relative_to(ROOT).parts)]


def github_slug(heading: str) -> str:
    text = re.sub(r"[`*$\\]", "", heading.strip().lower())
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(text: str) -> set[str]:
    explicit = set(re.findall(r'<a id="([^"]+)"></a>', text))
    return explicit | {github_slug(h) for h in re.findall(r"^#+ (.+)$", text, re.M)}


def test_relative_links_resolve() -> None:
    files = markdown_files()
    known = {p.resolve(): anchors(p.read_text()) for p in files}
    broken = []
    for page in files:
        text = re.sub(r"```.*?```", "", page.read_text(), flags=re.S)
        for url in LINK.findall(text):
            if re.match(r"^[a-z]+:", url):
                continue
            path, _, fragment = url.partition("#")
            target = (page.parent / path).resolve() if path else page.resolve()
            if not target.exists():
                broken.append(f"{page.relative_to(ROOT)}: {url} (no such file)")
            elif fragment and target.suffix == ".md" and fragment not in known.get(target, set()):
                broken.append(f"{page.relative_to(ROOT)}: {url} (no such heading)")
    assert not broken, "\n".join(broken)

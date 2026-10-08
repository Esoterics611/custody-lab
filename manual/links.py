#!/usr/bin/env python3
"""Pandoc JSON filter: make the chapters link to each other in every output format.

Quarto runs this for each chapter and passes the output format as the first argument: ``latex``
for the PDF, ``commonmark`` for the GitHub Markdown in ``manual/chapters/*.md``. The filter:

- rewrites a link to a sibling chapter source (``02-mpc-custody.qmd``, optionally with
  ``#section``) to that chapter's output in the same format (``.pdf`` or ``.md``);
- turns every "chapter N" or "Module N" in running text into such a link, and in "chapters 2, 4
  and 6" links each number; headings, code and existing links are left alone, and a chapter does
  not link to itself;
- adds a previous / next line at the top and bottom of each chapter, with a link to the manual's
  contents page in Markdown output;
- in Markdown output, puts an explicit anchor before every heading, because the GitHub Markdown
  writer drops heading ids and section links would otherwise have nothing to land on.

Standard library only, so the manual needs no filter toolchain beyond Python.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

CHAPTERS = Path(__file__).resolve().parent / "chapters"
EXTENSION = {"latex": ".pdf", "commonmark": ".md", "gfm": ".md", "markdown": ".md"}
MARKDOWN = {"commonmark", "gfm", "markdown"}
SOURCE_LINK = re.compile(r"^(\d\d-[\w-]+)\.qmd(#.*)?$")
WORD = re.compile(r"^(\W*)([Cc]hapters?|[Mm]odules?)$")
NUMBER = re.compile(r"^(\d+)(\D.*)?$")
SKIP = {"Link", "Image", "Code", "Math", "RawInline", "Header"}
BREAK = {"Space", "SoftBreak"}
INLINE = {
    "Str",
    "Space",
    "SoftBreak",
    "LineBreak",
    "Emph",
    "Underline",
    "Strong",
    "Strikeout",
    "Superscript",
    "Subscript",
    "SmallCaps",
    "Quoted",
    "Cite",
    "Code",
    "Math",
    "RawInline",
    "Link",
    "Image",
    "Note",
    "Span",
}

Node = dict[str, Any]


def chapters() -> dict[int, tuple[str, str]]:
    """Chapter number -> (file stem, short title), read from each source's front matter."""
    found = {}
    for path in sorted(CHAPTERS.glob("[0-9][0-9]-*.qmd")):
        title = re.search(r'^title: "(.*)"$', path.read_text(), re.M)
        name = title.group(1) if title else path.stem
        name = re.sub(r"^Module \d+: ", "", name).split(":")[0]
        found[int(path.stem[:2])] = (path.stem, name)
    return found


def text(words: str) -> list[Node]:
    inlines: list[Node] = []
    for i, word in enumerate(words.split(" ")):
        if i:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return inlines


def link(inlines: list[Node], url: str) -> Node:
    return {"t": "Link", "c": [["", [], []], inlines, [url, ""]]}


class Linker:
    def __init__(self, fmt: str, current: str) -> None:
        self.ext = EXTENSION.get(fmt, ".html")
        self.markdown = fmt in MARKDOWN
        self.chapters = chapters()
        self.current = current

    def target(self, number: int, module: bool) -> str | None:
        if module and number == 0:  # Module 0 is the toolchain, which has no chapter
            return None
        stem = self.chapters.get(number, ("", ""))[0]
        if not stem or stem == self.current:
            return None
        return stem + self.ext

    def autolink(self, xs: list[Node]) -> list[Node]:
        out: list[Node] = []
        i = 0
        while i < len(xs):
            word = WORD.match(xs[i]["c"]) if xs[i].get("t") == "Str" else None
            if word and i + 2 < len(xs) and xs[i + 1].get("t") in BREAK:
                prefix, name = word.groups()
                module = name.lower().startswith("module")
                if name.lower().endswith("s"):
                    out.append(xs[i])
                    i = self.link_numbers(xs, i + 1, out, module)
                    continue
                number = NUMBER.match(xs[i + 2]["c"]) if xs[i + 2].get("t") == "Str" else None
                url = number and self.target(int(number.group(1)), module)
                if number and url:
                    if prefix:
                        out.append({"t": "Str", "c": prefix})
                    out.append(link(text(f"{name} {number.group(1)}"), url))
                    if number.group(2):
                        out.append({"t": "Str", "c": number.group(2)})
                    i += 3
                    continue
            out.append(xs[i])
            i += 1
        return out

    def link_numbers(self, xs: list[Node], k: int, out: list[Node], module: bool) -> int:
        """After "chapters", link each number in a run such as "2, 4 and 6"."""
        while k + 1 < len(xs) and xs[k].get("t") in BREAK and xs[k + 1].get("t") == "Str":
            token = xs[k + 1]["c"]
            number = NUMBER.match(token)
            if number:
                url = self.target(int(number.group(1)), module)
                out.append(xs[k])
                out.append(
                    link(text(number.group(1)), url) if url else {"t": "Str", "c": number.group(1)}
                )
                if number.group(2):
                    out.append({"t": "Str", "c": number.group(2)})
                k += 2
                if number.group(2) and number.group(2) != ",":
                    break
            elif token in ("and", "to", "or"):
                out.extend(xs[k : k + 2])
                k += 2
            else:
                break
        return k

    def walk(self, node: Any) -> Any:
        if isinstance(node, list):
            if node and isinstance(node[0], dict) and node[0].get("t") in INLINE:
                node = self.autolink(node)
            return [self.walk(n) for n in node]
        if not isinstance(node, dict):
            return node
        kind = node.get("t")
        if kind == "Link":
            target = node["c"][2]
            source = SOURCE_LINK.match(target[0])
            if source:
                target[0] = source.group(1) + self.ext + (source.group(2) or "")
            return node
        if kind in SKIP:
            return node
        return {key: self.walk(value) for key, value in node.items()}

    def navigation(self) -> Node:
        numbers = sorted(self.chapters)
        here = next(n for n in numbers if self.chapters[n][0] == self.current)
        parts: list[list[Node]] = []
        if here - 1 in self.chapters:
            stem, name = self.chapters[here - 1]
            parts.append(
                [
                    *text("Previous:"),
                    {"t": "Space"},
                    link(text(f"Chapter {here - 1}, {name}"), stem + self.ext),
                ]
            )
        if self.markdown:
            parts.append([link(text("All chapters"), "../README.md")])
        if here + 1 in self.chapters:
            stem, name = self.chapters[here + 1]
            parts.append(
                [
                    *text("Next:"),
                    {"t": "Space"},
                    link(text(f"Chapter {here + 1}, {name}"), stem + self.ext),
                ]
            )
        inlines: list[Node] = []
        for i, part in enumerate(parts):
            if i:
                inlines.extend([{"t": "Space"}, {"t": "Str", "c": "|"}, {"t": "Space"}])
            inlines.extend(part)
        return {"t": "Para", "c": inlines}

    def anchors(self, blocks: list[Node]) -> list[Node]:
        out = []
        for block in blocks:
            if block.get("t") == "Header" and block["c"][1][0]:
                out.append({"t": "RawBlock", "c": ["html", f'<a id="{block["c"][1][0]}"></a>']})
            elif block.get("t") == "Div":
                block["c"][1] = self.anchors(block["c"][1])
            out.append(block)
        return out


def main() -> None:
    fmt = sys.argv[1] if len(sys.argv) > 1 else ""
    current = Path(os.environ.get("QUARTO_DOCUMENT_FILE", "")).stem
    doc = json.load(sys.stdin)
    linker = Linker(fmt, current)
    blocks = linker.walk(doc["blocks"])
    if current in {stem for stem, _ in linker.chapters.values()}:
        nav = linker.navigation()
        blocks = [nav, *blocks, {"t": "HorizontalRule"}, nav]
    if linker.markdown:
        blocks = linker.anchors(blocks)
    doc["blocks"] = blocks
    json.dump(doc, sys.stdout)


if __name__ == "__main__":
    main()

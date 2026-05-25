"""Render guidance markdown subset to HTML."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Literal

LineKind = Literal[
    "blank",
    "footnote",
    "list",
    "sublist",
    "italic_heading",
    "underline_heading",
    "md_heading",
    "paragraph",
]

FOOTNOTE_DEF_RE = re.compile(r"^\[\^(\d+)\]:\s*(.*)$")
LIST_ITEM_RE = re.compile(r"^(\s+)\(([a-z]|[ivx]+)\)\s*(.*)$", re.IGNORECASE)
SUBLIST_ITEM_RE = re.compile(r"^(\s{4,})\(([ivx]+)\)\s*(.*)$", re.IGNORECASE)
ITALIC_HEADING_RE = re.compile(r"^\*(.+)\*$")
UNDERLINE_HEADING_RE = re.compile(r"^<u>(.+?)</u(?:l)?>$")
MD_HEADING_RE = re.compile(r"^(#{1,2})\s+(.*)$")

INLINE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("fn_ref", re.compile(r"\[\^(\d+)\]")),
    ("underline_bold", re.compile(r"<u>\*\*(.+?)\*\*</u(?:l)?>")),
    ("bold", re.compile(r"\*\*(.+?)\*\*")),
    ("underline", re.compile(r"<u>(.+?)</u(?:l)?>")),
    ("italic", re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")),
]


@dataclass
class Segment:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    footnote_ref: str | None = None


@dataclass
class Line:
    kind: LineKind
    raw: str
    indent: int = 0
    label: str = ""
    content: str = ""
    footnote_num: str = ""


def _heading_id(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def plain_text(text: str) -> str:
    segments = parse_inline(text)
    return "".join(seg.text for seg in segments)


def parse_inline(text: str) -> list[Segment]:
    segments: list[Segment] = []
    pos = 0
    while pos < len(text):
        best_match = None
        best_kind = ""
        for kind, pattern in INLINE_PATTERNS:
            match = pattern.search(text, pos)
            if match and match.start() == pos:
                if best_match is None or len(match.group(0)) > len(best_match.group(0)):
                    best_match = match
                    best_kind = kind
        if best_match is None:
            next_pos = len(text)
            for _, pattern in INLINE_PATTERNS:
                match = pattern.search(text, pos + 1)
                if match:
                    next_pos = min(next_pos, match.start())
            if next_pos > pos:
                segments.append(Segment(text=text[pos:next_pos]))
            pos = next_pos if next_pos > pos else pos + 1
            continue

        if best_kind == "fn_ref":
            segments.append(Segment(text=best_match.group(1), footnote_ref=best_match.group(1)))
        elif best_kind == "underline_bold":
            segments.append(Segment(text=best_match.group(1), bold=True, underline=True))
        elif best_kind == "bold":
            segments.append(Segment(text=best_match.group(1), bold=True))
        elif best_kind == "underline":
            segments.append(Segment(text=best_match.group(1), underline=True))
        elif best_kind == "italic":
            segments.append(Segment(text=best_match.group(1), italic=True))
        pos = best_match.end()
    return [seg for seg in segments if seg.text or seg.footnote_ref]


def classify_line(line: str) -> Line:
    raw = line.rstrip()
    if not raw.strip():
        return Line(kind="blank", raw=raw)

    footnote = FOOTNOTE_DEF_RE.match(raw)
    if footnote:
        return Line(
            kind="footnote",
            raw=raw,
            footnote_num=footnote.group(1),
            content=footnote.group(2),
        )

    md_heading = MD_HEADING_RE.match(raw.strip())
    if md_heading:
        level = len(md_heading.group(1))
        return Line(
            kind="md_heading",
            raw=raw,
            label=str(level),
            content=md_heading.group(2).strip(),
        )

    sublist = SUBLIST_ITEM_RE.match(raw)
    if sublist:
        return Line(
            kind="sublist",
            raw=raw,
            indent=len(sublist.group(1)),
            label=sublist.group(2),
            content=sublist.group(3),
        )

    list_match = LIST_ITEM_RE.match(raw)
    if list_match and len(list_match.group(1)) <= 2:
        return Line(
            kind="list",
            raw=raw,
            indent=len(list_match.group(1)),
            label=list_match.group(2),
            content=list_match.group(3) or "",
        )

    italic = ITALIC_HEADING_RE.match(raw.strip())
    if italic:
        return Line(kind="italic_heading", raw=raw, content=italic.group(1))

    underline = UNDERLINE_HEADING_RE.match(raw.strip())
    if underline:
        return Line(kind="underline_heading", raw=raw, content=underline.group(1))

    return Line(kind="paragraph", raw=raw, content=raw.strip())


def split_lines(md: str) -> list[Line]:
    return [classify_line(line) for line in md.splitlines()]


def _wrap_segment(seg: Segment, highlight: str | None = None) -> str:
    if seg.footnote_ref is not None:
        inner = f'<sup class="fn-ref">[{html.escape(seg.footnote_ref)}]</sup>'
    else:
        inner = html.escape(seg.text)
        if seg.underline:
            inner = f"<u>{inner}</u>"
        if seg.bold:
            inner = f"<strong>{inner}</strong>"
        if seg.italic:
            inner = f"<em>{inner}</em>"
    if highlight:
        inner = f'<span style="background-color: {highlight};">{inner}</span>'
    return inner


def render_inline(text: str, highlight: str | None = None) -> str:
    return "".join(_wrap_segment(seg, highlight) for seg in parse_inline(text))


def _render_line_content(line: Line, highlight: str | None = None) -> str:
    if line.kind == "footnote":
        body = render_inline(line.content, highlight)
        return f'<p class="fn-def"><sup>{html.escape(line.footnote_num)}</sup> {body}</p>'
    if line.kind == "list":
        body = render_inline(line.content, highlight)
        return f'<li class="list-item"><span class="list-label">({html.escape(line.label)})</span> {body}</li>'
    if line.kind == "sublist":
        body = render_inline(line.content, highlight)
        return (
            f'<li class="list-item sublist-item">'
            f'<span class="list-label">({html.escape(line.label)})</span> {body}</li>'
        )
    if line.kind == "italic_heading":
        return f'<p class="para-heading"><em>{render_inline(line.content, highlight)}</em></p>'
    if line.kind == "underline_heading":
        return f'<p class="underline-heading"><u>{render_inline(line.content, highlight)}</u></p>'
    if line.kind == "md_heading":
        level = line.label
        tag = "h1" if level == "1" else "h2"
        cls = "doc-title" if level == "1" else "section-heading"
        anchor = _heading_id(line.content) if level == "2" else ""
        id_attr = f' id="{anchor}"' if anchor else ""
        inner = render_inline(line.content, highlight)
        return f'<{tag} class="{cls}"{id_attr}>{inner}</{tag}>'
    return f"<p>{render_inline(line.content, highlight)}</p>"


def _line_plain(line: Line) -> str:
    if line.kind == "blank":
        return ""
    if line.kind == "footnote":
        return plain_text(line.content)
    return plain_text(line.content)


def _group_lines(lines: list[Line], highlight: str | None = None) -> list[str]:
    parts: list[str] = []
    list_open = False

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            parts.append("</ul>")
            list_open = False

    for line in lines:
        if line.kind == "blank":
            close_list()
            continue
        if line.kind in {"list", "sublist"}:
            if not list_open:
                parts.append('<ul class="md-list">')
                list_open = True
            parts.append(_render_line_content(line, highlight))
            continue
        close_list()
        parts.append(_render_line_content(line, highlight))

    close_list()
    return parts


def render_markdown(md: str, highlight: str | None = None) -> str:
    if not md.strip():
        return ""
    lines = split_lines(md)
    return "".join(_group_lines(lines, highlight))

"""Word-level diff utilities with punctuation-aware tokenization."""

from __future__ import annotations

import difflib
import html
import re
from dataclasses import dataclass

from src.md_render import Line, _line_plain, plain_text, render_markdown, split_lines, parse_inline, _render_line_content

NO_SPACE_BEFORE = set(",.;:!?%)]}'")
NO_SPACE_AFTER = set("([{\"'/$")


@dataclass
class _CharSpan:
    start: int
    end: int
    bold: bool = False
    italic: bool = False
    underline: bool = False
    footnote_ref: bool = False


def token_spans(text: str) -> list[tuple[str, int, int]]:
    """Return word/punctuation tokens with their start/end offsets in text."""
    return [
        (match.group(0), match.start(), match.end())
        for match in re.finditer(r"\w+|[^\w\s]", text, re.UNICODE)
    ]


def tokenize(text: str) -> list[str]:
    return [token for token, _, _ in token_spans(text)]


def _char_spans(segments) -> list[_CharSpan]:
    spans: list[_CharSpan] = []
    pos = 0
    for seg in segments:
        length = len(seg.text)
        if length:
            spans.append(
                _CharSpan(
                    start=pos,
                    end=pos + length,
                    bold=seg.bold,
                    italic=seg.italic,
                    underline=seg.underline,
                    footnote_ref=seg.footnote_ref is not None,
                )
            )
            pos += length
    return spans


def _format_for_range(spans: list[_CharSpan], start: int, end: int) -> _CharSpan:
    fmt = _CharSpan(start, end)
    for span in spans:
        if span.start < end and span.end > start:
            fmt.bold |= span.bold
            fmt.italic |= span.italic
            fmt.underline |= span.underline
            fmt.footnote_ref |= span.footnote_ref
    return fmt


def _needs_space_before(prev: str, token: str) -> bool:
    if not prev:
        return False
    if token in NO_SPACE_BEFORE:
        return False
    if prev in NO_SPACE_AFTER:
        return False
    return True


def _render_token(token: str, fmt: _CharSpan, highlight: str | None, prev: str | None) -> str:
    prefix = " " if prev and _needs_space_before(prev, token) else ""
    if fmt.footnote_ref and token.isdigit():
        inner = f'<sup class="fn-ref">[{html.escape(token)}]</sup>'
    else:
        inner = html.escape(token)
        if fmt.underline:
            inner = f"<u>{inner}</u>"
        if fmt.bold:
            inner = f"<strong>{inner}</strong>"
        if fmt.italic:
            inner = f"<em>{inner}</em>"
    if highlight:
        inner = f'<span style="background-color: {highlight};">{inner}</span>'
    return prefix + inner


def render_inline_diff(text1: str, text2: str) -> str:
    segs1 = parse_inline(text1)
    segs2 = parse_inline(text2)
    plain1 = "".join(seg.text for seg in segs1)
    plain2 = "".join(seg.text for seg in segs2)
    char_spans1 = _char_spans(segs1)
    char_spans2 = _char_spans(segs2)

    tokens1 = tokenize(plain1)
    tokens2 = tokenize(plain2)
    tok_spans1 = token_spans(plain1)
    tok_spans2 = token_spans(plain2)
    diff = difflib.ndiff(tokens1, tokens2)

    parts: list[str] = []
    prev: str | None = None
    i1 = 0
    i2 = 0

    for entry in diff:
        if entry.startswith("? "):
            continue
        code, token = entry[:2], entry[2:]

        if code == "  ":
            _, start1, end1 = tok_spans1[i1]
            _, start2, end2 = tok_spans2[i2]
            fmt = _format_for_range(char_spans1, start1, end1)
            fmt2 = _format_for_range(char_spans2, start2, end2)
            fmt.bold |= fmt2.bold
            fmt.italic |= fmt2.italic
            fmt.underline |= fmt2.underline
            parts.append(_render_token(token, fmt, None, prev))
            i1 += 1
            i2 += 1
        elif code == "- ":
            _, start1, end1 = tok_spans1[i1]
            fmt = _format_for_range(char_spans1, start1, end1)
            parts.append(_render_token(token, fmt, "#fbb6c2", prev))
            i1 += 1
        elif code == "+ ":
            _, start2, end2 = tok_spans2[i2]
            fmt = _format_for_range(char_spans2, start2, end2)
            parts.append(_render_token(token, fmt, "#d4fcbc", prev))
            i2 += 1
        prev = token

    return "".join(parts)


def _render_line_diff(line1: Line | None, line2: Line | None) -> str:
    if line1 is None and line2 is not None:
        return _render_line_content(line2, highlight="#d4fcbc")
    if line2 is None and line1 is not None:
        return _render_line_content(line1, highlight="#fbb6c2")

    assert line1 is not None and line2 is not None
    kind = line2.kind if line2.kind != "blank" else line1.kind

    if kind == "footnote":
        body = render_inline_diff(line1.content, line2.content)
        num = line2.footnote_num or line1.footnote_num
        return f'<p class="fn-def"><sup>{html.escape(num)}</sup> {body}</p>'
    if kind == "list":
        label = line2.label or line1.label
        body = render_inline_diff(line1.content, line2.content)
        return f'<li class="list-item"><span class="list-label">({html.escape(label)})</span> {body}</li>'
    if kind == "sublist":
        label = line2.label or line1.label
        body = render_inline_diff(line1.content, line2.content)
        return (
            f'<li class="list-item sublist-item">'
            f'<span class="list-label">({html.escape(label)})</span> {body}</li>'
        )
    if kind == "italic_heading":
        return f'<p class="para-heading"><em>{render_inline_diff(line1.content, line2.content)}</em></p>'
    if kind == "underline_heading":
        return f'<p class="underline-heading"><u>{render_inline_diff(line1.content, line2.content)}</u></p>'
    return f"<p>{render_inline_diff(line1.content, line2.content)}</p>"


def _line_key(line: Line) -> str:
    if line.kind == "blank":
        return ""
    if line.kind in {"list", "sublist"}:
        return f"{line.kind}:{line.label}:{_line_plain(line)}"
    return f"{line.kind}:{_line_plain(line)}"


def _render_line_group(lines: list[tuple[Line | None, Line | None]]) -> str:
    parts: list[str] = []
    list_open = False

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            parts.append("</ul>")
            list_open = False

    for line1, line2 in lines:
        line = line2 or line1
        assert line is not None
        if line.kind == "blank":
            close_list()
            continue
        if line.kind in {"list", "sublist"}:
            if not list_open:
                parts.append('<ul class="md-list">')
                list_open = True
            parts.append(_render_line_diff(line1, line2))
            continue
        close_list()
        parts.append(_render_line_diff(line1, line2))

    close_list()
    return "".join(parts)


def generate_formatted_diff_html(md1: str, md2: str) -> str:
    """Diff two markdown blocks while preserving structure and inline formatting."""
    if not md1.strip():
        return render_markdown(md2, highlight="#d4fcbc")
    if not md2.strip():
        return render_markdown(md1, highlight="#fbb6c2")
    if plain_text(md1) == plain_text(md2):
        return render_markdown(md2)

    lines1 = split_lines(md1)
    lines2 = split_lines(md2)
    plain1 = [_line_key(line) for line in lines1 if line.kind != "blank"]
    plain2 = [_line_key(line) for line in lines2 if line.kind != "blank"]

    idx1 = [i for i, line in enumerate(lines1) if line.kind != "blank"]
    idx2 = [i for i, line in enumerate(lines2) if line.kind != "blank"]

    matcher = difflib.SequenceMatcher(None, plain1, plain2)
    rendered_groups: list[tuple[Line | None, Line | None]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                rendered_groups.append((lines1[idx1[k]], lines2[idx2[j1 + (k - i1)]]))
        elif tag == "replace":
            len1 = i2 - i1
            len2 = j2 - j1
            count = max(len1, len2)
            for n in range(count):
                l1 = lines1[idx1[i1 + n]] if n < len1 else None
                l2 = lines2[idx2[j1 + n]] if n < len2 else None
                rendered_groups.append((l1, l2))
        elif tag == "delete":
            for k in range(i1, i2):
                rendered_groups.append((lines1[idx1[k]], None))
        elif tag == "insert":
            for k in range(j1, j2):
                rendered_groups.append((None, lines2[idx2[k]]))

    return _render_line_group(rendered_groups)


def generate_diff_html(text1: str, text2: str) -> str:
    """Plain-text diff (legacy). Prefer generate_formatted_diff_html for markdown."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    diff = difflib.ndiff(tokens1, tokens2)

    parts: list[str] = []
    prev: str | None = None
    for entry in diff:
        if entry.startswith("? "):
            continue
        code, token = entry[:2], entry[2:]
        prefix = " " if prev and _needs_space_before(prev, token) else ""
        escaped = html.escape(token)
        if code == "  ":
            parts.append(prefix + escaped)
        elif code == "- ":
            parts.append(f'{prefix}<span style="background-color: #fbb6c2;">{escaped}</span>')
        elif code == "+ ":
            parts.append(f'{prefix}<span style="background-color: #d4fcbc;">{escaped}</span>')
        prev = token

    return "".join(parts)

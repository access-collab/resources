#!/usr/bin/env python3
"""Build a single HTML viewer for CnaM Article 40 guidance v1, v2, and comparison."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.diff_utils import generate_formatted_diff_html
from src.md_render import render_markdown

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "data" / "changes_guidance_v1_v2.csv"
V1_PATH = BASE / "data" / "guidance_v1.md"
V2_PATH = BASE / "data" / "guidance_v2.md"
OUT_PATH = BASE / "index.html"

SECTION_NAMES = {
    "Sec1": "1. Introduction",
    "Sec2": "2. Overview of Guidance",
    "Sec3": "3. Overview of VR status application process",
    "Sec4": "4. How to apply",
    "Sec5": "5. Application Requirements",
    "Sec6": "6. Information to be provided (Article 40(8))",
    "Sec7": "7. Further guidance in respect of applications",
    "Sec8": "8. Access Modalities",
    "Sec9": "9. After an application for VR status is approved",
    "Preamble": "Title and publication details",
}

SECTION_ORDER = [
    "Preamble",
    "Sec1",
    "Sec2",
    "Sec3",
    "Sec4",
    "Sec5",
    "Sec6",
    "Sec7",
    "Sec8",
    "Sec9",
]

FN_RE = re.compile(r"^fn(\d+)$", re.I)
_P_RE = re.compile(r"^(.+)_p(\d+)$")
_H_RE = re.compile(r"^(.+)_h$")
_U_RE = re.compile(r"^(.+)_u(\d+)$")
_LIST_RE = re.compile(r"^(.+)\([a-z]\)$")


def _clean(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none"} else text


def format_para(para: str, block_type: str = "") -> str:
    if not para:
        return ""
    if para == "title":
        return "Title"
    if para == "contents":
        return "Contents"
    fn = FN_RE.match(para)
    if fn:
        return f"Footnote {fn.group(1)}"
    heading = _H_RE.match(para)
    if heading:
        return f"Heading ({heading.group(1)})"
    sub = _U_RE.match(para)
    if sub:
        return f"Subheading ({sub.group(1)})"
    if _LIST_RE.match(para):
        return para
    numbered = _P_RE.match(para)
    if numbered:
        return f"{numbered.group(1)}, ¶{numbered.group(2)}"
    if block_type == "footnote":
        return f"Footnote ({para})"
    return para


def format_side_label(pos: str, para: str, block_type: str, version: str) -> str:
    section = SECTION_NAMES.get(pos, pos or "—")
    para_label = format_para(para, block_type)
    if para_label:
        return f"{section}, {para_label} ({version})"
    return f"{section} ({version})"


def format_changed_label(
    v1_pos: str,
    v1_para: str,
    v2_pos: str,
    v2_para: str,
    block_type_v1: str,
    block_type_v2: str,
    version: str,
) -> str:
    pos = v2_pos or v1_pos
    section = SECTION_NAMES.get(pos, pos or "—")
    if v2_pos and v1_pos and v2_pos != v1_pos:
        section = f'<span class="ref-changed">{section}</span>'

    para_label = format_para(v2_para or v1_para, block_type_v2 or block_type_v1)
    if v2_para and v1_para and v2_para != v1_para:
        para_label = f'<span class="ref-changed">{para_label}</span>'
    if para_label:
        return f"{section}, {para_label} ({version})"
    return f"{section} ({version})"


def build_compare_header(row: pd.Series) -> str:
    v1_pos, v1_para = _clean(row["V1_pos"]), _clean(row["V1_para"])
    v2_pos, v2_para = _clean(row["V2_pos"]), _clean(row["V2_para"])
    bt1, bt2 = _clean(row.get("block_type_v1", "")), _clean(row.get("block_type_v2", ""))
    t1, t2 = _clean(row["text_V1"]), _clean(row["text_V2"])

    if t1 and not t2:
        return f"{format_side_label(v1_pos, v1_para, bt1, 'v1')} → removed in v2"
    if t2 and not t1:
        return f"→ {format_changed_label('', '', v2_pos, v2_para, '', bt2, 'v2')} (new in v2)"

    from_str = format_side_label(v1_pos, v1_para, bt1, "v1")
    to_str = format_changed_label(v1_pos, v1_para, v2_pos, v2_para, bt1, bt2, "v2")
    return f"{from_str} → {to_str}"


def build_compare_body(row: pd.Series) -> str:
    t1, t2 = _clean(row["text_V1"]), _clean(row["text_V2"])
    if t1 and not t2:
        return render_markdown(t1, highlight="#fbb6c2")
    if t2 and not t1:
        return render_markdown(t2)
    return generate_formatted_diff_html(t1, t2)


def compare_body_class(row: pd.Series) -> str:
    t1, t2 = _clean(row["text_V1"]), _clean(row["text_V2"])
    if t2 and not t1:
        return "subsection-body block-new-v2"
    if t1 and not t2:
        return "subsection-body block-removed-v1"
    return "subsection-body"


def section_for_row(row: pd.Series) -> str:
    for col in ("V1_pos", "V2_pos"):
        pos = _clean(row[col])
        if pos:
            return pos
    return ""


def build_comparison_html(df: pd.DataFrame) -> tuple[str, str]:
    present_sections = []
    seen: set[str] = set()
    for pos in SECTION_ORDER:
        if pos in seen:
            continue
        mask = (df["V1_pos"].apply(_clean) == pos) | (df["V2_pos"].apply(_clean) == pos)
        if mask.any():
            present_sections.append(pos)
            seen.add(pos)

    toc_links = ", ".join(
        f'<a href="#cmp-{key}">{SECTION_NAMES[key]}</a>' for key in present_sections
    )

    intro = """
<div class="intro">
    <p>This view compares <strong>guidance v1</strong>
    (20 February 2026; <em>Guidance for Applicants</em>)
    with <strong>guidance v2</strong>
    (25 May 2026; <em>Guidance on Article 40(4-11) DSA</em>).</p>
    <p><strong>In the text:</strong></p>
    <ul>
        <li><span class="swatch swatch-new"></span> Light green background — wholly new in v2</li>
        <li><span class="swatch swatch-removed"></span> Pink background — removed in v2</li>
        <li><span class="swatch swatch-del"></span> Red — v1 text changed or removed within a paired block</li>
        <li><span class="swatch swatch-add"></span> Green — v2 text added or changed within a paired block</li>
    </ul>
    <p><strong>In the headings:</strong> <span class="swatch swatch-ref"></span> Yellow — section or paragraph reference changed.</p>
</div>
"""

    parts = [intro, f'<h2 class="panel-toc">Table of Contents</h2><p class="panel-toc-links">{toc_links}</p>']
    added_anchors: set[str] = set()

    for _, row in df.iterrows():
        anchor_pos = section_for_row(row)
        if anchor_pos and anchor_pos not in added_anchors:
            section_label = SECTION_NAMES.get(anchor_pos, anchor_pos)
            parts.append(
                f'<hr class="section-break">\n<h2 id="cmp-{anchor_pos}">{section_label}</h2>'
            )
            added_anchors.add(anchor_pos)

        parts.append(
            f'<div class="diff">'
            f'<div class="header">{build_compare_header(row)}</div>'
            f'<div class="{compare_body_class(row)}">{build_compare_body(row)}</div>'
            f"</div>"
        )

    return "".join(parts), toc_links


def build_document_html(path: Path, doc_id: str) -> str:
    md = path.read_text(encoding="utf-8")
    body = render_markdown(md)
    meta = {
        "v1": ("Guidance for Applicants", "20 February 2026"),
        "v2": ("Guidance on Article 40(4-11) DSA", "25 May 2026"),
    }[doc_id]
    title, date = meta
    return f"""
<div class="intro">
    <p><strong>{title}</strong><br>Publication date: {date}</p>
    <p>Machine-readable HTML rendering of the tidied guidance text.</p>
</div>
<div class="document-body">{body}</div>
"""


STYLES = """
        :root {
            --tab-bg: #f4f4f4;
            --tab-active: #fff;
            --tab-border: #ccc;
            --accent: #1a5276;
        }
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px 40px;
            color: #222;
        }
        .site-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: #fff;
            border-bottom: 1px solid var(--tab-border);
            padding: 16px 0 0;
            margin-bottom: 24px;
        }
        .site-header h1 {
            font-size: 1.35em;
            margin: 0 0 12px;
            line-height: 1.3;
        }
        .view-tabs {
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }
        .view-tabs button {
            appearance: none;
            border: 1px solid var(--tab-border);
            border-bottom: none;
            background: var(--tab-bg);
            padding: 10px 18px;
            font-size: 0.95em;
            cursor: pointer;
            border-radius: 6px 6px 0 0;
            color: #444;
        }
        .view-tabs button:hover { background: #eaeaea; }
        .view-tabs button.active {
            background: var(--tab-active);
            font-weight: bold;
            color: var(--accent);
            border-bottom: 1px solid var(--tab-active);
            margin-bottom: -1px;
        }
        .view-panel { display: none; }
        .view-panel.active { display: block; }
        .intro {
            margin-bottom: 28px;
            padding: 16px 18px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid var(--accent);
        }
        .intro ul { margin: 0.5em 0; padding-left: 1.4em; }
        .swatch {
            display: inline-block;
            width: 14px;
            height: 14px;
            vertical-align: middle;
            margin-right: 4px;
            border-radius: 2px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .swatch-new { background: #e8f7e3; }
        .swatch-removed { background: #fde8eb; }
        .swatch-del { background: #fbb6c2; }
        .swatch-add { background: #d4fcbc; }
        .swatch-ref { background: #fff3b0; }
        .ref-changed { background-color: #fff3b0; }
        .diff { margin-bottom: 24px; }
        .header { font-weight: bold; margin-bottom: 8px; font-size: 0.95em; }
        h2.section-heading, h2.panel-toc {
            margin-top: 40px;
            font-size: 1.25em;
        }
        hr.section-break { margin: 40px 0; border: 0; border-top: 2px solid #ccc; }
        .doc-title { font-size: 1.5em; margin: 0 0 0.5em; }
        .document-body .section-heading { margin-top: 2em; }
        .subsection-body p, .document-body p { margin: 0.65em 0; }
        .subsection-body .para-heading, .document-body .para-heading {
            font-style: italic; font-weight: 600; margin-top: 1em;
        }
        .subsection-body .underline-heading, .document-body .underline-heading {
            text-decoration: underline; font-weight: 600; margin-top: 1em;
        }
        .subsection-body .fn-def, .document-body .fn-def {
            font-size: 0.92em; color: #444; margin: 0.5em 0 0.5em 1.5em;
        }
        .fn-ref { font-size: 0.75em; vertical-align: super; }
        ul.md-list { list-style: none; margin: 0.5em 0; padding-left: 0; }
        li.list-item { margin: 0.35em 0; padding-left: 1.5em; text-indent: -1.5em; }
        li.sublist-item { padding-left: 3em; text-indent: -1.5em; }
        .subsection-body.block-new-v2 {
            background-color: #e8f7e3;
            padding: 10px 12px;
            border-radius: 4px;
            border-left: 4px solid #7bc47b;
        }
        .subsection-body.block-removed-v1 {
            background-color: #fde8eb;
            padding: 10px 12px;
            border-radius: 4px;
            border-left: 4px solid #e08a96;
        }
"""

SCRIPT = """
(function () {
    const tabs = document.querySelectorAll('.view-tabs button');
    const panels = document.querySelectorAll('.view-panel');
    const valid = new Set(['compare', 'v1', 'v2']);

    function show(view) {
        if (!valid.has(view)) view = 'compare';
        tabs.forEach(function (btn) {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        panels.forEach(function (panel) {
            panel.classList.toggle('active', panel.id === 'view-' + view);
        });
        history.replaceState(null, '', '#' + view);
    }

    tabs.forEach(function (btn) {
        btn.addEventListener('click', function () { show(btn.dataset.view); });
    });

    var initial = (location.hash || '#compare').slice(1);
    show(initial);
})();
"""


def main() -> None:
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    compare_html, _ = build_comparison_html(df)
    v1_html = build_document_html(V1_PATH, "v1")
    v2_html = build_document_html(V2_PATH, "v2")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CnaM Article 40 Guidance — v1, v2 &amp; comparison</title>
    <style>{STYLES}</style>
</head>
<body>
    <header class="site-header">
        <h1>Coimisiún na Meán — Article 40 Data Access Guidance</h1>
        <nav class="view-tabs" aria-label="Document view">
            <button type="button" data-view="compare" class="active">Comparison</button>
            <button type="button" data-view="v1">Guidance v1</button>
            <button type="button" data-view="v2">Guidance v2</button>
        </nav>
    </header>

    <main id="view-compare" class="view-panel active" aria-label="Comparison">
        {compare_html}
    </main>
    <main id="view-v1" class="view-panel" aria-label="Guidance v1">
        {v1_html}
    </main>
    <main id="view-v2" class="view-panel" aria-label="Guidance v2">
        {v2_html}
    </main>

    <script>{SCRIPT}</script>
</body>
</html>
"""

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(df)} comparison rows)")


if __name__ == "__main__":
    main()

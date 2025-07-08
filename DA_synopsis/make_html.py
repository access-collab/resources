import difflib
import pandas as pd
import re

def generate_diff_html(text1, text2):
    """Returns HTML showing differences between text1 and text2."""
    diff = difflib.ndiff(text1.split(), text2.split())
    html = ''
    for token in diff:
        if token.startswith('? '):
            continue 
        elif token.startswith('+ '):
            html += f'<span style="background-color: #d4fcbc;">{token[2:]}</span> '
        elif token.startswith('- '):
            html += f'<span style="background-color: #fbb6c2;">{token[2:]}</span> '
        elif token.startswith('  '):
            html += token[2:] + ' '
    return html

def format_plain_label(pos, para, label):
    if "Rec" in pos or "Art" in pos:
        formatted = f"{pos[:3]}. {pos[3:]}"
    else:
        formatted = pos
    parts = []
    if pos:
        parts.append(formatted)
    if para == "title":
        parts.append("Title")
    elif para:
        parts.append(f"paragraph {para}")
    return f"{', '.join(parts)} {label}"

def format_changed_label(dda_pos, dda_para, da_pos, da_para, label):
    parts = []

    # Format position
    if "Rec" in da_pos or "Art" in da_pos:
        formatted_pos = f"{da_pos[:3]}. {da_pos[3:]}"
    else:
        formatted_pos = da_pos

    if da_pos != dda_pos:
        formatted_pos = f'<span style="background-color: #fff3b0;">{formatted_pos}</span>'
    parts.append(formatted_pos)

    # Format paragraph
    if da_para == "title":
        parts.append("Title")
    elif da_para:
        if da_para != dda_para:
            parts.append(f'<span style="background-color: #fff3b0;">paragraph {da_para}</span>')
        else:
            parts.append(f"paragraph {da_para}")

    return f"{', '.join(parts)} {label}"




# Load df
df = pd.read_csv("./data/changes_DDA_DA.csv").fillna("")

# Patterns for Articles and Recitals
art_pattern = re.compile(r'Art\d+\w*', re.IGNORECASE)
rec_pattern = re.compile(r'Rec\d+\w*', re.IGNORECASE)

# Populate Table of Contents

seen_articles = {}
seen_recitals = {}
for _, row in df.iterrows():
    dda_pos = row['DDA_pos']

    match_art = art_pattern.search(dda_pos)
    if match_art:
        key = match_art.group()
        if key not in seen_articles:
            seen_articles[key] = f"Article {key[3:]}"

    match_rec = rec_pattern.search(dda_pos)
    if match_rec:
        key = match_rec.group()
        if key not in seen_recitals:
            seen_recitals[key] = f"Recital {key[3:]}"

# Create Table of Contents HTML
recital_links = ", ".join(
    f'<a href="#{key}">{seen_recitals[key]}</a>' for key in seen_recitals
)
article_links = ", ".join(
    f'<a href="#{key}">{seen_articles[key]}</a>' for key in seen_articles
)

intro_html = """
<div style="margin-bottom: 30px;">
    <p>This document presents a comparison between the <strong>Draft Delegated Act on Data Access (DDA)</strong> (<a href="https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/13817-Delegated-Regulation-on-data-access-provided-for-in-the-Digital-Services-Act_en" target="_blank">link to document</a>) and the <strong>Adopted Delegated Act (DA)</strong> (<a href="https://digital-strategy.ec.europa.eu/en/library/delegated-act-data-access-under-digital-services-act-dsa" target="_blank">link to document</a>).<br>Since it unilaterally compares the DDA with the DA, the Table of Contents only includes the original rectials and articles of the DDA. New recitals can be found under the <i>Recital 28</i> heading.</p>

    <p>The highlighted colors indicate the following differences:<br><u>In the text:</u>
    <ul>
        <li><span style="background-color: #fbb6c2; padding: 2px 4px;">Red</span>: Text removed from the DDA</li>
        <li><span style="background-color: #d4fcbc; padding: 2px 4px;">Green</span>: Text added in the DA</li>
    </ul>
    <u>In the headings:</u>
    <ul>
        <li><span style="background-color: #fff3b0; padding: 2px 4px;">Yellow</span>: Changes in references (e.g. article numbers and/or paragraph labels)</li>
    </ul></p>
    <br>
    <p>The overview is based on work done by LK Seiling at the <a href="https://dsa40collaboratory.eu/" target="__blank">DSA40 Data Access Collaboratory</a>, who is responsible for splitting and aligning the texts to achieve a meaningful comparison. All data and the code on which this simple html page is based on, can be found at <a href="https://github.com/access-collab/resources/tree/main/DA_synopsis" target="__blank">https://github.com/access-collab/resources/tree/main/DA_synopsis</a>.</p>
    <p><strong>Citation:</strong> If you wish to cite this comparison, please use the following format:</p>
    <blockquote style="background-color: #f0f0f0; padding: 10px; border-left: 4px solid #999;">
        LK Seiling (2025). Comparison of the Draft and Adopted Delegated Act on Data Access. <i>DSA 40 Data Access Collaboratory</i>. Available at: <a href="https://dsa40collaboratory.eu/dda-da-comparison/">https://dsa40collaboratory.eu/dda-da-comparison/</a>.
    </blockquote>
    <br>
</div>
"""

toc_html = f"""
<h2>Table of Contents</h2>
<table class="toc" border="0" cellspacing="5" cellpadding="5">
<tr><th>Recitals</th><th>Articles</th></tr>
<tr><td>{recital_links}</td><td>{article_links}</td></tr>
</table>
"""

# Start HTML
html_output = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Comparison: Draft vs. Adopted Delegated Act on Data Access</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
        .diff {{ margin-bottom: 30px; }}
        .header {{ font-weight: bold; margin-bottom: 5px; }}
        h2 {{ margin-top: 40px; }}
        table {{ border-collapse: collapse; }}
        th, td {{ padding: 8px 15px; text-align: left; }}
        table.toc {{ table-layout: fixed; width: 85%; margin-left: auto; margin-right: auto; display: table; }}
        table.toc th,
        table.toc td {{ width: 50%; vertical-align: top; word-wrap: break-word; }}
    </style>
</head>
<body>
<h1>Comparison of the Draft and Adopted Delegated Act on Data Access</h1>
{intro_html}
{toc_html}
"""

# Basis for tracking of subheading and anchor tag insertion
expl_inserted = False
recitals_inserted = False
articles_inserted = False
added_anchors = set()

# For each diff block
for _, row in df.iterrows():
    text1 = str(row['text_DDA'])
    text2 = str(row['text_DA'])
    html_diff = generate_diff_html(text1, text2)

    dda_pos, dda_para = row['DDA_pos'], row['DDA_para']
    da_pos, da_para = row['DA_pos'], row['DA_para']
    
    
    from_str = format_plain_label(dda_pos, dda_para, "DDA")
    to_str = format_changed_label(dda_pos, dda_para, da_pos, da_para, "DA")
    if da_pos == "":
        header_str = f"{from_str} → removed"
    elif dda_pos == "":
        header_str = f"→ {to_str}"
    else:
        header_str = f"{from_str} → {to_str}"


    # Insert subheadings
    dda_pos_lower = da_pos.lower()
    if not expl_inserted and "exp" in dda_pos_lower:
        html_output += "<h2>Explanatory Memorandum</h2>\n"
        expl_inserted = True
    if not recitals_inserted and "title" in dda_pos_lower:
        html_output += "<h2>Recitals</h2>\n"
        recitals_inserted = True
    elif not articles_inserted and "art" in dda_pos_lower:
        html_output += "<h2>Articles</h2>\n"
        articles_inserted = True

    anchor_tag = ""
    section_break_html = ""
    section_label_html = ""
    
    for pattern in [art_pattern, rec_pattern]:
        match = pattern.search(row['DDA_pos'])
        if match:
            key = match.group()
            if key not in added_anchors:
                anchor_tag = f' id="{key}"'
                section_label = seen_articles.get(key) or seen_recitals.get(key)
                section_break_html = f'<hr class="section-break">\n<h3>{section_label}</h3>\n'
                added_anchors.add(key)
                break

    html_output += f"""
        {section_break_html}
        <div class="diff"{anchor_tag}>
            <div class="header">{header_str}</div>
            <div>{html_diff}</div>
        </div>
    """
html_output += "</body></html>"

# Write to file
with open('compare_DDA_DA.html', 'w', encoding='utf-8') as f:
    f.write(html_output)


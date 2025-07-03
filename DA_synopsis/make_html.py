import difflib
import pandas as pd
import re

def generate_diff_html(text1, text2):
    """Returns HTML showing differences between text1 and text2."""
    diff = difflib.ndiff(text1.split(), text2.split())
    html = ''
    for token in diff:
        if token.startswith('+'):
            html += f'<span style="background-color: #d4fcbc;">{token[2:]}</span> '
        elif token.startswith('-'):
            html += f'<span style="background-color: #fbb6c2;">{token[2:]}</span> '
        else:
            html += token[2:] + ' '
    return html

def format_position(pos, para, label):
    if not pos:
        return "removed" if label == "DA" else ""
    
    if "Rec" in pos or "Art" in pos:
        formatted = f"{pos[:3]}. {pos[3:]}"
    else:
        formatted = pos
    
    if para == "title":
        formatted += " Title"
    elif para:
        formatted += f", paragraph {para}"
    
    return f"{formatted} {label}"


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
        table.toc {{ table-layout: fixed; width: 85%; }}
        table.toc th,
        table.toc td {{ width: 50%; vertical-align: top; word-wrap: break-word; }}
    </style>
</head>
<body>
<h1>Comparison: Draft Delegated Act on Data Access (DDA) vs. Adopted Delegated Act on Data Access (DA)</h1>
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
    from_str = format_position(row['DDA_pos'], row['DDA_para'], "DDA")
    to_str = format_position(row['DA_pos'], row['DA_para'], "DA")

    dda_pos_lower = row['DDA_pos'].lower()

    # Insert subheadings
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
    
    for pattern in [article_pattern, recital_pattern]:
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
            <div class="header">{from_str} → {to_str}</div>
            <div>{html_diff}</div>
        </div>
        """
html_output += "</body></html>"

# Write to file
with open('compare_DDA_DA.html', 'w', encoding='utf-8') as f:
    f.write(html_output)


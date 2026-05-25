# Coimisiún na Meán — Article 40 Data Access Guidance (v1 vs v2)

Machine-readable HTML versions of Coimisiún na Meán’s guidance on data access applications under Article 40(4–11) DSA, plus a block-level comparison between the two published versions.

| Version | Title | Publication date |
|---------|-------|------------------|
| **v1** | *Guidance for Applicants* | 20 February 2026 |
| **v2** | *Guidance on Article 40(4-11) DSA* | 25 May 2026 |

The original PDFs are image-only (text cannot be selected or linked). The markdown files in `data/` are tidied, searchable transcriptions of those documents.

**👉 [View online](https://dsa40collaboratory.eu/cnam-guidance/)** 

---

## Run locally

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Build the HTML**

   ```bash
   python3 build_html.py
   ```

3. **Open** `index.html` in a browser.

4. (Optional) Update the comparison after editing the alignment CSV or guidance files.


   ```bash
   python3 build_html.py
   ```
---

## Credits and citation

The comparison is based on work by **LK Seiling** at the [DSA40 Data Access Collaboratory](https://dsa40collaboratory.eu/), who transcribed the PDFs, aligned the texts at block level, and adapted the comparison workflow originally developed for the [Delegated Act synopsis](https://dsa40collaboratory.eu/dda-da-comparison/).

**Citation**:

> **LK Seiling** (2026). Comparison of Coimisiún na Meán Article 40 Data Access Guidance (v1 vs v2). *DSA 40 Data Access Collaboratory*. Available at: [https://dsa40collaboratory.eu/cnam-guidance/](https://dsa40collaboratory.eu/cnam-guidance/).

---
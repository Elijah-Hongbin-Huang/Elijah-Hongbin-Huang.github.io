#!/usr/bin/env python3
# tex_to_cv.py

import re
from collections import OrderedDict

import pypandoc
from bs4 import BeautifulSoup, NavigableString, Tag
from jinja2 import Template

# 1) File paths
TEX_FILE     = r'C:\Users\elija\Desktop\cv.tex'
RAW_HTML     = "cv_raw.html"
OUTPUT_HTML  = "cv_body.html"
FINAL_HTML   = "cv.html"

PDF_DOWNLOAD = "/assets/CV_Elijah.pdf"
PHOTO_PATH   = "/assets/photo.jpg"
CSS_PATH     = "/assets/style.css"
FAVICON_PATH = "/assets/web icon.ico"


# ----------------------------
# Helpers
# ----------------------------
def clean_text(text: str) -> str:
    return " ".join(text.split()) if text else ""


def is_effectively_empty(node) -> bool:
    if node is None:
        return True
    if isinstance(node, NavigableString):
        return not node.strip()
    if isinstance(node, Tag):
        return not node.get_text(" ", strip=True) and node.name not in {"hr", "img", "a", "ul", "ol", "table"}
    return False


def remove_rule_artifacts_from_section_html(html: str) -> str:
    """
    Pandoc may convert \\rule{\\linewidth}{0.5pt} into <hr>, or sometimes
    weird paragraph artifacts. Since the Jinja template already inserts <hr>,
    remove leading horizontal-rule artifacts from section bodies.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove leading empty nodes / hr tags / paragraphs that are just lines
    changed = True
    while changed and soup.contents:
        changed = False
        first = soup.contents[0]

        if isinstance(first, NavigableString) and not first.strip():
            first.extract()
            changed = True
            continue

        if isinstance(first, Tag):
            text = clean_text(first.get_text(" ", strip=True))

            if first.name == "hr":
                first.extract()
                changed = True
                continue

            # remove paragraphs/divs that are basically just separator lines
            if first.name in {"p", "div"} and re.fullmatch(r"[-‐-‒–—_\. ]{3,}", text or ""):
                first.extract()
                changed = True
                continue

            # remove empty paragraphs/divs
            if first.name in {"p", "div"} and not text:
                first.extract()
                changed = True
                continue

    return str(soup).strip()


def extract_header_info(soup: BeautifulSoup):
    """
    Try to recover the centered CV header robustly.
    Works whether Pandoc emits a div.center, a center tag, or plain early paragraphs.
    """
    name = "Your Name"
    lines = []

    # Prefer a centered block if Pandoc created one
    header_block = soup.find("div", class_="center") or soup.find("center")

    if header_block:
        text_chunks = []
        for elem in header_block.find_all(["p", "tr"]):
            text = clean_text(elem.get_text(" ", strip=True))
            if text:
                text_chunks.append(text)

        # Name
        strong = header_block.find(["strong", "b"])
        if strong:
            name = clean_text(strong.get_text(" ", strip=True))

        # Table rows / paragraphs
        lines.extend(text_chunks)

    else:
        # Fallback: look at content before the first heading
        body = soup.body or soup
        first_heading = body.find(re.compile(r"^h[1-6]$"))

        header_nodes = []
        for child in body.children:
            if child == first_heading:
                break
            if isinstance(child, Tag):
                text = clean_text(child.get_text(" ", strip=True))
                if text:
                    header_nodes.append(text)

        if header_nodes:
            # first non-empty line is often the name
            name = header_nodes[0]
            lines = header_nodes[1:]

    # Deduplicate lines and remove ones that just repeat the name
    cleaned_lines = []
    for line in lines:
        if line and line != name and line not in cleaned_lines:
            cleaned_lines.append(line)

    line1 = cleaned_lines[0] if len(cleaned_lines) > 0 else ""
    line2 = cleaned_lines[1] if len(cleaned_lines) > 1 else ""
    line3 = cleaned_lines[2] if len(cleaned_lines) > 2 else ""

    return name, line1, line2, line3


def extract_sections_from_headings(soup: BeautifulSoup):
    """
    Extract sections based on Pandoc-generated heading tags from \\section*{...}.
    This replaces the old logic that expected:
        <p><strong><span>Section</span></strong></p>
    """
    body = soup.body or soup
    headings = body.find_all(re.compile(r"^h[1-6]$"))

    sections = OrderedDict()

    for heading in headings:
        section_name = clean_text(heading.get_text(" ", strip=True))
        if not section_name:
            continue

        content_parts = []
        for sib in heading.next_siblings:
            if isinstance(sib, Tag) and re.fullmatch(r"h[1-6]", sib.name or ""):
                break
            if is_effectively_empty(sib):
                continue
            content_parts.append(str(sib))

        section_html = "".join(content_parts).strip()
        section_html = remove_rule_artifacts_from_section_html(section_html)

        # skip fake or empty sections
        if section_html:
            sections[section_name] = section_html

    return sections


# ----------------------------
# 2) Convert TeX → raw HTML via Pandoc
# ----------------------------
pypandoc.convert_file(
    TEX_FILE,
    "html",
    outputfile=RAW_HTML,
    extra_args=["--mathjax"]
)

# ----------------------------
# 3) Parse raw HTML
# ----------------------------
with open(RAW_HTML, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# ----------------------------
# 4) Extract header info
# ----------------------------
name, line1, line2, line3 = extract_header_info(soup)

# ----------------------------
# 5) Extract sections from real heading tags
# ----------------------------
sections = extract_sections_from_headings(soup)

# Optional debug
print("Detected sections:", list(sections.keys()))

header = """\
---
layout: none
---

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Home – Hongbin Huang</title>

  <!-- add website icon -->
  <link rel="icon" href="assets/web icon.ico">

  <!-- Google Fonts -->
  <link
    href="https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Montserrat:wght@400;600&display=swap"
    rel="stylesheet"
  >

  <!-- Site stylesheet -->
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>

<!-- Pull in nav + sidebar from one file -->
{% include config.html %}
"""

with open("header.txt", "w", encoding="utf-8") as f:
    f.write(header)
print("Created header.txt")

# ----------------------------
# 6) Jinja2 template
# ----------------------------
template_str = """
<!-- Main content area -->
<main class="content">
  <section>
    <p>
      <a href="{{ pdf }}" download="Hongbin_Huang_CV.pdf">
        📄Click here to download my CV (PDF)
      </a>
    </p>
  </section>

  <!-- DYNAMIC SECTIONS -->
  {% for section, html in sections.items() %}
  <section>
    <h2>{{ section }}</h2>
    <hr>
    {{ html | safe }}
  </section>
  {% endfor %}
</main>
</body>
</html>
"""

# ----------------------------
# 7) Render & write cv_body.html
# ----------------------------
template = Template(template_str)
rendered = template.render(
    name=name,
    line1=line1,
    line2=line2,
    line3=line3,
    sections=sections,
    pdf=PDF_DOWNLOAD,
    photo=PHOTO_PATH,
    css=CSS_PATH,
    favicon=FAVICON_PATH
)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(rendered)

# ----------------------------
# 8) Combine header + body
# ----------------------------
with open("header.txt", "r", encoding="utf-8") as header_file, \
     open(OUTPUT_HTML, "r", encoding="utf-8") as cv_file, \
     open(FINAL_HTML, "w", encoding="utf-8") as output_file:
    output_file.write(header_file.read())
    output_file.write("\n")
    output_file.write(cv_file.read())

print(f"✅ {FINAL_HTML} has been created.")

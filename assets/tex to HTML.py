#!/usr/bin/env python3
# tex_to_cv.py

import pypandoc
from bs4 import BeautifulSoup
from jinja2 import Template

# 1) File paths
TEX_FILE     = "cv.tex"
RAW_HTML     = "cv_raw.html"
OUTPUT_HTML  = "cv_body.html"
PDF_DOWNLOAD = "/assets/CV_Elijah.pdf"
PHOTO_PATH   = "/assets/photo.jpg"
CSS_PATH     = "/assets/style.css"
FAVICON_PATH = "/assets/web icon.ico"

# 2) Convert TeX → raw HTML via Pandoc
pypandoc.convert_file(
    TEX_FILE,
    'html',
    outputfile=RAW_HTML,
    extra_args=['--mathjax']
)

# 3) Parse the raw HTML
with open(RAW_HTML, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# 4) Extract header info (name + table rows)
header_div = soup.find("div", class_="center") or soup.body
name_tag   = header_div.find("strong")
name       = name_tag.get_text(strip=True) if name_tag else "Your Name"

rows  = header_div.find_all("tr")
lines = [
    " ".join(td.get_text(" ", strip=True).split())
    for tr in rows
    for td in tr.find_all("td")
]
line1 = lines[0] if len(lines) > 0 else ""
line2 = lines[1] if len(lines) > 1 else ""
line3 = lines[2] if len(lines) > 2 else ""

# 5) Extract each Section by <p><strong><span>SectionName</span></strong></p>
sections = {}
for p in soup.find_all("p"):
    span = p.find("span")
    if span:
        section_name = span.get_text(strip=True)
        content_html = []
        for sib in p.next_siblings:
            if getattr(sib, "name", None) == "p" and sib.find("span"):
                break
            content_html.append(str(sib))
        sections[section_name] = "\n".join(content_html).strip()

header= '''\
---
layout: none
---

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Home – Hongbin (Elijah) Huang</title>

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
'''

with open('header.txt', "w", encoding="utf-8") as f:
    f.write(header)
print("Created header.txt")

# 6) Jinja2 template with inline nav + sidebar
template_str = """
 <!-- Main content area -->
    <main class="content">
<section>

          <p>
            <a href="/assets/CV_Elijah.pdf" download="Hongbin_Huang_CV.pdf">
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
  </div>

</body>
</html>
"""

# 7) Render & write the final cv.html
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


with open("header.txt", "r", encoding="utf-8") as header_file, \
     open("cv_body.html", "r", encoding="utf-8") as cv_file, \
     open("cv.html", "w", encoding="utf-8") as output_file:
    # Write header first
    output_file.write(header_file.read())
    output_file.write("\n")
    # Then write the original cv.html content
    output_file.write(cv_file.read())

print("✅ combined_cv.html has been created.")




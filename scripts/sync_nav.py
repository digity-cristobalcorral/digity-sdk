"""
Reads docs/SUMMARY.md (GitBook format) and rewrites the nav section
in mkdocs.yml so both stay in sync automatically.
"""
import re

with open("docs/SUMMARY.md") as f:
    lines = f.read().splitlines()

nav = []
current_section = None
current_items = []

SKIP_FILES = {"README.md", "index.md"}

for line in lines:
    m = re.match(r"^## (.+)", line)
    if m:
        if current_section is not None and current_items:
            nav.append((current_section, current_items))
        current_section = m.group(1).strip()
        current_items = []
        continue

    m = re.match(r"^\*\s+\[(.+?)\]\((.+?)\)", line)
    if m:
        title, path = m.group(1), m.group(2)
        if path not in SKIP_FILES:
            current_items.append((title, path))

if current_section is not None and current_items:
    nav.append((current_section, current_items))

nav_lines = ["nav:"]
for section, items in nav:
    nav_lines.append(f"  - {section}:")
    for title, path in items:
        nav_lines.append(f"    - {title}: {path}")

nav_yaml = "\n".join(nav_lines) + "\n"

with open("mkdocs.yml") as f:
    content = f.read()

# Replace the nav: block (everything from 'nav:' up to the next top-level key)
new_content = re.sub(
    r"^nav:.*?(?=^\S|\Z)",
    nav_yaml + "\n",
    content,
    flags=re.MULTILINE | re.DOTALL,
)

with open("mkdocs.yml", "w") as f:
    f.write(new_content)

print("Nav synced from SUMMARY.md:")
print(nav_yaml)

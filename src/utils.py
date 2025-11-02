import re
from bs4 import BeautifulSoup
from pathlib import Path
import json

def html_to_text(html):
    if not html:
        return ""
    # Jira sometimes stores as plain text or HTML-ish markup
    if not isinstance(html, str):
        return str(html)
    soup = BeautifulSoup(html, "lxml")
    # preserve pre/code blocks
    for pre in soup.find_all("pre"):
        pre.string = "\n" + pre.get_text() + "\n"
    text = soup.get_text("\n")
    # collapse multiple blank lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)

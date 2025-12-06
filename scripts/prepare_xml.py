#!/usr/bin/env python3
"""
prepare_xml.py

- Extract raw tarballs from raw/tarballs/ into raw/xml_original/
- Pretty-print Lovdata HTML/XML into data/xml_pretty/
- Generate simple HTML + Markdown in data/html/ and data/markdown/

Now includes:
    ✔ Rich progress bar
    ✔ Graceful Ctrl-C handling
    ✔ Minimal console output
"""

import tarfile
from pathlib import Path
from textwrap import fill

import chardet
from lxml import etree, html
from rich.progress import Progress, TimeElapsedColumn, TimeRemainingColumn, BarColumn, TextColumn

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "raw"
TARBALL_DIR = RAW_DIR / "tarballs"
XML_ORIG_DIR = RAW_DIR / "xml_original"

DATA_DIR = BASE_DIR / "data"
XML_PRETTY_DIR = DATA_DIR / "xml_pretty"
HTML_DIR = DATA_DIR / "html"
MD_DIR = DATA_DIR / "markdown"

WRAP_WIDTH = 100


def detect_encoding(raw: bytes) -> str:
    guess = chardet.detect(raw)
    enc = guess.get("encoding") or "utf-8"
    if enc.lower() in ("latin-1", "iso-8859-1"):
        return "iso-8859-1"
    return enc


def wrap_text_nodes(element, width=WRAP_WIDTH):
    """Wrap long text nodes."""
    if element.text and element.text.strip():
        element.text = fill(" ".join(element.text.split()), width=width)

    if element.tail and element.tail.strip():
        element.tail = fill(" ".join(element.tail.split()), width=width)

    for child in element:
        wrap_text_nodes(child, width=width)


def extract_tarballs():
    """Extract the public Lovdata tarballs into raw/xml_original."""
    XML_ORIG_DIR.mkdir(parents=True, exist_ok=True)

    for tar_path in TARBALL_DIR.glob("*.tar.bz2"):
        print(f"Extracting: {tar_path.name}")

        with tarfile.open(tar_path, "r:bz2") as tf:
            subdir = XML_ORIG_DIR / tar_path.stem
            subdir.mkdir(parents=True, exist_ok=True)
            tf.extractall(subdir)


def pretty_and_derive():
    """Pretty-print XML and generate HTML/Markdown with a progress bar."""

    XML_PRETTY_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    MD_DIR.mkdir(parents=True, exist_ok=True)

    files = list(XML_ORIG_DIR.rglob("*.xml"))
    total = len(files)

    if total == 0:
        print("No XML files found in raw/xml_original. Did you run download_raw.py first?")
        return

    print(f"Processing {total} XML files…")

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )

    try:
        with progress:
            task = progress.add_task("Processing files", total=total)

            for xml_file in files:
                rel = xml_file.relative_to(XML_ORIG_DIR)

                pretty_path = XML_PRETTY_DIR / rel
                html_path = HTML_DIR / rel.with_suffix(".html")
                md_path = MD_DIR / rel.with_suffix(".md")

                pretty_path.parent.mkdir(parents=True, exist_ok=True)
                html_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.parent.mkdir(parents=True, exist_ok=True)

                raw = xml_file.read_bytes()
                enc = detect_encoding(raw)

                # Parse with fallback
                try:
                    doc = html.fromstring(raw.decode(enc, errors="replace"))
                    is_html = True
                except Exception:
                    parser = etree.XMLParser(recover=True)
                    doc = etree.fromstring(raw, parser=parser)
                    is_html = False

                # Wrap text nodes to prevent very long lines
                wrap_text_nodes(doc, width=WRAP_WIDTH)

                # Pretty-print XML/HTML
                if is_html:
                    pretty_bytes = etree.tostring(
                        doc, pretty_print=True, encoding="utf-8", method="html"
                    )
                else:
                    pretty_bytes = etree.tostring(
                        doc,
                        pretty_print=True,
                        encoding="utf-8",
                        xml_declaration=True,
                    )

                pretty_path.write_bytes(pretty_bytes)

                # Generate simple HTML + Markdown
                title_nodes = doc.xpath("//dd[@class='titleShort'] | //dd[@class='title'] | //h1")
                title = title_nodes[0].text_content().strip() if title_nodes else rel.stem

                body_nodes = doc.xpath("//main")
                body_text = (
                    body_nodes[0].text_content().strip()
                    if body_nodes
                    else doc.text_content().strip()
                )

                paragraphs = [
                    fill(" ".join(p.split()), width=WRAP_WIDTH)
                    for p in body_text.split("\n")
                    if p.strip()
                ]

                # HTML output
                html_out = [
                    "<!DOCTYPE html>",
                    '<html lang="no">',
                    "<head>",
                    '<meta charset="utf-8">',
                    f"<title>{title}</title>",
                    "<style>body{font-family:sans-serif;max-width:700px;margin:2rem auto;}p{margin-bottom:1rem;}</style>",
                    "</head>",
                    "<body>",
                    f"<h1>{title}</h1>",
                ]
                html_out.extend(f"<p>{p}</p>" for p in paragraphs)
                html_out.append("</body></html>")

                html_path.write_text("\n".join(html_out), encoding="utf-8")

                # Markdown output
                md_out = [f"# {title}", ""]
                md_out.extend(f"{p}\n" for p in paragraphs)

                md_path.write_text("\n".join(md_out), encoding="utf-8")

                progress.update(task, advance=1)

    except KeyboardInterrupt:
        progress.stop()
        print("\n\n❌ Interrupted by user (Ctrl-C).")
        print("Partial output has been saved safely.")
        return


def main():
    try:
        extract_tarballs()
        pretty_and_derive()
        print("Done prepare_xml.")
    except KeyboardInterrupt:
        print("\nStopped by user. Goodbye.")


if __name__ == "__main__":
    main()
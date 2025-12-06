#!/usr/bin/env python3
"""
build_dataset.py

Create clean JSON representations of Lovdata documents.

Modes:
    --mode examples   (default)  Only Offentleglova + Rakfisk-forskriften
    --mode all                    Process all documents

Processing:
    - Extract metadata
    - Normalize whitespace (Option B)
    - Remove Lovdata-specific markup
    - Build section list
    - Write cleaned JSON
    - Write featured examples

Now includes:
    ✔ Rich progress bar
    ✔ Graceful Ctrl-C handling
"""

import argparse
import json
from pathlib import Path

from lxml import html
from rich.progress import (
    Progress,
    TimeElapsedColumn,
    TimeRemainingColumn,
    BarColumn,
    TextColumn
)

BASE_DIR = Path(__file__).resolve().parents[1]

XML_PRETTY_DIR = BASE_DIR / "data" / "xml_pretty"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
EXAMPLES_DIR = BASE_DIR / "data" / "examples"

# Featured examples
FEATURED_LAW_REFID = "lov/2006-05-19-16"          # Offentleglova
FEATURED_REG_REFID = "forskrift/2006-10-27-1196"  # Rakfisk-forskriften


def clean_text(s: str) -> str:
    """Normalize whitespace without altering meaning."""
    if not s:
        return ""
    return " ".join(s.split())


def parse_document(path: Path) -> dict | None:
    """Parse a single pretty XML/HTML document."""
    raw = path.read_bytes()

    try:
        doc = html.fromstring(raw)
    except Exception:
        return None

    def first(xpath):
        nodes = doc.xpath(xpath)
        return nodes[0].text_content().strip() if nodes else None

    ref_id = first("//dd[@class='refid']")
    dok_id = first("//dd[@class='dokid']")
    title_short = first("//dd[@class='titleShort']")
    title = first("//dd[@class='title']") or title_short or first("//h1")
    date = first("//dd[@class='dateInForce']") or first("//dd[@class='legacyID']")

    ministries = [
        clean_text(li.text_content())
        for li in doc.xpath("//dd[@class='ministry']//li")
    ] or []

    # Fallback for ref_id
    if not ref_id:
        ref_id = dok_id or path.stem

    # Determine category + normalized ID
    if ref_id.startswith("lov/"):
        category = "laws"
        norm_id = f"lov-{ref_id.split('lov/', 1)[1]}"
    elif ref_id.startswith("forskrift/"):
        category = "regulations"
        norm_id = f"forskrift-{ref_id.split('forskrift/', 1)[1]}"
    else:
        return None

    # Official link guess
    if dok_id and dok_id.startswith("NL/"):
        official_link = f"https://lovdata.no/dokument/NL/{ref_id}"
    elif dok_id and dok_id.startswith("SF/"):
        official_link = f"https://lovdata.no/dokument/SF/{ref_id}"
    else:
        official_link = f"https://lovdata.no/dokument/{ref_id}"

    # Extract sections
    sections = []
    articles = doc.xpath("//article[contains(@class, 'legalArticle')]")

    for art in articles:
        nr_node = art.xpath(".//h2//span[contains(@class,'legalArticleValue')]")
        nr = nr_node[0].text_content().strip() if nr_node else None

        title_node = art.xpath(".//h2//span[contains(@class,'legalArticleTitle')]")
        sec_title = title_node[0].text_content().strip() if title_node else None

        ledd = [
            clean_text(p.text_content())
            for p in art.xpath(".//article[contains(@class,'legalP')]")
        ]

        if not ledd:
            full = clean_text(art.text_content())
            if nr:
                full = full.replace(nr, "").strip()
            if sec_title:
                full = full.replace(sec_title, "").strip()
            ledd = [full]

        sections.append({
            "number": nr,
            "label": f"§ {nr}" if nr else None,
            "title": sec_title,
            "text": " ".join(ledd),
        })

    return {
        "category": category,
        "id": norm_id,
        "refId": ref_id,
        "dokId": dok_id,
        "title": title,
        "shortTitle": title_short,
        "date": date,
        "ministry": ministries,
        "links": {"official": official_link},
        "sections": sections,
    }


def save_document(doc: dict):
    """Write cleaned dataset + featured examples."""
    category = doc["category"]
    norm_id = doc["id"]
    ref_id = doc["refId"]

    out_dir = CLEANED_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{norm_id}.json"
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    # Featured examples
    if ref_id == FEATURED_LAW_REFID:
        ex = EXAMPLES_DIR / "law-offentleglova"
        ex.mkdir(parents=True, exist_ok=True)
        (ex / "offentleglova.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    if ref_id == FEATURED_REG_REFID:
        ex = EXAMPLES_DIR / "forskrift-rakfisk"
        ex.mkdir(parents=True, exist_ok=True)
        (ex / "rakfiskforskriften.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["examples", "all"],
        default="examples",
        help="Process only featured examples or the entire corpus"
    )
    args = parser.parse_args()

    XML_PRETTY_DIR.mkdir(parents=True, exist_ok=True)

    files = list(XML_PRETTY_DIR.rglob("*.xml"))
    if not files:
        print("No prettified XML found. Run prepare_xml.py first.")
        return

    if args.mode == "examples":
        target_refids = {FEATURED_LAW_REFID, FEATURED_REG_REFID}
        files = [
            f for f in files
            if any(rid in f.read_text(errors="ignore") for rid in target_refids)
        ]

    print(f"Processing {len(files)} cleaned XML files…")

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
            task = progress.add_task("Building dataset", total=len(files))

            for f in files:
                doc = parse_document(f)
                if doc:
                    save_document(doc)

                progress.update(task, advance=1)

    except KeyboardInterrupt:
        progress.stop()
        print("\n❌ Interrupted. Partial output was saved.")
        return

    print("Done build_dataset.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
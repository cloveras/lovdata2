#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lxml import etree
from mcp.server.fastmcp import FastMCP

# =============================================================================
# CONFIGURATION
# =============================================================================

def resolve_data_root() -> Path:
    """
    Resolve the data root directory.

    Priority:
    1. Environment variable LOVDATA2_DATA_ROOT
    2. ../data relative to this server.py
    """
    env = os.environ.get("LOVDATA2_DATA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return (Path(__file__).resolve().parents[1] / "data").resolve()


DATA_ROOT = resolve_data_root()
XML_ROOT = DATA_ROOT / "xml_pretty"
HTML_ROOT = DATA_ROOT / "html"
MD_ROOT = DATA_ROOT / "markdown"
JSON_ROOT = DATA_ROOT / "json"

print(f"[lovdata2-mcp] DATA_ROOT = {DATA_ROOT}", file=sys.stderr)
print(f"[lovdata2-mcp] XML_ROOT  = {XML_ROOT}", file=sys.stderr)

# Under xml_pretty we typically have xml_pretty/xml/{nl,sf}/...
XML_DIR = XML_ROOT / "xml" if (XML_ROOT / "xml").exists() else XML_ROOT

if not XML_DIR.exists():
    print(f"[lovdata2-mcp] WARNING: XML_DIR does not exist: {XML_DIR}", file=sys.stderr)

# =============================================================================
# DOCUMENT LOADING & PARSING
# =============================================================================

HtmlParser = etree.HTMLParser(encoding="utf-8", recover=True)


def tokenize(text: str) -> List[str]:
    """Very simple tokenizer for scoring."""
    return re.findall(r"\w+", text.lower())


def classify_doc_id(doc_id: str) -> str:
    """Classify by filename prefix."""
    if doc_id.startswith("nl-"):
        return "law"
    if doc_id.startswith("sf-"):
        return "regulation"
    return "other"


def compute_related_paths(xml_path: Path) -> Dict[str, Optional[str]]:
    """
    Given an XML path like:
        data/xml_pretty/xml/sf/sf-20061027-1196.xml

    Derive possible HTML, Markdown and JSON paths:
        data/html/xml/sf/sf-20061027-1196.html
        data/markdown/xml/sf/sf-20061027-1196.md
        data/json/xml/sf/sf-20061027-1196.json
    """
    try:
        rel = xml_path.relative_to(XML_DIR).with_suffix("")  # e.g. sf/sf-20061027-1196
    except ValueError:
        rel = xml_path.name.rsplit(".", 1)[0]

    html_path = HTML_ROOT / "xml" / rel.with_suffix(".html")
    md_path = MD_ROOT / "xml" / rel.with_suffix(".md")
    json_path = JSON_ROOT / "xml" / rel.with_suffix(".json")

    def _opt(p: Path) -> Optional[str]:
        return str(p) if p.exists() else None

    return {
        "xml": str(xml_path),
        "html": _opt(html_path),
        "markdown": _opt(md_path),
        "json": _opt(json_path),
    }


def parse_document(xml_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a single Lovdata 'XML' document (really HTML-ish) into a structured dict.

    We:
    - Use lxml's HTML parser with recover=True (tolerant)
    - Extract title
    - Extract header metadata (dt/dd pairs)
    - Extract legal sections with headings and paragraphs
    - Build a canonical text body used for search
    """
    try:
        tree = etree.parse(str(xml_path), HtmlParser)
        root = tree.getroot()
    except Exception as e:
        print(
            f"[lovdata2-mcp] Failed to parse {xml_path}: {e}",
            file=sys.stderr,
        )
        return None

    # Title
    title_el = root.find(".//title")
    title = title_el.text.strip() if title_el is not None and title_el.text else "Untitled"

    # Metadata from <header class="documentHeader"> <dl>...
    metadata: Dict[str, Any] = {}
    for dt in root.findall(".//header//dt"):
        if dt.text is None:
            continue
        key = dt.text.strip()
        if not key:
            continue
        # Normalize key: "Korttittel" -> "korttittel"
        norm_key = re.sub(r"\s+", "_", key.strip().lower())
        dd = dt.getnext()
        if dd is not None:
            value = " ".join(dd.itertext()).strip()
            metadata[norm_key] = value

    # Sections
    sections: List[Dict[str, Any]] = []
    for art in root.findall(".//article[@class='legalArticle']"):
        heading_el = art.find(".//h2")
        heading = (
            " ".join(heading_el.itertext()).strip()
            if heading_el is not None
            else None
        )

        paragraphs: List[str] = [
            " ".join(p.itertext()).strip()
            for p in art.findall(".//article[@class='legalP']")
        ]
        sections.append(
            {
                "heading": heading,
                "paragraphs": [p for p in paragraphs if p],
            }
        )

    # Canonical text body for search – prefer legal paragraphs, then full text
    if sections:
        body_parts: List[str] = []
        for sec in sections:
            if sec.get("heading"):
                body_parts.append(str(sec["heading"]))
            body_parts.extend(sec.get("paragraphs") or [])
        raw_text = "\n".join(body_parts)
    else:
        raw_text = "\n".join(root.itertext())

    raw_text = raw_text.strip()
    raw_text_lower = raw_text.lower()

    doc_id = xml_path.stem  # e.g. "sf-20061027-1196"
    kind = classify_doc_id(doc_id)
    paths = compute_related_paths(xml_path)

    return {
        "id": doc_id,
        "kind": kind,
        "title": title,
        "metadata": metadata,
        "sections": sections,
        "raw_text": raw_text,
        "raw_text_lower": raw_text_lower,
        "paths": paths,
    }


def load_corpus() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    """Load and index all documents under XML_DIR."""
    corpus: Dict[str, Dict[str, Any]] = {}
    search_index: Dict[str, str] = {}

    if not XML_DIR.exists():
        print(
            f"[lovdata2-mcp] WARNING: XML_DIR does not exist, corpus will be empty: {XML_DIR}",
            file=sys.stderr,
        )
        return corpus, search_index

    xml_files = list(XML_DIR.rglob("*.xml"))
    print(
        f"[lovdata2-mcp] Scanning {len(xml_files)} XML files under {XML_DIR}",
        file=sys.stderr,
    )

    parsed_count = 0
    for xml_path in xml_files:
        doc = parse_document(xml_path)
        if not doc:
            continue

        doc_id = doc["id"]
        corpus[doc_id] = doc
        search_index[doc_id] = doc["raw_text_lower"]
        parsed_count += 1

    print(
        f"[lovdata2-mcp] Loaded {parsed_count} documents into corpus "
        f"(failed: {len(xml_files) - parsed_count})",
        file=sys.stderr,
    )

    return corpus, search_index


CORPUS, SEARCH_INDEX = load_corpus()

# =============================================================================
# SEARCH
# =============================================================================

def score_document(text_lower: str, query_terms: List[str]) -> int:
    """
    Very simple scoring: sum of term frequencies for all query terms.
    """
    score = 0
    for term in query_terms:
        if not term:
            continue
        score += text_lower.count(term)
    return score


def extract_snippet(text_lower: str, original_text: str, query_term: str, radius: int = 120) -> str:
    """
    Extract a small snippet around the first match of `query_term` in `text_lower`.
    Falls back to the beginning if term is not found.
    """
    idx = text_lower.find(query_term)
    if idx == -1:
        return original_text[: radius * 2] + ("..." if len(original_text) > radius * 2 else "")

    start = max(0, idx - radius)
    end = min(len(original_text), idx + radius)
    snippet = original_text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(original_text):
        snippet = snippet + "..."
    return snippet


def search_documents(
    query: str,
    kind: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search in CORPUS using a very simple term-frequency scoring.
    """
    q = query.strip()
    if not q:
        return []

    terms = tokenize(q)
    if not terms:
        return []

    results: List[Tuple[int, Dict[str, Any]]] = []
    for doc_id, doc in CORPUS.items():
        if kind and doc["kind"] != kind:
            continue

        text_lower = SEARCH_INDEX.get(doc_id, "")
        if not text_lower:
            continue

        score = score_document(text_lower, terms)
        if score <= 0:
            continue

        # Use the first term for snippet extraction
        snippet = extract_snippet(
            text_lower=text_lower,
            original_text=doc["raw_text"],
            query_term=terms[0],
        )

        results.append(
            (
                score,
                {
                    "id": doc_id,
                    "kind": doc["kind"],
                    "title": doc["title"],
                    "score": score,
                    "snippet": snippet,
                },
            )
        )

    # Sort by score desc, then title
    results.sort(key=lambda tup: (-tup[0], tup[1]["title"]))
    return [r for _, r in results[: max(1, min(limit, 100))]]


# =============================================================================
# MCP SETUP
# =============================================================================

mcp = FastMCP("lovdata2-mcp")


@mcp.tool()
def search_lovdata(
    query: str,
    kind: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Search across the local Lovdata corpus.

    Args:
        query: Free-text query (Norwegian or English).
        kind:  Optional filter: "law", "regulation", or "other".
        limit: Maximum number of results (1–100).

    Returns:
        A dict containing the query, kind, and a list of result objects.
    """
    if not CORPUS:
        return {
            "error": "corpus_empty",
            "message": "No documents loaded from xml_pretty.",
        }

    if kind and kind not in {"law", "regulation", "other"}:
        return {
            "error": "invalid_kind",
            "message": "kind must be one of: law, regulation, other.",
        }

    limit = max(1, min(limit, 100))
    results = search_documents(query=query, kind=kind, limit=limit)
    return {
        "query": query,
        "kind": kind or "all",
        "limit": limit,
        "count": len(results),
        "results": results,
    }


@mcp.tool()
def list_documents(
    kind: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List documents in the corpus with light metadata.

    Args:
        kind:   Optional filter: "law", "regulation", or "other".
        limit:  Max items to return (1–200).
        offset: Start offset for paging (0-based).
    """
    if not CORPUS:
        return {
            "error": "corpus_empty",
            "message": "No documents loaded from xml_pretty.",
        }

    if kind and kind not in {"law", "regulation", "other"}:
        return {
            "error": "invalid_kind",
            "message": "kind must be one of: law, regulation, other.",
        }

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    docs = [
        {
            "id": doc_id,
            "kind": doc["kind"],
            "title": doc["title"],
            "korttittel": doc["metadata"].get("korttittel"),
            "datokode": doc["metadata"].get("datokode"),
        }
        for doc_id, doc in CORPUS.items()
        if not kind or doc["kind"] == kind
    ]

    total = len(docs)
    sliced = docs[offset : offset + limit]

    return {
        "kind": kind or "all",
        "offset": offset,
        "limit": limit,
        "total": total,
        "items": sliced,
    }


@mcp.tool()
def get_document(doc_id: str) -> Dict[str, Any]:
    """
    Return a full parsed document (metadata, sections, raw_text, paths).
    """
    doc = CORPUS.get(doc_id)
    if not doc:
        return {
            "error": "not_found",
            "message": f"Document '{doc_id}' not found in corpus.",
        }

    # Copy but drop the lowercase index field, which is internal
    doc_public = {k: v for k, v in doc.items() if k != "raw_text_lower"}
    return doc_public


@mcp.tool()
def get_section(doc_id: str, heading_query: str) -> Dict[str, Any]:
    """
    Return a specific section from a document, by heading match.

    Example heading_query:
      - "§ 1"
      - "§ 3. Vilkår for bruk av produktbetegnelsen"
    """
    doc = CORPUS.get(doc_id)
    if not doc:
        return {
            "error": "not_found",
            "message": f"Document '{doc_id}' not found in corpus.",
        }

    q = heading_query.strip().lower()
    if not q:
        return {
            "error": "invalid_heading_query",
            "message": "heading_query must be a non-empty string.",
        }

    for sec in doc.get("sections", []):
        heading = sec.get("heading") or ""
        heading_norm = heading.lower()
        if q == heading_norm or q in heading_norm:
            return {
                "document_id": doc_id,
                "heading_query": heading_query,
                "section": sec,
            }

    return {
        "error": "section_not_found",
        "message": f"No section whose heading matches '{heading_query}' was found in '{doc_id}'.",
    }


@mcp.tool()
def get_raw_view(doc_id: str, fmt: str = "xml") -> Dict[str, Any]:
    """
    Return the raw underlying representation for a document.

    Args:
        doc_id: Document id (e.g. 'sf-20061027-1196').
        fmt:    One of 'xml', 'html', 'markdown', 'json'.

    NOTE: This is for local / personal use. Respect Lovdata's terms if you
    modify or redistribute anything built from their datasets.
    """
    doc = CORPUS.get(doc_id)
    if not doc:
        return {
            "error": "not_found",
            "message": f"Document '{doc_id}' not found in corpus.",
        }

    fmt = fmt.lower()
    if fmt not in {"xml", "html", "markdown", "json"}:
        return {
            "error": "invalid_format",
            "message": "fmt must be one of: xml, html, markdown, json.",
        }

    path_str = (doc.get("paths") or {}).get(fmt)
    if not path_str:
        return {
            "error": "format_not_available",
            "message": f"Format '{fmt}' not available for '{doc_id}'.",
        }

    path = Path(path_str)
    if not path.exists():
        return {
            "error": "file_missing",
            "message": f"File not found on disk: {path}",
        }

    if fmt == "json":
        import json

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "doc_id": doc_id,
            "format": fmt,
            "path": str(path),
            "content": data,
        }

    # All other formats: treat as text
    with path.open("r", encoding="utf-8") as f:
        text = f.read()

    return {
        "doc_id": doc_id,
        "format": fmt,
        "path": str(path),
        "content": text,
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Runs an MCP stdio server; Claude/Cursor will spawn this as a subprocess.
    mcp.run()
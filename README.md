# lovdata2

This tiny hobby project contains:

* A rapid [API spec prototype](#api)
 showing how the
 [Lovdata API](https://api.lovdata.no/swagger)
  might look if redesigned according to modern REST best practices.
* A [MCP server example]() of how to search the local content with
 [Claude desktop](https://www.claude.com/download).

The repository also includes [scrips](#scripts) for downloading and processing Lovdata’s publicly
available datasets. These scripts generate a simplified, machine-readable dataset without
Lovdata’s editorial markup, suitable for research, indexing, or experimentation with
alternative API designs.

## API

The [Lovdata API]((https://api.lovdata.no/swagger).) is, technically speaking, a ‘REST API’,
but it behaves more like a download service than something that actually follows REST principles:
The URIs, methods, and structure feel more like
‘hey, here are some files’ than a clean, resource-oriented interface.”

The goal here is to illustrate how Norwegian laws and regulations could be exposed through a
clean, predictable, developer-friendly REST interface, in
[OpenAPI 3.1](https://github.com/cloveras/lovdata2/blob/main/openapi/lovdata-api.yaml)
and [Swagger UI](https://cloveras.github.io/lovdata2/api.html).

## Scripts

Scripts to retrieve and process the public Lovdata datasets:

* [scripts/download_raw.py](scripts/download_raw.py) — Downloads the official Lovdata tarballs (laws and central regulations) into raw/.
* [scripts/prepare_xml.py](scripts/prepare_xml.py) — Extracts, normalizes, and pretty-prints the raw XML into xml_pretty/ for parsing.
* [scripts/build_dataset.py](scripts/build_dataset.py) — Builds HTML, Markdown, and JSON versions and generates cleaned metadata for local use and tooling.

## MCP Integration

Lovdata2 includes an example of a local MCP (Model Context Protocol) server so you can use
Claude Desktop to interactively query your private Lovdata dataset.

This provides a chat interface where Claude can:

* Search across all Norwegian laws & regulations locally
* Retrieve any law or forskrift by ID
* Extract a specific section (e.g., “§ 1”) from any document
* Get summaries or explanations of laws and sections

See the full MCP setup instructions: [README-mcp.md](README-mcp.md)

Here is one example of using Claude with the local MCP and dataset:

![MCP example in Claude desktop](mcp-lovdata/mcp-example.png)

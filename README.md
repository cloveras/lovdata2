# lovdata2

This project is a rapid prototype showing how the Lovdata API might look if redesigned
according to modern REST best practices.

And also a barebones example of how to set up a local MCP server to search the local content
with Claude desktop.

## API

It is not the official Lovdata API — see the real version here:
https://api.lovdata.no/swagger

The goal is to illustrate how Norwegian laws and regulations could be exposed through a
clean, predictable, developer-friendly REST interface.

The repository also includes tools for downloading and processing Lovdata’s publicly
available datasets. These scripts generate a simplified, machine-readable dataset without
Lovdata’s editorial markup, suitable for research, indexing, or experimentation with
alternative API designs.

ReDoc version of the OpenAPI specification: https://cloveras.github.io/lovdata2/api.html

### Workflow

Scripots to retrieve the data from Lovdata, prettify XML, etc:

```bash
python3 scripts/download_raw.py
python3 scripts/prepare_xml.py
python3 scripts/build_dataset.py
```

## MCP Integration (Model Context Protocol)

Lovdata2 includes an example of a local MCP server so you can use Claude Desktop to
interactively query your private Lovdata dataset.

This provides a chat interface where Claude can:

- Search in your local legal archive  
- Retrieve full laws or forskrifter  
- Use tool calls to analyze Norwegian legislation  
- Do all processing **fully offline** (no legal data leaves your machine)

To keep this main README small, full MCP setup instructions live here: [README-mcp.md](README-mcp.md)

Here is one example of using Claude with the local MCP and dataset:

![MCP example in Claude desktop](mcp-lovdata/mcp-example.png)

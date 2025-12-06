# Lovdata2 – Local MCP Server

A complete guide to using the **Lovdata2 MCP server** for private, local-only access to Norwegian laws and forskrifter inside **Claude Desktop**.

This MCP server allows Claude to:

- Search your local legal dataset  
- Retrieve laws and regulations  
- Inspect metadata  
- Use tool calls during a conversation  
- Operate fully offline  
- Avoid any license problems (your data never leaves your computer)

This is ideal for legal research, drafting, compliance work, or experimentation with a clean legal corpus.

# 1. What the MCP server does

The server exposes your dataset via the Model Context Protocol using tools:

| Tool | Description |
|------|-------------|
| `search(query)` | Full-text substring search across all local documents |
| `get_document(id)` | Fetch the entire content of one document |
| `list_documents()` | Enumerate document IDs available to the MCP server |
| *(more tools can easily be added)* | |

Every tool uses only your local filesystem.

# 2. Requirements

- macOS (Linux works too; Windows WSL works)
- Python 3.10+  
- Claude Desktop 1.4+ (with MCP support)
- A local Lovdata2 dataset (generated with [`scripts/download_raw.py`](scripts/download_raw.py), [`scripts/prepare_xml.py`](scripts/prepare_xml.py), etc.)

Your dataset should live here or similar:

- lovdata2/data/
- cleaned/
- examples/

# 3. Install the MCP server

```bash
cd lovdata2/mcp-lovdata
python3 -m venv venv
source venv/bin/activate
pip install mcp python-dotenv
```

# Configure Claude desktop (macOS)

Add _something similar to_ this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lovdata2-local": {
      "command": "/Users/cl/Dev/lovdata2/mcp-lovdata/venv/bin/python3",
      "args": [
        "/Users/cl/Dev/lovdata2/mcp-lovdata/server.py"
      ],
      "env": {
        "LOVDATA2_DATA_ROOT": "/Users/cl/Dev/lovdata2/data"
      }
    }
  }
}
```

Claude automatically starts the server.

# Example queries

* Use the lovdata2-local MCP server to search for “offentliglova”.
* Fetch document lov-2006-05-19-16.
* Retrieve the document with ID forskrift-2006-10-27-1196.

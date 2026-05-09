# GradGate MCP server (optional)

stdio [Model Context Protocol](https://modelcontextprotocol.io/) server that proxies the existing GradGate FastAPI and exposes read-only curriculum files as MCP resources. Install only when you need MCP; the rest of the project does not depend on it.

## Install

From the GradGate-v2 repository root, with the Python environment where you develop GradGate activated (Conda, `venv`, or another isolated env):

```bash
pip install -e ".[mcp]"
```

The API must be running separately (for tools that call HTTP), e.g.:

```bash
pip install -e ".[api]"
make serve-api
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GRADGATE_API_URL` | No | Base URL of the FastAPI app. Default: `http://127.0.0.1:8000` |
| `GRADGATE_API_TOKEN` | For authenticated tools | Bearer token (same as web/mobile). For local dev with `TEST_MODE`, you can use `GET /test-token` from the API |

Unauthenticated tools: `gradgate_health`, `gradgate_audit_options`, `gradgate_ocr_status`.

Authenticated tools: `gradgate_audit_csv`, `gradgate_history_list`, `gradgate_history_get`.

## Run (stdio)

```bash
python -m gradgate_mcp
```

or:

```bash
gradgate-mcp
```

## Cursor MCP configuration

Add a server block (adjust paths to your machine):

```json
{
  "mcpServers": {
    "gradgate": {
      "command": "python",
      "args": ["-m", "gradgate_mcp"],
      "cwd": "/absolute/path/to/GradGate-v2",
      "env": {
        "GRADGATE_API_URL": "http://127.0.0.1:8000",
        "GRADGATE_API_TOKEN": "your-bearer-token"
      }
    }
  }
}
```

Point `command` at that environment’s `python` (e.g. Conda: `.../envs/gradgate/bin/python`) and the repo root as `cwd` so imports resolve.

## MCP resources

Read-only files from `data/curriculum/` (no network):

- `gradgate://curriculum/catalog` — full `catalog.json` (large)
- `gradgate://curriculum/official-bucket-models` — `official_bucket_models.json`

Do not commit secrets; set tokens only in your local MCP config or environment.

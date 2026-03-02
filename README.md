# Korean Stock MCP

Python MCP server for Korean stocks with:

- `FinanceDataReader` for listings, stock profile fields, and daily OHLCV
- Naver chart API for `10-minute` intraday candles
- `STDIO` and `HTTP/SSE` transports
- local technical indicator calculation

## Features

- `search_korean_stocks`
- `get_korean_stock_profile`
- `get_korean_stock_daily_history`
- `get_korean_stock_intraday_10m`
- `get_korean_stock_indicators`

## Requirements

- Python 3.11+
- `FinanceDataReader`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run

### STDIO

```bash
korean-stock-mcp
```

### HTTP

```bash
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8000 korean-stock-mcp
```

Health endpoint:

```text
GET /healthz
```

JSON-RPC endpoint:

```text
POST /mcp
```

SSE endpoint:

```text
GET /sse
```

## Tool examples

### Search

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_korean_stocks","arguments":{"query":"삼성전자"}}}
```

### Daily history

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_korean_stock_daily_history","arguments":{"symbol_or_name":"005930","limit_days":30}}}
```

### Intraday 10-minute history

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_korean_stock_intraday_10m","arguments":{"symbol_or_name":"252670","lookback_days":5}}}
```

## Production deployment

The repository includes:

- GitHub Actions CI workflow: `.github/workflows/ci.yml`
- GitHub Actions deployment workflow for self-hosted runner label `macmini`: `.github/workflows/deploy-macmini.yml`
- `launchd` template: `deploy/launchd/com.ctk03272.mcp-korean-stock.plist`

Production runtime expects:

- `MCP_TRANSPORT=http`
- host-local `.env`
- deployment root under `/Users/<runner-user>/services/mcp-korean-stock`
- `launchd` starts the service through `deploy/run_server.sh`, which loads `shared/.env` before executing Python

## Notes

- Intraday `10-minute` data uses an unofficial Naver endpoint and may be delayed or subject to upstream schema changes.
- Profile fields are limited to what `FinanceDataReader` exposes in listing datasets.

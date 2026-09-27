# Dashboard

One page that starts a demo run and shows each step as the server streams it (`POST /api/runs`,
one JSON event per line; see `src/custody_lab/demo/server.py`), with a panel showing which signer
process holds which key share.

```bash
npm --prefix web run build   # then `uv run custody-lab serve` and open http://127.0.0.1:8000
npm --prefix web run dev     # hot reload; proxies /api to `custody-lab serve` on port 8000
```

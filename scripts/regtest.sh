#!/usr/bin/env bash
# Local Bitcoin regtest node for the demo. Data lives in var/regtest (gitignored).
#   scripts/regtest.sh start | stop | cli <bitcoin-cli args>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONF="$ROOT/scripts/bitcoin-regtest.conf"
DATADIR="$ROOT/var/regtest"

cli() { bitcoin-cli -conf="$CONF" -datadir="$DATADIR" "$@"; }

case "${1:-}" in
  start)
    mkdir -p "$DATADIR"
    bitcoind -conf="$CONF" -datadir="$DATADIR" -daemonwait
    ;;
  stop) cli stop ;;
  cli) shift; cli "$@" ;;
  *) echo "usage: $0 start|stop|cli <args>" >&2; exit 2 ;;
esac

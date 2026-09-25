# From FIX fills to a settlement instruction

**Definition.** Trading runs over FIX 5.0 SP2 on the FIXT.1.1 session layer (`8=FIXT.1.1`, Logon
`1137=9`). Fills arrive as ExecutionReports with ExecType F, carrying LastQty/LastPx, TradeDate and
TransactTime and no AvgPx. A settlement cycle's fills are netted into one instruction per asset:
asset, amount and destination (the exchange's settlement address).

**Why custody cares.**
- The execution report is the only thing settlement trusts from the trading side.
- The instruction is the only thing the policy engine sees.
- Keeping FIX out of the settlement and signing layers keeps those layers small enough to audit.

**In the demo.** `src/custody_lab/trading/fix.py` (`trade`, `ToyExchange`, `Session`),
`src/custody_lab/settlement/netting.py` (`net`). Session conventions follow `~/code/fix-client/ROE.md`.

**In the manual.** Chapter 5, "The FIX leg" and "The FIX session".

**Sources.** FIX Trading Community, FIX 5.0 SP2 and FIXT.1.1 specifications.

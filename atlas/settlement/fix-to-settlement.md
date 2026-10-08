# From FIX fills to a settlement instruction

**In one sentence.** Trading runs over a FIX 5.0 SP2 session whose fills arrive as ExecutionReports,
and the settlement layer consumes only those fills, netting each cycle's into one instruction per
asset: asset, amount and destination.

## The problem

Trading systems speak FIX; the policy engine and the signers must stay small enough to audit and
should not parse trading protocols at all. Something has to turn a stream of execution reports into
the one thing the policy engine evaluates.

## The idea

The session runs FIX 5.0 SP2 application messages on the FIXT.1.1 session layer: `8=FIXT.1.1`, and
the Logon carries `1137=9` (DefaultApplVerID = FIX50SP2). The client sends NewOrderSingle (35=D)
messages; the exchange answers each fill with an ExecutionReport (35=8) with ExecType(150)=F and
OrdStatus(39)=2, carrying LastQty(32), LastPx(31), TradeDate(75) and TransactTime(60). There is no
AvgPx(6): an average is a derived number that could disagree with the fills, so the receiver computes
what it needs from LastQty and LastPx.

At the end of a cycle the fills are netted (see [netting](netting.md)) into one settlement
instruction: in the demo, deliver 0.85 BTC to the exchange's settlement address, raised by ops-desk.
Nothing downstream of netting parses FIX.

## Why custody cares

- The execution report is the only thing settlement trusts from the trading side.
- The instruction is the only thing the policy engine sees.
- Keeping FIX out of the settlement and signing layers keeps those layers small enough to audit.

## In the demo

`src/custody_lab/trading/fix.py` (`trade`, `ToyExchange`, `Session`),
`src/custody_lab/settlement/netting.py` (`net`). The session is minimal: no heartbeats, resend
requests or gap fill. It runs in the demo's steps 4 and 5.

## In the manual

[Chapter 5](../../manual/chapters/05-settlement.md),
"[The FIX leg](../../manual/chapters/05-settlement.md#the-fix-leg)" (the tags glossed) and
"[The FIX session](../../manual/chapters/05-settlement.md#the-fix-session)" (the transcript of a
real session, line by line).

## Sources

FIX Trading Community, FIX 5.0 SP2 and FIXT.1.1 specifications.

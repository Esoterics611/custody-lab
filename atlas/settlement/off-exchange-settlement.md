# Off-exchange settlement

**Definition.** The client's assets stay with a custodian while it trades. The exchange sees a
mirrored balance backed by assets the custodian has locked for it. Net obligations settle at the
end of each cycle, and exchanges may post collateral with the custodian as well.

**Why custody cares.**
- Pre-funding an exchange turns the client's assets into a claim in the exchange's insolvency
  (FTX, November 2022).
- Off-exchange settlement limits exposure to one cycle's unsettled net position.
- It is a product custodians sell: Copper's ClearLoop (launched 2022) and comparable networks
  (**verify current**).

**In the demo.** The settlement half: fills are netted per cycle and only the net BTC moves on
chain. The mirrored-balance and collateral mechanics are prose only.

**In the manual.** Chapter 5, "Intuition", "How this shows up in production", Exercise 5.

**Sources.** Copper, *ClearLoop* product documentation (**verify current**).

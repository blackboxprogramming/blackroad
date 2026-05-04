BlackRoad — Atomic Pricing Model

Monthly bill =
  base_tier
  + routed_event_tolls
  + customer_day_tolls
  + memory_provenance_tolls
  + infra_cost_markup
  + volatility_premium
  - verified_road_credits (applied later)

Where:
- base_tier: fixed monthly recurring price for the selected tier.
- routed_event_tolls: aggregated billed at routed_events_1k price. Client should aggregate raw events into 1,000-event buckets (quantity = ceil(events / 1000)).
- customer_day_tolls: charged per customer-day touched (price unit = $0.01 per customer-day). Quantity = total customer-days for the billing period.
- memory_provenance_tolls: aggregated billed at memory_records_1k (per 1,000 records).
- infra_cost_markup: report infrastructure cost in integer cents as quantity (see catalog price blackroad_infra_cost_markup_cents). The system owner can apply a markup multiplier to the reported infra cost before including it on the invoice.
- volatility_premium: manual or placeholder item until policy for automatic volatility billing is finalized.

Statistical bands (for alerts/pricing knobs):
- Normal band: usage ≤ μ + 2σ
- Critical band: usage > μ + 2σ
- Danger band: usage > μ + 3σ

Behavioral notes (documented; not implemented):
- For traffic within the Normal band, bill as usual.
- For usage entering the Critical band, mark account for review — consider throttling, higher billing tier, or manual outreach.
- For usage in the Danger band, flag for urgent review and consider manual intervention. Auto-shutdown is intentionally NOT implemented at this time — only alerting and manual processes are documented.

Aggregation notes
- Stripe enforces integer cents for USD prices. Very small per-event prices are represented as prices per 1,000 events (routed_events_1k at $0.10 per 1k) or per 1,000 records for memory.
- Customer-day pricing ($0.01) is supported directly as 1 cent per unit.

Examples
- 150,000 routed events in a month → quantity billed = ceil(150000 / 1000) = 150 units at $0.10 = $15.00
- 3,241 memory records → quantity billed = ceil(3241 / 1000) = 4 units at $1.00 = $4.00
- Infra cost reported as $123.45 → report quantity = 12345 (cents); billed = 12345 * $0.01 = $123.45 (before any markup)

Road Credits
- Road Credits are described in a separate document and are NOT applied automatically in this model yet. They will be applied post-verification and require additional identity/trust proofs from contributing nodes.

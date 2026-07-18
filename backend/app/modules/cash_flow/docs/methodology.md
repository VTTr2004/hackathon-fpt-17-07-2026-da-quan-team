# Methodology

## Cash-flow normalization

Transactions are normalized to period, direction, activity, category, amount and source identity. Amounts must be finite and non-negative. Direction carries the sign; stored amounts remain positive. Operating, investing and financing classification follows the nature of activity. Unclassified amounts remain visible and force a partial report.

AI may map unfamiliar workbook columns to canonical fields, but code validates the mapping and performs extraction. Workbook cell content is untrusted data and is never treated as instructions.

## Core calculations

- `net operating cash flow = operating inflow - operating outflow`.
- `net burn = max(-average net operating cash flow, 0)`.
- `runway = available cash / net burn` only when net burn is positive.
- `expected ending cash = opening cash + total inflows - total outflows`.
- `break-even revenue = fixed costs / (1 - variable-cost ratio)` when ratio is in `[0, 1)`.
- `net working capital = accounts receivable + inventory - accounts payable` when all balances exist.
- `DSO = AR / period revenue × period days`; `DPO = AP / period COGS × period days`; `inventory days = inventory / period COGS × period days`; CCC is DSO plus inventory days minus DPO.

All calculations use deterministic tools and `Decimal`. Missing denominators produce unavailable metrics, not estimated values.

## Reconciliation and evidence

Opening cash, transaction movement and reported ending cash are reconciled within an explicit tolerance. Conflicting balances from documents are not silently resolved. Findings reference calculation evidence; workbook-derived proposals retain document, sheet and range provenance.

## Scenarios

The latest normalized operating period is the starting operating pattern. Defaults are explicit:

- base: unchanged inflow/outflow;
- best: inflow `+10%`, outflow `-5%`;
- downside: inflow `-15%`, outflow `+5%`;
- severe: inflow `-30%`, outflow `+15%`.

These are sensitivity scenarios, not statistical forecasts. User overrides must be recorded in tool input.

## Sales and purchase support

Sales workbooks are used to reconcile cash inflow and summarize period/channel/payment data. AOV is calculated only when a true order identifier exists. Purchase workbooks support category/supplier/VAT totals and AP only when payment status is mapped. Purchases are not automatically treated as COGS, and sales/purchases do not prove AR or inventory balances.

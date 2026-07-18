# Analysis tools

All tools are deterministic and owned by Cash Flow.

| Tool | Version | Purpose |
|---|---:|---|
| `cash_flow_normalizer` | 1.0.0 | Normalize period, direction, activity and source identity. |
| `normalize_cashbook` | 1.0.0 | Execute an AI/heuristic column mapping against a detailed cashbook. |
| `extract_financial_facts` | 1.0.0 | Extract allowlisted label/value facts with cell provenance. |
| `summarize_sales` | 1.0.0 | Aggregate net sales by period/channel/payment/category; AOV only with order ID. |
| `summarize_purchases` | 1.0.0 | Aggregate expenses, VAT, suppliers and mapped unpaid amounts. |
| `cash_reconciliation` | 1.0.0 | Tie opening cash and movements to reported ending cash. |
| `cash_metrics_calculator` | 1.0.0 | Calculate operating inflow/outflow, burn, trend and runway. |
| `break_even_calculator` | 1.0.0 | Calculate contribution margin ratio and break-even revenue. |
| `working_capital_calculator` | 1.0.0 | Calculate NWC and optional DSO/DPO/inventory days/CCC. |
| `cash_scenario_simulator` | 1.0.0 | Run base, best, downside and severe scenarios. |
| `cash_flow_score_calculator` | 1.0.0 | Score runway and data quality; returns null on critical mismatch/insufficient metrics. |

## Ingestion request schema

```json
{
  "tool": "normalize_cashbook|extract_financial_facts|summarize_sales|summarize_purchases",
  "document_id": "string",
  "sheet": "string",
  "header_row": 4,
  "columns": {"canonical_field": 1},
  "field_map": {},
  "notes": "string|null"
}
```

Column indices and header rows are one-based. Unknown tools/columns, missing required mappings, unavailable sheets and invalid amounts are rejected. Tool errors remain structured warnings; AI cannot replace them with guessed numbers.

`ingestion_tool_catalog()` is the canonical runtime contract exposed to the mapping agent.

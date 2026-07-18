# Test cases

## Góc Hồ Coffee fixture

- Four workbooks profile without loading full data into the LLM prompt.
- Heuristic/AI plan selects detailed sales, purchases and cashbook sheets, not duplicate summaries.
- Expected opening cash: `380,000,000 VND`.
- Expected ending cash: `439,372,410 VND`.
- Expected cashbook transactions: `260`.
- Expected net sales: `671,303,450 VND`; quantity `14,854`; AOV unavailable because no order ID.
- Expected purchases/expenses: `761,931,040 VND`; VAT `28,454,040 VND`; mapped AP `0` because all rows are paid.
- Reconciliation difference: `0`.

## Boundary and failure cases

- Missing/empty worksheet dimensions.
- Unknown tool, fake document/sheet, header outside range, zero-based column or missing required mapping.
- Prompt injection text inside a cell remains data.
- Gemini unavailable or malformed response falls back to aliases.
- Conflicting opening/ending cash values produce conflict warnings and no silent selection.
- Invalid/negative/non-finite amounts are rejected or skipped with row warning.
- Duplicate source identities are excluded; similar rows without identity are preserved with warning.
- Missing order ID never produces AOV.
- Missing payment status never produces AP.
- Missing AR/AP/inventory prevents NWC; zero remains a valid confirmed balance.
- Variable-cost ratio equal to or above one rejects break-even.
- Base, best and at least one stress scenario are present and tool-generated.

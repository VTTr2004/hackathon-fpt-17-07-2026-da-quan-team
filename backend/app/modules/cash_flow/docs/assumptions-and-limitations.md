# Assumptions and limitations

- Currency conversion and inflation are not performed. A dataset must use one declared currency.
- Monthly burn assumes periods have comparable length; irregular periods must be normalized or warned.
- Runway is a liquidity sensitivity measure, not a full financial forecast.
- Scenario defaults repeat the latest operating pattern and do not model seasonality, tax timing, financing access or operational capacity.
- Workbook formulas are read as cached values (`data_only=True`) and are never executed by the backend.
- The mapping agent receives bounded samples, so uncommon headers may require confirmation. Every mapping is validated before execution.
- Imported proposals never overwrite confirmed facts automatically. Conflicts are marked and cannot be applied by the module helper.
- A purchase is not necessarily COGS; purchase timing and inventory movement may differ.
- AOV is unavailable without a real order identifier. Product/day rows or SKU batches are not treated as orders.
- AP requires payment status or equivalent evidence. AR requires receivable evidence; inventory requires an as-of snapshot. Missing balances are not inferred.
- Break-even requires confirmed fixed cost and variable-cost ratio. AI category classification alone is insufficient.
- DSO/DPO/inventory days require matching period balances and revenue/COGS; mixed periods invalidate interpretation.
- PDF invoice OCR and folder persistence are integration-layer concerns and are not implemented inside this module.

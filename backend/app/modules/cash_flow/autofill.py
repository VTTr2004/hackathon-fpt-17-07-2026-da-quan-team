import hashlib
import json
from typing import Any

from .ingestion_schemas import CashFlowIngestionResult

CASH_FLOW_AUTOFILL_FIELDS = frozenset(
    {
        "cash_flow_dataset",
        "current_cash",
        "minimum_cash_buffer",
        "fixed_monthly_costs",
        "variable_cost_ratio",
        "accounts_receivable",
        "accounts_payable",
        "inventory",
        "working_capital_period_revenue",
        "working_capital_period_cogs",
        "working_capital_period_days",
        "cash_flow_period_start",
        "cash_flow_period_end",
        "cash_as_of",
        "currency",
        "opening_cash",
        "reported_ending_cash",
        "sales_support_metrics",
        "purchase_cost_metrics",
        "monthly_rent",
        "lease_deposit",
        "employee_count",
    }
)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_cash_flow_facts_patch(
    preview: CashFlowIngestionResult,
    accepted_proposal_ids: set[str],
) -> dict[str, Any]:
    """Build a module-owned patch; persistence and concurrency checks belong to the integration layer."""
    patch: dict[str, Any] = {}
    for proposal in preview.proposals:
        if proposal.proposal_id not in accepted_proposal_ids:
            continue
        if proposal.status == "conflict":
            raise ValueError(f"Conflicting proposal cannot be applied: {proposal.proposal_id}")
        if proposal.field not in CASH_FLOW_AUTOFILL_FIELDS:
            raise ValueError(f"Cash Flow does not own autofill field: {proposal.field}")
        if proposal.field in patch and patch[proposal.field] != proposal.value:
            raise ValueError(f"Accepted proposals contain conflicting values for {proposal.field}")
        patch[proposal.field] = proposal.value
    return patch

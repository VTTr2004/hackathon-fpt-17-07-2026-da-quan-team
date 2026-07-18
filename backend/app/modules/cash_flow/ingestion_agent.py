import json
from collections import defaultdict
from typing import Any
from unicodedata import normalize as unicode_normalize

from app.llm.base import LLMClient
from app.llm.gemini import GeminiNotConfiguredError
from app.modules.cash_flow.autofill import stable_hash
from app.modules.cash_flow.ingestion_schemas import (
    CashFlowIngestionPlan,
    CashFlowIngestionResult,
    FieldProposal,
    IngestionToolName,
    IngestionToolRequest,
    ProposalSource,
    ToolExecutionResult,
    WorkbookSheetProfile,
)
from app.modules.cash_flow.prompts import load_ingestion_prompt
from app.modules.cash_flow.schemas import CashFlowDataset
from app.modules.cash_flow.tools.ingestion import (
    TOOL_VERSION,
    execute_ingestion_tool,
    ingestion_tool_catalog,
)
from app.modules.cash_flow.workbook_profiler import profile_cash_flow_workbooks
from app.schemas.common import Evidence, ToolCall

HEADER_ALIASES: dict[IngestionToolName, dict[str, tuple[str, ...]]] = {
    IngestionToolName.NORMALIZE_CASHBOOK: {
        "date": ("ngay", "date", "transaction date"),
        "inflow": ("tien vao", "inflow", "cash in", "receipt"),
        "outflow": ("tien ra", "outflow", "cash out", "payment"),
        "transaction_id": ("ma giao dich", "transaction id", "reference id"),
        "type": ("loai", "type"),
        "category": ("nhom", "category"),
        "description": ("dien giai", "description", "memo"),
        "account": ("tai khoan", "account"),
        "source_ref": ("chung tu nguon", "source ref", "document ref"),
    },
    IngestionToolName.EXTRACT_FINANCIAL_FACTS: {
        "label": ("chi tieu", "truong", "label", "metric"),
        "value": ("gia tri", "value", "amount"),
        "unit": ("don vi", "unit"),
        "notes": ("ghi chu", "notes"),
    },
    IngestionToolName.SUMMARIZE_SALES: {
        "date": ("ngay", "date"),
        "net_amount": ("doanh thu thuan", "net sales", "net revenue", "net amount"),
        "quantity": ("so luong", "quantity", "qty"),
        "channel": ("kenh", "channel"),
        "payment_method": ("thanh toan", "payment method", "payment"),
        "category": ("nhom", "category"),
        "order_id": ("ma don hang", "order id", "invoice id"),
    },
    IngestionToolName.SUMMARIZE_PURCHASES: {
        "date": ("ngay", "date"),
        "total_amount": ("tong thanh toan", "total amount", "total paid", "amount"),
        "category": ("nhom", "category"),
        "supplier": ("nha cung cap", "supplier", "vendor"),
        "payment_status": ("trang thai thanh toan", "trang thai", "payment status", "status"),
        "vat_amount": ("vat", "vat amount", "tax amount"),
        "invoice_id": ("ma chung tu", "invoice id", "document id"),
    },
}

REQUIRED_COLUMNS: dict[IngestionToolName, set[str]] = {
    IngestionToolName.NORMALIZE_CASHBOOK: {"date", "inflow", "outflow"},
    IngestionToolName.EXTRACT_FINANCIAL_FACTS: {"label", "value"},
    IngestionToolName.SUMMARIZE_SALES: {"date", "net_amount"},
    IngestionToolName.SUMMARIZE_PURCHASES: {"date", "total_amount"},
}


def _normalized_text(value: Any) -> str:
    raw = str(value or "").replace("đ", "d").replace("Đ", "D")
    text = unicode_normalize("NFKD", raw).encode("ascii", "ignore").decode().casefold()
    return " ".join(text.split())


def _column_mapping(values: list[Any], aliases: dict[str, tuple[str, ...]]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    normalized_values = [_normalized_text(value) for value in values]
    for canonical, names in aliases.items():
        exact = next(
            (index for index, value in enumerate(normalized_values, 1) if value and value in names),
            None,
        )
        if exact is not None:
            mapping[canonical] = exact
            continue
        prefix = next(
            (
                index
                for index, value in enumerate(normalized_values, 1)
                if value and any(value.startswith(f"{alias} ") for alias in names)
            ),
            None,
        )
        if prefix is not None:
            mapping[canonical] = prefix
    return mapping


def build_heuristic_plan(profiles: list[WorkbookSheetProfile]) -> CashFlowIngestionPlan:
    calls: list[IngestionToolRequest] = []
    candidates: dict[tuple[str, IngestionToolName], list[tuple[int, IngestionToolRequest]]] = defaultdict(list)
    for profile in profiles:
        for row in profile.sampled_rows:
            for tool, aliases in HEADER_ALIASES.items():
                columns = _column_mapping(row.values, aliases)
                if not REQUIRED_COLUMNS[tool].issubset(columns):
                    continue
                request = IngestionToolRequest(
                    tool=tool,
                    document_id=profile.document_id,
                    sheet=profile.sheet,
                    header_row=row.row_number,
                    columns=columns,
                )
                optional_count = len(columns) - len(REQUIRED_COLUMNS[tool])
                score = optional_count * 1_000_000 + max(profile.max_row - row.row_number, 0)
                candidates[(profile.document_id, tool)].append((score, request))

    for (_, tool), choices in candidates.items():
        if tool == IngestionToolName.EXTRACT_FINANCIAL_FACTS:
            calls.extend(request for _, request in sorted(choices, key=lambda item: item[0], reverse=True))
        else:
            calls.append(max(choices, key=lambda item: item[0])[1])
    deduplicated: dict[tuple[str, str, str, int], IngestionToolRequest] = {}
    for call in calls:
        deduplicated[(call.tool.value, call.document_id, call.sheet, call.header_row)] = call
    return CashFlowIngestionPlan(
        calls=list(deduplicated.values()),
        assumptions=["Header aliases were used because an AI mapping plan was unavailable."],
    )


def _merge_datasets(results: list[ToolExecutionResult], warnings: list[str]) -> CashFlowDataset | None:
    transactions = [transaction for result in results if result.dataset for transaction in result.dataset.transactions]
    opening_values = {
        result.dataset.opening_cash for result in results if result.dataset and result.dataset.opening_cash is not None
    }
    ending_values = {
        result.dataset.reported_ending_cash
        for result in results
        if result.dataset and result.dataset.reported_ending_cash is not None
    }
    if len(opening_values) > 1:
        warnings.append("Conflicting opening cash values were found; opening_cash was not auto-selected.")
    if len(ending_values) > 1:
        warnings.append("Conflicting ending cash values were found; reported_ending_cash was not auto-selected.")
    if not transactions and not opening_values and not ending_values:
        return None
    return CashFlowDataset(
        opening_cash=next(iter(opening_values)) if len(opening_values) == 1 else None,
        reported_ending_cash=next(iter(ending_values)) if len(ending_values) == 1 else None,
        transactions=transactions,
        source_type="agent_tool_ingestion",
        warnings=list(warnings),
    )


def _merge_proposals(proposals: list[FieldProposal]) -> list[FieldProposal]:
    grouped: dict[str, list[FieldProposal]] = defaultdict(list)
    for proposal in proposals:
        grouped[proposal.field].append(proposal)
    merged: list[FieldProposal] = []
    for field, items in grouped.items():
        serialized_values = {json.dumps(item.value, ensure_ascii=False, sort_keys=True, default=str) for item in items}
        if len(serialized_values) == 1:
            primary = items[0].model_copy(deep=True)
            primary.sources = [source for item in items for source in item.sources]
            primary.warnings = list(dict.fromkeys(warning for item in items for warning in item.warnings))
            merged.append(primary)
        else:
            for item in items:
                conflict = item.model_copy(deep=True)
                conflict.status = "conflict"
                conflict.confidence = "low"
                conflict.warnings = [*conflict.warnings, f"Conflicting proposals exist for {field}."]
                merged.append(conflict)
    for proposal in merged:
        proposal.proposal_id = stable_hash(
            {
                "field": proposal.field,
                "value": proposal.value,
                "tool": proposal.generated_by_tool,
                "sources": [source.model_dump(mode="json") for source in proposal.sources],
            }
        )[:20]
    return merged


def _dataset_proposals(dataset: CashFlowDataset | None, evidence: list[Evidence]) -> list[FieldProposal]:
    if dataset is None or not dataset.transactions:
        return []
    sources: dict[tuple[str, str, str], ProposalSource] = {}
    for transaction in dataset.transactions:
        key = (transaction.document_id or "", transaction.filename or "", transaction.sheet or "")
        sources[key] = ProposalSource(
            document_id=key[0],
            filename=key[1],
            sheet=key[2],
            range=None,
        )
    proposals = [
        FieldProposal(
            field="cash_flow_dataset",
            value=dataset.model_dump(mode="json"),
            confidence="high" if evidence else "medium",
            sources=list(sources.values()),
            generated_by_tool=IngestionToolName.NORMALIZE_CASHBOOK.value,
            warnings=dataset.warnings,
        )
    ]
    return proposals


def _monthly_operating_proposals(results: list[ToolExecutionResult]) -> list[FieldProposal]:
    proposals: list[FieldProposal] = []
    for result in results:
        sales = result.metrics.get("sales")
        if sales and sales.get("by_period"):
            source = next((item.sources[0] for item in result.proposals if item.sources), None)
            if source is not None:
                periods = len(sales["by_period"])
                proposals.append(
                    FieldProposal(
                        field="monthly_revenue",
                        value=sales["net_sales"] / periods,
                        confidence="high",
                        sources=[source],
                        generated_by_tool=IngestionToolName.SUMMARIZE_SALES.value,
                        warnings=["Derived as net sales divided by the number of reported months."],
                    )
                )
        purchases = result.metrics.get("purchases")
        if purchases and purchases.get("by_period") and purchases.get("by_category"):
            source = next((item.sources[0] for item in result.proposals if item.sources), None)
            if source is None:
                continue
            periods = len(purchases["by_period"])
            fixed_markers = {"tien thue", "tien luong", "phan mem"}
            fixed_total = sum(
                amount
                for category, amount in purchases["by_category"].items()
                if _normalized_text(category) in fixed_markers
            )
            total = purchases["total_purchases_and_expenses"]
            variable_total = total - fixed_total
            proposals.extend(
                [
                    FieldProposal(
                        field="fixed_monthly_costs",
                        value=fixed_total / periods,
                        confidence="medium",
                        sources=[source],
                        generated_by_tool=IngestionToolName.SUMMARIZE_PURCHASES.value,
                        warnings=["Derived from rent, payroll and software categories, averaged by reported month."],
                    ),
                    FieldProposal(
                        field="variable_costs",
                        value=variable_total / periods,
                        confidence="medium",
                        sources=[source],
                        generated_by_tool=IngestionToolName.SUMMARIZE_PURCHASES.value,
                        warnings=["Derived from remaining purchase and expense categories, averaged by reported month."],
                    ),
                ]
            )
    return proposals


class CashFlowIngestionAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    async def ingest(
        self,
        documents: list[dict[str, Any]],
        *,
        use_ai: bool = True,
    ) -> CashFlowIngestionResult:
        profiles, profile_warnings = profile_cash_flow_workbooks(documents)
        if not profiles:
            return CashFlowIngestionResult(
                plan_source="none",
                plan=CashFlowIngestionPlan(),
                warnings=profile_warnings,
            )

        plan_source = "heuristic"
        plan: CashFlowIngestionPlan | None = None
        warnings = list(profile_warnings)
        if use_ai and self.llm_client is not None:
            prompt = json.dumps(
                {
                    "sheet_profiles": [profile.model_dump(mode="json") for profile in profiles],
                    "tool_catalog": ingestion_tool_catalog(),
                },
                ensure_ascii=False,
                default=str,
            )
            try:
                plan = await self.llm_client.generate_structured(
                    prompt=prompt,
                    system_instruction=load_ingestion_prompt(),
                    response_model=CashFlowIngestionPlan,
                )
                plan_source = "ai"
            except GeminiNotConfiguredError:
                warnings.append("Gemini is not configured; deterministic header mapping was used.")
            except Exception as exc:
                warnings.append(f"AI mapping failed ({type(exc).__name__}); deterministic header mapping was used.")
        if plan is None or not plan.calls:
            plan = build_heuristic_plan(profiles)
            plan_source = "heuristic"

        available_sheets = {(profile.document_id, profile.sheet) for profile in profiles}
        documents_by_id = {str(document.get("id", "")): document for document in documents}
        results: list[ToolExecutionResult] = []
        tool_calls: list[ToolCall] = []
        for request in plan.calls:
            if (request.document_id, request.sheet) not in available_sheets:
                warnings.append(f"Rejected mapping to unavailable sheet: {request.document_id}/{request.sheet}")
                continue
            try:
                result = execute_ingestion_tool(request, documents_by_id)
            except (TypeError, ValueError) as exc:
                warnings.append(f"{request.tool.value} failed for {request.sheet}: {exc}")
                continue
            results.append(result)
            warnings.extend(result.warnings)
            tool_calls.append(
                ToolCall(
                    name=f"cash_flow_{request.tool.value}",
                    version=TOOL_VERSION,
                    input=request.model_dump(mode="json"),
                    output={
                        "transaction_count": len(result.dataset.transactions) if result.dataset else 0,
                        "opening_cash": result.dataset.opening_cash if result.dataset else None,
                        "reported_ending_cash": result.dataset.reported_ending_cash if result.dataset else None,
                        "metrics": result.metrics,
                        "proposal_fields": [proposal.field for proposal in result.proposals],
                    },
                    warnings=result.warnings,
                )
            )

        dataset = _merge_datasets(results, warnings)
        evidence = [item for result in results for item in result.evidence]
        proposals = [item for result in results for item in result.proposals]
        proposals.extend(_monthly_operating_proposals(results))
        proposals.extend(_dataset_proposals(dataset, evidence))
        supporting_metrics: dict[str, Any] = defaultdict(list)
        for result in results:
            for key, value in result.metrics.items():
                supporting_metrics[key].append(value)
        merged_proposals = _merge_proposals(proposals)
        preview_id = stable_hash(
            {
                "plan": plan.model_dump(mode="json"),
                "proposals": [proposal.model_dump(mode="json") for proposal in merged_proposals],
                "tool_version": TOOL_VERSION,
            }
        )
        return CashFlowIngestionResult(
            preview_id=preview_id,
            plan_source=plan_source,
            plan=plan,
            dataset=dataset,
            supporting_metrics=dict(supporting_metrics),
            proposals=merged_proposals,
            evidence=evidence,
            tool_calls=tool_calls,
            warnings=list(dict.fromkeys(warnings)),
        )

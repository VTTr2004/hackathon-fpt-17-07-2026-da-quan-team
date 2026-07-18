from decimal import Decimal
from pathlib import Path
from typing import Any

from app.schemas.common import Evidence

from .schemas import CashActivity, CashDirection, CashFlowDataset, CashFlowTransaction


def extract_cash_flow_documents(
    documents: list[dict[str, Any]],
) -> tuple[CashFlowDataset | None, list[Evidence], list[str]]:
    try:
        from openpyxl import load_workbook
    except ImportError:
        return None, [], ["Workbook extraction is unavailable because openpyxl is not installed."]
    transactions: list[CashFlowTransaction] = []
    evidence: list[Evidence] = []
    warnings: list[str] = []
    for doc in documents:
        path = Path(doc.get("storage_path") or "")
        if path.suffix.lower() != ".xlsx" or not path.exists():
            continue
        workbook = load_workbook(path, read_only=True, data_only=True)
        for worksheet in workbook.worksheets:
            headers = [str(x or "").strip().lower() for x in next(worksheet.iter_rows(values_only=True), ())]
            is_cashbook = any("tiền vào" in x or "tien vao" in x for x in headers) and any(
                "tiền ra" in x or "tien ra" in x for x in headers
            )
            if not is_cashbook:
                continue

            def index(*names: str, header_row: list[str] = headers) -> int | None:
                return next((i for i, header in enumerate(header_row) if any(name in header for name in names)), None)

            date_i, in_i, out_i, description_i, category_i = (
                index("ngày", "ngay", "date"),
                index("tiền vào", "tien vao", "inflow"),
                index("tiền ra", "tien ra", "outflow"),
                index("diễn giải", "dien giai", "description"),
                index("nhóm", "nhom", "category"),
            )
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), 2):
                raw_date = row[date_i] if date_i is not None else None
                period = raw_date.strftime("%Y-%m") if hasattr(raw_date, "strftime") else None
                if not period:
                    continue
                for direction, value_i in ((CashDirection.INFLOW, in_i), (CashDirection.OUTFLOW, out_i)):
                    value = row[value_i] if value_i is not None else None
                    if value in (None, 0):
                        continue
                    try:
                        amount = Decimal(str(value))
                    except Exception:
                        continue
                    evidence_id = f"{doc['id']}:{worksheet.title}:{row_number}"
                    transactions.append(
                        CashFlowTransaction(
                            period=period,
                            date=raw_date,
                            direction=direction,
                            activity=CashActivity.UNCLASSIFIED,
                            category=str(row[category_i] if category_i is not None else "cashbook"),
                            description=str(row[description_i] if description_i is not None else ""),
                            amount=amount,
                            document_id=doc["id"],
                            filename=doc["filename"],
                            sheet=worksheet.title,
                            row_number=row_number,
                            evidence_id=evidence_id,
                        )
                    )
                    evidence.append(
                        Evidence(
                            evidence_id=evidence_id,
                            source_type="uploaded_workbook",
                            title=f"{doc['filename']} / {worksheet.title} row {row_number}",
                            document_id=doc["id"],
                        )
                    )
    return (
        (CashFlowDataset(transactions=transactions, source_type="cashbook") if transactions else None),
        evidence,
        warnings,
    )

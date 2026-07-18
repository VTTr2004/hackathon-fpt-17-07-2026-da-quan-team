from pathlib import Path

import pytest

from app.modules.cash_flow.classification import classify_transactions
from app.modules.cash_flow.extractor import extract_cash_flow_documents
from app.modules.cash_flow.schemas import CashActivity


def test_extractor_reads_demo_cashbook_with_title_rows() -> None:
    pytest.importorskip("openpyxl")
    repository_root = Path(__file__).resolve().parents[2]
    workbook = repository_root / "sample-data" / "goc-ho-coffee" / "05_so_thu_chi_3_thang.xlsx"

    dataset, evidence, warnings = extract_cash_flow_documents(
        [{"id": "demo-cashbook", "filename": workbook.name, "storage_path": str(workbook)}]
    )

    assert dataset is not None
    assert dataset.opening_cash == 380_000_000
    assert dataset.reported_ending_cash == 439_372_410
    assert len(dataset.transactions) > 1
    assert len(evidence) == len(dataset.transactions)
    assert not [warning for warning in warnings if "no detailed cashbook" in warning]
    assert CashActivity.UNCLASSIFIED not in {item.activity for item in classify_transactions(dataset.transactions)}

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import document_classifier
from app.services.document_classifier import classify_document_fallback, classify_documents


@pytest.mark.parametrize(
    ("filename", "text", "expected"),
    [
        ("giay_chung_nhan_dang_ky_kinh_doanh.pdf", "", "legal"),
        ("hoa_don_ban_hang_thang_6.xlsx", "", "sales_revenue"),
        ("danh_sach_nha_cung_cap.xlsx", "", "purchases_expenses"),
        ("so_quy_tien_mat.xlsx", "", "accounting_cashflow"),
        ("bao_cao_van_hanh_cua_hang.md", "", "location_operations"),
        ("ghi_chu_chung.txt", "Nội dung chưa xác định", "unclassified"),
    ],
)
def test_fallback_classifier(filename: str, text: str, expected: str) -> None:
    assert classify_document_fallback(filename, text) == expected


@pytest.mark.asyncio
async def test_ai_classification_is_validated_and_missing_results_use_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_id = uuid4()
    second_id = uuid4()
    documents = [
        SimpleNamespace(id=first_id, filename="invoice.pdf", extracted_text="Doanh thu bán hàng"),
        SimpleNamespace(id=second_id, filename="so_quy.xlsx", extracted_text="Sổ quỹ tiền mặt"),
    ]

    class FakeClient:
        async def generate_structured(self, **_: object) -> document_classifier.ClassificationBatch:
            return document_classifier.ClassificationBatch(
                predictions=[
                    document_classifier.ClassificationPrediction(
                        document_id=str(first_id), category="sales_revenue"
                    ),
                    document_classifier.ClassificationPrediction(
                        document_id=str(uuid4()), category="legal"
                    ),
                ]
            )

    monkeypatch.setattr(document_classifier, "get_llm_client", lambda: FakeClient())
    result = await classify_documents(documents)

    assert result[str(first_id)] == ("sales_revenue", "ai")
    assert result[str(second_id)] == ("accounting_cashflow", "rules")


@pytest.mark.asyncio
async def test_ai_failure_uses_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, filename="hop_dong_thue.pdf", extracted_text="Mặt bằng cửa hàng")

    class FailingClient:
        async def generate_structured(self, **_: object) -> object:
            raise RuntimeError("offline")

    monkeypatch.setattr(document_classifier, "get_llm_client", lambda: FailingClient())

    assert await classify_documents([document]) == {str(document_id): ("location_operations", "rules")}

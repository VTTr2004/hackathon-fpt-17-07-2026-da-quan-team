from .schemas import CashActivity, CashDirection, CashFlowTransaction

FINANCING_INFLOW = (
    "vốn góp",
    "góp vốn",
    "bổ sung vốn",
    "vốn chủ",
    "capital injection",
    "equity",
    "loan received",
    "nhận khoản vay",
    "giải ngân",
)
FINANCING_OUTFLOW = (
    "trả nợ gốc",
    "principal repayment",
    "dividend",
    "cổ tức",
    "hoàn vốn",
)
INVESTING = (
    "mua máy",
    "mua thiết bị",
    "capex",
    "tài sản cố định",
    "cải tạo",
    "xây dựng",
    "bán tài sản",
    "thanh lý",
)
OPERATING = (
    "trả lãi vay",
    "lãi vay",
    "interest",
    "bán hàng",
    "doanh thu",
    "khách hàng",
    "nguyên liệu",
    "cà phê",
    "bao bì",
    "bánh",
    "phần mềm",
    "nhà cung cấp",
    "tiền thuê",
    "lương",
    "điện",
    "nước",
    "internet",
    "marketing",
    "thuế",
    "phí",
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def classify_transaction(transaction: CashFlowTransaction) -> CashFlowTransaction:
    if transaction.activity != CashActivity.UNCLASSIFIED:
        return transaction

    text = f"{transaction.category} {transaction.description or ''}".lower()
    if transaction.direction == CashDirection.INFLOW and _contains_any(text, FINANCING_INFLOW):
        return transaction.model_copy(update={"activity": CashActivity.FINANCING})
    if transaction.direction == CashDirection.OUTFLOW and _contains_any(text, FINANCING_OUTFLOW):
        return transaction.model_copy(update={"activity": CashActivity.FINANCING})
    if _contains_any(text, INVESTING):
        return transaction.model_copy(update={"activity": CashActivity.INVESTING})
    if _contains_any(text, OPERATING):
        return transaction.model_copy(update={"activity": CashActivity.OPERATING})
    return transaction


def classify_transactions(transactions: list[CashFlowTransaction]) -> list[CashFlowTransaction]:
    return [classify_transaction(item) for item in transactions]

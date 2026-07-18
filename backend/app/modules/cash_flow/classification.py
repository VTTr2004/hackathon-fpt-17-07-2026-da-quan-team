from .schemas import CashActivity, CashFlowTransaction

RULES = {
    CashActivity.FINANCING: (
        "vốn góp",
        "góp vốn",
        "đầu tư",
        "equity",
        "capital injection",
        "loan received",
        "vay",
        "giải ngân",
        "trả nợ gốc",
        "dividend",
        "hoàn vốn",
    ),
    CashActivity.INVESTING: (
        "mua máy",
        "mua thiết bị",
        "capex",
        "tài sản cố định",
        "cải tạo",
        "xây dựng",
        "bán tài sản",
        "thanh lý",
    ),
    CashActivity.OPERATING: (
        "bán hàng",
        "doanh thu",
        "khách hàng",
        "nguyên liệu",
        "nhà cung cấp",
        "tiền thuê",
        "lương",
        "điện",
        "nước",
        "internet",
        "marketing",
        "thuế",
        "phí",
        "lãi vay",
        "interest",
    ),
}


def classify_transaction(transaction: CashFlowTransaction) -> CashFlowTransaction:
    if transaction.activity != CashActivity.UNCLASSIFIED:
        return transaction
    text = f"{transaction.category} {transaction.description or ''}".lower()
    for activity, keywords in RULES.items():
        if any(keyword in text for keyword in keywords):
            return transaction.model_copy(update={"activity": activity})
    return transaction


def classify_transactions(transactions: list[CashFlowTransaction]) -> list[CashFlowTransaction]:
    return [classify_transaction(item) for item in transactions]

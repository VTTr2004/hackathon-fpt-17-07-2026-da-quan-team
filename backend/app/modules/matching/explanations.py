LABELS = {
    "industry_fit": "Lĩnh vực phù hợp khẩu vị",
    "stage_fit": "Giai đoạn đầu tư phù hợp",
    "ticket_fit": "Nhu cầu vốn nằm trong ticket",
    "location_fit": "Địa điểm phù hợp",
    "traction_fit": "Traction đáp ứng kỳ vọng",
    "unit_economics_fit": "Có tín hiệu unit economics",
    "scalability_fit": "Có khả năng nhân rộng",
    "funding_timing_fit": "Runway phù hợp thời điểm gọi vốn",
    "capability_need_fit": "Nhu cầu khớp năng lực nhà đầu tư",
}


def explain(breakdown: dict[str, float], maxima: dict[str, float]) -> tuple[list[str], list[str]]:
    matched = [LABELS[key] for key, value in breakdown.items() if key != "total" and value >= maxima[key] * 0.7]
    mismatched = [
        f"Cần xác minh: {LABELS[key].lower()}"
        for key, value in breakdown.items()
        if key != "total" and value < maxima[key] * 0.4
    ]
    return matched[:4], mismatched[:3]

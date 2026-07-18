from types import SimpleNamespace

from app.modules.matching.confidence import confidence_score
from app.modules.matching.feature_builder import build_features
from app.modules.matching.hard_filters import hard_filter_reasons
from app.modules.matching.scoring import score_match


def preference(**overrides):
    values = {
        "preferred_industries": ["F&B", "Retail"],
        "preferred_subsectors": ["Coffee"],
        "preferred_stages": ["Seed"],
        "preferred_locations": ["Hà Nội"],
        "ticket_min": 3_000_000_000,
        "ticket_max": 10_000_000_000,
        "minimum_monthly_revenue": 500_000_000,
        "minimum_revenue_growth": None,
        "maximum_runway_months": 12,
        "strategic_capabilities": ["mở rộng chuỗi", "phân phối"],
        "required_capabilities": [],
        "exclusion_rules": {},
        "weights": {},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def snapshot(**facts):
    return {
        "name": "Góc Hồ Coffee",
        "industry": "F&B",
        "stage": "Seed",
        "primary_location": "Hà Nội",
        "facts": {
            "subsector": "Coffee",
            "fundraising_amount": 5_000_000_000,
            "monthly_revenue": 600_000_000,
            "revenue_growth": 18,
            "runway_months": 8,
            "gross_margin": 62,
            "scalability": "Mở thêm 10 cửa hàng",
            "needed_capabilities": ["mở rộng chuỗi"],
            **facts,
        },
    }


def test_hard_filter_rejects_wrong_industry() -> None:
    features = build_features(snapshot())
    assert hard_filter_reasons(features, preference(preferred_industries=["SaaS"])) == ["industry"]


def test_hard_filter_rejects_ticket_outside_range() -> None:
    features = build_features(snapshot(fundraising_amount=20_000_000_000))
    assert "ticket" in hard_filter_reasons(features, preference())


def test_fit_score_and_breakdown_are_bounded_and_consistent() -> None:
    result = score_match(snapshot(), preference())
    assert 0 <= result.fit_score <= 100
    components = [value for key, value in result.score_breakdown.items() if key != "total"]
    assert round(sum(components), 1) == result.score_breakdown["total"] == result.fit_score


def test_missing_data_lowers_confidence_without_zeroing_fit() -> None:
    sparse = {"name": "Sparse Coffee", "industry": "F&B", "stage": "Seed", "primary_location": "Hà Nội", "facts": {}}
    rich_score, _ = confidence_score(build_features(snapshot()))
    result = score_match(sparse, preference())
    assert 0 < result.confidence_score < rich_score
    assert result.fit_score > 0

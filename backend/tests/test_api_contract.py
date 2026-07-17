from app.main import app


def test_required_api_paths_are_registered() -> None:
    paths = set(app.openapi()["paths"])
    assert "/api/v1/health" in paths
    assert "/api/v1/startups" in paths
    assert "/api/v1/startups/{startup_id}/documents" in paths
    assert "/api/v1/startups/{startup_id}/analyses/{module}" in paths
    assert "/api/v1/startups/{startup_id}/chat" in paths

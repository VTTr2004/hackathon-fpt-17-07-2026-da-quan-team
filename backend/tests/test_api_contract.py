from app.main import app


def test_required_api_paths_are_registered() -> None:
    paths = set(app.openapi()["paths"])
    assert "/api/v1/health" in paths
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/startups" in paths
    assert "/api/v1/startups/{startup_id}/completeness" in paths
    assert "/api/v1/startups/{startup_id}/extractions" in paths
    assert "/api/v1/startups/{startup_id}/extractions/{extraction_id}" in paths
    assert "/api/v1/startups/{startup_id}/extractions/{extraction_id}/confirm" in paths
    assert "/api/v1/startups/{startup_id}/profile-interviews" in paths
    assert "/api/v1/startups/{startup_id}/profile-interviews/{interview_id}/answer" in paths
    assert "/api/v1/startups/{startup_id}/profile-interviews/{interview_id}/confirm" in paths
    assert "/api/v1/startups/{startup_id}/submit" in paths
    assert "/api/v1/startups/{startup_id}/versions" in paths
    assert "/api/v1/startups/{startup_id}/access" in paths
    assert "/api/v1/startups/{startup_id}/access-request" in paths
    assert "/api/v1/startups/{startup_id}/access/{investor_id}/approve" in paths
    assert "/api/v1/startups/{startup_id}/access/{investor_id}/reject" in paths
    assert "/api/v1/startups/{startup_id}/documents" in paths
    assert "/api/v1/startups/{startup_id}/analyses/{module}" in paths
    assert "/api/v1/startups/{startup_id}/chat" in paths

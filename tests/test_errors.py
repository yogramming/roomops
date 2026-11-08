def test_unknown_route_returns_json_404(client):
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    assert response.is_json
    assert response.json["error"] == "not_found"


def test_unexpected_exception_returns_json_500(client, app):
    def raise_error():
        raise RuntimeError("Sensitive internal error")

    app.add_url_rule(
        "/test-error",
        "test_error",
        raise_error,
    )

    response = client.get("/test-error")

    assert response.status_code == 500
    assert response.is_json
    assert response.json["error"] == "internal_server_error"
    assert "Sensitive internal error" not in response.get_data(as_text=True)

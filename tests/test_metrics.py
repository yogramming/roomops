def test_metrics_endpoint_returns_prometheus_format(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.content_type
    assert b"roomops_http_requests_total" in response.data
    assert b"roomops_http_request_duration_seconds" in response.data


def test_metrics_endpoint_does_not_count_itself(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert b'endpoint="/metrics"' not in response.data

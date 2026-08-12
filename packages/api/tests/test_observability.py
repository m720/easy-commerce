"""Correlation IDs, metrics exposition, and health/readiness probes."""

import json
import logging

from app.config import settings
from app.core import metrics
from app.core.logging import JsonFormatter, get_request_id, set_request_id, set_user_id


def _capture_log_context(client, path: str, headers: dict | None = None) -> dict:
    """Run a request and report the log context seen by the access log line."""
    from app.core.logging import _user_id

    captured: dict = {}

    class Capture(logging.Handler):
        def emit(self, record):
            captured.setdefault("user_id", _user_id.get())

    request_logger = logging.getLogger("app.request")
    handler = Capture()
    original_level = request_logger.level
    request_logger.setLevel(logging.INFO)  # the suite runs at WARNING by default
    request_logger.addHandler(handler)
    try:
        client.get(path, headers=headers or {})
    finally:
        request_logger.removeHandler(handler)
        request_logger.setLevel(original_level)

    assert captured, "no access log line was emitted"
    return captured


def test_response_carries_a_correlation_id(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get(settings.REQUEST_ID_HEADER)


def test_inbound_correlation_id_is_adopted(client):
    """A gateway-supplied ID must survive the hop so a trace stays joined up."""
    incoming = "trace-from-the-gateway"
    resp = client.get("/health", headers={settings.REQUEST_ID_HEADER: incoming})
    assert resp.headers[settings.REQUEST_ID_HEADER] == incoming


def test_generated_ids_are_unique_per_request(client):
    first = client.get("/health").headers[settings.REQUEST_ID_HEADER]
    second = client.get("/health").headers[settings.REQUEST_ID_HEADER]
    assert first != second


def test_absurdly_long_inbound_id_is_truncated(client):
    resp = client.get("/health", headers={settings.REQUEST_ID_HEADER: "a" * 500})
    assert len(resp.headers[settings.REQUEST_ID_HEADER]) == 64


def test_metrics_endpoint_exposes_the_core_signals(client):
    client.get("/health")
    resp = client.get("/metrics")

    assert resp.status_code == 200
    body = resp.text
    # Latency, error rate (status-labelled counter) and pool usage.
    assert "http_request_duration_seconds" in body
    assert "http_requests_total" in body
    assert "db_pool_connections" in body


def test_request_metrics_use_route_templates_not_raw_paths(client, admin_headers):
    """Labelling by raw path would mint a time series per product ID."""
    client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    body = client.get("/metrics").text

    assert 'route="/api/v1/products/{product_id}"' in body
    assert "00000000-0000-0000-0000-000000000000" not in body


def test_checkout_failures_are_counted_by_reason(client, user_headers):
    """A checkout error spike should name its own cause on the dashboard."""
    client.post("/api/v1/orders", json={"address_id": "00000000-0000-0000-0000-000000000000"}, headers=user_headers)

    body = client.get("/metrics").text
    assert 'order_placement_failures_total{reason="address_not_found"}' in body


def test_json_log_lines_include_the_correlation_id():
    set_request_id("abc123")
    set_user_id("user-42")
    try:
        record = logging.LogRecord(
            name="app.test", level=logging.INFO, pathname=__file__, lineno=1,
            msg="order placed", args=None, exc_info=None,
        )
        record.order_id = "order-7"
        payload = json.loads(JsonFormatter().format(record))
    finally:
        set_request_id(None)
        set_user_id(None)

    assert payload["request_id"] == "abc123"
    assert payload["user_id"] == "user-42"
    assert payload["order_id"] == "order-7"
    assert payload["message"] == "order placed"
    assert payload["service"] == settings.SERVICE_NAME


def test_authenticated_requests_are_attributed_to_the_caller(client, user_headers):
    """Log lines for an authenticated request must carry the user, not just the request.

    The identity is resolved in the middleware rather than the auth dependency:
    sync endpoints run in their own threadpool contexts, so a contextvar set
    inside a dependency never reaches the handler or the access log.
    """
    captured = _capture_log_context(client, "/api/v1/auth/me", headers=user_headers)
    assert captured.get("user_id"), "authenticated request logged without a user_id"


def test_unauthenticated_requests_have_no_user_attribution(client):
    captured = _capture_log_context(client, "/api/v1/products")
    assert captured.get("user_id") is None


def test_garbage_bearer_token_does_not_break_the_request(client):
    """A malformed token must fail auth, not the logging path."""
    resp = client.get("/api/v1/products", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 200


def test_request_context_is_cleared_between_requests(client):
    client.get("/health")
    # Nothing may leak into the next request's log lines.
    assert get_request_id() is None


def test_health_is_dependency_free(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_readiness_reports_dependency_state(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"


def test_route_template_falls_back_for_unmatched_paths(client):
    client.get("/definitely-not-a-route")
    body = client.get("/metrics").text
    assert "<unmatched>" in body


def test_metrics_render_is_prometheus_text_format():
    rendered = metrics.render().decode()
    assert rendered.startswith("#") or rendered == ""

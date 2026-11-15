from fastapi.testclient import TestClient

from busmora_ai import __version__
from busmora_ai.entrypoints.http.app import create_health_app, create_http_app
from tests.fakes import FakeProbe


def test_live_does_not_call_dependencies() -> None:
    probe = FakeProbe("postgres", error=RuntimeError("down"))
    client = TestClient(create_http_app(probes=[probe], timeout_seconds=1))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "live", "role": "ai-http", "version": __version__}
    assert probe.calls == 0


def test_ready_returns_200_when_dependencies_are_reachable() -> None:
    client = TestClient(
        create_http_app(probes=[FakeProbe("postgres"), FakeProbe("qdrant")], timeout_seconds=1)
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["postgres"]["ok"] is True


def test_ready_returns_503_when_a_dependency_fails() -> None:
    client = TestClient(
        create_health_app(
            role="ai-crawl",
            probes=[FakeProbe("redis", error=OSError("refused"))],
            timeout_seconds=1,
        )
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["role"] == "ai-crawl"
    assert body["checks"]["redis"] == {
        "ok": False,
        "latency_ms": body["checks"]["redis"]["latency_ms"],
        "error": "OSError",
    }


def test_docs_are_hidden_unless_requested() -> None:
    hidden = TestClient(create_http_app(probes=[], timeout_seconds=1))
    shown = TestClient(create_http_app(probes=[], timeout_seconds=1, expose_docs=True))

    assert hidden.get("/openapi.json").status_code == 404
    assert shown.get("/openapi.json").status_code == 200

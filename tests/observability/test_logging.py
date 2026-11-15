from busmora_ai.observability.logging import REDACTED, redact_sensitive


def test_redacts_sensitive_keys_at_any_depth() -> None:
    event = {
        "event": "connected",
        "password": "hunter2",
        "db": {"dsn": "postgresql://u:p@h/d", "host": "h"},
        "headers": [{"Authorization": "Bearer abc"}],
        "api_key": "k",
    }

    result = redact_sensitive(None, "info", event)

    assert result["password"] == REDACTED
    assert result["api_key"] == REDACTED
    assert result["db"] == {"dsn": REDACTED, "host": "h"}
    assert result["headers"] == [{"Authorization": REDACTED}]
    assert result["event"] == "connected"

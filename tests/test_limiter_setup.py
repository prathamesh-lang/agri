from types import SimpleNamespace

from slowapi.errors import RateLimitExceeded

from backend.core import limiter as limiter_module


class FakeApp:
    def __init__(self):
        self.state = SimpleNamespace()
        self.handlers = {}

    def add_exception_handler(self, exception_class, handler):
        self.handlers[exception_class] = handler


class BrokenLimiter:
    def limit(self, rate):
        raise RuntimeError("bad rate")


def test_safe_limit_logs_when_decorator_fails(monkeypatch, caplog):
    monkeypatch.setattr(
        limiter_module,
        "build_limiter",
        lambda default_limits=None: BrokenLimiter(),
    )

    app = FakeApp()
    limiter = limiter_module.setup_rate_limiter(app)

    def endpoint():
        return {"ok": True}

    with caplog.at_level("ERROR", logger=limiter_module.__name__):
        decorated = limiter.limit("abc/minute")(endpoint)

    assert decorated is endpoint
    assert app.state.limiter is limiter
    assert RateLimitExceeded in app.handlers
    assert "Endpoint is UNPROTECTED" in caplog.text
    assert "abc/minute" in caplog.text
    assert "endpoint" in caplog.text

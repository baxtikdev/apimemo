from __future__ import annotations

import threading

from apimemo.config import ApiMemoConfig, configure, get_config


class TestApiMemoConfig:
    def test_defaults(self) -> None:
        config = ApiMemoConfig()
        assert config.enabled is True
        assert config.max_body_size == 10240
        assert config.ttl_days == 30
        assert config.batch_size == 50
        assert config.flush_interval == 5.0
        assert config.ignore_hosts == ()
        assert config.ignore_paths == ()
        assert config.log_request_body is True
        assert config.log_response_body is True
        assert config.log_headers is False

    def test_frozen(self) -> None:
        config = ApiMemoConfig()
        try:
            config.enabled = False  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass

    def test_should_ignore_host(self) -> None:
        config = ApiMemoConfig(ignore_hosts=("localhost", "*.internal.io"))
        assert config.should_ignore("localhost", "/api") is True
        assert config.should_ignore("db.internal.io", "/api") is True
        assert config.should_ignore("api.example.com", "/api") is False

    def test_should_ignore_path(self) -> None:
        config = ApiMemoConfig(ignore_paths=("/health", "/metrics*"))
        assert config.should_ignore("api.com", "/health") is True
        assert config.should_ignore("api.com", "/metrics/cpu") is True
        assert config.should_ignore("api.com", "/api/v1") is False


class TestConfigure:
    def test_configure_returns_config(self) -> None:
        config = configure(enabled=False, max_body_size=5000)
        assert config.enabled is False
        assert config.max_body_size == 5000

    def test_configure_updates_global(self) -> None:
        configure(batch_size=100)
        config = get_config()
        assert config.batch_size == 100

    def test_configure_partial_preserves_defaults(self) -> None:
        config = configure(log_headers=True)
        assert config.log_headers is True
        assert config.enabled is True  # default preserved

    def test_configure_merges_with_previous(self) -> None:
        """Calling configure() twice should merge, not reset."""
        configure(batch_size=100)
        config = configure(log_headers=True)
        assert config.batch_size == 100  # preserved from first call
        assert config.log_headers is True  # set by second call

    def test_configure_no_args_resets(self) -> None:
        """Calling configure() with no args resets to defaults."""
        configure(batch_size=200, log_headers=True)
        config = configure()  # reset
        assert config.batch_size == 50
        assert config.log_headers is False

    def test_thread_safety(self) -> None:
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(100):
                    configure(batch_size=25)
                    get_config()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def teardown_method(self) -> None:
        configure()  # reset to defaults

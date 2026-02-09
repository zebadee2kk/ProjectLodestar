"""Tests for base module infrastructure."""

import pytest
from modules.base import LodestarPlugin, EventBus


class ConcretePlugin(LodestarPlugin):
    """Minimal concrete plugin for testing the ABC."""

    def __init__(self, config):
        super().__init__(config)
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def health_check(self):
        return {"status": "healthy", "enabled": self.enabled}


class TestLodestarPlugin:
    """Tests for the LodestarPlugin abstract base class."""

    def test_plugin_enabled_from_config(self):
        plugin = ConcretePlugin({"enabled": True})
        assert plugin.enabled is True

    def test_plugin_disabled_by_default(self):
        plugin = ConcretePlugin({})
        assert plugin.enabled is False

    def test_plugin_stores_config(self):
        config = {"enabled": True, "custom_key": "value"}
        plugin = ConcretePlugin(config)
        assert plugin.config is config

    def test_plugin_start_stop(self):
        plugin = ConcretePlugin({"enabled": True})
        plugin.start()
        assert plugin.started is True
        plugin.stop()
        assert plugin.stopped is True

    def test_plugin_health_check(self):
        plugin = ConcretePlugin({"enabled": True})
        health = plugin.health_check()
        assert health["status"] == "healthy"
        assert health["enabled"] is True

    def test_cannot_instantiate_abc_directly(self):
        with pytest.raises(TypeError):
            LodestarPlugin({"enabled": True})


class TestEventBus:
    """Tests for the EventBus publish-subscribe system."""

    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda data: received.append(data))
        bus.publish("test_event", {"key": "value"})
        assert received == [{"key": "value"}]

    def test_multiple_subscribers(self):
        bus = EventBus()
        results_a = []
        results_b = []
        bus.subscribe("evt", lambda d: results_a.append(d))
        bus.subscribe("evt", lambda d: results_b.append(d))
        bus.publish("evt", 42)
        assert results_a == [42]
        assert results_b == [42]

    def test_publish_no_subscribers(self):
        bus = EventBus()
        bus.publish("nobody_listening", "data")  # should not raise

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        callback = lambda d: received.append(d)
        bus.subscribe("evt", callback)
        bus.unsubscribe("evt", callback)
        bus.publish("evt", "data")
        assert received == []

    def test_unsubscribe_nonexistent_event(self):
        bus = EventBus()
        bus.unsubscribe("nope", lambda d: None)  # should not raise

    def test_subscriber_error_does_not_block_others(self):
        bus = EventBus()
        received = []

        def bad_callback(data):
            raise RuntimeError("boom")

        bus.subscribe("evt", bad_callback)
        bus.subscribe("evt", lambda d: received.append(d))
        bus.publish("evt", "hello")
        assert received == ["hello"]

    def test_publish_with_none_data(self):
        bus = EventBus()
        received = []
        bus.subscribe("evt", lambda d: received.append(d))
        bus.publish("evt")
        assert received == [None]

    def test_separate_events_are_independent(self):
        bus = EventBus()
        a_results = []
        b_results = []
        bus.subscribe("event_a", lambda d: a_results.append(d))
        bus.subscribe("event_b", lambda d: b_results.append(d))
        bus.publish("event_a", 1)
        bus.publish("event_b", 2)
        assert a_results == [1]
        assert b_results == [2]

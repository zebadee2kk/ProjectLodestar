import pytest
import os
import shutil
from modules.routing.cache import CacheManager

class TestCacheManager:
    TEST_DB = ".lodestar/test_cache.db"

    @pytest.fixture
    def cache(self):
        if os.path.exists(".lodestar"):
            shutil.rmtree(".lodestar")
        cache = CacheManager(db_path=self.TEST_DB)
        yield cache
        cache.close()
        if os.path.exists(".lodestar"):
            shutil.rmtree(".lodestar")

    def test_set_get(self, cache):
        model = "gpt-4o"
        messages = [{"role": "user", "content": "hi"}]
        response = {"output": "hello"}
        
        cache.set(model, messages, response)
        
        result = cache.get(model, messages)
        assert result == response

    def test_cache_miss(self, cache):
        result = cache.get("gpt-4o", [{"role": "user", "content": "unknown"}])
        assert result is None

    def test_clear(self, cache):
        cache.set("model", [], {})
        assert cache.stats()["entries"] == 1
        
        cache.clear()
        assert cache.stats()["entries"] == 0

    def test_ttl(self, cache):
        # Set super short TTL
        cache.ttl_seconds = 0.1
        cache.set("model", [], {})
        
        import time
        time.sleep(0.2)
        
        result = cache.get("model", [])
        assert result is None

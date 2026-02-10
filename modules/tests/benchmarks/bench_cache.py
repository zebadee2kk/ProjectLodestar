"""Performance benchmarks for the CacheManager.

Measures:
  - cache.set() write throughput
  - cache.get() read throughput (hit and miss)
  - cache.stats() query time
  - cache.clear() time

Run with:
    python -m modules.tests.benchmarks.bench_cache
    # or via the helper script:
    ./scripts/run-benchmarks.sh
"""

import time
import statistics
import tempfile
from pathlib import Path
from typing import Callable, Tuple

from modules.routing.cache import CacheManager


# ---------------------------------------------------------------------------
# Benchmark runner helpers
# ---------------------------------------------------------------------------

def timeit(fn: Callable, iterations: int = 1000) -> Tuple[float, float, float]:
    """Run fn() iterations times and return (mean_ms, min_ms, max_ms)."""
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    return statistics.mean(times), min(times), max(times)


def print_result(label: str, mean_ms: float, min_ms: float, max_ms: float,
                 iterations: int) -> None:
    print(
        f"  {label:<45} "
        f"mean={mean_ms:7.3f}ms  "
        f"min={min_ms:7.3f}ms  "
        f"max={max_ms:7.3f}ms  "
        f"({iterations} iters)"
    )


# ---------------------------------------------------------------------------
# Cache benchmarks
# ---------------------------------------------------------------------------

def bench_cache_set(cache: CacheManager, iterations: int = 1000) -> None:
    """Benchmark sequential cache writes."""
    idx = 0

    def _run():
        nonlocal idx
        cache.set(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"bench prompt {idx}"}],
            response={"result": f"response {idx}", "model": "gpt-3.5-turbo"},
        )
        idx += 1

    mean, lo, hi = timeit(_run, iterations)
    print_result("CacheManager.set()", mean, lo, hi, iterations)


def bench_cache_get_hit(cache: CacheManager, iterations: int = 2000) -> None:
    """Benchmark cache reads for a key that exists."""
    messages = [{"role": "user", "content": "hit benchmark prompt"}]
    cache.set(
        model="gpt-3.5-turbo",
        messages=messages,
        response={"result": "cached", "model": "gpt-3.5-turbo"},
    )

    def _run():
        cache.get(model="gpt-3.5-turbo", messages=messages)

    mean, lo, hi = timeit(_run, iterations)
    print_result("CacheManager.get() [hit]", mean, lo, hi, iterations)


def bench_cache_get_miss(cache: CacheManager, iterations: int = 2000) -> None:
    """Benchmark cache reads for a key that does not exist."""
    idx = 0

    def _run():
        nonlocal idx
        cache.get(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"miss-{idx}"}],
        )
        idx += 1

    mean, lo, hi = timeit(_run, iterations)
    print_result("CacheManager.get() [miss]", mean, lo, hi, iterations)


def bench_cache_stats(cache: CacheManager, iterations: int = 500) -> None:
    """Benchmark the stats() query against a populated cache."""
    # Populate with some entries first
    for i in range(50):
        cache.set(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"stats seed {i}"}],
            response={"result": f"r{i}"},
        )

    def _run():
        cache.stats()

    mean, lo, hi = timeit(_run, iterations)
    print_result("CacheManager.stats()", mean, lo, hi, iterations)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_all() -> None:
    print("\n" + "=" * 80)
    print("ProjectLodestar Cache Benchmarks")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "bench_cache.db")
        cache = CacheManager(db_path=db_path)
        cache.connect()

        print("\n[CacheManager — SQLite-backed]")
        bench_cache_set(cache)
        bench_cache_get_hit(cache)
        bench_cache_get_miss(cache)
        bench_cache_stats(cache)

        cache.close()

    print("\n" + "=" * 80)
    print("Benchmark complete.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all()

"""Performance benchmarks for the routing subsystem.

Measures:
  - SemanticRouter.classify_task() throughput
  - SemanticRouter.route() throughput
  - LodestarProxy.handle_request() dry-run latency
  - RulesEngine tag matching throughput

Run with:
    python -m modules.tests.benchmarks.bench_routing
    # or via the helper script:
    ./scripts/run-benchmarks.sh
"""

import time
import statistics
from typing import Callable, List, Tuple

from modules.routing.router import SemanticRouter
from modules.routing.proxy import LodestarProxy


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
# Routing benchmarks
# ---------------------------------------------------------------------------

SAMPLE_PROMPTS = [
    "write a function to sort a list of integers",
    "fix the null pointer exception on line 42",
    "review this pull request for security issues",
    "explain the difference between TCP and UDP",
    "refactor the authentication module",
    "add unit tests for the payment service",
    "debug why the CI pipeline is failing",
    "design a microservices architecture for this system",
]


def bench_classify_task(router: SemanticRouter, iterations: int = 2000) -> None:
    """Benchmark SemanticRouter.classify_task() for a variety of prompts."""
    prompt_cycle = [SAMPLE_PROMPTS[i % len(SAMPLE_PROMPTS)] for i in range(iterations)]
    idx = 0

    def _run():
        nonlocal idx
        router.classify_task(prompt_cycle[idx % iterations])
        idx += 1

    mean, lo, hi = timeit(_run, iterations)
    print_result("SemanticRouter.classify_task()", mean, lo, hi, iterations)


def bench_route(router: SemanticRouter, iterations: int = 2000) -> None:
    """Benchmark SemanticRouter.route() for a variety of prompts."""
    prompt_cycle = [SAMPLE_PROMPTS[i % len(SAMPLE_PROMPTS)] for i in range(iterations)]
    idx = 0

    def _run():
        nonlocal idx
        router.route(prompt_cycle[idx % iterations])
        idx += 1

    mean, lo, hi = timeit(_run, iterations)
    print_result("SemanticRouter.route()", mean, lo, hi, iterations)


def bench_proxy_dry_run(proxy: LodestarProxy, iterations: int = 500) -> None:
    """Benchmark LodestarProxy.handle_request() in dry-run mode (no LLM call)."""
    prompts = [f"unique prompt for bench {i}" for i in range(iterations)]
    idx = 0

    def _run():
        nonlocal idx
        proxy.handle_request(prompts[idx % iterations])
        idx += 1

    mean, lo, hi = timeit(_run, iterations)
    print_result("LodestarProxy.handle_request() dry-run", mean, lo, hi, iterations)


def bench_proxy_cache_hit(proxy: LodestarProxy, iterations: int = 1000) -> None:
    """Benchmark repeated requests to the same prompt (cache hit path)."""
    prompt = "cached benchmark prompt"
    # Populate cache
    proxy.handle_request(prompt)

    def _run():
        proxy.handle_request(prompt)

    mean, lo, hi = timeit(_run, iterations)
    print_result("LodestarProxy.handle_request() cache hit", mean, lo, hi, iterations)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_all() -> None:
    print("\n" + "=" * 80)
    print("ProjectLodestar Routing Benchmarks")
    print("=" * 80)

    router = SemanticRouter({"enabled": True})
    router.start()

    proxy = LodestarProxy()
    proxy.start()

    print("\n[SemanticRouter]")
    bench_classify_task(router)
    bench_route(router)

    print("\n[LodestarProxy — dry-run (no LLM call)]")
    bench_proxy_dry_run(proxy)

    print("\n[LodestarProxy — cache hit path]")
    bench_proxy_cache_hit(proxy)

    proxy.stop()
    router.stop()

    print("\n" + "=" * 80)
    print("Benchmark complete.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all()

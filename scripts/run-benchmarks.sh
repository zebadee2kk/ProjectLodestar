#!/bin/bash
# run-benchmarks.sh — Run all ProjectLodestar performance benchmarks
#
# Usage:
#   ./scripts/run-benchmarks.sh           # Run all benchmarks
#   ./scripts/run-benchmarks.sh routing   # Run routing benchmarks only
#   ./scripts/run-benchmarks.sh cache     # Run cache benchmarks only
#
# Results are printed to stdout and optionally saved to .lodestar/benchmarks/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Ensure we run from project root
cd "$PROJECT_DIR"

PYTHON="${PYTHON:-/usr/bin/python3}"

# Create benchmark results directory if it doesn't exist
RESULTS_DIR=".lodestar/benchmarks"
mkdir -p "$RESULTS_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RESULTS_FILE="$RESULTS_DIR/bench_${TIMESTAMP}.txt"

echo "ProjectLodestar Performance Benchmarks"
echo "======================================="
echo "Timestamp: $(date)"
echo "Python: $($PYTHON --version)"
echo ""

run_benchmark() {
    local module="$1"
    local name="$2"
    echo "Running $name benchmark..."
    $PYTHON -m "modules.tests.benchmarks.$module" 2>&1
}

TARGET="${1:-all}"

case "$TARGET" in
    routing)
        run_benchmark bench_routing "routing" | tee -a "$RESULTS_FILE"
        ;;
    cache)
        run_benchmark bench_cache "cache" | tee -a "$RESULTS_FILE"
        ;;
    all|*)
        run_benchmark bench_routing "routing" | tee -a "$RESULTS_FILE"
        run_benchmark bench_cache "cache" | tee -a "$RESULTS_FILE"
        ;;
esac

echo ""
echo "Results saved to: $RESULTS_FILE"

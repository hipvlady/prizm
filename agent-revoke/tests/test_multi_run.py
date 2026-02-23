# Copyright (c) 2026 Prizm contributors.
"""Tests for multi-run statistical aggregation."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.simulation.aggregation import AggregatedMetrics
from src.simulation.metrics import SimulationMetrics


@pytest.fixture()
def scenarios_path():
    return Path(__file__).parent.parent / "scenarios"


def _make_metrics(
    strategy: str = "eager",
    unauthorized: int = 100,
    staleness_max: int = 5,
    p50: float = 3.0,
    p99: float = 8.0,
    messages: int = 10,
    revalidation: int = 0,
    convergence: float = 5.0,
    wall_time: float = 0.01,
    by_depth: dict[int, int] | None = None,
    bound_violations: dict[int, int] | None = None,
) -> SimulationMetrics:
    """Build a SimulationMetrics with controllable values."""
    return SimulationMetrics(
        scenario="test-scenario",
        strategy=strategy,
        total_ticks=100,
        total_actions=1000,
        unauthorized_actions_count=unauthorized,
        unauthorized_actions_by_depth=by_depth or {0: unauthorized},
        revocation_latency_p50=p50,
        revocation_latency_p99=p99,
        staleness_window_max=staleness_max,
        message_overhead=messages,
        revalidation_count=revalidation,
        convergence_time=convergence,
        wall_time_seconds=wall_time,
        bound_violations_by_depth=bound_violations or {},
    )


class TestAggregatedMetrics:
    def test_single_run_std_zero(self):
        """A single run should produce std = 0."""
        runs = [_make_metrics(unauthorized=500)]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.unauthorized_ops_mean == 500.0
        assert agg.unauthorized_ops_std == 0.0
        assert agg.num_runs == 1

    def test_identical_runs_std_zero(self):
        """Identical runs should produce std = 0 (deterministic strategy)."""
        runs = [_make_metrics(strategy="exec_count", unauthorized=50) for _ in range(10)]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.unauthorized_ops_mean == 50.0
        assert agg.unauthorized_ops_std == 0.0
        assert agg.num_runs == 10

    def test_varying_runs_nonzero_std(self):
        """Runs with different values should have nonzero std."""
        runs = [
            _make_metrics(unauthorized=100, staleness_max=5),
            _make_metrics(unauthorized=200, staleness_max=10),
        ]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.unauthorized_ops_mean == 150.0
        assert agg.unauthorized_ops_std == 50.0  # pstdev([100, 200]) = 50
        assert agg.staleness_max_mean == 7.5
        assert agg.staleness_max_std == 2.5

    def test_seed_range_formatting(self):
        """seed_range should reflect the provided start."""
        runs = [_make_metrics() for _ in range(5)]
        agg = AggregatedMetrics.from_runs(runs, seed_start=3)
        assert agg.seed_range == "3-7"

    def test_per_depth_aggregation(self):
        """Per-depth unauthorized counts should aggregate correctly."""
        runs = [
            _make_metrics(by_depth={0: 100, 1: 50}),
            _make_metrics(by_depth={0: 200, 1: 50, 2: 10}),
        ]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.unauthorized_by_depth_mean[0] == 150.0
        assert agg.unauthorized_by_depth_std[0] == 50.0
        assert agg.unauthorized_by_depth_mean[1] == 50.0
        assert agg.unauthorized_by_depth_std[1] == 0.0
        # Depth 2 only appears in one run; the other defaults to 0
        assert agg.unauthorized_by_depth_mean[2] == 5.0
        assert agg.unauthorized_by_depth_std[2] == 5.0

    def test_bound_violations_summed(self):
        """Bound violations should sum across all runs."""
        runs = [
            _make_metrics(bound_violations={0: 1}),
            _make_metrics(bound_violations={0: 2, 1: 1}),
        ]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.total_bound_violations == 4

    def test_format_metric_zero_std(self):
        """format_metric should show +/- 0 for zero std."""
        agg = AggregatedMetrics.from_runs([_make_metrics()])
        assert agg.format_metric(50.0, 0.0) == "50.0 +/- 0"

    def test_format_metric_nonzero_std(self):
        """format_metric should show +/- sigma."""
        agg = AggregatedMetrics.from_runs([_make_metrics()])
        assert agg.format_metric(50.0, 3.5) == "50.0 +/- 3.5"

    def test_empty_runs_raises(self):
        """Aggregating zero runs should raise."""
        with pytest.raises(ValueError, match="zero"):
            AggregatedMetrics.from_runs([])


class TestMultiRunIntegration:
    """Integration tests that actually run the simulation engine multiple times."""

    def test_exec_count_deterministic_across_seeds(self, scenarios_path):
        """exec_count unauthorized ops should be identical across seeds (sigma = 0)."""
        crm_path = scenarios_path / "crm-bulk-ops.yaml"
        if not crm_path.exists():
            pytest.skip("CRM scenario not available")

        from scripts.run_strategy_comparison import run_single

        runs = [run_single(crm_path, "exec_count", seed=s) for s in range(3)]
        agg = AggregatedMetrics.from_runs(runs)
        assert agg.unauthorized_ops_std == 0.0, (
            f"exec_count should be deterministic but got std={agg.unauthorized_ops_std}"
        )

    def test_single_run_backward_compat(self, scenarios_path):
        """Single-run (no --runs) should produce identical output to the legacy path."""
        crm_path = scenarios_path / "crm-bulk-ops.yaml"
        if not crm_path.exists():
            pytest.skip("CRM scenario not available")

        from scripts.run_strategy_comparison import run_comparison

        metrics = run_comparison(crm_path, ("eager",))
        assert len(metrics) == 1
        assert metrics[0].strategy == "eager"
        assert metrics[0].unauthorized_actions_count >= 0


class TestJsonOutput:
    """Test JSON serialization of aggregated results."""

    def test_save_and_load_json(self, tmp_path):
        from scripts.run_strategy_comparison import save_aggregated_json

        runs_eager = [_make_metrics(strategy="eager", unauthorized=500) for _ in range(3)]
        runs_exec = [_make_metrics(strategy="exec_count", unauthorized=50) for _ in range(3)]
        aggregated = [
            AggregatedMetrics.from_runs(runs_eager, seed_start=0),
            AggregatedMetrics.from_runs(runs_exec, seed_start=0),
        ]

        json_path = tmp_path / "test.json"
        save_aggregated_json(aggregated, json_path)

        data = json.loads(json_path.read_text())
        assert data["methodology"]["runs_per_config"] == 3
        assert data["methodology"]["std_type"] == "population (pstdev)"
        assert len(data["results"]) == 2
        assert data["results"][0]["strategy"] == "eager"
        assert data["results"][0]["unauthorized_ops"]["mean"] == 500.0
        assert data["results"][0]["unauthorized_ops"]["std"] == 0.0
        assert data["results"][1]["strategy"] == "exec_count"

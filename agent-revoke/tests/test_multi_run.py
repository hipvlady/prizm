# Copyright (c) 2026 Prizm contributors.
"""Tests for multi-run strategy comparison aggregation."""

from pathlib import Path
import subprocess
import sys

import yaml

from scripts.run_strategy_comparison import build_dashboard_payload, run_comparison
from src.output.report import generate_aggregated_comparison_report
from src.simulation.aggregation import aggregate_comparison_runs


def _write_tiny_scenario(path: Path) -> None:
    scenario = {
        "simulation": {
            "duration_ticks": 4,
            "agents": 2,
            "actions_per_tick": 1,
            "latency_ticks": 1,
            "transient_timeout_ticks": 10,
        },
        "scenario": {
            "name": "tiny",
            "delegation_depth": 1,
            "cascade_revocation": False,
            "revocation_trigger_tick": 1,
        },
        "strategies": {
            "lazy": {"check_interval_ticks": 2},
            "lease": {"default_ttl_ticks": 5},
            "exec_count": {"max_operations": 3},
        },
        "trust": {
            "initial_score": 0.8,
            "anomaly_threshold": 0.4,
            "score_decay_on_anomaly": 0.3,
        },
        "delegation": {
            "max_depth": 3,
            "require_scope_subset": True,
            "propagate_remaining_ops": True,
        },
    }
    path.write_text(yaml.safe_dump(scenario), encoding="utf-8")


def test_run_comparison_supports_multiple_runs(tmp_path: Path) -> None:
    scenario_path = tmp_path / "tiny.yaml"
    _write_tiny_scenario(scenario_path)

    metrics_by_strategy = run_comparison(
        scenario_path,
        ("eager", "exec_count"),
        runs=2,
        seed_start=10,
    )

    assert set(metrics_by_strategy.keys()) == {"eager", "exec_count"}
    assert len(metrics_by_strategy["eager"]) == 2
    assert len(metrics_by_strategy["exec_count"]) == 2
    assert all(m.strategy == "eager" for m in metrics_by_strategy["eager"])
    assert all(m.strategy == "exec_count" for m in metrics_by_strategy["exec_count"])


def test_aggregate_comparison_report_includes_run_metadata(tmp_path: Path) -> None:
    scenario_path = tmp_path / "tiny.yaml"
    _write_tiny_scenario(scenario_path)
    metrics_by_strategy = run_comparison(
        scenario_path,
        ("eager", "lazy"),
        runs=2,
        seed_start=5,
    )
    aggregated = aggregate_comparison_runs(metrics_by_strategy)

    html = generate_aggregated_comparison_report(
        aggregated,
        scenario=str(scenario_path),
        seed_start=5,
        template_dir=str(Path(__file__).resolve().parent.parent / "src" / "output" / "templates"),
    )

    assert "comparison (aggregated)" in html
    assert "Runs:</strong> 2" in html
    assert "seed=5..6" in html
    assert "±" in html


def test_comparison_script_accepts_runs_and_seed_start(tmp_path: Path) -> None:
    scenario_path = tmp_path / "tiny.yaml"
    report_path = tmp_path / "tiny-report.html"
    _write_tiny_scenario(scenario_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_strategy_comparison.py",
            "--scenario",
            str(scenario_path),
            "--output",
            str(report_path),
            "--strategies",
            "eager,lazy",
            "--runs",
            "2",
            "--seed-start",
            "3",
        ],
        cwd=str(Path(__file__).resolve().parent.parent),
        check=True,
        capture_output=True,
        text=True,
    )

    assert report_path.exists()
    report_html = report_path.read_text(encoding="utf-8")
    assert "Runs:</strong> 2" in report_html
    assert "seed=3..4" in report_html
    assert "comparison (aggregated)" in report_html
    assert "Runs per strategy: 2" in result.stdout


def test_build_dashboard_payload_has_expected_shape(tmp_path: Path) -> None:
    scenario_path = tmp_path / "tiny.yaml"
    _write_tiny_scenario(scenario_path)
    metrics_by_strategy = run_comparison(
        scenario_path,
        ("eager", "lazy"),
        runs=2,
        seed_start=11,
    )
    payload = build_dashboard_payload(
        scenario_path=scenario_path,
        strategies=("eager", "lazy"),
        runs=2,
        seed_start=11,
        metrics_by_strategy=metrics_by_strategy,
    )

    assert payload["version"] == "1.0"
    assert payload["scenario"].endswith("tiny.yaml")
    assert payload["runs_per_strategy"] == 2
    assert payload["seed_start"] == 11
    assert payload["seed_end"] == 12
    assert len(payload["aggregated"]) == 2
    assert set(payload["runs"].keys()) == {"eager", "lazy"}
    assert len(payload["runs"]["eager"]) == 2


def test_comparison_script_writes_dashboard_json(tmp_path: Path) -> None:
    scenario_path = tmp_path / "tiny.yaml"
    report_path = tmp_path / "tiny-report.html"
    json_path = tmp_path / "tiny-dashboard.json"
    _write_tiny_scenario(scenario_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_strategy_comparison.py",
            "--scenario",
            str(scenario_path),
            "--output",
            str(report_path),
            "--json-output",
            str(json_path),
            "--strategies",
            "eager,lazy",
            "--runs",
            "2",
            "--seed-start",
            "3",
        ],
        cwd=str(Path(__file__).resolve().parent.parent),
        check=True,
        capture_output=True,
        text=True,
    )

    assert report_path.exists()
    assert json_path.exists()
    payload = yaml.safe_load(json_path.read_text(encoding="utf-8"))
    assert payload["runs_per_strategy"] == 2
    assert payload["seed_start"] == 3
    assert "aggregated" in payload
    assert "runs" in payload
    assert "Dashboard JSON:" in result.stdout

#!/usr/bin/env python3
# Copyright (c) 2026 Prizm contributors.
"""Run all strategies for a scenario and emit one comparison report.

Supports multi-run statistical aggregation via --runs N --seed-start S.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.logging_utils import configure_logging
from src.output.report import (
    generate_aggregated_comparison_report,
    generate_strategy_comparison_report,
    save_report,
)
from src.simulation.aggregation import AggregatedMetrics
from src.simulation.engine import SimulationEngine
from src.simulation.metrics import SimulationMetrics

DEFAULT_STRATEGIES = ("eager", "lazy", "lease", "exec_count")


def run_single(scenario_path: Path, strategy: str, seed: int) -> SimulationMetrics:
    """Run one strategy with one seed.

    Parameters
    ----------
    scenario_path : Path
        Scenario YAML file.
    strategy : str
        Strategy name.
    seed : int
        RNG seed to inject into the config.

    Returns
    -------
    SimulationMetrics
        Metrics from the single run.
    """
    with scenario_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["simulation"]["seed"] = seed
    engine = SimulationEngine(config, strategy, str(scenario_path))
    return engine.run()


def run_comparison(scenario_path: Path, strategies: tuple[str, ...]):
    """Execute each strategy and collect metrics (single-run, legacy mode).

    Parameters
    ----------
    scenario_path : Path
        Scenario file path.
    strategies : tuple[str, ...]
        Strategy names to run.

    Returns
    -------
    list[SimulationMetrics]
        Metrics in strategy order.
    """
    with scenario_path.open("r", encoding="utf-8") as f:
        base_config = yaml.safe_load(f)

    metrics_list = []
    for strategy in strategies:
        config = copy.deepcopy(base_config)
        engine = SimulationEngine(config, strategy, str(scenario_path))
        metrics = engine.run()
        metrics_list.append(metrics)
    return metrics_list


def save_aggregated_json(
    aggregated: list[AggregatedMetrics],
    path: Path,
) -> None:
    """Save aggregated results as JSON for paper table generation.

    Parameters
    ----------
    aggregated : list[AggregatedMetrics]
        Aggregated metrics per strategy.
    path : Path
        Output JSON path.
    """
    data = {
        "methodology": {
            "runs_per_config": aggregated[0].num_runs if aggregated else 0,
            "seed_range": aggregated[0].seed_range if aggregated else "",
            "std_type": "population (pstdev)",
        },
        "results": [
            {
                "scenario": agg.scenario,
                "strategy": agg.strategy,
                "unauthorized_ops": {
                    "mean": agg.unauthorized_ops_mean,
                    "std": agg.unauthorized_ops_std,
                },
                "staleness_max": {
                    "mean": agg.staleness_max_mean,
                    "std": agg.staleness_max_std,
                },
                "latency_p50": {
                    "mean": agg.latency_p50_mean,
                    "std": agg.latency_p50_std,
                },
                "latency_p99": {
                    "mean": agg.latency_p99_mean,
                    "std": agg.latency_p99_std,
                },
                "convergence": {
                    "mean": agg.convergence_mean,
                    "std": agg.convergence_std,
                },
                "messages": {
                    "mean": agg.messages_mean,
                    "std": agg.messages_std,
                },
                "revalidation": {
                    "mean": agg.revalidation_mean,
                    "std": agg.revalidation_std,
                },
                "wall_time_s": {
                    "mean": agg.wall_time_mean,
                    "std": agg.wall_time_std,
                },
                "unauthorized_by_depth": {
                    str(d): {
                        "mean": agg.unauthorized_by_depth_mean[d],
                        "std": agg.unauthorized_by_depth_std[d],
                    }
                    for d in sorted(agg.unauthorized_by_depth_mean.keys())
                },
                "bound_violations": agg.total_bound_violations,
            }
            for agg in aggregated
        ],
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> None:
    """Parse CLI arguments and generate comparison report."""
    parser = argparse.ArgumentParser(
        description="Run all strategies for a scenario and emit one comparison HTML report."
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to scenario yaml file (for example scenarios/crm-bulk-ops.yaml).",
    )
    parser.add_argument(
        "--output",
        default="comparison-report.html",
        help="Output HTML report path.",
    )
    parser.add_argument(
        "--strategies",
        default=",".join(DEFAULT_STRATEGIES),
        help="Comma-separated strategy list. Default: eager,lazy,lease,exec_count",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per strategy. Seeds will be seed-start through seed-start+runs-1.",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=0,
        help="Starting seed for multi-run mode (default: 0).",
    )
    args = parser.parse_args()

    configure_logging(getattr(logging, args.log_level))

    scenario_path = Path(args.scenario)
    output_path = Path(args.output)
    strategies = tuple(s.strip() for s in args.strategies.split(",") if s.strip())
    num_runs = args.runs
    seed_start = args.seed_start

    if num_runs == 1:
        # Legacy single-run mode (backward compatible)
        metrics_list = run_comparison(scenario_path, strategies)
        html = generate_strategy_comparison_report(metrics_list)
        save_report(html, output_path)

        print(f"Scenario: {scenario_path}")
        print(f"Strategies: {', '.join(strategies)}")
        print(f"Report: {output_path}")
        for m in metrics_list:
            print(
                f"- {m.strategy}: unauthorized={m.unauthorized_actions_count}, "
                f"staleness_max={m.staleness_window_max}, p50={m.revocation_latency_p50}, "
                f"wall_s={m.wall_time_seconds:.6f}"
            )
    else:
        # Multi-run aggregation mode
        all_runs: dict[str, list[SimulationMetrics]] = {s: [] for s in strategies}

        for seed in range(seed_start, seed_start + num_runs):
            print(f"Run {seed - seed_start + 1}/{num_runs} (seed={seed})")
            for strategy in strategies:
                metrics = run_single(scenario_path, strategy, seed)
                all_runs[strategy].append(metrics)

        aggregated = [
            AggregatedMetrics.from_runs(all_runs[s], seed_start=seed_start)
            for s in strategies
        ]

        html = generate_aggregated_comparison_report(aggregated)
        save_report(html, output_path)

        json_path = output_path.with_suffix(".json")
        save_aggregated_json(aggregated, json_path)

        print(f"\nScenario: {scenario_path}")
        print(f"Strategies: {', '.join(strategies)}")
        print(f"Runs: {num_runs} (seeds {seed_start}-{seed_start + num_runs - 1})")
        print(f"Report: {output_path}")
        print(f"JSON: {json_path}")
        print()
        for agg in aggregated:
            print(
                f"- {agg.strategy}: "
                f"unauthorized={agg.format_metric(agg.unauthorized_ops_mean, agg.unauthorized_ops_std)}, "
                f"staleness_max={agg.format_metric(agg.staleness_max_mean, agg.staleness_max_std)}, "
                f"bound_violations={agg.total_bound_violations}"
            )


if __name__ == "__main__":
    main()

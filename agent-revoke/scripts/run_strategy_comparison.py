#!/usr/bin/env python3
# Copyright (c) 2026 Prizm contributors.
"""Run all strategies for a scenario and emit one comparison report."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.logging_utils import configure_logging
from src.output.report import (
    generate_aggregated_comparison_report,
    generate_strategy_comparison_report,
    save_report,
)
from src.simulation.aggregation import aggregate_comparison_runs
from src.simulation.engine import SimulationEngine
from src.simulation.scenarios import load_scenario

DEFAULT_STRATEGIES = ("eager", "lazy", "lease", "exec_count")


def run_comparison(
    scenario_path: Path,
    strategies: tuple[str, ...],
    *,
    runs: int = 1,
    seed_start: int = 0,
):
    """Execute each strategy and collect metrics.

    Parameters
    ----------
    scenario_path : Path
        Scenario file path.
    strategies : tuple[str, ...]
        Strategy names to run.
    runs : int, optional
        Number of runs per strategy.
    seed_start : int, optional
        First seed to use. Subsequent runs increment by 1.

    Returns
    -------
    dict[str, list[SimulationMetrics]]
        Metrics grouped by strategy.
    """
    base_config = load_scenario(str(scenario_path))

    metrics_by_strategy = {}
    for strategy in strategies:
        strategy_runs = []
        for run_idx in range(runs):
            config = copy.deepcopy(base_config)
            config.setdefault("simulation", {})
            config["simulation"]["seed"] = seed_start + run_idx
            engine = SimulationEngine(config, strategy, str(scenario_path))
            metrics = engine.run()
            strategy_runs.append(metrics)
        metrics_by_strategy[strategy] = strategy_runs
    return metrics_by_strategy


def build_dashboard_payload(
    *,
    scenario_path: Path,
    strategies: tuple[str, ...],
    runs: int,
    seed_start: int,
    metrics_by_strategy: dict,
) -> dict:
    """Build JSON payload consumed by the interactive dashboard."""
    aggregated = aggregate_comparison_runs(metrics_by_strategy)
    serialized_runs = {
        strategy: [dataclasses.asdict(item) for item in items]
        for strategy, items in metrics_by_strategy.items()
    }
    serialized_aggregated = [dataclasses.asdict(item) for item in aggregated]
    return {
        "version": "1.0",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "scenario": str(scenario_path),
        "strategies": list(strategies),
        "runs_per_strategy": runs,
        "seed_start": seed_start,
        "seed_end": seed_start + runs - 1,
        "aggregated": serialized_aggregated,
        "runs": serialized_runs,
    }


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
        help="Runs per strategy (seeds: seed-start to seed-start+runs-1).",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=0,
        help="Start seed used for repeated strategy runs.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON output path for the React dashboard dataset.",
    )
    args = parser.parse_args()

    configure_logging(getattr(logging, args.log_level))

    scenario_path = Path(args.scenario)
    output_path = Path(args.output)
    strategies = tuple(s.strip() for s in args.strategies.split(",") if s.strip())

    metrics_by_strategy = run_comparison(
        scenario_path,
        strategies,
        runs=max(1, args.runs),
        seed_start=args.seed_start,
    )
    if args.runs > 1:
        aggregated = aggregate_comparison_runs(metrics_by_strategy)
        html = generate_aggregated_comparison_report(
            aggregated,
            scenario=str(scenario_path),
            seed_start=args.seed_start,
        )
    else:
        metrics_list = [metrics_by_strategy[s][0] for s in strategies]
        html = generate_strategy_comparison_report(metrics_list)
    save_report(html, output_path)

    if args.json_output:
        payload = build_dashboard_payload(
            scenario_path=scenario_path,
            strategies=strategies,
            runs=max(1, args.runs),
            seed_start=args.seed_start,
            metrics_by_strategy=metrics_by_strategy,
        )
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Scenario: {scenario_path}")
    print(f"Strategies: {', '.join(strategies)}")
    print(f"Runs per strategy: {max(1, args.runs)}")
    print(f"Seed range: {args.seed_start}..{args.seed_start + max(1, args.runs) - 1}")
    print(f"Report: {output_path}")
    if args.json_output:
        print(f"Dashboard JSON: {args.json_output}")
    if args.runs > 1:
        for item in aggregate_comparison_runs(metrics_by_strategy):
            print(
                f"- {item.strategy}: unauthorized={item.unauthorized_mean:.2f} ± {item.unauthorized_std:.2f}, "
                f"staleness_max={item.staleness_max_mean:.2f} ± {item.staleness_max_std:.2f}, "
                f"p50={item.p50_mean:.2f} ± {item.p50_std:.2f}"
            )
    else:
        for strategy in strategies:
            m = metrics_by_strategy[strategy][0]
            print(
                f"- {m.strategy}: unauthorized={m.unauthorized_actions_count}, "
                f"staleness_max={m.staleness_window_max}, p50={m.revocation_latency_p50}, "
                f"wall_s={m.wall_time_seconds:.6f}"
            )


if __name__ == "__main__":
    main()

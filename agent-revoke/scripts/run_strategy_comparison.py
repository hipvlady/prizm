#!/usr/bin/env python3
# Copyright (c) 2026 Prizm contributors.
"""Run all strategies for a scenario and emit one comparison report."""

from __future__ import annotations

import argparse
import copy
import logging
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.logging_utils import configure_logging
from src.output.report import generate_strategy_comparison_report, save_report
from src.simulation.engine import SimulationEngine

DEFAULT_STRATEGIES = ("eager", "lazy", "lease", "exec_count")


def run_comparison(scenario_path: Path, strategies: tuple[str, ...]):
    """Execute each strategy and collect metrics.

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
    args = parser.parse_args()

    configure_logging(getattr(logging, args.log_level))

    scenario_path = Path(args.scenario)
    output_path = Path(args.output)
    strategies = tuple(s.strip() for s in args.strategies.split(",") if s.strip())

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


if __name__ == "__main__":
    main()

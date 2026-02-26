# Copyright (c) 2026 Prizm contributors.
"""HTML report generation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.simulation.aggregation import AggregatedMetrics


def _format_mean_std(mean: float, std: float, precision: int = 2) -> str:
    """Format an aggregated value as 'mean ± std'."""
    return f"{mean:.{precision}f} ± {std:.{precision}f}"


def _get_template(env: Environment, preferred: str):
    """Load template with fallback to legacy single-template file."""
    try:
        return env.get_template(preferred)
    except Exception:
        return env.get_template("report_template.html")


def generate_html_report(metrics, template_dir: str = "src/output/templates"):
    """Generate HTML for either single-strategy or comparison reporting.

    Parameters
    ----------
    metrics : SimulationMetrics | Sequence[SimulationMetrics]
        Metrics payload.
    template_dir : str, optional
        Template directory path.

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    template = _get_template(env, "report.html.j2")

    if isinstance(metrics, Sequence) and not isinstance(metrics, (str, bytes)):
        return generate_strategy_comparison_report(list(metrics), template_dir=template_dir)

    return template.render(
        scenario=metrics.scenario,
        strategy=metrics.strategy,
        unauthorized_ops=metrics.unauthorized_actions_count,
        p50_latency=metrics.revocation_latency_p50,
        p99_latency=metrics.revocation_latency_p99,
        convergence_time=metrics.convergence_time,
        chart_labels=["Unauthorized Ops", "P50 Latency", "P99 Latency", "Convergence Time"],
        chart_values=[
            metrics.unauthorized_actions_count,
            metrics.revocation_latency_p50,
            metrics.revocation_latency_p99,
            metrics.convergence_time,
        ],
        comparison_rows=[],
        depth_rows=[],
        clock_rows=[],
        bound_rows=[{"depth": depth, "count": count} for depth, count in sorted(metrics.bound_violations_by_depth.items())],
        num_runs=1,
        seed_range=None,
    )


def generate_strategy_comparison_report(metrics_list, template_dir: str = "src/output/templates"):
    """Generate a multi-strategy comparison report.

    Parameters
    ----------
    metrics_list : list[SimulationMetrics]
        Strategy metrics to compare.
    template_dir : str, optional
        Template directory path.

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    template = _get_template(env, "comparison.html.j2")

    scenario = metrics_list[0].scenario if metrics_list else "comparison"
    labels = [m.strategy for m in metrics_list]
    unauthorized_values = [m.unauthorized_actions_count for m in metrics_list]

    all_depths = sorted({d for m in metrics_list for d in m.unauthorized_actions_by_depth.keys()})
    depth_rows = [
        {
            "depth": depth,
            "counts": {m.strategy: m.unauthorized_actions_by_depth.get(depth, 0) for m in metrics_list},
        }
        for depth in all_depths
    ]

    comparison_rows = [
        {
            "strategy": m.strategy,
            "unauthorized": m.unauthorized_actions_count,
            "p50": m.revocation_latency_p50,
            "p99": m.revocation_latency_p99,
            "staleness_max": m.staleness_window_max,
            "convergence": m.convergence_time,
            "message_overhead": m.message_overhead,
            "revalidations": m.revalidation_count,
            "timeouts": m.transient_state_timeouts,
            "wall_time_seconds": m.wall_time_seconds,
            "avg_tick_seconds": m.avg_tick_seconds,
        }
        for m in metrics_list
    ]

    clock_rows = [
        {"strategy": "eager", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lazy", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lease", "clock_dependent": "Yes", "robustness": "Fragile"},
        {"strategy": "exec_count", "clock_dependent": "No", "robustness": "High"},
    ]

    return template.render(
        scenario=scenario,
        strategy="comparison",
        unauthorized_ops=sum(unauthorized_values),
        p50_latency=0,
        p99_latency=0,
        convergence_time=0,
        chart_labels=labels,
        chart_values=unauthorized_values,
        comparison_rows=comparison_rows,
        depth_rows=depth_rows,
        clock_rows=clock_rows,
        bound_rows=[
            {
                "strategy": m.strategy,
                "violations": sum(m.bound_violations_by_depth.values()),
                "by_depth": dict(sorted(m.bound_violations_by_depth.items())),
            }
            for m in metrics_list
        ],
        num_runs=1,
        seed_range=None,
    )


def generate_aggregated_comparison_report(
    aggregated: list[AggregatedMetrics],
    *,
    scenario: str,
    seed_start: int,
    template_dir: str = "src/output/templates",
):
    """Generate a multi-run aggregated comparison report."""
    env = Environment(loader=FileSystemLoader(template_dir))
    template = _get_template(env, "aggregated.html.j2")

    labels = [item.strategy for item in aggregated]
    chart_values = [item.unauthorized_mean for item in aggregated]
    all_depths = sorted(
        {
            depth
            for item in aggregated
            for depth in item.unauthorized_by_depth_mean.keys()
        }
    )
    depth_rows = [
        {
            "depth": depth,
            "counts": {
                item.strategy: _format_mean_std(
                    item.unauthorized_by_depth_mean.get(depth, 0.0),
                    item.unauthorized_by_depth_std.get(depth, 0.0),
                )
                for item in aggregated
            },
        }
        for depth in all_depths
    ]

    comparison_rows = [
        {
            "strategy": item.strategy,
            "unauthorized": _format_mean_std(item.unauthorized_mean, item.unauthorized_std),
            "p50": _format_mean_std(item.p50_mean, item.p50_std),
            "p99": _format_mean_std(item.p99_mean, item.p99_std),
            "staleness_max": _format_mean_std(item.staleness_max_mean, item.staleness_max_std),
            "convergence": _format_mean_std(item.convergence_mean, item.convergence_std),
            "message_overhead": _format_mean_std(
                item.message_overhead_mean, item.message_overhead_std
            ),
            "revalidations": _format_mean_std(item.revalidations_mean, item.revalidations_std),
            "timeouts": _format_mean_std(
                item.transient_timeouts_mean, item.transient_timeouts_std
            ),
            "wall_time_seconds": "",
            "avg_tick_seconds": "",
        }
        for item in aggregated
    ]

    num_runs = aggregated[0].runs if aggregated else 0
    seed_end = seed_start + num_runs - 1 if num_runs > 0 else seed_start

    clock_rows = [
        {"strategy": "eager", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lazy", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lease", "clock_dependent": "Yes", "robustness": "Fragile"},
        {"strategy": "exec_count", "clock_dependent": "No", "robustness": "High"},
    ]

    return template.render(
        scenario=scenario,
        strategy="comparison (aggregated)",
        unauthorized_ops=round(sum(chart_values), 2),
        p50_latency=0,
        p99_latency=0,
        convergence_time=0,
        chart_labels=labels,
        chart_values=chart_values,
        comparison_rows=comparison_rows,
        depth_rows=depth_rows,
        clock_rows=clock_rows,
        bound_rows=[],
        num_runs=num_runs,
        seed_range=f"{seed_start}..{seed_end}",
    )


def save_report(report_html: str, output_path):
    """Persist an HTML report to file.

    Parameters
    ----------
    report_html : str
        HTML content.
    output_path : str | Path
        Destination path.
    """
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as f:
        f.write(report_html)

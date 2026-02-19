# Copyright (c) 2026 Prizm contributors.
"""HTML report generation helpers."""

from __future__ import annotations

from collections.abc import Sequence

from jinja2 import Environment, FileSystemLoader


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
    template = env.get_template("report_template.html")

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
    template = env.get_template("report_template.html")

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
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_html)

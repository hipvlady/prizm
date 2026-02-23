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


def generate_aggregated_comparison_report(
    aggregated_list,
    template_dir: str = "src/output/templates",
):
    """Generate a multi-strategy comparison report with mean +/- sigma.

    Parameters
    ----------
    aggregated_list : list[AggregatedMetrics]
        Aggregated metrics per strategy.
    template_dir : str, optional
        Template directory path.

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("aggregated_comparison.html")

    scenario = aggregated_list[0].scenario if aggregated_list else "comparison"
    num_runs = aggregated_list[0].num_runs if aggregated_list else 0
    seed_range = aggregated_list[0].seed_range if aggregated_list else ""
    strategies = [a.strategy for a in aggregated_list]

    def _fmt(mean: float, std: float) -> str:
        if std == 0:
            return f"{mean:.1f} \u00b1 0"
        return f"{mean:.1f} \u00b1 {std:.1f}"

    comparison_rows = [
        {
            "strategy": a.strategy,
            "unauthorized": _fmt(a.unauthorized_ops_mean, a.unauthorized_ops_std),
            "unauthorized_std": a.unauthorized_ops_std,
            "staleness": _fmt(a.staleness_max_mean, a.staleness_max_std),
            "staleness_std": a.staleness_max_std,
            "p50": _fmt(a.latency_p50_mean, a.latency_p50_std),
            "p99": _fmt(a.latency_p99_mean, a.latency_p99_std),
            "convergence": _fmt(a.convergence_mean, a.convergence_std),
            "messages": _fmt(a.messages_mean, a.messages_std),
            "revalidations": _fmt(a.revalidation_mean, a.revalidation_std),
            "bound_violations": a.total_bound_violations,
        }
        for a in aggregated_list
    ]

    # Per-depth rows
    all_depths: set[int] = set()
    for a in aggregated_list:
        all_depths.update(a.unauthorized_by_depth_mean.keys())

    depth_rows = [
        {
            "depth": d,
            "values": {
                a.strategy: _fmt(
                    a.unauthorized_by_depth_mean.get(d, 0.0),
                    a.unauthorized_by_depth_std.get(d, 0.0),
                )
                for a in aggregated_list
            },
        }
        for d in sorted(all_depths)
    ]

    clock_rows = [
        {"strategy": "eager", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lazy", "clock_dependent": "No", "robustness": "High"},
        {"strategy": "lease", "clock_dependent": "Yes", "robustness": "Fragile"},
        {"strategy": "exec_count", "clock_dependent": "No", "robustness": "High"},
    ]

    return template.render(
        scenario=scenario,
        num_runs=num_runs,
        seed_range=seed_range,
        strategies=strategies,
        chart_labels=strategies,
        chart_means=[a.unauthorized_ops_mean for a in aggregated_list],
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

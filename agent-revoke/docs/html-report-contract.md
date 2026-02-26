# HTML Report Contract

Implementation file: `src/output/report.py`
Templates: `src/output/templates/`

## Report APIs

- `generate_html_report(metrics, template_dir=...)`
  - single-strategy report
- `generate_strategy_comparison_report(metrics_list, template_dir=...)`
  - multi-strategy report
- `generate_aggregated_comparison_report(aggregated, scenario, seed_start, template_dir=...)`
  - multi-run aggregated comparison (`mean ± std`)
- `save_report(html, path)`
  - persists report and creates parent directories

## Template Variables

Core variables used across templates:

- scenario metadata: `scenario`, `strategy`, `num_runs`, `seed_range`
- headline metrics: unauthorized, p50/p99 latency, staleness, convergence
- chart payload: `chart_labels`, `chart_values`
- tables:
  - `comparison_rows`
  - `depth_rows`
  - `clock_rows`
  - `bound_rows`

## Template Layout

Current split:

- `report.html.j2` -> includes `report_template.html`
- `comparison.html.j2` -> includes `report_template.html`
- `aggregated.html.j2` -> includes `report_template.html`

The shared template renders:

- strategy comparison summary
- per-depth analysis
- clock dependence comparison
- bound violation table

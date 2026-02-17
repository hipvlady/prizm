from jinja2 import Environment, FileSystemLoader
import os

def generate_html_report(metrics, template_dir="src/output/templates"):
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    # This is a simplified version of what the prompt asks for.
    # A full implementation would require more data processing.
    
    html_content = template.render(
        scenario=metrics.scenario,
        strategy=metrics.strategy,
        unauthorized_ops=metrics.unauthorized_actions_count,
        p50_latency=metrics.revocation_latency_p50,
        p99_latency=metrics.revocation_latency_p99,
        convergence_time=metrics.convergence_time_ticks,
    )
    return html_content

def save_report(report_html, output_path):
    with open(output_path, "w") as f:
        f.write(report_html)

# I will also need a template file. I'll create a simple one.
# I'll create a new directory `src/output/templates` and place the file there.

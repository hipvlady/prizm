import { useEffect, useMemo, useState } from 'react';
import type { ChangeEvent } from 'react';
import './App.css';

type AggregatedMetrics = {
  strategy: string;
  runs: number;
  unauthorized_mean: number;
  unauthorized_std: number;
  p50_mean: number;
  p50_std: number;
  p99_mean: number;
  p99_std: number;
  staleness_max_mean: number;
  staleness_max_std: number;
  convergence_mean: number;
  convergence_std: number;
  message_overhead_mean: number;
  message_overhead_std: number;
  revalidations_mean: number;
  revalidations_std: number;
  transient_timeouts_mean: number;
  transient_timeouts_std: number;
  unauthorized_by_depth_mean: Record<string, number>;
  unauthorized_by_depth_std: Record<string, number>;
};

type SimulationRun = {
  strategy: string;
  unauthorized_actions_count: number;
  revocation_latency_p50: number;
  staleness_window_max: number;
  convergence_time: number;
  message_overhead: number;
  revalidation_count: number;
  transient_state_timeouts: number;
};

type DashboardPayload = {
  version: string;
  generated_at: string;
  scenario: string;
  strategies: string[];
  runs_per_strategy: number;
  seed_start: number;
  seed_end: number;
  aggregated: AggregatedMetrics[];
  runs: Record<string, SimulationRun[]>;
};

type MetricOption = {
  id: 'unauthorized_mean' | 'staleness_max_mean' | 'p50_mean' | 'convergence_mean' | 'message_overhead_mean';
  label: string;
};

const METRICS: MetricOption[] = [
  { id: 'unauthorized_mean', label: 'Unauthorized Mean' },
  { id: 'staleness_max_mean', label: 'Staleness Max Mean' },
  { id: 'p50_mean', label: 'P50 Revocation Mean' },
  { id: 'convergence_mean', label: 'Convergence Mean' },
  { id: 'message_overhead_mean', label: 'Message Overhead Mean' },
];

function formatValue(value: number): string {
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function App() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [metric, setMetric] = useState<MetricOption['id']>('unauthorized_mean');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const loadSample = async () => {
      try {
        const response = await fetch('/dashboard-sample.json');
        if (!response.ok) {
          return;
        }
        const data = (await response.json()) as DashboardPayload;
        setPayload(data);
      } catch {
        // Optional sample; leave state untouched.
      }
    };
    void loadSample();
  }, []);

  const maxMetric = useMemo(() => {
    if (!payload?.aggregated.length) {
      return 1;
    }
    return Math.max(...payload.aggregated.map((item) => item[metric]), 1);
  }, [metric, payload]);

  const depthRows = useMemo(() => {
    if (!payload) {
      return [] as string[];
    }
    const keys = new Set<string>();
    payload.aggregated.forEach((entry) => {
      Object.keys(entry.unauthorized_by_depth_mean).forEach((depth) => keys.add(depth));
    });
    return Array.from(keys).sort((a, b) => Number(a) - Number(b));
  }, [payload]);

  const onUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as DashboardPayload;
        if (!parsed?.aggregated || !parsed?.runs) {
          throw new Error('Missing required fields: aggregated/runs');
        }
        setPayload(parsed);
        setError('');
      } catch (uploadError) {
        const message = uploadError instanceof Error ? uploadError.message : 'Failed to parse file';
        setError(`Invalid dashboard JSON: ${message}`);
      }
    };
    reader.readAsText(file);
  };

  return (
    <main className="page-shell">
      <section className="hero reveal">
        <p className="eyebrow">Prizm Agent Revoke</p>
        <h1>Interactive Strategy Dashboard</h1>
        <p className="subhead">
          Explore revocation impact across strategies with aggregated runs, depth patterns, and
          latency windows.
        </p>
        <div className="hero-actions">
          <label className="upload-btn">
            Upload JSON
            <input type="file" accept="application/json" onChange={onUpload} />
          </label>
          <a
            className="link-btn"
            href="/dashboard-sample.json"
            download
          >
            Download sample
          </a>
        </div>
        {error ? <p className="error-box">{error}</p> : null}
      </section>

      {payload ? (
        <>
          <section className="meta-grid reveal delay-1">
            <article>
              <h2>Scenario</h2>
              <p>{payload.scenario}</p>
            </article>
            <article>
              <h2>Run Envelope</h2>
              <p>
                {payload.runs_per_strategy} run(s) per strategy, seed {payload.seed_start}..{payload.seed_end}
              </p>
            </article>
            <article>
              <h2>Generated</h2>
              <p>{new Date(payload.generated_at).toLocaleString()}</p>
            </article>
          </section>

          <section className="panel reveal delay-2">
            <div className="panel-head">
              <h2>Metric Lens</h2>
              <select value={metric} onChange={(e) => setMetric(e.target.value as MetricOption['id'])}>
                {METRICS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="bar-list">
              {payload.aggregated.map((entry) => {
                const width = (entry[metric] / maxMetric) * 100;
                return (
                  <div key={entry.strategy} className="bar-row">
                    <div className="bar-meta">
                      <span>{entry.strategy}</span>
                      <strong>{formatValue(entry[metric])}</strong>
                    </div>
                    <div className="bar-track">
                      <span className="bar-fill" style={{ width: `${Math.max(width, 4)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="cards reveal delay-3">
            {payload.aggregated.map((entry) => (
              <article key={entry.strategy} className="strategy-card">
                <h3>{entry.strategy}</h3>
                <ul>
                  <li>Unauthorized: {formatValue(entry.unauthorized_mean)} ± {formatValue(entry.unauthorized_std)}</li>
                  <li>Staleness max: {formatValue(entry.staleness_max_mean)} ± {formatValue(entry.staleness_max_std)}</li>
                  <li>P50 latency: {formatValue(entry.p50_mean)} ± {formatValue(entry.p50_std)}</li>
                  <li>Revalidations: {formatValue(entry.revalidations_mean)} ± {formatValue(entry.revalidations_std)}</li>
                </ul>
              </article>
            ))}
          </section>

          <section className="panel reveal delay-4">
            <h2>Depth Impact Matrix (Unauthorized Mean)</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Depth</th>
                    {payload.aggregated.map((entry) => (
                      <th key={entry.strategy}>{entry.strategy}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {depthRows.map((depth) => (
                    <tr key={depth}>
                      <td>{depth}</td>
                      {payload.aggregated.map((entry) => (
                        <td key={`${entry.strategy}-${depth}`}>
                          {formatValue(entry.unauthorized_by_depth_mean[depth] ?? 0)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel reveal delay-5">
            <h2>Run Slices</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Runs</th>
                    <th>Unauthorized (first run)</th>
                    <th>Staleness (first run)</th>
                  </tr>
                </thead>
                <tbody>
                  {payload.strategies.map((strategy) => {
                    const runs = payload.runs[strategy] ?? [];
                    const first = runs[0];
                    return (
                      <tr key={`run-${strategy}`}>
                        <td>{strategy}</td>
                        <td>{runs.length}</td>
                        <td>{first ? formatValue(first.unauthorized_actions_count) : '-'}</td>
                        <td>{first ? formatValue(first.staleness_window_max) : '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <section className="panel reveal delay-1">
          <h2>No dataset loaded</h2>
          <p>
            Generate one with:
            <code>
              python scripts/run_strategy_comparison.py --scenario scenarios/crm-bulk-ops.yaml --output /tmp/report.html --json-output /tmp/dashboard.json --runs 10
            </code>
          </p>
        </section>
      )}
    </main>
  );
}

export default App;

# Interactive Dashboard (React)

This dashboard provides an interactive view over strategy-comparison simulation output.

## What it reads

Upload the JSON payload produced by:

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --json-output /tmp/crm-dashboard.json \
  --runs 10 \
  --seed-start 0
```

## Local run

```bash
cd web/dashboard
npm install
npm run dev
```

Open the printed local URL and upload `/tmp/crm-dashboard.json`.

## Build and lint

```bash
npm run lint
npm run build
```

## Notes

- `public/dashboard-sample.json` is included for immediate UI preview.
- The app is static (no backend service required).

# Development Standards

This project tracks the code-quality baseline from `main` and validates changes on `feature/phase2` before merge.

## Authoritative Config

- Python packaging/testing/type-check config: `agent-revoke/pyproject.toml`
- Scenario contract: `docs/scenario-schema.md`
- Dashboard frontend toolchain: `web/dashboard/package.json`

## Required Checks Before Merge

### Python simulation changes

```bash
cd agent-revoke
pytest -q
```

### Dashboard changes

```bash
cd agent-revoke/web/dashboard
npm run lint
npm run build
```

## Typing Standard

- `mypy` is configured in strict mode in `pyproject.toml`.
- Full strict conformance remains an active cleanup stream; do not lower the strict settings when adding new features.

## Documentation Standard

When behavior changes, update at least one of:

- `README.md` (feature surface and quick-start commands)
- `docs/metrics-and-evidence.md` (latest verified outcomes)
- `docs/scenario-schema.md` (input contract changes)

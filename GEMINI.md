# GEMINI.md

## Project Overview

This project, `agent-revoke`, is a simulation environment for exploring temporal consistency in multi-agent authorization systems. It uses an adaptation of the MESI cache coherence protocol to manage the state of capabilities.

The core of the project is a simulation engine that orchestrates interactions between agents and a central authority. The authority grants, delegates, and revokes capabilities, while agents attempt to use them. The simulation can be configured with different revocation strategies (e.g., eager invalidation, lazy invalidation, leases) to study their impact on the system.

**Key Technologies:**

*   Python 3.11+
*   Pytest for testing
*   Mypy for static type checking
*   Rich for terminal-based UI
*   Jinja2 for report templating
*   PyYAML for scenario configuration

## Building and Running

### Running the Simulation

The `pyproject.toml` file defines a script entry point `simulate` that points to `src.simulation.engine:main`. However, the `main` function in `src/simulation/engine.py` is currently empty.

**TODO:** Implement the `main` function in `src/simulation/engine.py` to parse a scenario configuration file (from the `scenarios/` directory) and run the simulation.

A possible implementation would be:

```python
def main():
    parser = argparse.ArgumentParser(description="Run an agent revocation simulation.")
    parser.add_argument("scenario", help="Path to the scenario YAML file.")
    parser.add_argument("--strategy", help="Revocation strategy to use.", default="eager")
    args = parser.parse_args()

    with open(args.scenario, 'r') as f:
        config = yaml.safe_load(f)

    engine = SimulationEngine(config, args.strategy)
    metrics = engine.run()
    print(metrics)

if __name__ == "__main__":
    main()
```

### Running Tests

To run the test suite, use `pytest`:

```bash
pytest
```

## Development Conventions

### Code Style

The project uses `mypy` for static type checking. To ensure code quality, run `mypy` before committing changes:

```bash
mypy src/ --strict
```

### Known Issues and Inconsistencies

*   **Critical Bug in `AuthorityService` Instantiation:** There is a major inconsistency in the codebase. `src/simulation/engine.py` instantiates `AuthorityService` with `config` and `clock` objects:

    ```python
    self.authority = AuthorityService(config, self.clock)
    ```

    However, the `AuthorityService` constructor in `src/authority/service.py` expects `registry`, `broadcaster`, `trust_scorer`, and `clock`:

    ```python
    def __init__(
        self,
        registry: CapabilityRegistry,
        broadcaster: RevocationBroadcaster,
        trust_scorer: TrustScorer,
        clock: LogicalClock,
    ):
    ```

    This will cause a runtime error and needs to be fixed. It's likely that the `SimulationEngine` is responsible for creating the dependencies of `AuthorityService`.

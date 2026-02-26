# Copyright (c) 2026 Prizm contributors.
"""Simulation engine for temporal consistency experiments."""

from __future__ import annotations

import argparse
import copy
import logging
import random
from collections import defaultdict
from time import perf_counter
from typing import Any, Dict
from uuid import UUID, uuid4

from src.agent.runtime import AgentRuntime
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.registry import CapabilityRegistry
from src.authority.service import AuthorityService
from src.authority.trust_scorer import TrustScorer
from src.core.clock import LogicalClock
from src.core.exceptions import StaleCredentialError
from src.core.logging_utils import configure_logging, get_logger
from src.core.types import DelegationPolicy, MESIState, RevocationReason
from src.output.terminal import SimulationLiveView
from src.simulation.consistency import ConsistencyMonitor
from src.simulation.metrics import MetricsCollector
from src.simulation.network import Network
from src.simulation.bounds import calculate_depth_bound
from src.simulation.scenarios import load_scenario
from src.strategies.base import RevocationStrategy
from src.strategies.eager import EagerInvalidationStrategy
from src.strategies.exec_count import ExecCountStrategy
from src.strategies.lazy import LazyInvalidationStrategy
from src.strategies.lease import LeaseBasedStrategy
from src.strategies.selector import StrategySelector

LOGGER = get_logger(__name__)


class SimulationEngine:
    """Drive scenario execution and collect consistency metrics."""

    def __init__(self, config: Dict[str, Any], strategy_name: str, scenario_name: str):
        """Initialise simulation components.

        Parameters
        ----------
        config : dict
            Scenario configuration.
        strategy_name : str
            Strategy identifier.
        scenario_name : str
            Scenario label for reporting.
        """
        self.config = copy.deepcopy(config)
        self.clock = LogicalClock()
        self.strategy_name = strategy_name
        self.scenario_name = scenario_name
        self.rng = random.Random(self.config["simulation"].get("seed", 42))

        self.consistency_monitor = ConsistencyMonitor()
        self.metrics_collector = MetricsCollector(scenario_name, strategy_name)
        self._depth_unauthorized_counts: Dict[int, int] = defaultdict(int)
        self._remaining_ops_at_revoke_by_depth: Dict[int, int] = {}
        self._bound_violation_recorded_depths: set[int] = set()
        self._anomaly_revoked_agents: set[UUID] = set()
        self.live_view = SimulationLiveView(
            enabled=bool(self.config["simulation"].get("live_output", False))
        )

        network_cfg = self.config["network"]
        latency_ticks = int(network_cfg["latency_ticks"])
        message_loss_rate = float(network_cfg["message_loss_rate"])
        self.network = Network(latency_ticks, message_loss_rate, self.rng)
        registry = CapabilityRegistry()
        broadcaster = RevocationBroadcaster(
            self.network,
            latency_ticks,
            self.clock,
            self.metrics_collector,
        )
        trust_scorer = TrustScorer()
        delegation_cfg = self.config.get("delegation", {})
        delegation_policy = DelegationPolicy(
            max_depth=delegation_cfg.get("max_depth", 16),
            require_scope_subset=delegation_cfg.get("require_scope_subset", True),
            propagate_remaining_ops=delegation_cfg.get("propagate_remaining_ops", True),
        )
        self.authority = AuthorityService(
            registry,
            broadcaster,
            trust_scorer,
            self.clock,
            self.consistency_monitor,
            delegation_policy=delegation_policy,
        )
        self.strategy = self._create_strategy(strategy_name)
        heterogeneous_cfg = self.config.get("heterogeneous", {})
        self.heterogeneous_enabled = bool(heterogeneous_cfg.get("enabled", False))
        self.strategy_selector = StrategySelector(heterogeneous_cfg.get("policy", {}))
        self.agent_roles = list(heterogeneous_cfg.get("agent_roles", []))
        self.agent_strategy_names: Dict[UUID, str] = {}
        if self.heterogeneous_enabled:
            self.strategy_name = "heterogeneous"

        self.agents: Dict[UUID, AgentRuntime] = {}
        transient_timeout_ticks = int(self.config["transient"]["timeout_ticks"])
        for idx in range(config["simulation"]["num_agents"]):
            agent_id = uuid4()
            agent_strategy = self.strategy
            if self.heterogeneous_enabled:
                role = self.agent_roles[idx] if idx < len(self.agent_roles) else ""
                selected_strategy = self.strategy_selector.select(role)
                agent_strategy = self._create_strategy(selected_strategy)
                self.agent_strategy_names[agent_id] = selected_strategy
            else:
                self.agent_strategy_names[agent_id] = strategy_name

            self.agents[agent_id] = AgentRuntime(
                agent_id=agent_id,
                authority=self.authority,
                strategy=agent_strategy,
                clock=self.clock,
                transient_timeout_ticks=transient_timeout_ticks,
                monitor=self.consistency_monitor,
                metrics_collector=self.metrics_collector,
            )

        self.config["scenario"]["root_capability_id"] = None

    def _create_strategy(self, name: str) -> RevocationStrategy:
        """Create strategy instance by name."""
        strat_config = self.config["strategies"].get(name, {})
        match name:
            case "eager":
                return EagerInvalidationStrategy()
            case "lazy":
                return LazyInvalidationStrategy(**strat_config)
            case "lease":
                return LeaseBasedStrategy(**strat_config)
            case "exec_count":
                return ExecCountStrategy(**strat_config)
            case _:
                raise ValueError(f"Unknown strategy: {name}")

    def run(self):
        """Execute simulation and return aggregated metrics."""
        self._setup_scenario()
        LOGGER.info(
            "event=simulation_start scenario=%s strategy=%s",
            self.scenario_name,
            self.strategy_name,
        )
        self.live_view.start()

        duration_ticks = self.config["simulation"]["duration_ticks"]
        run_started = perf_counter()
        try:
            for _ in range(duration_ticks):
                current_tick = self.clock.now()
                tick_started = perf_counter()
                self._tick(current_tick)
                tick_elapsed = perf_counter() - tick_started
                self.metrics_collector.record_tick_duration(tick_elapsed)
                self.live_view.update(current_tick, self.strategy_name, self.agents)
                self.clock.advance()
        finally:
            self.live_view.stop()
        run_elapsed = perf_counter() - run_started

        LOGGER.info(
            "event=simulation_complete scenario=%s strategy=%s wall_seconds=%.6f",
            self.scenario_name,
            self.strategy_name,
            run_elapsed,
        )
        return self.metrics_collector.finalize(
            self.scenario_name,
            self.strategy_name,
            duration_ticks,
            self.consistency_monitor,
            wall_time_seconds=run_elapsed,
        )

    def _tick(self, tick: int):
        """Execute one logical simulation tick."""
        self._process_message_bus(tick)
        self._run_agent_maintenance(tick)
        self._trigger_scheduled_revocations(tick)
        self._run_agent_actions(tick)
        self._run_anomaly_detection(tick)
        self.consistency_monitor.check_staleness(self.agents, tick, self.authority.registry)
        self.metrics_collector.record_convergence(tick)

    def _process_message_bus(self, tick: int) -> None:
        """Deliver due revocation messages for current tick."""
        for msg in self.network.deliver_due(tick):
            self.agents[msg.destination].on_revocation_received(msg.payload, tick)
            self.metrics_collector.record_revocation_latency(tick - msg.payload.issued_tick)

    def _run_agent_maintenance(self, tick: int) -> None:
        """Run per-agent timeout and strategy tick handlers."""
        for agent in self.agents.values():
            timed_out = agent.check_transient_timeouts(tick)
            if timed_out:
                for cap_id in timed_out:
                    LOGGER.warning(
                        "event=transient_timeout agent=%s capability=%s tick=%d",
                        agent.agent_id,
                        cap_id,
                        tick,
                    )
            agent.strategy.on_tick(agent, tick)

    def _trigger_scheduled_revocations(self, tick: int) -> None:
        """Apply scenario-configured revocation trigger if due."""
        revocation_tick = self.config["scenario"].get("revocation_tick")
        if tick == revocation_tick:
            root_cap_id = self.config["scenario"].get("root_capability_id")
            if root_cap_id:
                self._remaining_ops_at_revoke_by_depth = self._snapshot_remaining_ops_by_depth(
                    root_cap_id, self.config["scenario"]["cascade_on_revoke"]
                )
                event = self.authority.revoke_capability(
                    capability_id=root_cap_id,
                    reason=RevocationReason.EXPLICIT,
                    cascade=self.config["scenario"]["cascade_on_revoke"],
                    completion_semantics=self._revocation_completion_semantics(),
                )
                if self.strategy_name == "eager":
                    self._complete_eager_revocation(event.id, tick)
                LOGGER.info(
                    "event=scheduled_revoke tick=%d capability=%s",
                    tick,
                    root_cap_id,
                )

    def _run_agent_actions(self, tick: int) -> None:
        """Run action attempts and stale credential accounting for all agents."""
        for idx, agent in enumerate(self.agents.values()):
            attempts = self._determine_action_attempts_for_agent(
                tick=tick,
                agent_index=idx,
            )
            if attempts <= 0:
                continue

            for _ in range(attempts):
                agent_caps = list(agent.state.capabilities.values())
                if not agent_caps:
                    break
                selected_cap = self.rng.choice(agent_caps)
                action_record = agent.attempt_action(selected_cap.resource, tick)
                self.metrics_collector.record_action(action_record)

                if action_record.authorized and action_record.capability_id is not None:
                    authority_cap = self.authority.registry.get(action_record.capability_id)
                    if authority_cap and authority_cap.state == MESIState.INVALID:
                        try:
                            raise StaleCredentialError(
                                agent.agent_id,
                                action_record.capability_id,
                                "action authorised on stale credential",
                            )
                        except StaleCredentialError as exc:
                            LOGGER.warning("event=stale_action %s", exc)
                        self.metrics_collector.record_unauthorized_action(action_record)
                        depth = action_record.delegation_depth
                        self._depth_unauthorized_counts[depth] += 1
                        self.consistency_monitor.record_unauthorized_action(depth)
                        self._check_bound_violation(depth)

    def _determine_action_attempts_for_agent(
        self,
        *,
        tick: int,
        agent_index: int,
    ) -> int:
        """Return action attempts for one agent in the current tick."""
        scenario_conf = self.config.get("scenario", {})
        anomaly_start = scenario_conf.get("anomaly_start_tick")
        anomaly_target = int(scenario_conf.get("anomaly_target_agent_index", 0))
        anomaly_burst = int(scenario_conf.get("anomaly_burst_rate", 0) or 0)

        if (
            anomaly_start is not None
            and tick >= anomaly_start
            and agent_index == anomaly_target
            and anomaly_burst > 0
        ):
            return anomaly_burst

        action_probability = float(scenario_conf.get("action_probability", 0.0))
        velocity = int(scenario_conf.get("agent_velocity", 1))
        if self.rng.random() >= action_probability:
            return 0
        return max(0, velocity)

    def _run_anomaly_detection(self, tick: int) -> None:
        """Run trust scorer anomaly detection and trigger auto-revocation."""
        anomaly_start = self.config.get("scenario", {}).get("anomaly_start_tick")
        if anomaly_start is not None and tick < anomaly_start:
            return

        for agent in self.agents.values():
            if agent.agent_id in self._anomaly_revoked_agents:
                continue
            is_anomaly = self.authority.trust_scorer.check_anomaly(
                agent.agent_id, agent.state.action_history
            )
            if is_anomaly:
                for cap in agent.state.capabilities.values():
                    if cap.state != MESIState.INVALID:
                        LOGGER.info(
                            "event=auto_revoke agent=%s capability=%s reason=trust_violation",
                            agent.agent_id,
                            cap.id,
                        )
                        self.authority.revoke_capability(
                            capability_id=cap.id,
                            reason=RevocationReason.TRUST_VIOLATION,
                            cascade=True,
                            completion_semantics=self._revocation_completion_semantics(),
                        )
                        self._anomaly_revoked_agents.add(agent.agent_id)
                        break

    def _revocation_completion_semantics(self) -> str:
        """Return completion semantics tag for current strategy mode."""
        if self.heterogeneous_enabled:
            accepts_push = [agent.strategy.accepts_push_revocation for agent in self.agents.values()]
            if all(accepts_push):
                return "push"
            if any(accepts_push):
                return "mixed"
            return "pull_eventual"
        return "push" if self.strategy.accepts_push_revocation else "pull_eventual"

    def _snapshot_remaining_ops_by_depth(self, root_capability_id: UUID, cascade: bool) -> Dict[int, int]:
        """Snapshot remaining operation budgets grouped by depth at revoke tick."""
        root = self.authority.registry.get(root_capability_id)
        if root is None:
            return {}
        caps = [root]
        if cascade:
            caps.extend(self.authority.registry.get_delegation_chain(root_capability_id))
        grouped: Dict[int, int] = defaultdict(int)
        for cap in caps:
            if cap.max_operations is None:
                continue
            remaining = max(0, cap.max_operations - cap.operations_used)
            grouped[cap.delegation_depth] += remaining
        return dict(grouped)

    def _check_bound_violation(self, depth: int) -> None:
        """Check and record per-depth unauthorized bound violations."""
        if self.heterogeneous_enabled:
            return
        if depth in self._bound_violation_recorded_depths:
            return
        bound = calculate_depth_bound(
            self.strategy_name,
            depth,
            self.config,
            remaining_ops_at_revoke=self._remaining_ops_at_revoke_by_depth.get(depth),
        )
        if self._depth_unauthorized_counts[depth] > bound:
            self._bound_violation_recorded_depths.add(depth)
            self.metrics_collector.record_bound_violation(depth)

    def _complete_eager_revocation(self, event_id: UUID, tick: int) -> None:
        """Synchronously deliver eager revocation messages before proceeding."""
        pending = self.authority.get_revocation_status(event_id)["pending_acks"]
        if pending <= 0:
            return
        due_tick = tick + self.network.latency_ticks
        for msg in self.network.deliver_due(due_tick):
            self.agents[msg.destination].on_revocation_received(msg.payload, due_tick)
        latency = due_tick - tick
        self.metrics_collector.record_revocation_latency(latency)

    def _setup_scenario(self):
        """Initialise capabilities and delegation topology for scenario."""
        scenario_conf = self.config["scenario"]
        agent_list = list(self.agents.values())
        if not agent_list:
            return

        root_agent = agent_list[0]
        root_cap = self.authority.grant_capability(
            agent_id=root_agent.agent_id,
            resource="resource:read_write",
            scope=("read", "write"),
            ttl=self.config["strategies"].get("lease", {}).get("default_ttl_ticks"),
            max_operations=self.config["strategies"].get("exec_count", {}).get("max_operations"),
        )
        root_agent.cache.update(root_cap)
        self.config["scenario"]["root_capability_id"] = root_cap.id

        parent_agent = root_agent
        parent_cap = root_cap
        for i in range(1, scenario_conf["delegation_depth"]):
            if i >= len(agent_list):
                break
            child_agent = agent_list[i]
            child_cap = self.authority.delegate_capability(
                from_agent_id=parent_agent.agent_id,
                to_agent_id=child_agent.agent_id,
                parent_cap_id=parent_cap.id,
                attenuated_scope=("read",),
            )
            child_agent.cache.update(child_cap)
            parent_agent = child_agent
            parent_cap = child_cap
        self.consistency_monitor.set_delegation_tree(
            self.authority.registry.get_delegation_tree_snapshot()
        )


def main():
    """CLI entry-point for single-strategy simulation run."""
    parser = argparse.ArgumentParser(description="Run an agent revocation simulation.")
    parser.add_argument("scenario", help="Path to the scenario YAML file.")
    parser.add_argument(
        "--strategy",
        help="Revocation strategy to use.",
        default="eager",
        choices=["eager", "lazy", "lease", "exec_count"],
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level.",
    )
    args = parser.parse_args()
    configure_logging(getattr(logging, args.log_level))

    config = load_scenario(args.scenario)

    engine = SimulationEngine(config, args.strategy, args.scenario)
    metrics = engine.run()
    print(metrics)


if __name__ == "__main__":
    main()

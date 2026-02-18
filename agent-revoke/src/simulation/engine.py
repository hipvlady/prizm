import argparse
import yaml
import random
import time
from collections import deque
from typing import Dict, List, Any
from uuid import UUID, uuid4

from src.core.clock import LogicalClock
from src.core.types import MESIState, RevocationReason
from src.authority.service import AuthorityService
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer
from src.agent.runtime import AgentRuntime
from src.strategies.base import RevocationStrategy
from src.strategies.eager import EagerInvalidationStrategy
from src.strategies.lazy import LazyInvalidationStrategy
from src.strategies.lease import LeaseBasedStrategy
from src.strategies.exec_count import ExecCountStrategy
from src.simulation.metrics import MetricsCollector

class SimulationEngine:
    """
    Orchestrates the entire simulation.
    - Manages the logical clock.
    - Runs the main tick loop.
    - Initializes all components (Authority, Agents, Strategies).
    - Collects and reports metrics.
    """
    def __init__(self, config: Dict[str, Any], strategy_name: str):
        self.config = config
        self.clock = LogicalClock()
        
        # Messaging
        self.message_bus = deque()
        latency_ticks = self.config['simulation'].get('latency_ticks', 1)
        
        # Authority (PDP)
        registry = CapabilityRegistry()
        broadcaster = RevocationBroadcaster(self.message_bus, latency_ticks, self.clock)
        trust_scorer = TrustScorer()
        self.authority = AuthorityService(registry, broadcaster, trust_scorer, self.clock)
        
        # Strategy
        strategy = self._create_strategy(strategy_name)
        
        # Agents (PEPs)
        self.agents: Dict[UUID, AgentRuntime] = {}
        transient_timeout_ticks = self.config['simulation'].get('transient_timeout_ticks', 5)
        for _ in range(config['simulation']['agents']):
            agent_id = uuid4()
            self.agents[agent_id] = AgentRuntime(agent_id, self.authority, strategy, self.clock, transient_timeout_ticks)

        self.metrics_collector = MetricsCollector()
        self.config['scenario']['root_capability_id'] = None

    def _create_strategy(self, name: str) -> RevocationStrategy:
        strat_config = self.config['strategies'].get(name, {})
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
        self._setup_scenario()

        for tick in range(self.config['simulation']['duration_ticks']):
            self.clock.advance()
            current_tick = self.clock.now()
            self._tick(current_tick)
        
        return self.metrics_collector.finalize()

    def _tick(self, tick: int):
        # 1. Process Message Bus
        for _ in range(len(self.message_bus)):
            if self.message_bus[0]['deliver_at'] <= tick:
                msg = self.message_bus.popleft()
                self.agents[msg['recipient']].on_revocation_received(msg['event'])

        # 2. Run agent-level and strategy-level tick logic
        for agent in self.agents.values():
            agent.check_transient_timeouts(tick)
            agent.strategy.on_tick(agent, tick)

        # 3. Agents attempt actions
        for agent in self.agents.values():
            if random.random() < self.config['simulation']['action_probability']:
                action_record = agent.attempt_action("resource:read_write", tick)
                self.metrics_collector.record_action(action_record)
                if not action_record.authorized:
                    self.metrics_collector.record_unauthorized_action(action_record)

        # 4. Trigger scheduled revocations from scenario config
        revocation_tick = self.config['scenario'].get('revocation_trigger_tick')
        if tick == revocation_tick:
            root_cap_id = self.config['scenario'].get('root_capability_id')
            if root_cap_id:
                self.authority.revoke_capability(
                    capability_id=root_cap_id,
                    reason=RevocationReason.EXPLICIT,
                    cascade=self.config['scenario']['cascade_revocation']
                )

    def _setup_scenario(self):
        scenario_conf = self.config['scenario']
        agent_list = list(self.agents.values())
        if not agent_list: return
        
        root_agent = agent_list[0]
        root_cap = self.authority.grant_capability(
            agent_id=root_agent.agent_id,
            resource="resource:read_write",
            scope=("read", "write"),
            ttl=self.config['strategies'].get('lease', {}).get('default_ttl_ticks'),
            max_operations=self.config['strategies'].get('exec_count', {}).get('max_operations')
        )
        root_agent.state.capabilities[root_cap.id] = root_cap
        self.config['scenario']['root_capability_id'] = root_cap.id

        parent_agent = root_agent
        parent_cap = root_cap
        for i in range(1, scenario_conf['delegation_depth']):
            if i >= len(agent_list): break
            child_agent = agent_list[i]
            child_cap = self.authority.delegate_capability(
                from_agent_id=parent_agent.agent_id,
                to_agent_id=child_agent.agent_id,
                parent_cap_id=parent_cap.id,
                attenuated_scope=("read",)
            )
            child_agent.state.capabilities[child_cap.id] = child_cap
            parent_agent = child_agent
            parent_cap = child_cap

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
import argparse
import yaml
from typing import Dict, List
from uuid import UUID, uuid4
import time
import random

from core.clock import LogicalClock
from core.types import Capability, ActionResult, MESIState
from strategies.base import RevocationStrategy
from strategies.eager import EagerInvalidationStrategy
from strategies.lazy import LazyInvalidationStrategy
from strategies.lease import LeaseBasedStrategy
from strategies.exec_count import ExecCountBoundedStrategy
from authority.service import AuthorityService
from authority.registry import CapabilityRegistry
from authority.broadcaster import RevocationBroadcaster
from authority.trust_scorer import TrustScorer
from agent.runtime import AgentRuntime
from agent.cache import CapabilityCache
from simulation.network import SimulatedNetwork
from simulation.metrics import SimulationMetrics, MetricsCollector
from output.terminal import print_tick
from simulation.scenarios import load_scenario

class SimulationEngine:
    def __init__(self, config: Dict, strategy: RevocationStrategy):
        self.config = config
        self.strategy = strategy
        self.clock = LogicalClock()
        self.network = SimulatedNetwork(latency_ticks=config.get('network_latency_ticks', 1))
        
        self.registry = CapabilityRegistry()
        self.broadcaster = RevocationBroadcaster()
        self.trust_scorer = TrustScorer()
        self.authority = AuthorityService(self.registry, self.broadcaster, self.trust_scorer, self.clock)
        
        self.agents: Dict[UUID, AgentRuntime] = {}
        for i in range(config['agents']):
            agent_id = uuid4()
            cache = CapabilityCache()
            self.agents[agent_id] = AgentRuntime(agent_id, self.authority, cache, self.clock)

        self.metrics_collector = MetricsCollector()

    def run(self) -> SimulationMetrics:
        # Initial capability grants
        agent_list = list(self.agents.values())
        parent_agent = agent_list[0]
        parent_cap = self.authority.grant_capability(
            parent_agent.agent_id,
            "resource:read",
            scope=["read", "write"],
            ttl=self.config.get('credentials', {}).get('lease_ttl_ticks'),
            max_operations=self.config.get('credentials', {}).get('exec_count_max_operations')
        )
        parent_agent.cache.store(parent_cap)

        for i in range(1, len(agent_list)):
            child_agent = agent_list[i]
            child_cap = self.authority.delegate_capability(
                parent_agent.agent_id,
                child_agent.agent_id,
                parent_cap.id,
                ["read"]
            )
            child_agent.cache.store(child_cap)
            parent_agent = child_agent
            parent_cap = child_cap

        for tick in range(self.config.get('simulation_ticks', 1000)):
            self.clock.advance()
            self._tick()
            print_tick(self.clock.now(), "Tick")
            time.sleep(0.01)

        return self.metrics_collector.finalize(self.config['scenario'], self.strategy.name, self.clock.now())

    def _tick(self):
        # Process network messages
        self.network.process(self.clock.now())

        # Agent actions
        for agent in self.agents.values():
            cap = agent.cache.get_by_resource("resource:read")
            if cap:
                if random.random() < 0.2: # 20% chance of a write
                    result = agent.attempt_write_action("resource:read")
                else:
                    result = self.strategy.on_action_attempt(agent, "resource:read", cap)
                
                if result == ActionResult.ALLOWED:
                    auth_cap = self.authority.registry.get(cap.id)
                    if auth_cap and auth_cap.state == MESIState.INVALID:
                        self.metrics_collector.record_unauthorized_action()

        # Revocation trigger
        revocation_config = self.config.get('revocation', {})
        if self.clock.now() == revocation_config.get('trigger_at_tick'):
            root_cap = None
            for cap in self.registry._capabilities.values():
                if cap.delegator_id is None:
                    root_cap = cap
                    break
            if root_cap:
                self.authority.revoke_capability(root_cap.id, revocation_config['reason'], revocation_config['cascade'])

def main():
    parser = argparse.ArgumentParser(description="Run agent-revoke simulation.")
    parser.add_argument("--scenario", type=str, required=True, help="Path to the scenario YAML file.")
    parser.add_argument("--export-metrics", type=str, help="Path to export metrics JSON file.")
    parser.add_argument("--export-html", type=str, help="Path to export HTML report.")
    args = parser.parse_args()

    config = load_scenario(args.scenario)
    
    strategies: List[RevocationStrategy] = []
    if 'strategies' in config:
        for strat_name in config['strategies']:
            if strat_name == 'eager': strategies.append(EagerInvalidationStrategy())
            if strat_name == 'lazy': strategies.append(LazyInvalidationStrategy())
            if strat_name == 'lease': strategies.append(LeaseBasedStrategy())
            if strat_name == 'exec_count': strategies.append(ExecCountBoundedStrategy(config.get('credentials',{}).get('exec_count_max_operations', 50)))
    else:
        strat_name = config['strategy']
        if strat_name == 'eager': strategies.append(EagerInvalidationStrategy())
        if strat_name == 'lazy': strategies.append(LazyInvalidationStrategy())
        if strat_name == 'lease': strategies.append(LeaseBasedStrategy())
        if strat_name == 'exec_count': strategies.append(ExecCountBoundedStrategy(config.get('credentials',{}).get('exec_count_max_operations', 50)))


    for strategy in strategies:
        engine = SimulationEngine(config, strategy)
        metrics = engine.run()
        print(metrics.summary_table())

if __name__ == "__main__":
    main()

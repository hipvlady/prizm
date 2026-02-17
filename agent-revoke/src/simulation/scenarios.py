import yaml
from typing import Dict

def load_scenario(scenario_path: str) -> Dict:
    with open(scenario_path, 'r') as f:
        return yaml.safe_load(f)

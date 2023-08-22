import argparse
import copyreg
import json
import pandas as pd
from os import listdir
from os.path import isfile, join
from pathlib import Path

import csv

import BioCrowds
	

if __name__ == '__main__':
    scenario_names = ["Scenario1", "Scenario2", "Scenario3", "Scenario4", "Scenario5"]
    configs_per_scenario = [3, 3, 3, 4, 3]
    seeds_per_scenario = [50, 50, 30, 20, 20]
    config_names = ["ConfigA", "ConfigB", "ConfigC", "ConfigD"]
    base_path = Path() / "OutputExperiments"

    for scenario_id in range(len(scenario_names)):
        scenario_path = base_path / scenario_names[scenario_id]

        for config in range(configs_per_scenario[scenario_id]):

            for seed in range(seeds_per_scenario[scenario_id] + 1):
                seed_path = scenario_path / f"Seed{seed}"

            
                files = [f for f in listdir(seed_path) if isfile(join(seed_path, f))]
                print()


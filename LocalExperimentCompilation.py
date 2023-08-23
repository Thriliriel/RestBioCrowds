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
    #scenario_names = ["Scenario1"]
    configs_per_scenario = [3, 3, 3, 4, 3]
    hypotenuse_per_scenario = [42.426406871192, 42.426406871192, 42.426406871192, 42.426406871192, 61.84658438426490824]
    seeds_per_scenario = [50, 50, 30, 20, 20]
    config_names = ["ConfigA", "ConfigB", "ConfigC", "ConfigD"]
    base_path = Path() / "OutputExperiments"

    for scenario_id in range(len(scenario_names)):
        scenario_path = base_path / scenario_names[scenario_id]

        for config in range(configs_per_scenario[scenario_id]):
            output_path = base_path / (scenario_names[scenario_id] + "-" +config_names[config] + ".csv")
            
            with open(output_path, mode='w') as csv_file:
                fieldnames = ["Simulation ID", "Reference-Total Simulation Time", "Reference-Average Simulation Time", 
                              "Reference-Average Speed", "Reference-Average Distance Walked",
                              "Final-Total Simulation Time", "Final-Average Simulation Time",
                              "Final-Average Density", "Final-Average Speed", "Final-Average Distance Walked",
                              "Normalized Total Simulation Time", "Normalized Average Simulation Time",
                              "Normalized Average Speed", "Normalized Average Distance Walked"]#, "Ours","Cassol et al"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';', lineterminator = '\n')
                #writer.writeheader()
                print(output_path)
                for seed in range(seeds_per_scenario[scenario_id] + 1):
                    seed_path = scenario_path / f"Seed{seed}"

                    files = [f for f in listdir(seed_path) if isfile(join(seed_path, f))]
                    if len(files) < configs_per_scenario[scenario_id] * 2:
                        print(f"Data not available for {scenario_names[scenario_id]}, {config_names[config]}, Seed {seed}")
                        continue
                    
                    ref_df = pd.read_csv(seed_path / f"Reference-{config_names[config]}.csv",  usecols=["0","1"], index_col="0", sep=';').transpose()
                    final_df = pd.read_csv(seed_path / f"Final-{config_names[config]}.csv",  usecols=["0","1"], index_col="0",sep=';').transpose()

                    writer.writerow({"Simulation ID" : seed, 
                                     "Reference-Total Simulation Time" : float(ref_df["simulation_time"][0]), 
                                     "Reference-Average Simulation Time": float(ref_df["average_time"][0]),
                                     "Reference-Average Speed": float(ref_df["average_speed"][0]), 
                                     "Reference-Average Distance Walked": float(ref_df["average_distance_walked"][0]),
                                     "Final-Total Simulation Time": float(final_df["simulation_time"][0]), 
                                     "Final-Average Simulation Time": float(final_df["average_time"][0]),
                                     "Final-Average Density": float(final_df["average_density"][0]), 
                                     "Final-Average Speed": float(final_df["average_speed"][0]), 
                                     "Final-Average Distance Walked": float(final_df["average_distance_walked"][0]),
                                     "Normalized Total Simulation Time": float(final_df["normalized_total_simulation_time"][0]), 
                                     "Normalized Average Simulation Time": float(final_df["normalized_average_simulation_time"][0]),
                                     "Normalized Average Speed": float(final_df["normalized_average_speed"][0]), 
                                     "Normalized Average Distance Walked": float(final_df["average_distance_walked"][0])/ hypotenuse_per_scenario[scenario_id]})
    
                    #print()


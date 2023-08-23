import argparse
import copy
import json
import pandas as pd

from pathlib import Path

import BioCrowds
	
def load_biocrowds_simulation(experiment_path: str,
							  configuration_count: int,
							  starting_seed: int, 
							  ending_seed: int):
	
	config_names = ["ConfigA", "ConfigB", "ConfigC", "ConfigD"]
	config_data = []

	# read simulation data once
	for conf_id in range(configuration_count):
		exp_file = open(experiment_path + "\\" + config_names[conf_id] + ".txt", "r")
		file_data = json.loads(exp_file.read())
		config_data.append(file_data)
		exp_file.close()


	reference_results = []
	final_results = []
	current_seed = starting_seed
	
	for s in range(starting_seed, ending_seed + 1):
		print("Seed", s)
		current_seed = s
		output_path = Path() / "OutputExperiments" / experiment_path.replace("\\ExperimentsData", "") / f"Seed{current_seed}"
		output_path.mkdir(parents=True, exist_ok=True)
		removed_agents_in_ref:int = 0

		for conf_id in range(configuration_count):
			print("Ref", conf_id)
			exp_data = copy.deepcopy(config_data[conf_id])
			exp_data["simId"] = conf_id + 1
			biocrowds = BioCrowds.BioCrowdsClass()
			output_ref, removed_agents = biocrowds.run(exp_data, current_seed, reference_simulation= True)
			removed_agents_in_ref += removed_agents # type: ignore
			output_ref.to_csv(output_path / ("Reference-" +config_names[conf_id] + ".csv"), sep=';', encoding='utf-8')
			reference_results.append(output_ref)

		if removed_agents_in_ref > 0:
			continue

		for conf_id in range(configuration_count):
			print("Final", conf_id)
			exp_data = copy.deepcopy(config_data[conf_id])
			exp_data["simId"] = conf_id + 1
			biocrowds = BioCrowds.BioCrowdsClass()
			output_final, rem = biocrowds.run(exp_data, 
					current_seed, 
					reference_simulation= False, 
					reference_output=reference_results[conf_id])
			output_final.to_csv(output_path / ("Final-" +config_names[conf_id] + ".csv"), sep=';', encoding='utf-8')
			final_results.append(output_final)

	
	

if __name__ == '__main__':
	#print("Return without running code")
	#return;
	arg_parser = argparse.ArgumentParser(description="Run a local experiment of webcrowds, requires the data path and a seed range")
	arg_parser.add_argument('--p', metavar="P", type=str, default = None, help='Scenario path')
	arg_parser.add_argument('--c', metavar="C", type=int, default = None, help='Number of configurations (1 to 4)')
	arg_parser.add_argument('--s', metavar="S", type=int, default = 0, help='Starting Seed')
	arg_parser.add_argument('--e', metavar="E", type=int, default = 0, help='Ending Seed')
	args = vars(arg_parser.parse_args())
	print(args)
	load_biocrowds_simulation(experiment_path= args['p'],
							  configuration_count= args['c'],
							  starting_seed=args['s'],
							  ending_seed=args['e'])
	
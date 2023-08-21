import os
from pathlib import Path
import random
from AgentClass import AgentClass
from BioCrowdsDatabase import BioCrowdsDataBase
from Vector3Class import Vector3
from CellClass import CellClass
from GoalClass import GoalClass
from Parsing.ParserJSON import ParserJSON
import Util.DataParsing as Parsing_Util
import Util.HeatmapGeneration as HM_Gen
import Util.TrajectoriesGeneration as TJ_Gen
import Util.SimulationMetrics as Metrics_Util
import pandas as pd
from statistics import fmean
import time
import requests
import json
import math
from VisualizeMarkersResults import visualize_markers
from VisualizeAgentPaths import visualize_agent_paths_python, visualize_agent_paths_unity
# import gc


class BioCrowdsClass():
	def run(self, data, seed = 0, reference_simulation = False, reference_output: pd.DataFrame = None):
		self.ip: str = ""
		self.output_dir = os.path.abspath(
			os.path.dirname(__file__)) + "/OutputData"
		Path(self.output_dir).mkdir(parents=True, exist_ok=True)
		write_result = []
		self.seed = seed
		start_time = time.time()
		self.agents_removed:int = 0
		# simulation id for multiple alternatives
		self.simulation_id: int = 0
		self.stuck_threshold = 50
		self.reference_agent = {}
		self.run_on_server = False
		self.visualize_runtime_data = False
		self.database = BioCrowdsDataBase()
		self.execution_times = []
		self.execution_times.append(start_time)

		if self.run_on_server:
			self.database.connect_to_database()

		# default values
		# size of the scenario
		self.map_size = Vector3.Zero
		# markers density
		self.PORC_QTD_Marcacoes = 0.65
		# FPS (default: 50FPS)
		self.time_step: float = 0.02
		# size of each square cell (Ex: 2 -> cell 2x2)
		self.cell_size: float = 1
		# using path planning?
		self.path_planning = True
		# it is a reference simulation (for cassol metrics)?
		self.ref_simulation = False

		self.simulation_time: float = 0

		# read the config file
		Parsing_Util.parse_config_file(self, "Input/config.txt")

		# goals
		self.goals: list[GoalClass] = []

		# agents
		self.agents: list[AgentClass] = []
		self.removed_agents: list[AgentClass] = []

		# obstacles
		self.obstacles = []

		# cells
		self.cells: list[CellClass] = []
		
		# set reference simulation info
		data["reference_simulation"] = reference_simulation
		self.ref_simulation = bool(data["reference_simulation"])

		# add the reference simulation, if none
		#if "reference_simulation" not in data:
		#	data["reference_simulation"] = False
		#self.ref_simulation = bool(data["reference_simulation"])
		
		# from json
		# json or database?
		if data['terrains'] == 'db':
			self.ip = str(data['time_stamp'])
			# take the : out
			self.ip = self.ip.replace(':', '')
			# self.LoadDatabase()
			self.database.load_database(self)
		else:
			self.simulation_time = 0
			self.map_size, self.goals, self.agents, self.obstacles, self.ip = ParserJSON.ParseJsonContent(
				data)
			# take the : out
			self.ip = self.ip.replace(':', '')
			self.create_map()

		# if this one is not a reference simulation, we need to simulate it with only one agent (unless it is only one),
		# to be able to normalize the metrics later
		self.reference_agent = {}
		
		if self.ref_simulation or len(self.agents) == 1:
			self.select_reference_agent()
		else:
			#jason = reference_output.to_json()
			#jason = json.loads(json.loads(str(reference_output)))
			self.simulation_id = int(data["simId"])
			print("Simulation ID", self.simulation_id)
			print("World Size", self.map_size)
			# self.dump_simulation_json_data(data)
			self.reference_agent = Parsing_Util.parse_reference_simulation_data_int_keys(
				reference_output.to_dict()[1])
			self.stuck_threshold = int(
				self.reference_agent["total_simulation_time"]/self.time_step)
			self.stuck_threshold = max(self.stuck_threshold, 1000)
			# print("dist walked type:", type(self.reference_agent["total_average_distance_walked"]))
			# print(self.reference_agent["agents_distance_walked"])
			# print(self.reference_agent)

		# timing until parsing
		self.execution_times.append(time.time())
		
		random.seed(self.seed)
		# Create and save Markers
		self.create_markers()
		self.save_markers_to_file()

		# for each goal, vinculate the cell
		self.vinculate_goals_to_cells()

		# for each cell, find its neighbors
		self.find_cell_neighbors()

		# for each agent, find its initial cell
		self.find_agents_initial_cell()

		# for each agent, calculate the path, if true (comes from Json, dont need to calculate)
		if self.path_planning:
			self.find_agents_path_json()

		if not self.ref_simulation and self.visualize_runtime_data:
			visualize_agent_paths_python(agents=self.agents, 
										 id=self.simulation_id,
										 map_width=int(self.map_size.x), 
										 map_height=int(self.map_size.y))
			visualize_agent_paths_unity(agents=data["agents"], 
										id=self.simulation_id,
										 map_width=int(self.map_size.x),
										map_height=int(self.map_size.y))

		# open file to write or keep writing
		result_file = Parsing_Util.open_result_file(
			self.output_dir, self.ip, data['terrains'])

		simulation_frame: int = 0

		# timing until setup
		self.execution_times.append(time.time())

		# walking loop
		timeout = False
		while True:
			# if no agents anymore, break
			if len(self.agents) == 0:
				break

			# add new entry for agents in cell
			for _cell in self.cells:
				_cell.agents_in_cell.append(0)

			# for each agent, we reset their info
			for ag in self.agents:
				ag.ClearAgent()
			# print("markers", len(agents[0].markers))
			# reset the markers
			for _cell in self.cells:
				for marker in _cell.markers:
					marker.ResetMarker()

			# find nearest markers for each agent
			for ag in self.agents:
				ag.FindNearMarkers()
			# print(sum([len(c.markers) for c in cells]), len(agents[i].markers))

			# /*to find where the agent must move, we need to get the vectors from the agent to each auxin he has, and compare with
			#   the vector from agent to goal, generating a angle which must lie between 0 (best case) and 180 (worst case)
			#   The calculation formula was taken from the Bicho´s mastery tesis and from Paravisi algorithm, all included
			#   in AgentController.
			#   */

			#   /*for each agent, we:
			#   1 - verify existence
			#   2 - find him
			#   3 - for each marker near him, find the distance vector between it and the agent
			#   4 - calculate the movement vector (CalculateMotionVector())
			#   5 - calculate speed vector (CalculateSpeed())
			#   6 - walk (Walk())
			#   7 - verify if the agent has reached the goal. If so, destroy it
			#   */

			agents_to_kill = []

			for _agent in self.agents:
				# vector for each marker
				for _ag_marker in _agent.markers:
					# add the distance vector between it and the agent
					# print (_agent.position, _ag_marker.position)
					_agent.dist_to_markers.append(Vector3.Sub_vec(
						_ag_marker.position, _agent.position))

				# print("total", len(_agent.vetorDistRelacaoMarcacao))
				# calculate the movement vector
				_agent.CalculateMotionVector()

				# print(_agent.m)
				# calculate speed vector
				_agent.CalculateSpeed()

				# walk
				_agent.Walk(self.time_step)

				# update cell after movement
				_agent.UpdateCell()

				# write in file (agent id, X, Y, Z)
				result_file.write(str(_agent.id) + ";" +
								  _agent.position.get_formatted_str(";") + "\n")

				# verify agent position, in relation to the goal. If arrived, bye
				dist = Vector3.Distance(_agent.goal.position, _agent.position)
				# print(_agent.id, " -- Dist: ", dist, " -- Radius: ", _agent.radius, " -- Agent: ", _agent.position.x, _agent.position.y)
				# print(_agent.speed.x, _agent.speed.y)
				if dist < _agent.radius / 2:
					agents_to_kill.append(_agent)

				# update lastdist (max = 5)
				quant = _agent.count_distances_to_goal(
					dist, self.stuck_threshold)

				# if distances does not change, assume agent is stuck
				if quant == self.stuck_threshold:
					agents_to_kill.append(_agent)
					self.removed_agents.append(_agent)

			# add agents in cell
			for _agent in self.agents:
				_agent.cell.increase_agent_in_cell()

			# die!
			for _to_kill in agents_to_kill:
				self.agents.remove(_to_kill)

			# print("Simulation Frame:", simulationFrame, end='\r')
			simulation_frame += 1

			# check the total time. If higher than 30 seconds, save in Database and leaves
			# timeout has problems with the extra simulation for the reference agent.
			# easiest way to solve: remove it, since LAD does not have this problem.
			if time.time() - start_time > 30000:
				timeout = True
				break

		# close file
		result_file.close()

		self.simulation_time += (simulation_frame) * self.time_step

		# if timeout, need to keep going later
		if timeout:
			self.database.save_database(self)
			return pd.DataFrame(["nope"])

		# otherwise, it is done
		# Simulation Finished
		print(
			f'Total Simulation Time: {self.simulation_time} "seconds. ({simulation_frame+1} frames)')

		# print agents that were stuck
		for _rem_agent in self.removed_agents:
			self.agents_removed += 1
			print(
				f"Agent {_rem_agent.id} was removed at position: {_rem_agent.position}")

		# save the cells, for heatmap
		Parsing_Util.save_cells_file(self.output_dir, self.ip, self.cells)

		# timing until simulation finished
		self.execution_times.append(time.time())

		# ---------- Generate Results ----------
		agent_positions_per_frame, x_data, y_data = Parsing_Util.parse_agent_position_per_frame(
			self.output_dir, self.ip)

		# calculate densities, distances and velocities
		# distances
		total_dist_walked, agent_dist_walked, agents_min_disp, agents_max_disp = Metrics_Util.walked_distances(
			agent_positions_per_frame)
		max_dist_walked = max(agent_dist_walked.values())
		min_dist_walked = min(agent_dist_walked.values())

		# how many frames each agent was in the simulation
		agent_frame_count = {
			ag: len(pos_list) for ag, pos_list in agent_positions_per_frame.items()}

		# average walked
		average_dist_walked = total_dist_walked / (len(agent_frame_count))
		# with the distance walked, as well as the qnt of frames of each agent (size of each), we can calculate mean speed
		total_agent_speed, agent_speeds = Metrics_Util.average_agent_speed(self.time_step,
																		   agent_frame_count, agent_dist_walked)

		# average speed
		average_speed = total_agent_speed / (len(agent_frame_count))
		min_agent_speed = min(agents_min_disp.values()) / self.time_step
		max_agent_speed = max(agents_max_disp.values()) / self.time_step

		# average density
		# using frame
		average_frame_density = Metrics_Util.frame_average_local_density(
			self.cells)
		max_average_density = max(average_frame_density)
		max_average_density_frame = average_frame_density.index(
			max_average_density)
		average_density = fmean(average_frame_density)
		max_cell_density, max_cell_density_frame, max_cell_density_id = Metrics_Util.cell_maximum_local_density(
			self.cells)

		# average density
		# using agents
		# #for densities, we calculate the local densities for each agent, each frame
		# local_density_per_frame = Metrics_Util.agent_local_density_per_frame(agent_frame_count, agent_positions_per_frame)

		# #calculate mean values
		# total_density_sum, agent_average_local_density = Metrics_Util.agent_average_local_densities(
		# 		local_density_per_frame, agent_frame_count)
		# average_density = total_density_sum / len(agent_frame_count)
		# end densities, distances and velocities

		# average simulation time
		average_simulation_time = (
			sum(agent_frame_count.values()) * self.time_step)/len(agent_frame_count)
		min_simulation_time = min(agent_frame_count.values()) * self.time_step

		# normalizations
		if not self.ref_simulation and self.reference_agent:
			sim_time_nn = self.simulation_time / \
				self.reference_agent["total_simulation_time"]
			avg_time_nn = average_simulation_time / \
				self.reference_agent["total_simulation_time"]
			avg_spd_nn = math.exp(
				self.reference_agent["total_average_speed"] / average_speed)
			# avg_walk_nn = average_dist_walked / self.reference_agent["total_average_distance_walked"]
			avg_walk_nn = average_dist_walked / \
				(self.map_size.x * self.map_size.y)
			# avg_walk_nn = average_dist_walked / self.reference_agent["total_average_distance_walked"]
		else:
			sim_time_nn = self.simulation_time
			avg_time_nn = average_simulation_time
			avg_spd_nn = average_speed
			avg_walk_nn = average_dist_walked
		# end normalizations
		new_metric = 5 / ((1 / sim_time_nn) + (1 / avg_time_nn) +
						  (1 / average_density) + (1 / avg_spd_nn) + (1 / avg_walk_nn))
		cassol_metric = 4 / ((1 / sim_time_nn) + (1 / avg_time_nn) +
							 (1 / average_density) + (1 / avg_spd_nn))
		print("New Metric: " + str(new_metric))
		print("Cassol Metric: " + str(cassol_metric))

		# generate heatmap and trajectories
		if self.ref_simulation:
			write_result.append(["noNeed"])
			write_result.append(["noNeed"])
		else:
			write_result.append(HM_Gen.generate_heatmap(self))
			write_result.append(
				TJ_Gen.generate_trajectories(self, x_data, y_data))

		# write other results
		write_result.append(["simulation_time", self.simulation_time])
		write_result.append(["agents_distance_walked", agent_dist_walked])
		write_result.append(["average_distance_walked", average_dist_walked])
		write_result.append(["agents_speeds", agent_speeds])
		write_result.append(["average_speed", average_speed])
		write_result.append(["average_density", average_density])
		write_result.append(["average_time", average_simulation_time])
		write_result.append(["new_metric", new_metric])
		write_result.append(["cassol_metric", cassol_metric])
		# normalized results for Cassol metric
		write_result.append(["normalized_total_simulation_time", sim_time_nn])
		write_result.append(
			["normalized_average_simulation_time", avg_time_nn])
		write_result.append(["normalized_average_speed", avg_spd_nn])
		write_result.append(
			["normalized_average_distance_walked", avg_walk_nn])
		# additional results
		write_result.append(["minimum_simulation_time", min_simulation_time])
		write_result.append(["maximum_average_density", max_average_density])
		write_result.append(
			["maximum_average_density_frame", max_average_density_frame])
		write_result.append(["maximum_cell_density", max_cell_density])
		write_result.append(
			["maximum_cell_density_frame", max_cell_density_frame])
		write_result.append(["maximum_cell_density_id", max_cell_density_id])
		write_result.append(["maximum_agent_speed", max_agent_speed])
		write_result.append(["minimum_agent_speed", min_agent_speed])
		write_result.append(["maximum_distance_walked", max_dist_walked])
		write_result.append(["minimum_distance_walked", min_dist_walked])

		# clear Database, just to be sure
		if self.run_on_server:
			self.database.clear_database(self.ip, close_conn=True)

		if not self.ref_simulation and self.visualize_runtime_data:
			visualize_markers(ip=self.ip,
							  simulation_id=self.simulation_id,
							  map_width=int(self.map_size.x),
							  map_height=int(self.map_size.y))
		Parsing_Util.remove_result_files(self.output_dir, self.ip)
		# gc.collect()

		# timing until simulation finished
		self.execution_times.append(time.time())
		print("Time required to load data:",
			  self.execution_times[1]-self.execution_times[0])
		print("Time required to setup:",
			  self.execution_times[2]-self.execution_times[1])
		print("Time required to run simulation:",
			  self.execution_times[3]-self.execution_times[2])
		print("Time required to generate results:",
			  self.execution_times[4]-self.execution_times[3])

		return pd.DataFrame(write_result), self.agents_removed

	def create_map(self):
		i = j = 0
		while i < self.map_size.x:
			while j < self.map_size.y:
				self.cells.append(CellClass(
					str(i)+"-"+str(j), Vector3(i, j, 0), self.cell_size, self.PORC_QTD_Marcacoes, []))
				j += self.cell_size
			i += self.cell_size
			j = 0

	def create_markers(self):
		for _cell in self.cells:
			_cell.CreateMarkers(self.obstacles)

	def save_markers_to_file(self):
		_markerFile = open(self.output_dir + "/markers_" +
						   self.ip.replace(":", "_") + ".csv", "w")
		for _cell in self.cells:
			for _marker in _cell.markers:
				_line = _cell.id + ";" + _marker.position.get_formatted_str() + "\n"
				_markerFile.write(_line)
		_markerFile.close()

	# for each goal, vinculate the cell
	def vinculate_goals_to_cells(self):
		for _goal in self.goals:
			totalDistance = self.cell_size * 2
			for _cell in self.cells:
				distance = Vector3.Distance(_goal.position, _cell.position)

				# if distance is lower than total, change
				if distance < totalDistance:
					totalDistance = distance
					_goal.cell = _cell

	# for each cell, find its neighbors
	def find_cell_neighbors(self):
		for _cell in self.cells:
			_cell.FindNeighbor(self.cells)

	# for each agent, find its initial cell
	def find_agents_initial_cell(self):
		for _agent in self.agents:
			_distances = [Vector3.Distance(
				_agent.position, c.get_cell_center()) for c in self.cells]
			_agent.cell = self.cells[_distances.index(min(_distances))]

	# calculate the path for each agent
	def find_agents_path_json(self):
		for _agent in self.agents:
			_agent.FindPathJson(self.cells)

	# select the agent with largest distance as a reference agent
	def select_reference_agent(self):
		ref_agent: AgentClass = self.agents[0]
		max_dist = 0
		for _agent in self.agents:
			dst = _agent.GetAgentEditorPathLenght()
			if dst > max_dist:
					max_dist = dst
					ref_agent = _agent
			#for _goal in self.goals:
				#dst = Vector3.Distance(_agent.position, _goal.position)
				#if dst > max_dist:
					#max_dist = dst
					#ref_agent = _agent
		self.agents.clear()
		self.agents.append(ref_agent)

	def dump_simulation_json_data(self, data) -> None:
		f = open(f"{self.output_dir}/request_{self.simulation_id}.json", "w")
		f.write(json.dumps(data))
		f.close()

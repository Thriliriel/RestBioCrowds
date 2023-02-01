import os
from pathlib import Path
from AgentClass import AgentClass
from BioCrowdsDatabase import BioCrowdsDataBase
from Vector3Class import Vector3
from CellClass import CellClass
from MarkerClass import MarkerClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass
from Parsing.ParserJSON import ParserJSON
import Util.BioCrowdsUtil as BC_Util
import Util.HeatmapGeneration as HM_Gen
import Util.TrajectoriesGeneration as TJ_Gen
import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# import matplotlib.lines as mlines
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import base64
#import argparse
#import mysql.connector
#from mysql.connector import Error
import time
import requests
import json
import math
#import gc

class BioCrowdsClass():
	def run(self, data):
		self.ip:str = ""
		self.output_dir = os.path.abspath(os.path.dirname(__file__)) + "/OutputData"
		Path(self.output_dir).mkdir(parents=True, exist_ok=True)
		write_result = []
		start_time = time.time()
		self.reference_agent = {}
		self.run_on_server = False
		self.database = BioCrowdsDataBase()

		if self.run_on_server:
			self.database.connect_to_database()

		#default values
		#size of the scenario
		self.map_size = Vector3.Zero
		#markers density
		self.PORC_QTD_Marcacoes = 0.65
		#FPS (default: 50FPS)
		self.time_step:float = 0.02
		#size of each square cell (Ex: 2 -> cell 2x2)
		self.cell_size:float = 1
		#using path planning?
		self.path_planning = True
		#it is a reference simulation (for cassol metrics)?
		self.ref_simulation = False
		
		self.simulation_time:float = 0

		#read the config file
		BC_Util.parse_config_file(self, "Input/config.txt")
		
		#goals
		self.goals = []

		#agents
		self.agents = []

		#obstacles
		self.obstacles = []

		#cells
		self.cells:list[CellClass] = []

		#add the reference simulation, if none
		if "reference_simulation" not in data:
			data["reference_simulation"] = False
		self.ref_simulation = bool(data["reference_simulation"])

		#from json
		#json or database?
		if data['terrains'] == 'db':
			self.ip = str(data['time_stamp'])
			#take the : out
			self.ip = self.ip.replace(':', '')
			#self.LoadDatabase()
			self.database.load_database(self)
		else:
			self.simulation_time = 0
			self.map_size, self.goals, self.agents, self.obstacles, self.ip = ParserJSON.ParseJsonContent(data)
			#take the : out
			self.ip = self.ip.replace(':', '')
			self.create_map()

		#if this one is not a reference simulation, we need to simulate it with only one agent (unless it is only one), 
		#to be able to normalize the metrics later
		self.reference_agent = {}
		if not self.ref_simulation and len(self.agents) > 1:
			data["reference_simulation"] = True
			headers = {'Content-Type': 'application/json'}
			response = requests.post('http://localhost:5000/runSim', json.dumps(data), headers=headers) 
			#print("Code status: " + str(response.status_code)) 
			#ffs = json.loads(response.text)
			#print(type(ffs))
			#print("Return: " + response.text)

			#if the response contains "nope", it means it reached the 30 seconds without finishing
			#need to run again until done
			while "nope" in response.text:
				data["terrains"] = "db"
				headers = {'Content-Type': 'application/json'}
				response = requests.post('http://localhost:5000/runSim', json.dumps(data), headers=headers)

			print(response.text)
			jason = json.loads(json.loads(response.text))
			jason = jason["1"]
			self.reference_agent = BC_Util.parse_reference_simulation(jason)
			#print("dist walked type:", type(self.reference_agent["total_average_distance_walked"]))
			#print(self.reference_agent["agents_distance_walked"])
			#print(self.reference_agent)
		else:
			#if it is a reference simulation, one agent only
			#find the agent farther away from the goals
			thisLittleFucker = BC_Util.find_reference_agent(self.agents, self.goals)
			self.agents.clear()
			self.agents.append(thisLittleFucker)

		# Create and save Markers
		self.create_markers()
		self.save_markers_to_file()

		#for each goal, vinculate the cell
		self.vinculate_goals_to_cells()

		#for each cell, find its neighbors
		self.find_cell_neighbors()

		#for each agent, find its initial cell
		self.find_agents_initial_cell()

		#for each agent, calculate the path, if true (comes from Json, dont need to calculate)
		if self.path_planning:
			self.find_agents_path_json()

		#open file to write or keep writing
		result_file = BC_Util.open_result_file(self.output_dir, self.ip, data['terrains'])

		simulation_frame:int = 0

		#walking loop
		timeout = False
		while True:
			#if no agents anymore, break
			if len(self.agents) == 0:
				break

			#for each agent, we reset their info
			for ag in self.agents:
				ag.ClearAgent()
			#print("markers", len(agents[0].markers))
			#reset the markers
			for _cell in self.cells:
				for marker in _cell.markers:
					marker.ResetMarker()

			#find nearest markers for each agent
			for ag in self.agents:
				ag.FindNearMarkers()
			#	print(sum([len(c.markers) for c in cells]), len(agents[i].markers))

			#/*to find where the agent must move, we need to get the vectors from the agent to each auxin he has, and compare with
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
				#vector for each marker
				for _ag_marker in _agent.markers:
					#add the distance vector between it and the agent
					#print (_agent.position, _ag_marker.position)
					_agent.dist_to_markers.append(Vector3.Sub_vec(_ag_marker.position, _agent.position))

				#print("total", len(_agent.vetorDistRelacaoMarcacao))
				#calculate the movement vector
				_agent.CalculateMotionVector()

				#print(_agent.m)
				#calculate speed vector
				_agent.CalculateSpeed()

				#walk
				_agent.Walk(self.time_step)

				#write in file (agent id, X, Y, Z)
				result_file.write(str(_agent.id) + ";" + _agent.position.get_formatted_str(";") + "\n")

				#verify agent position, in relation to the goal. If arrived, bye
				dist = Vector3.Distance(_agent.goal.position, _agent.position)
				#print(_agent.id, " -- Dist: ", dist, " -- Radius: ", _agent.radius, " -- Agent: ", _agent.position.x, _agent.position.y)
				#print(_agent.speed.x, _agent.speed.y)
				if dist < _agent.radius / 4:
					agents_to_kill.append(_agent)

				#update lastdist (max = 5)
				if len(_agent.last_dist) == 5:
					_agent.last_dist.pop(0)

				_agent.last_dist.append(dist)

				#check them all
				qntFound = 0
				for ck in _agent.last_dist:
					if ck == dist:
						qntFound += 1

				#if distances does not change, assume agent is stuck
				if qntFound == 5:
					agents_to_kill.append(_agent)

			#die!
			for _to_kill in agents_to_kill:
				self.agents.remove(_to_kill)

			#print("Simulation Frame:", simulationFrame, end='\r')
			simulation_frame += 1

			#check the total time. If higher than 30 seconds, save in Database and leaves
			#timeout has problems with the extra simulation for the reference agent. 
			#easiest way to solve: remove it, since LAD does not have this problem.
			if time.time() - start_time > 30000:
				timeout = True
				break

		#close file
		result_file.close()

		self.simulation_time += (simulation_frame+1) * self.time_step

		#if timeout, need to keep going later
		if timeout:
			self.database.save_database(self)
			return pd.DataFrame(["nope"])
			
		#otherwise, it is done
		# Simulation Finished
		print(f'Total Simulation Time: {self.simulation_time} "seconds. ({simulation_frame+1} frames)')

		#save the cells, for heatmap
		BC_Util.save_cells_file(self.output_dir, self.ip, self.cells)
		
		# ---------- Generate Results ----------
		agent_positions_per_frame, x_data, y_data = BC_Util.parse_agent_position_by_frame(self.output_dir, self.ip)

		#generate heatmap and trajectories
		if self.ref_simulation:
			write_result.append(["noNeed"])
			write_result.append(["noNeed"])
		else:
			write_result.append(HM_Gen.generate_heatmap(self))
			write_result.append(TJ_Gen.generate_trajectories(self, x_data, y_data))

		#sim time
		hm = ["simTime", self.simulation_time]
		write_result.append(hm)

		#densities, distances and velocities
		#distances
		distanceWalked = {}
		qntFrames = {}
		totalWalked = 0

		#for each agent
		for ag in agent_positions_per_frame:
			agentWalked = 0
			lastPos = -1

			#for each position of this agent
			for pos in agent_positions_per_frame[ag]:
				#qnt frames
				if ag not in qntFrames:
					qntFrames[ag] = 1
				else:
					qntFrames[ag] += 1

				#if no position yet, just continue (need two to calculate)
				if lastPos == -1:
					#update lastPos, so we can use later
					lastPos = pos

					continue
				#else, calculate
				else:
					#distance
					agentWalked += abs(Vector3.Distance(pos, lastPos))
					lastPos = pos

			#update the dict. 
			totalWalked += agentWalked
			distanceWalked[ag] = agentWalked

		#average walked
		averageWalked = totalWalked / (len(qntFrames))
		hm = ["distanceWalked", distanceWalked]
		write_result.append(hm)
		hm = ["totalWalked", averageWalked]
		write_result.append(hm)

		#with the distance walked, as well as the qnt of frames of each agent (size of each), we can calculate mean speed
		velocities = {}
		sumVelocity = 0
		for ag in distanceWalked:
			vel = distanceWalked[ag] / (qntFrames[ag] * self.time_step)
			sumVelocity += vel
			velocities[ag] = vel

		#average velocity
		averageVelocity = sumVelocity / (len(qntFrames))

		#print(velocities)
		hm = ["velocities", velocities]
		write_result.append(hm)
		hm = ["averageVelocity", averageVelocity]
		write_result.append(hm)

		#for densities, we calculate the local densities for each agent, each frame
		localDensities = {}

		#get the maximum amount of frames
		maxframes = 0
		for fram in qntFrames:
			if qntFrames[fram] > maxframes:
				maxframes = qntFrames[fram]
		print("max comparison", maxframes, max(qntFrames.values()))

		#for each frame	
		#if dist is lower or equal sqrt(1/pi) (area of the circle, 1m²ish), update density
		maxDistance = math.sqrt(1 / math.pi)
		for frame in range(maxframes):
			localDensities[frame] = {}
			#for each agent, we check local density
			for ag in agent_positions_per_frame:
				#maybe this agent is not present in the simulation on this frame, so check it
				if frame >= len(agent_positions_per_frame[ag]):
					continue

				localDensity = 1
				for ag2 in agent_positions_per_frame:
					#maybe this agent is not present in the simulation on this frame, so check it
					if frame >= len(agent_positions_per_frame[ag2]):
						continue

					#if ag is equal ag2, it is the same agent
					if ag != ag2:
						#check distance
						distDen = Vector3.Distance(agent_positions_per_frame[ag][frame], agent_positions_per_frame[ag2][frame])
						#if dist is lower or equal 1/pi (area of the circle, 1m²ish), update density
						if distDen <= maxDistance:
							localDensity += 1

				#update local densities
				localDensities[frame][ag] = localDensity
		#if not self.refSimulation:
		#	m = open(self.outputDir + "/localdensities_" + self.ip.replace(":", "_") + ".txt", "w")
		#	for ld in localDensities:
		#		m.write(str(localDensities[ld]) + "\n")
		#	m.close()

		#print(localDensities)
		#calculate mean values
		meanLocalDensities = {}
		for ld in localDensities:
			for ag in localDensities[ld]:
				if ag not in meanLocalDensities:
					meanLocalDensities[ag] = localDensities[ld][ag]
				else:
					meanLocalDensities[ag] += localDensities[ld][ag]
		
		#if not self.refSimulation:
		#	m = open(self.outputDir + "/localdensities_" + self.ip.replace(":", "_") + ".txt", "w")
		#	m.write(str(meanLocalDensities))
		#	m.close()

		#if not self.refSimulation:
		#	m = open(self.outputDir + "/qntframes_" + self.ip.replace(":", "_") + ".txt", "w")
		#	m.write(str(qntFrames))
		#	m.close()

		mld = {}
		sumDensity = 0
		for ld in meanLocalDensities:
			dnt = meanLocalDensities[ld] / qntFrames[ld]
			sumDensity += dnt
			mld[ld] = dnt
			
		#print(mld)

		#if not self.refSimulation:
		#	m = open(self.outputDir + "/meanlocaldensities_" + self.ip.replace(":", "_") + ".txt", "w")
		#	m.write(str(mld))
		#	m.close()

		#average density
		averageDensity = sumDensity / len(qntFrames)

		hm = ["localDensities", mld]
		write_result.append(hm)
		hm = ["averageDensity", averageDensity]
		write_result.append(hm)
		#end densities, distances and velocities

		#average time
		avt = sum(qntFrames.values())
		avt /= len(qntFrames)
		avt *= self.time_step

		hm = ["averageTime", avt]
		write_result.append(hm)
		#end average time

		#normalizations. ReferenceAgent had time on index 0 and speed on index 1
		if not self.ref_simulation:
			if self.reference_agent:
				simTimeNN = self.simulation_time / self.reference_agent["total_simulation_time"]
				avgTimeNN = avt / self.reference_agent["total_simulation_time"]
				avgVelNN = math.exp(self.reference_agent["total_average_speed"] / averageVelocity)
				avgWalNN = averageWalked / self.reference_agent["total_average_distance_walked"]
			else:
				simTimeNN = self.simulation_time
				avgTimeNN = avt
				avgVelNN = averageVelocity
				avgWalNN = averageWalked
		else:
			simTimeNN = self.simulation_time
			avgTimeNN = avt
			avgVelNN = averageVelocity
			avgWalNN = averageWalked
		#end normalizations

		#Cassol metric (harmonic mean)
		#extra: average distance walked
		cassol = 5 / ((1 / simTimeNN) + (1 / avgTimeNN) + (1 / averageDensity) + (1 / avgVelNN) + + (1 / avgWalNN))
		print ("Cassol: " + str(cassol))
		hm = ["cassol", cassol]
		write_result.append(hm)
		#end Cassol metric (harmonic mean)

		#just to test stuff
		#if self.refSimulation:
		#	m = open(self.outputDir + "/metricsRef_" + self.ip.replace(":", "_") + ".txt", "w")
		#else:
		#	m = open(self.outputDir + "/metrics_" + self.ip.replace(":", "_") + ".txt", "w")
		#m.write(str(writeResult))
		#m.close()

		#clear Database, just to be sure
		if self.run_on_server:
			self.database.clear_database(self.ip, close_conn=True)

		# plt.close()

		# resultFile.csv
		self.remove_result_files()
		#gc.collect()

		#return plt
		return pd.DataFrame(write_result)


	def create_map(self):
		i = j = 0
		while i < self.map_size.x:
			while j < self.map_size.y:
				self.cells.append(CellClass(str(i)+"-"+str(j), Vector3(i, j, 0), self.cell_size, self.PORC_QTD_Marcacoes, []))
				j += self.cell_size
			i += self.cell_size
			j = 0

	def create_markers(self):
		for _cell in self.cells:
			_cell.CreateMarkers(self.obstacles)

	def save_markers_to_file(self):
		_markerFile = open(self.output_dir + "/markers_" + self.ip.replace(":", "_") + ".csv", "w")
		for _cell in self.cells:
			for _marker in _cell.markers:
				_line = _cell.id + ";" + _marker.position.get_formatted_str() + "\n"
				_markerFile.write(_line)
		_markerFile.close()

	#for each goal, vinculate the cell
	def vinculate_goals_to_cells(self):
		for _goal in self.goals:
			totalDistance = self.cell_size * 2
			for _cell in self.cells:
				distance = Vector3.Distance(_goal.position, _cell.position)

				#if distance is lower than total, change
				if distance < totalDistance:
					totalDistance = distance
					_goal.cell = _cell

	#for each cell, find its neighbors
	def find_cell_neighbors(self):
		for _cell in self.cells: 
			_cell.FindNeighbor(self.cells)

	#for each agent, find its initial cell
	def find_agents_initial_cell(self):
		for _agent in self.agents:
			minDis = 5
			for _cell in self.cells:
				dist = Vector3.Distance(_agent.position,_cell.position)
				if dist < minDis:
					minDis = dist
					_agent.cell = _cell

	#calculate the path for each agent
	def find_agents_path_json(self):
		for _agents in self.agents:
			_agents.FindPathJson(self.cells)
		

	#remove result files
	def remove_result_files(self):
		csv_str = self.ip.replace(":", "_") + ".csv"
		png_str = self.ip.replace(":", "_") + ".png"
		txt_str = self.ip.replace(":", "_") + ".txt"

		if os.path.isfile(self.output_dir + "/resultFile_" + csv_str):
			os.remove(self.output_dir + "/resultFile_" + csv_str)

		# heatmap.png
		if os.path.isfile(self.output_dir + "/heatmap_" + png_str):
			os.remove(self.output_dir + "/heatmap_" + png_str)

		# markers.csv
		if os.path.isfile(self.output_dir + "/markers_" + csv_str):
			os.remove(self.output_dir + "/markers_" + csv_str)

		# resultCellFile.txt
		if os.path.isfile(self.output_dir + "/resultCellFile_" + txt_str):
			os.remove(self.output_dir + "/resultCellFile_" + txt_str)

		# trajectories.png
		if os.path.isfile(self.output_dir + "/trajectories_" + png_str):
			os.remove(self.output_dir + "/trajectories_" + png_str)
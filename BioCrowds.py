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
import psycopg2
import requests
import json
import math
#import gc

class BioCrowdsClass():
	def run(self, data):
		self.ip = ''
		self.outputDir = os.path.abspath(os.path.dirname(__file__)) + "/OutputData"
		Path(self.outputDir).mkdir(parents=True, exist_ok=True)
		writeResult = []
		startTime = time.time()
		self.reference_agent = {}
		self.run_on_server = False
		self.database = BioCrowdsDataBase()

		if self.run_on_server:
			self.database.ConnectDB()

		#default values
		#size of the scenario
		self.mapSize = Vector3.Zero
		#markers density
		self.PORC_QTD_Marcacoes = 0.65
		#FPS (default: 50FPS)
		self.timeStep = 0.02
		#size of each square cell (Ex: 2 -> cell 2x2)
		self.cellSize = 1
		#using path planning?
		self.pathPlanning = True
		#it is a reference simulation (for cassol metrics)?
		self.refSimulation = False

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

		self.refSimulation = bool(data["reference_simulation"])

		#from json
		#json or database?
		if data['terrains'] == 'db':
			self.ip = data['time_stamp']
			#take the : out
			self.ip = self.ip.replace(':', '')
			self.LoadDatabase()
		else:
			self.simulationTime = 0
			self.mapSize, self.goals, self.agents, self.obstacles, self.ip = ParserJSON.ParseJsonContent(data)
			#take the : out
			self.ip = self.ip.replace(':', '')
			self.create_map()

		#if this one is not a reference simulation, we need to simulate it with only one agent (unless it is only one), 
		#to be able to normalize the metrics later
		self.reference_agent = {}
		if not self.refSimulation and len(self.agents) > 1:
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
		#if self.pathPlanning:
		#	for i in range(0, len(self.agents)):
		#		self.agents[i].FindPath()
		if self.pathPlanning:
			for a in self.agents:
				a.FindPathJson(self.cells)

		#open file to write or keep writing
		cSVPath = self.outputDir + "/resultFile_" + (self.ip.replace(":", "_")) + ".csv"
		if data['terrains'] == 'db':
			resultFile = open(cSVPath, "a")
			# resultFile = open("resultFile.csv", "a")
		else:
			resultFile = open(cSVPath, "w")
			# resultFile = open("resultFile.csv", "w")

		simulationFrame = 0

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

			agentsToKill = []
			frame = 0
			while frame < len(self.agents):
				agentMarkers = self.agents[frame].markers

				#vector for each marker
				for j in range(0, len(agentMarkers)):
					#add the distance vector between it and the agent
					#print (agents[i].position, agentMarkers[j].position)
					self.agents[frame].vetorDistRelacaoMarcacao.append(Vector3.Sub_vec(agentMarkers[j].position, self.agents[frame].position))

				#print("total", len(agents[i].vetorDistRelacaoMarcacao))
				#calculate the movement vector
				self.agents[frame].CalculateMotionVector()

				#print(agents[i].m)
				#calculate speed vector
				self.agents[frame].CalculateSpeed()

				#walk
				self.agents[frame].Walk(self.timeStep)

				#write in file (agent id, X, Y, Z)
				resultFile.write(str(self.agents[frame].id) + ";" + str(self.agents[frame].position.x) + ";" + str(self.agents[frame].position.y) + ";" + str(self.agents[frame].position.z) + "\n")

				#verify agent position, in relation to the goal. If arrived, bye
				dist = Vector3.Distance(self.agents[frame].goal.position, self.agents[frame].position)
				#print(agents[i].id, " -- Dist: ", dist, " -- Radius: ", agents[i].radius, " -- Agent: ", agents[i].position.x, agents[i].position.y)
				#print(agents[i].speed.x, agents[i].speed.y)
				if dist < self.agents[frame].radius / 4:
					agentsToKill.append(frame)

				#update lastdist (max = 5)
				if len(self.agents[frame].lastDist) == 5:
					self.agents[frame].lastDist.pop(0)

				self.agents[frame].lastDist.append(dist)

				#check them all
				qntFound = 0
				for ck in self.agents[frame].lastDist:
					if ck == dist:
						qntFound += 1

				#if distances does not change, assume agent is stuck
				if qntFound == 5:
					agentsToKill.append(frame)

				frame += 1

			#die!
			if len(agentsToKill) > 0:
				for frame in range(0, len(agentsToKill)):
					self.agents.pop(agentsToKill[frame])

			#print("Simulation Frame:", simulationFrame, end='\r')
			simulationFrame += 1

			#check the total time. If higher than 30 seconds, save in Database and leaves
			#timeout has problems with the extra simulation for the reference agent. 
			#easiest way to solve: remove it, since LAD does not have this problem.
			if time.time() - startTime > 30000:
				timeout = True
				break

		#close file
		resultFile.close()

		self.simulationTime += (simulationFrame+1) * self.timeStep

		#if timeout, need to keep going later
		if timeout:
			self.SaveDatabase()
			return pd.DataFrame(["nope"])
			
		#otherwise, it is done
		# Simulation Finished
		print(f'Total Simulation Time: {self.simulationTime} "seconds. ({simulationFrame+1} frames)')

		#save the cells, for heatmap
		#resultCellsFile = open("resultCellFile.txt", "w")
		resultCellsFile = open(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt", "w")
		thisX = 0
		firstColumn = True
		for _cell in self.cells:
			if thisX != _cell.position.x:
				thisX = _cell.position.x
				resultCellsFile.write("\n")
				firstColumn = True

			if firstColumn:
				resultCellsFile.write(str(len(_cell.passedAgents)))
				firstColumn = False
			else:
				resultCellsFile.write("," + str(len(_cell.passedAgents)))


		resultCellsFile.close()

		
		#generate heatmap
		dataFig = []
		dataTemp = []
	
		#open file to read
		# for line in open("resultCellFile.txt"):
		for line in open(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt"):
			stripLine = line.replace('\n', '')
			strip = stripLine.split(',')
			dataTemp = []

			for af in strip:
				dataTemp.insert(0, float(af))

			dataFig.append(dataTemp)

		#datafig has all qnt of agents passed for each cell.
		heatmap = np.array(dataFig)
		heatmap = heatmap.transpose()

		figHeatmap = px.imshow(heatmap, color_continuous_scale="Viridis", labels=dict(color="Densidade"))

		# Plotly configs

		figHeatmap.update_layout(
			template = "simple_white",
			#title = "Mapa de Densidades",
			title = "Density Map",
			title_x=0.5,
			#legend_title = "Densidade"
			legend_title = "Density"
		)

		figHeatmap.update_xaxes(range=[-0.5, self.mapSize.x - 0.5], visible = False)
		figHeatmap.update_yaxes(range=[-0.5, self.mapSize.y - 0.5], visible = False)

		figHeatmap.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
		figHeatmap.update_layout(yaxis=dict(tickmode='linear', tick0=0, dtick=1))

		figHeatmap.write_image(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png")

		hm = []
		# with open("heatmap.png", "rb") as img_file:
		with open(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png", "rb") as img_file:
			hm = ["heatmap", base64.b64encode(img_file.read())]

		#just need to generate the maps when it is not reference agent
		if not self.refSimulation:
			writeResult.append(hm)
		else:
			writeResult.append(["noNeed"])
		os.remove(self.outputDir + "/heatmap_"+self.ip.replace(":", "_")+".png")
		#end heatmap

		#trajectories
		# plt.close()
		dataFig = []
		# values on x-axis
		x = []
		# values on y-axis
		y = []

		#dictionary to calculate speeds, distances and densities later
		agentPositionsByFrame = {}

		#open file to read
		#id, x, y, z
		#for line in open("resultFile.csv"):
		for line in open(self.outputDir + "/resultFile_" + self.ip.replace(":", "_") + ".csv"):
			csv_row = line.split(';')

			#parse
			agentId = int(csv_row[0])
			agentX = float(csv_row[1])
			agentY = float(csv_row[2])
			agentZ = float(csv_row[3])

			#points for the trajectories
			x.append(agentX)
			y.append(agentY)

			#agents positions by frame, for density, distance and velocities
			#if not exists yet, create the list
			if agentId not in agentPositionsByFrame:
				agentPositionsByFrame[agentId] = []

			agentPositionsByFrame[agentId].append(Vector3(agentX, agentY, agentZ))
				
		# Creating trajetories figure

		figTrajectories = make_subplots(rows=1, cols=1)
			
		figTrajectories.add_scatter(x=x, 
									y=y, 
									mode='markers', 
									#name='Trajetória', 
									name='Trajectory', 
									marker=dict(size=4), 
									marker_color="rgb(0,0,255)")

		# figTrajectories = px.scatter(x = x, y = y)

		major_ticks = np.arange(0, self.mapSize.x + 1, self.cellSize)
		# ax.set_xticks(major_ticks)
		# ax.set_yticks(major_ticks)

		figTrajectories.update_xaxes(range = [0, self.mapSize.x], showgrid=True, gridwidth=1, gridcolor='Gray')
		figTrajectories.update_yaxes(range = [0, self.mapSize.y], showgrid=True, gridwidth=1, gridcolor='Gray')

		figTrajectories.update_layout(xaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))
		figTrajectories.update_layout(yaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))

		figTrajectories.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
		figTrajectories.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
			

		#draw obstacles
		for obs in range(0, len(self.obstacles)):
			coord = []
			for pnt in range(0, len(self.obstacles[obs].points)):
				coord.append([self.obstacles[obs].points[pnt].x, self.obstacles[obs].points[pnt].y])
			coord.append(coord[0]) #repeat the first point to create a 'closed loop'
			xs, ys = zip(*coord) #create lists of x and y values
			# plt.plot(xs,ys)
			figTrajectories.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False))
				

		x = []
		y = []

		#goals
		for _goal in self.goals:
			x.append(_goal.position.x)
			y.append(_goal.position.y)

		# plt.plot(x, y, 'bo', markersize=10, label = "Objetivo")
		figTrajectories.add_scatter(x = x, y = y, mode = 'markers', name = 'Objetivo', marker = dict( size = 12), marker_color="rgb(255,0,0)")
			
		figTrajectories.update_layout(
			template="simple_white",
			title="Trajetórias dos Agentes",
			title_x=0.5,
			legend = dict(
				orientation="h",
				yanchor="bottom",
				y=1.02,
				xanchor="right",
				x=1
			)
		)

		# plt.savefig("trajectories.png", dpi=75)
		# plt.savefig(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png", dpi=75)
		figTrajectories.write_image(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png")

		hm = []
		# with open("trajectories.png", "rb") as img_file:
		with open(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png", "rb") as img_file:
			hm = ["trajectories", base64.b64encode(img_file.read())]

		#just need to generate the maps when it is not reference agent
		if not self.refSimulation:
			writeResult.append(hm)
		else:
			writeResult.append(["noNeed"])
		os.remove(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png")
		#end trajectories

		#sim time
		hm = ["simTime", self.simulationTime]
		writeResult.append(hm)

		#densities, distances and velocities
		#distances
		distanceWalked = {}
		qntFrames = {}
		totalWalked = 0

		#for each agent
		for ag in agentPositionsByFrame:
			agentWalked = 0
			lastPos = -1

			#for each position of this agent
			for pos in agentPositionsByFrame[ag]:
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
		writeResult.append(hm)
		hm = ["totalWalked", averageWalked]
		writeResult.append(hm)

		#with the distance walked, as well as the qnt of frames of each agent (size of each), we can calculate mean speed
		velocities = {}
		sumVelocity = 0
		for ag in distanceWalked:
			vel = distanceWalked[ag] / (qntFrames[ag] * self.timeStep)
			sumVelocity += vel
			velocities[ag] = vel

		#average velocity
		averageVelocity = sumVelocity / (len(qntFrames))

		#print(velocities)
		hm = ["velocities", velocities]
		writeResult.append(hm)
		hm = ["averageVelocity", averageVelocity]
		writeResult.append(hm)

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
			for ag in agentPositionsByFrame:
				#maybe this agent is not present in the simulation on this frame, so check it
				if frame >= len(agentPositionsByFrame[ag]):
					continue

				localDensity = 1
				for ag2 in agentPositionsByFrame:
					#maybe this agent is not present in the simulation on this frame, so check it
					if frame >= len(agentPositionsByFrame[ag2]):
						continue

					#if ag is equal ag2, it is the same agent
					if ag != ag2:
						#check distance
						distDen = Vector3.Distance(agentPositionsByFrame[ag][frame], agentPositionsByFrame[ag2][frame])
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
		writeResult.append(hm)
		hm = ["averageDensity", averageDensity]
		writeResult.append(hm)
		#end densities, distances and velocities

		#average time
		avt = sum(qntFrames.values())
		avt /= len(qntFrames)
		avt *= self.timeStep

		hm = ["averageTime", avt]
		writeResult.append(hm)
		#end average time

		#normalizations. ReferenceAgent had time on index 0 and speed on index 1
		if not self.refSimulation:
			if self.reference_agent:
				simTimeNN = self.simulationTime / self.reference_agent["total_simulation_time"]
				avgTimeNN = avt / self.reference_agent["total_simulation_time"]
				avgVelNN = math.exp(self.reference_agent["total_average_speed"] / averageVelocity)
				avgWalNN = averageWalked / self.reference_agent["total_average_distance_walked"]
			else:
				simTimeNN = self.simulationTime
				avgTimeNN = avt
				avgVelNN = averageVelocity
				avgWalNN = averageWalked
		else:
			simTimeNN = self.simulationTime
			avgTimeNN = avt
			avgVelNN = averageVelocity
			avgWalNN = averageWalked
		#end normalizations

		#Cassol metric (harmonic mean)
		#extra: average distance walked
		cassol = 5 / ((1 / simTimeNN) + (1 / avgTimeNN) + (1 / averageDensity) + (1 / avgVelNN) + + (1 / avgWalNN))
		print ("Cassol: " + str(cassol))
		hm = ["cassol", cassol]
		writeResult.append(hm)
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
			self.database.ClearDatabase()
			self.database.close_connection()

		# plt.close()

		# resultFile.csv
		self.remove_result_files()
		#gc.collect()

		#return plt
		return pd.DataFrame(writeResult)


	def create_map(self):
		i = j = 0
		while i < self.mapSize.x:
			while j < self.mapSize.y:
				self.cells.append(CellClass(str(i)+"-"+str(j), Vector3(i, j, 0), self.cellSize, self.PORC_QTD_Marcacoes, []))
				j += self.cellSize
			i += self.cellSize
			j = 0

	def create_markers(self):
		for _cell in self.cells:
			_cell.CreateMarkers(self.obstacles)

	def save_markers_to_file(self):
		_markerFile = open(self.outputDir + "/markers_" + self.ip.replace(":", "_") + ".csv", "w")
		for _cell in self.cells:
			for _marker in _cell.markers:
				_line = _cell.id + ";" + _marker.position.get_formatted_str() + "\n"
				_markerFile.write(_line)
		_markerFile.close()

	#for each goal, vinculate the cell
	def vinculate_goals_to_cells(self):
		for _goal in self.goals:
			totalDistance = self.cellSize * 2
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

	def remove_result_files(self):
		csv_str = self.ip.replace(":", "_") + ".csv"
		png_str = self.ip.replace(":", "_") + ".png"
		txt_str = self.ip.replace(":", "_") + ".txt"

		if os.path.isfile(self.outputDir + "/resultFile_" + csv_str):
			os.remove(self.outputDir + "/resultFile_" + csv_str)

		# heatmap.png
		if os.path.isfile(self.outputDir + "/heatmap_" + png_str):
			os.remove(self.outputDir + "/heatmap_" + png_str)

		# markers.csv
		if os.path.isfile(self.outputDir + "/markers_" + csv_str):
			os.remove(self.outputDir + "/markers_" + csv_str)

		# resultCellFile.txt
		if os.path.isfile(self.outputDir + "/resultCellFile_" + txt_str):
			os.remove(self.outputDir + "/resultCellFile_" + txt_str)

		# trajectories.png
		if os.path.isfile(self.outputDir + "/trajectories_" + png_str):
			os.remove(self.outputDir + "/trajectories_" + png_str)

	def LoadDatabase(self):
		cursor = self.conn.cursor()

		#config
		#print("SELECT * FROM config where id = '" + self.ip + "'")
		cursor.execute("SELECT * FROM config where id = '" + self.ip + "'")
		myresult = cursor.fetchall()
		cursor.close()
		#print(myresult)
		self.mapSize = Vector3(float(myresult[0][1]), float(myresult[0][2]), float(myresult[0][3]))
		self.PORC_QTD_Marcacoes = float(myresult[0][4])
		self.timeStep = float(myresult[0][5])
		self.cellSize = float(myresult[0][6])
		if int(myresult[0][7]) == 0:
			self.pathPlanning =  False
		else:
			self.pathPlanning =  True

		self.simulationTime = float(myresult[0][8])

		cursor = self.conn.cursor()

		#goals
		cursor.execute("SELECT id, x, y, z FROM goals where ip = '" + self.ip + "'")
		myresult = cursor.fetchall()
		cursor.close()

		for res in myresult:
			self.goals.append(GoalClass(int(res[0]), Vector3(float(res[1]), float(res[2]), float(res[3]))))

		cursor = self.conn.cursor()

		#obstacles
		cursor.execute("SELECT id FROM obstacles where ip = '" + self.ip + "'")
		myresultObs = cursor.fetchall()
		cursor.close()

		for res in myresultObs:
			self.obstacles.append(ObstacleClass(int(res[0])))

			cursor = self.conn.cursor()
			#points
			cursor.execute("SELECT x, y, z FROM obstacles_points where ip = '"+self.ip+"' and id_obstacle = "+str(res[0]))
			myresult = cursor.fetchall()
			cursor.close()

			for pnt in myresult:
				self.obstacles[len(self.obstacles)-1].AddPoint(Vector3(float(pnt[0]), float(pnt[1]), float(pnt[2])))

		#agents
		cursor = self.conn.cursor()
		cursor.execute("SELECT id, x, y, z, goal, radius, maxspeed FROM agents where ip = '" + self.ip + "'")
		myresultag = cursor.fetchall()
		cursor.close()

		for res in myresultag:
			goalId = int(res[4])
			thisGoal = self.goals[0]
			for gl in self.goals:
				if goalId == gl.id:
					thisGoal = gl
					break

			self.agents.append(AgentClass(int(res[0]), thisGoal, float(res[5]), float(res[6]), self.pathPlanning, Vector3(float(res[1]), float(res[2]), float(res[3]))))

			cursor = self.conn.cursor()
			#paths
			cursor.execute("SELECT x, y, z FROM agents_paths where ip = '"+self.ip+"' and id_agent = "+str(res[0]))
			myresult = cursor.fetchall()
			cursor.close()

			for pnt in myresult:
				self.agents[len(self.agents)-1].AddTempPath(Vector3(float(pnt[0]), float(pnt[1]), float(pnt[2])))

		#cells
		cursor = self.conn.cursor()
		cursor.execute("SELECT name, x, y, z, radius, density, passedAgents FROM cells where ip = '" + self.ip + "' order by id asc")
		myresult = cursor.fetchall()
		cursor.close()

		for res in myresult:
			self.cells.append(CellClass(str(res[0]), Vector3(float(res[1]), float(res[2]), float(res[3])), float(res[4]), float(res[5]), []))

			#passed agents
			pas = str(res[6])
			if pas != "":
				passed = pas.split(',')
				for pa in passed:
					self.cells[len(self.cells)-1].AddPassedAgent(int(pa))

		#it is loaded, we can clear now
		self.database.ClearDatabase()

	def SaveDatabase(self):
		cursor = self.conn.cursor()

		#config
		sqlString = 'insert into config (id, mapx, mapy, mapz, markerdensity, timestep, cellsize, usepp, simtime) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);'
		records = (self.ip, self.mapSize.x, self.mapSize.y, self.mapSize.z, self.PORC_QTD_Marcacoes, self.timeStep, self.cellSize, int(self.pathPlanning == True), self.simulationTime)
		cursor.execute(sqlString, records)
		self.conn.commit()

		cursor.close()
		cursor = self.conn.cursor()

		#goals
		sqlString = 'insert into goals (ip, id, x, y, z) values (%s, %s, %s, %s, %s);'
		records = []
		for gl in self.goals:
			rec = [self.ip, gl.id, gl.position.x, gl.position.y, gl.position.z]
			records.append(rec)

		#print(sqlString)
		cursor.executemany(sqlString, records)
		self.conn.commit()

		cursor.close()
		cursor = self.conn.cursor()

		#obstacles
		for ob in self.obstacles:
			sqlString = 'insert into obstacles (ip, id) values (%s, %s);'
			records = (self.ip, ob.id)
			cursor.execute(sqlString, records)
			self.conn.commit()
			cursor.close()
			cursor = self.conn.cursor()

			#points
			sqlString = 'insert into obstacles_points (ip, id_obstacle, x, y, z) values (%s, %s, %s, %s, %s);'
			records = []
			for po in ob.points:
				rec = [self.ip, ob.id, po.x, po.y, po.z]
				records.append(rec)

			cursor.executemany(sqlString, records)
			self.conn.commit()

			cursor.close()
			cursor = self.conn.cursor()

		#agents
		for ag in self.agents:
			sqlString = 'insert into agents (ip, id, x, y, z, goal, radius, maxspeed) values (%s, %s, %s, %s, %s, %s, %s, %s);'
			records = [self.ip, ag.id, ag.position.x, ag.position.y, ag.position.z, ag.goal.id, ag.radius, ag.maxSpeed]
			cursor.execute(sqlString, records)
			self.conn.commit()
			cursor.close()
			cursor = self.conn.cursor()

			#paths
			sqlString = 'insert into agents_paths (ip, id_agent, x, y, z) values (%s, %s, %s, %s, %s);'
			records = []
			for po in ag.path:
				rec = [self.ip, ag.id, po.position.x, po.position.y, po.position.z]
				records.append(rec)

			cursor.executemany(sqlString, records)
			self.conn.commit()

			cursor.close()
			cursor = self.conn.cursor()

		#cells
		sqlString = 'insert into cells (ip, id, name, x, y, z, radius, density, passedAgents) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);'
		records = []
		idc = 0
		for cl in self.cells:
			#string for passed agents
			passed = ""
			for pa in cl.passedAgents:
				if passed == "":
					passed += str(pa)
				else:
					passed += "," + str(pa)

			#print(cl.id)
			rec = [self.ip, idc, cl.id, cl.position.x, cl.position.y, cl.position.z, cl.cellRadius, cl.density, passed]
			records.append(rec)
			idc += 1

		#print(sqlString)
		cursor.executemany(sqlString, records)
		self.conn.commit()

		cursor.close()
import os
from pathlib import Path
from AgentClass import AgentClass
from Vector3Class import Vector3
from CellClass import CellClass
from MarkerClass import MarkerClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass
from Parsing.ParserJSON import ParserJSON
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
#import gc

class BioCrowds():
	def run(self, data):
		self.ip = ''
		self.outputDir = os.path.abspath(os.path.dirname(__file__)) + "/OutputData/"
		writeResult = []
		startTime = time.time()

		#self.ConnectDB()

		#from Json
		#terrainSizeJson = data['terrains'][0]['terrain_size']
		#goalsJson = data['goals']
		#agentsJson = data
		#obstaclesJson = data['obstacles']

		#default values
		#size of the scenario
		self.mapSize = Vector3.Zero
		#markers density
		self.PORC_QTD_Marcacoes = 0.65
		#FPS (default: 50FPS)
		self.timeStep = 0.02
		#size of each square cell (Ex: 2 -> cell 2x2)
		self.cellSize = 2
		#using path planning?
		self.pathPlanning = True

		#read the config file
		lineCount = 1
		for line in open("Input/config.txt", "r"):
			if '#' in line:
				continue
			if lineCount == 1:
				#markers density
				self.PORC_QTD_Marcacoes = float(line)
			elif lineCount == 2:
				#FPS
				self.timeStep = float(line)
			elif lineCount == 3:
				#size of each square cell
				self.cellSize = int(line)
			elif lineCount == 4:
				#size of the scenario (comes from json, so no needed)
				sp = line.split(',')
				self.mapSize = Vector3(int(sp[0]), int(sp[1]), int(sp[2]))
			elif lineCount == 5:
				#using path planning?
				if line.lower() == 'false':
					self.pathPlanning = False
				else:
					self.pathPlanning = True

			lineCount += 1

		#goals
		self.goals = []

		#agents
		self.agents = []

		#obstacles
		self.obstacles = []

		#cells
		self.cells = []

		#create the cells and markers
		def CreateMap():
			i = j = 0
			while i < self.mapSize.x:
				while j < self.mapSize.y:
					self.cells.append(CellClass(str(i)+"-"+str(j), Vector3(i, j, 0), self.cellSize, self.PORC_QTD_Marcacoes, []))
					j += self.cellSize
				i += self.cellSize
				j = 0

		#create markers
		def CreateMarkers():
			for i in range(0, len(self.cells)):
				self.cells[i].CreateMarkers(self.obstacles)
				#print("Qnt created: ", len(self.cells[i].markers))

		#save markers in file
		def SaveMarkers():
			# markerFile = open("markers.csv", "w")
			markerFile = open(self.outputDir + "/markers_" + self.ip.replace(":", "_") + ".csv", "w")
			for i in range(0, len(self.cells)):
				for j in range(0, len(self.cells[i].markers)):
					markerFile.write(self.cells[i].id + ";" + str(self.cells[i].markers[j].position.x) + ";" + str(self.cells[i].markers[j].position.y) + ";" + str(self.cells[i].markers[j].position.z) + "\n")
			markerFile.close()

		#from json
		#json or database?
		if data['terrains'] == 'db':
			self.ip = data['time_stamp']
			self.LoadDatabase()
		else:
			self.simulationTime = 0
			self.mapSize, self.goals, self.agents, self.obstacles, self.ip = ParserJSON.ParseJsonContent(data)
			CreateMap()

		#print(self.cells[0].id)
		CreateMarkers()
		SaveMarkers()

		#for each goal, vinculate the cell
		for i in range(0, len(self.goals)):
			totalDistance = self.cellSize * 2
			for j in range(0, len(self.cells)):
				distance = Vector3.Distance(self.goals[i].position, self.cells[j].position)

				#if distance is lower than total, change
				if distance < totalDistance:
					totalDistance = distance
					self.goals[i].cell = self.cells[j]

		#for each cell, find its neighbors
		for i in range(0, len(self.cells)):
			self.cells[i].FindNeighbor(self.cells)

		#for each agent, find its initial cell
		for i in range(0, len(self.agents)):
			minDis = 5
			for c in range(0, len(self.cells)):
				dist = Vector3.Distance(self.agents[i].position, self.cells[c].position)
				if dist < minDis:
					minDis = dist
					self.agents[i].cell = self.cells[c]

		#for each agent, calculate the path, if true (comes from Json, dont need to calculate)
		#if self.pathPlanning:
		#	for i in range(0, len(self.agents)):
		#		self.agents[i].FindPath()
		if self.pathPlanning:
			for i in range(0, len(self.agents)):
				self.agents[i].FindPathJson(self.cells)

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
			for i in range(0, len(self.agents)):
				self.agents[i].ClearAgent()
			#print("markers", len(agents[0].markers))
			#reset the markers
			for i in range(0, len(self.cells)):
				for j in range(0, len(self.cells[i].markers)):
					self.cells[i].markers[j].ResetMarker()

			#find nearest markers for each agent
			for i in range(0, len(self.agents)):
				self.agents[i].FindNearMarkers()
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
			i = 0
			while i < len(self.agents):
				agentMarkers = self.agents[i].markers

				#vector for each marker
				for j in range(0, len(agentMarkers)):
					#add the distance vector between it and the agent
					#print (agents[i].position, agentMarkers[j].position)
					self.agents[i].vetorDistRelacaoMarcacao.append(Vector3.Sub_vec(agentMarkers[j].position, self.agents[i].position))

				#print("total", len(agents[i].vetorDistRelacaoMarcacao))
				#calculate the movement vector
				self.agents[i].CalculateMotionVector()

				#print(agents[i].m)
				#calculate speed vector
				self.agents[i].CalculateSpeed()

				#walk
				self.agents[i].Walk(self.timeStep)

				#write in file
				resultFile.write(str(self.agents[i].id) + ";" + str(self.agents[i].position.x) + ";" + str(self.agents[i].position.y) + ";" + str(self.agents[i].position.z) + "\n")

				#verify agent position, in relation to the goal. If arrived, bye
				dist = Vector3.Distance(self.agents[i].goal.position, self.agents[i].position)
				#print(agents[i].id, " -- Dist: ", dist, " -- Radius: ", agents[i].radius, " -- Agent: ", agents[i].position.x, agents[i].position.y)
				#print(agents[i].speed.x, agents[i].speed.y)
				if dist < self.agents[i].radius / 4:
					agentsToKill.append(i)

				#update lastdist (max = 5)
				if len(self.agents[i].lastDist) == 5:
					self.agents[i].lastDist.pop(0)

				self.agents[i].lastDist.append(dist)

				#check them all
				qntFound = 0
				for ck in self.agents[i].lastDist:
					if ck == dist:
						qntFound += 1

				#if distances does not change, assume agent is stuck
				if qntFound == 5:
					agentsToKill.append(i)

				i += 1

			#die!
			if len(agentsToKill) > 0:
				for i in range(0, len(agentsToKill)):
					self.agents.pop(agentsToKill[i])

			print("Simulation Frame:", simulationFrame, end='\r')
			simulationFrame += 1

			#check the total time. If higher than 20 seconds, save in Database and leaves
			#if time.time() - startTime > 2000:
			#	timeout = True
			#	break

		#close file
		resultFile.close()

		self.simulationTime += (simulationFrame+1) * self.timeStep

		#if timeout, need to keep going later
		if timeout:
		#	self.SaveDatabase()
			return pd.DataFrame(["nope"])
		#otherwise, it is done
		else:
			print(f'Total Simulation Time: {self.simulationTime} "seconds. ({simulationFrame+1} frames)')

			#save the cells, for heatmap
			#resultCellsFile = open("resultCellFile.txt", "w")
			resultCellsFile = open(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt", "w")
			thisX = 0
			firstColumn = True
			for cell in self.cells:
				if thisX != cell.position.x:
					thisX = cell.position.x
					resultCellsFile.write("\n")
					firstColumn = True

				if firstColumn:
					resultCellsFile.write(str(len(cell.passedAgents)))
					firstColumn = False
				else:
					resultCellsFile.write("," + str(len(cell.passedAgents)))


			resultCellsFile.close()

			#generate heatmap
			dataFig = []

			#open file to read
			# for line in open("resultCellFile.txt"):
			for line in open(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt"):
				stripLine = line.replace('\n', '')
				strip = stripLine.split(',')
				dataTemp = []

				for af in strip:
					dataTemp.insert(0, float(af))

				dataFig.append(dataTemp)

			heatmap = np.array(dataFig)
			heatmap = heatmap.transpose()

			# fig, ax = plt.subplots()
			# im = ax.imshow(heatmap)

			figHeatmap = px.imshow(heatmap, color_continuous_scale="Viridis", labels=dict(color="Densidade"))



			# Show all ticks and label them with the respective list entries
			# ax.set_xticks(np.arange(self.mapSize.x/self.cellSize))
			# ax.set_yticks(np.arange(self.mapSize.y/self.cellSize))

			#plt.axis([0, self.mapSize.x, 0, self.mapSize.y])

			# Rotate the tick labels and set their alignment.
			# plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
			# 		 rotation_mode="anchor")

			# ax.get_xaxis().set_visible(False)
			# ax.get_yaxis().set_visible(False)

			# Loop over data dimensions and create text annotations.
			#for i in range(int(self.mapSize.x/self.cellSize)):
			#	for j in range(int(self.mapSize.y/self.cellSize)):
			#		text = ax.text(j, i, heatmap[i, j],
			#						ha="center", va="center", color="w")
			# cbar = ax.figure.colorbar(im, ax=ax)
			# cbar.ax.set_ylabel("Densidade", rotation=-90, va="bottom")
			# ax.set_title("Mapa de Densidades")

			#ax.legend(title='Colors',title_fontsize=16,loc='center left', bbox_to_anchor=(1, 0.5))

			# fig.tight_layout()

			# Plotly configs

			figHeatmap.update_layout(
				template = "simple_white",
				title = "Mapa de Densidades",
				title_x=0.5,
				legend_title = "Densidade"
			)

			figHeatmap.update_xaxes(range=[-0.5, 14.5], visible = False)
			figHeatmap.update_yaxes(range=[-0.5, 14.5], visible = False)

			figHeatmap.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
			figHeatmap.update_layout(yaxis=dict(tickmode='linear', tick0=0, dtick=1))

			#plt.show()
			#figHeatmap.show()

			# plt.savefig("heatmap.png", dpi=75)
			# plt.savefig(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png", dpi=75)
			figHeatmap.write_image(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png")

			hm = []
			# with open("heatmap.png", "rb") as img_file:
			with open(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png", "rb") as img_file:
				hm = ["heatmap", base64.b64encode(img_file.read())]

			writeResult.append(hm)
			#end heatmap

			#trajectories
			# plt.close()
			dataFig = []
			# values on x-axis
			x = []
			# values on y-axis
			y = []

			#open file to read
			#for line in open("resultFile.csv"):
			for line in open(self.outputDir + "/resultFile_" + self.ip.replace(":", "_") + ".csv"):
				csv_row = line.split(';')
				x.append(float(csv_row[1]))
				y.append(float(csv_row[2]))

			# fig = plt.figure()
			# ax = fig.add_subplot(1, 1, 1)

			# Creating trajetories figure

			figTrajectories = make_subplots(rows=1, cols=1)

			# figTrajectories.add_trace(
			# 	go.Scatter(x = x, y = y),
			# 	row=1, col=1
			# )

			figTrajectories.add_scatter(x=x, y=y, mode='markers', name='Trajetória', marker=dict(size=4), marker_color="rgb(0,0,255)")

			# figTrajectories = px.scatter(x = x, y = y)

			major_ticks = np.arange(0, self.mapSize.x + 1, self.cellSize)
			# ax.set_xticks(major_ticks)
			# ax.set_yticks(major_ticks)

			figTrajectories.update_xaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')
			figTrajectories.update_yaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')

			figTrajectories.update_layout(xaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))
			figTrajectories.update_layout(yaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))

			figTrajectories.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
			figTrajectories.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True)

			# plt.axis([0, self.mapSize.x, 0, self.mapSize.y])

			# naming the x and y axis
			# plt.xlabel('x')
			# plt.ylabel('y')

			#draw obstacles
			for obs in range(0, len(self.obstacles)):
				coord = []
				for pnt in range(0, len(self.obstacles[obs].points)):
					coord.append([self.obstacles[obs].points[pnt].x, self.obstacles[obs].points[pnt].y])
				coord.append(coord[0]) #repeat the first point to create a 'closed loop'
				xs, ys = zip(*coord) #create lists of x and y values
				# plt.plot(xs,ys)
				figTrajectories.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False))

			# plt.title("Trajetorias dos Agentes")

			# plotting a line plot with it's default size
			# plt.plot(x, y, 'ro', markersize=1, label = "Trajetória")

			x = []
			y = []

			#goals
			for _goal in self.goals:
				x.append(_goal.position.x)
				y.append(_goal.position.y)

			# plt.plot(x, y, 'bo', markersize=10, label = "Objetivo")
			figTrajectories.add_scatter(x = x, y = y, mode = 'markers', name = 'Objetivo', marker = dict( size = 12), marker_color="rgb(255,0,0)")
			# red_patch = mpatches.Patch(color='red', label='Trajetória')
			# blue_dot = mlines.Line2D([0], [0], marker='o', color='w', label='Objetivo',
            #               markerfacecolor='b', markersize=10)
			# ax.legend(handles=[red_patch, blue_dot])

			# plt.grid()

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

			writeResult.append(hm)
			#end trajectories

			#sim time
			hm = ["simTime", self.simulationTime]
			writeResult.append(hm)

			#clear Database, just to be sure
			#self.ClearDatabase()

			#self.conn.close()

			# plt.close()

			# resultFile.csv
			if os.path.isfile(self.outputDir + "/resultFile_" + self.ip.replace(":", "_") + ".csv"):
				os.remove(self.outputDir + "/resultFile_" + self.ip.replace(":", "_") + ".csv")

			# heatmap.png
			if os.path.isfile(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png"):
				os.remove(self.outputDir + "/heatmap_" + self.ip.replace(":", "_") + ".png")

			# markers.csv
			if os.path.isfile(self.outputDir + "/markers_" + self.ip.replace(":", "_") + ".csv"):
				os.remove(self.outputDir + "/markers_" + self.ip.replace(":", "_") + ".csv")

			# resultCellFile.txt
			if os.path.isfile(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt"):
				os.remove(self.outputDir + "/resultCellFile_" + self.ip.replace(":", "_") + ".txt")

			# trajectories.png
			if os.path.isfile(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png"):
				os.remove(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png")

			#gc.collect()

			#return plt
			return pd.DataFrame(writeResult)

	def ConnectDB(self):
		self.conn = psycopg2.connect(host="localhost",
								database="biocrowds",
								user="postgres",
								password="postgres")

		#heroku
		#DATABASE_URL = os.environ.get('DATABASE_URL')
		#self.conn = psycopg2.connect(DATABASE_URL)

	def ClearDatabase(self):
		cursor = self.conn.cursor()
		cursor.execute("delete from config where id = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from agents where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from goals where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from obstacles where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from obstacles_points where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from cells where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

		cursor = self.conn.cursor()
		cursor.execute("delete from agents_paths where ip = '" + self.ip + "'")
		self.conn.commit()
		cursor.close()

	def LoadDatabase(self):
		cursor = self.conn.cursor()

		#config
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
		self.ClearDatabase()

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
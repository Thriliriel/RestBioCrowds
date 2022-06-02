import os
from AgentClass import AgentClass
from Vector3Class import Vector3
from CellClass import CellClass
from MarkerClass import MarkerClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

domain = "https://serene-beach-46283.herokuapp.com/"

class BioCrowds():
	def run(self, data):
		writeResult = []

		#from Json
		terrainSizeJson = data['terrains'][0]['terrain_size']
		goalsJson = data['goals']
		agentsJson = data #spawn areas. Gab, take a look
		obstaclesJson = data['obstacles']

		#default values
		#size of the scenario
		mapSize = Vector3(terrainSizeJson[0], terrainSizeJson[2], terrainSizeJson[1])
		#markers density
		PORC_QTD_Marcacoes = 0.65
		#FPS (default: 50FPS)
		timeStep = 0.02
		#size of each square cell (Ex: 2 -> cell 2x2)
		cellSize = 2
		#using path planning?
		pathPlanning = True

		#read the config file
		lineCount = 1
		for line in open("Input/config.txt", "r"):
			if '#' in line:
				continue
			if lineCount == 1:
				#markers density
				PORC_QTD_Marcacoes = float(line)
			elif lineCount == 2:
				#FPS
				timeStep = float(line)
			elif lineCount == 3:
				#size of each square cell
				cellSize = int(line)
			elif lineCount == 4:
				#size of the scenario (comes from json, so no needed)
				sp = line.split(',')
				#mapSize = Vector3(int(sp[0]), int(sp[1]), int(sp[2]))
			elif lineCount == 5:
				#using path planning?
				if line.lower() == 'false':
					pathPlanning = False
				else:
					pathPlanning = True

			lineCount += 1

		#goals
		goals = []

		#read the goals file (comes from json)
		#for line in open("Input/goals.txt", "r"):
		#	if '#' in line:
		#		continue

		#	#create goal
		#	gl = line.split(',')
		#	goals.append(GoalClass(int(gl[0]), Vector3(float(gl[1]), float(gl[2]), float(gl[3]))))
		idGoal = 1
		for gl in goalsJson:
			goals.append(GoalClass(idGoal, Vector3(gl['position'][0], gl['position'][2], gl['position'][1])))
			idGoal += 1

		#agents
		agents = []

		#read the agents file (comes from json)
		for line in open("Input/agents.txt", "r"):
			if '#' in line:
				continue

			#create agent
			ag = line.split(',')

			#find the goal with this id
			gl = None
			for i in range(0, len(goals)):
				if goals[i].id == int(ag[1]):
					gl = goals[i]
					break

			agents.append(AgentClass(int(ag[0]), gl, float(ag[2]), float(ag[3]), pathPlanning, Vector3(float(ag[4]), float(ag[5]), float(ag[6]))))



		#obstacles
		obstacles = []

		#read the obstacles file (comes from json)
		#for line in open("Input/obstacles.txt", "r"):
		#	if '#' in line:
		#		continue

		#	#create obstacle
		#	ob = line.split(',')

		#	#if size is one, it is the id
		#	if len(ob) == 1:
		#		obstacles.append(ObstacleClass(int(ob[0])))
		#	#if size is three, it is one of the points
		#	elif len(ob) == 3:
		#		obstacles[len(obstacles)-1].AddPoint(Vector3(float(ob[0]), float(ob[1]), float(ob[2])))
		#	#else, something is wrong
		#	else:
		#		print("Error: input size is wrong!")
		#		exit

		#points??
		idObs = 1
		for ob in obstaclesJson:
			obstacles.append(ObstacleClass(idObs))
			obstacles[len(obstacles)-1].AddPoint(Vector3(ob['transform']['position'][0], 
												ob['transform']['position'][2], 
												ob['transform']['position'][1]))
			print(obstacles[len(obstacles)-1].points[0].x)

			idObs += 1

		#cells
		cells = []

		#create the cells and markers
		def CreateMap():
			i = j = 0
			while i < mapSize.x:
				while j < mapSize.y:
					cells.append(CellClass(str(i)+"-"+str(j), Vector3(i, j, 0), cellSize, PORC_QTD_Marcacoes, []))
					j += cellSize
				i += cellSize
				j = 0

		#create markers
		def CreateMarkers():
			for i in range(0, len(cells)):
				cells[i].CreateMarkers(obstacles)
				#print("Qnt created: ", len(cells[i].markers))

		#save markers in file
		def SaveMarkers():
			markerFile = open("markers.csv", "w")
			for i in range(0, len(cells)):
				for j in range(0, len(cells[i].markers)):
					markerFile.write(cells[i].id + ";" + str(cells[i].markers[j].position.x) + ";" + str(cells[i].markers[j].position.y) + ";" + str(cells[i].markers[j].position.z) + "\n")
			markerFile.close()

		CreateMap()
		CreateMarkers()
		SaveMarkers()

		#for each goal, vinculate the cell
		for i in range(0, len(goals)):
			totalDistance = cellSize * 2
			for j in range(0, len(cells)):
				distance = Vector3.Distance(goals[i].position, cells[j].position)

				#if distance is lower than total, change
				if distance < totalDistance:
					totalDistance = distance
					goals[i].cell = cells[j]

		#for each cell, find its neighbors
		for i in range(0, len(cells)):
			cells[i].FindNeighbor(cells)

		#for each agent, find its initial cell
		for i in range(0, len(agents)):
			minDis = 5
			for c in range(0, len(cells)):
				dist = Vector3.Distance(agents[i].position, cells[c].position)
				if dist < minDis:
					minDis = dist
					agents[i].cell = cells[c]

		#for each agent, calculate the path, if true
		if pathPlanning:
			for i in range(0, len(agents)):
				agents[i].FindPath()

		#open file to write
		resultFile = open("resultFile.csv", "w")

		simulationFrame = 0

		#walking loop
		#check the distance to see if agent is stuck (TODO)
		while True:
			#if no agents anymore, break
			if len(agents) == 0:
				break

			#for each agent, we reset their info
			for i in range(0, len(agents)):
				agents[i].ClearAgent()
			#print("markers", len(agents[0].markers))
			#reset the markers
			for i in range(0, len(cells)):
				for j in range(0, len(cells[i].markers)):
					cells[i].markers[j].ResetMarker()
	
			#find nearest markers for each agent
			for i in range(0, len(agents)):
				agents[i].FindNearMarkers()
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
			while i < len(agents):
				agentMarkers = agents[i].markers

				#vector for each marker
				for j in range(0, len(agentMarkers)):
					#add the distance vector between it and the agent
					#print (agents[i].position, agentMarkers[j].position)
					agents[i].vetorDistRelacaoMarcacao.append(Vector3.Sub_vec(agentMarkers[j].position, agents[i].position))

				#print("total", len(agents[i].vetorDistRelacaoMarcacao))
				#calculate the movement vector
				agents[i].CalculateMotionVector()

				#print(agents[i].m)
				#calculate speed vector
				agents[i].CalculateSpeed()

				#walk
				agents[i].Walk(timeStep)

				#write in file
				resultFile.write(str(agents[i].id) + ";" + str(agents[i].position.x) + ";" + str(agents[i].position.y) + ";" + str(agents[i].position.z) + "\n")

				#verify agent position, in relation to the goal. If arrived, bye
				dist = Vector3.Distance(agents[i].goal.position, agents[i].position)
				#print(agents[i].id, " -- Dist: ", dist, " -- Radius: ", agents[i].radius, " -- Agent: ", agents[i].position.x, agents[i].position.y)
				#print(agents[i].speed.x, agents[i].speed.y)
				if dist < agents[i].radius / 4:
					agentsToKill.append(i)

				#update lastdist (max = 5)
				if len(agents[i].lastDist) == 5:
					agents[i].lastDist.pop(0)

				agents[i].lastDist.append(dist)

				#check them all
				qntFound = 0
				for ck in agents[i].lastDist:
					if ck == dist:
						qntFound += 1

				#if distances does not change, assume agent is stuck
				if qntFound == 5:
					agentsToKill.append(i)

				i += 1

			#die!
			if len(agentsToKill) > 0:
				for i in range(0, len(agentsToKill)):
					agents.pop(agentsToKill[i])

			print("Simulation Frame:", simulationFrame, end='\r')
			simulationFrame += 1

		#close file
		resultFile.close()

		simulationTime = (simulationFrame+1) * timeStep
		print(f'Total Simulation Time: {simulationTime} "seconds. ({simulationFrame+1} frames)')

		#save the cells, for heatmap
		resultCellsFile = open("resultCellFile.txt", "w")
		thisX = 0
		firstColumn = True
		for cell in cells:
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
		data = []

		#open file to read
		for line in open("resultCellFile.txt"):
			stripLine = line.replace('\n', '')
			strip = stripLine.split(',')
			dataTemp = []

			for af in strip:
				dataTemp.insert(0, float(af))

			data.append(dataTemp)

		heatmap = np.array(data)
		heatmap = heatmap.transpose()

		fig, ax = plt.subplots()
		im = ax.imshow(heatmap)

		# Show all ticks and label them with the respective list entries
		ax.set_xticks(np.arange(mapSize.x/cellSize))
		ax.set_yticks(np.arange(mapSize.y/cellSize))

		# Rotate the tick labels and set their alignment.
		plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
				 rotation_mode="anchor")

		# Loop over data dimensions and create text annotations.
		for i in range(int(mapSize.x/cellSize)):
			for j in range(int(mapSize.y/cellSize)):
				text = ax.text(j, i, heatmap[i, j],
								ha="center", va="center", color="w")

		ax.set_title("HeatMap")
		fig.tight_layout()
		#plt.show()

		plt.savefig("heatmap.png", dpi=75)

		#html
		#html = "<html><body><img src='"+domain+"heatmap.png' width='480' height='360' border='0'></body></html>"
		hm = []
		with open("heatmap.png", "rb") as img_file:
			hm = ["heatmap", base64.b64encode(img_file.read())]
		#end heatmap

		writeResult.append(hm)

		#return plt
		return pd.DataFrame(writeResult)
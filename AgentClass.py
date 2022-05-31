from os import path
from Vector3Class import Vector3
from MarkerClass import MarkerClass
from PathPlanningClass import PathPlanningClass

class AgentClass:
	def __init__(self, id, goal, radius, maxSpeed, usePathPlanning, position = Vector3.Zero()):
		self.goal = goal
		self.goalPosition = self.goal.position
		self.id = id
		self.radius = radius
		self.maxSpeed = maxSpeed
		self.markers = []
		self.position = position
		self.vetorDistRelacaoMarcacao = []
		self.denominadorW = False
		self.valorDenominadorW = 0
		self.m = Vector3.Zero()
		self.speedModule = 0
		self.speed = Vector3.Zero()
		self.cell = None
		self.usePathPlanning = usePathPlanning
		self.lastDist = [] # to check if agent is stuck
		if self.usePathPlanning:
			self.pathPlanning = PathPlanningClass(10000) #10000 = max iterations allowed to find a path
			self.path = []

	#clear agent´s informations
	def ClearAgent(self):
		#re-set inicial values
		self.valorDenominadorW = 0
		self.vetorDistRelacaoMarcacao = []
		self.denominadorW = False
		self.m = Vector3.Zero()
		self.speed = Vector3.Zero()
		self.markers = []
		self.speedModule = 0
		if self.usePathPlanning:
			self.CheckSubGoalDistance()

	def FindPath(self):
		self.path = self.pathPlanning.FindPath(self.cell, self.goal.cell)
		pt = self.path[0]
		self.goalPosition = Vector3(pt.position.x, pt.position.y, pt.position.z)

	#calculate W
	def CalculateWeight(self, indiceRelacao):
		#retorno = 0

		#calculate F (F is part of weight formula)
		valorF = self.CalculateF(indiceRelacao)

		if not self.denominadorW:
			self.valorDenominadorW = 0

			#for each agent´s marker
			for i in range(0, len(self.vetorDistRelacaoMarcacao)):
				#calculate F for this k index, and sum up
				self.valorDenominadorW += self.CalculateF(i)
			self.denominadorW = True

		retorno = valorF / self.valorDenominadorW
		#print(retorno)
		return retorno

	#calculate F (F is part of weight formula)
	def CalculateF(self, indiceRelacao):
		#distance between auxin´s distance and origin (dont know why origin...)
		moduloY = Vector3.Distance(self.vetorDistRelacaoMarcacao[indiceRelacao], Vector3.Zero())
		#distance between goal vector and origin (dont know why origin...)
		#print(Vector3.Sub_vec(self.goal.position, self.position))
		#print(Vector3.Zero())
		#print(Vector3.Distance(Vector3.Sub_vec(self.goal.position, self.position), Vector3.Zero()))
		#moduloX = Vector3.Distance(Vector3.Sub_vec(self.goal.position, self.position), Vector3.Zero())
		moduloX = 1.0
        
		if moduloY < 0.00001:
			return 0
		produtoEscalar = Vector3.Dot_vec(self.vetorDistRelacaoMarcacao[indiceRelacao],  Vector3.Nrm_vec(Vector3.Sub_vec(self.goalPosition, self.position)))
        
		retorno = (1.0 / (1.0 + moduloY)) * (1.0 + ((produtoEscalar) / (moduloX * moduloY)))
		return retorno

	#The calculation formula starts here
	#the ideia is to find m=SUM[k=1 to n](Wk*Dk)
	#where k iterates between 1 and n (number of auxins), Dk is the vector to the k auxin and Wk is the weight of k auxin
	#the weight (Wk) is based on the degree resulting between the goal vector and the auxin vector (Dk), and the
	#distance of the marker from the agent
	def CalculateMotionVector(self):
		#for each agent´s marker
		s = 0.0
		for i in range(0, len(self.vetorDistRelacaoMarcacao)):
			valorW = self.CalculateWeight(i)
			if self.valorDenominadorW < 0.0001:
				valorW = 0
			s += valorW

			#sum the resulting vector * weight (Wk*Dk)
			self.m = Vector3.Add_vec(self.m, Vector3.Mul_vec(self.vetorDistRelacaoMarcacao[i], self.maxSpeed, valorW))

		#print(self.m.x, self.m.y, self.m.z)
		#print("weights", s)

	#calculate speed vector
	def CalculateSpeed(self):
		moduloM = Vector3.Distance(self.m, Vector3.Zero())

		#multiply for PI
		s = moduloM * 3.14
		thisMaxSpeed = self.maxSpeed

		#if it is bigger than maxSpeed, use maxSpeed instead
		if s > thisMaxSpeed:
			s = thisMaxSpeed

		self.speedModule = s

		if moduloM > 0.0001:
			#calculate speed vector
			newX = s * (self.m.x / moduloM)
			newY = s * (self.m.y / moduloM)
			newZ = s * (self.m.z / moduloM)
			self.speed = Vector3(newX, newY, newZ)
		else:
			#else, he is idle
			self.speed = Vector3.Zero()

	#check markers on a cell
	def CheckMarkersCell(self, checkCell):
		#get all markers on cell
		cellMarkers = checkCell.markers

		#iterate all cell markers to check distance between markers and agent
		for i in range(0, len(cellMarkers)):
			#see if the distance between this agent and this marker is smaller than the actual value, and inside agent radius
			distance = Vector3.Distance(self.position, cellMarkers[i].position)
			#we also test if it is already inside someone's personal space
			if distance < cellMarkers[i].minDistance and distance <= self.radius:
				#take the marker!!
				#if this marker already was taken, need to remove it from the agent who had it
				if cellMarkers[i].taken and cellMarkers[i].owner.id != self.id:
					otherAgent = cellMarkers[i].owner
					otherAgent.markers.remove(cellMarkers[i])

				#marker is taken
				cellMarkers[i].taken = True
				#marker has agent
				cellMarkers[i].owner = self
				#update min distance
				cellMarkers[i].minDistance = distance

				#update my markers
				self.markers.append(cellMarkers[i])

	#find all markers near him (Voronoi Diagram)
	#call this method from Biocrowds, to make it sequential for each agent
	def FindNearMarkers(self):
		#clear all agents auxins, to start again for this iteration
		self.markers.clear()
		self.markers = []

		#check all markers on agent's cell
		self.CheckMarkersCell(self.cell)

		#distance from agent to cell, to define agent new cell
		distanceToCell = Vector3.Distance(self.position, self.cell.position)
		cellToChange = self.cell
        
		#iterate through neighbors of the agent cell
		for i in range(0, len(self.cell.neighborCells)):
			if i >= len(self.cell.neighborCells):
				break

			#check all markers on this cell
			try:
				self.CheckMarkersCell(self.cell.neighborCells[i])
			except:
				print(self.cell.id, len(self.cell.neighborCells), i) 

			#see distance to this cell
			#if it is lower, the agent is in another(neighbour) cell
			distanceToNeighbourCell = Vector3.Distance(self.position, self.cell.neighborCells[i].position)
			if distanceToNeighbourCell < distanceToCell:
				distanceToCell = distanceToNeighbourCell
				cellToChange = self.cell.neighborCells[i]

			self.cell = cellToChange

	#walk
	def Walk(self, timeStep):
		self.position = Vector3.Add_vec(self.position, Vector3.Mul_vec(self.speed, timeStep, 1))

	#check the sub-goal distance
	def CheckSubGoalDistance(self):
		#just check if the sub-goal is not the actual goal
		if self.goalPosition != self.goal.position:
			distanceSubGoal = Vector3.Distance(self.position, self.goalPosition)
			if distanceSubGoal < self.radius and len(self.path) > 1:
				self.path.pop(0)
				self.goalPosition = Vector3(self.path[0].position.x, self.path[0].position.y, self.path[0].position.z)
			elif distanceSubGoal < self.radius:
				self.goalPosition = self.goal.position

				
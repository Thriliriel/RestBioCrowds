from Vector3Class import Vector3
from NodeClass import NodeClass

class PathPlanningClass:
	def __init__(self, stopCondition):
		self.stopCondition = stopCondition
		self.nodesToCheck = [] #NodeClass array
		self.nodesChecked = [] #NodeClass array
		self.originNode = NodeClass()
		self.destinationNode = NodeClass()

	#find a path between two points
	def FindPath(self, cellOrigin, cellDestination):
		#add the origin cell to the open list
		newNode = NodeClass()
		newNode.cell = cellOrigin
		self.nodesToCheck.append(newNode)

		#set the origin node
		self.originNode.cell = cellOrigin

		#set the destination node
		self.destinationNode.cell = cellDestination

		#to control the stop condition
		nrIt = 0
		foundPath = False
		#while there are nodes to check, repeat
		while len(self.nodesToCheck) > 0:
			nrIt += 1
			#order the list
			self.ReorderCheckList()

			#check the neighbour cells of the first node of the list and create their nodes
			self.FindNodes(self.nodesToCheck[0])
            
			destinationId = self.destinationNode.cell.id

			#if arrived at destination, finished
			if self.nodesChecked[len(self.nodesChecked) - 1].cell.id == destinationId:
				foundPath = True
				break

			#if nrIt is bigger than the stop condition, byyye
			if nrIt > self.stopCondition:
				break

		#path
		path = []

		#add the destination
		path.append(self.destinationNode.cell)

		#if found Path, make the reverse way to mount it
		#else, path is empty. Agent tries to go directly towards it
		if foundPath:
			nodi = self.nodesChecked[len(self.nodesChecked) - 1]
			while nodi.parent is not None:
				#add to path
				path.append(nodi.parent.cell)
				#update node with the parent
				nodi = nodi.parent

		#revert it
		path.reverse()

		#clear lists
		self.nodesChecked.clear()
		self.nodesToCheck.clear()

		#now the full path is ready, find only the corners (JUST IF WANT TO USE)
	#      cornerPath = []
		#for i in range(0, len(path) - 1):
	#          #difference between next position and actual position
	#          nextDiffX = path[i + 1].position.x - path[i].position.x
	#          nextDiffZ = path[i + 1].position.z - path[i].position.z

	#          #difference between actual position and last position
	#          lastDiffX = path[i].position.x - path[i - 1].position.x
	#          lastDiffZ = path[i].position.z - path[i - 1].position.z

	#          #if the difference just calculated is equal than the difference between actual position and last position, it is following a straight line. So, no need for corner
	#          #otherwise, add it
	#          if nextDiffX not lastDiffX or nextDiffZ not lastDiffZ:
	#              cornerPath.append(path[i])

	#      #if goal is not already in the list, add it
	#      if cellDestination not in cornerPath:
	#          cornerPath.append(cellDestination)

		#return cornerPath;
		return path

	#reorder the nodes to check list, placing the lowest f at first
	def ReorderCheckList(self):
		for i in range(0, len(self.nodesToCheck)):
			for j in range(0, len(self.nodesToCheck)):
				#if second one is higher??? (worked...) than the first one, change places
				if self.nodesToCheck[j].f > self.nodesToCheck[i].f:
					auxNode = self.nodesToCheck[i]
					self.nodesToCheck[i] = self.nodesToCheck[j]
					self.nodesToCheck[j] = auxNode

	#find nodes around the chosen node
	def FindNodes(self, chosenNode):
		#iterate around the chosen node cell, using the neighborCells
		for i in range(0, len(chosenNode.cell.neighborCells)):
			#see it this node is not already in closed list
			goAhead = True
			if chosenNode.cell.neighborCells[i] in self.nodesChecked:
				goAhead = False

			#if it is not
			if goAhead:
				#check if this node is not already on the open node list
				alreadyInside = -1
				z = 0
				while z < len(self.nodesToCheck):
					if self.nodesToCheck[z].cell.id == chosenNode.cell.neighborCells[i].id:
						alreadyInside = z
						break
					z += 1

				#if it is, check to see if this chosen path is better
				if alreadyInside > -1:
					#if the g value of chosenNode, plus the cost to move to this neighbour, is lower than the nodeG value, this path is better. So, update
					#otherwise, do nothing.
					extraCost = 14
					if self.nodesToCheck[alreadyInside].cell.position.x == chosenNode.cell.position.x or self.nodesToCheck[alreadyInside].cell.position.y == chosenNode.cell.position.y:
						extraCost = 10

					if (chosenNode.g + extraCost) < self.nodesToCheck[alreadyInside].g:
						#re-calculate the values
						self.nodesToCheck[alreadyInside].g = (chosenNode.g + extraCost)
						self.nodesToCheck[alreadyInside].f = self.nodesToCheck[alreadyInside].g + self.nodesToCheck[alreadyInside].h
						#change parent
						self.nodesToCheck[alreadyInside].parent = chosenNode

				#else, just create it
				else:
					#create its node
					newNode = NodeClass()
					#initialize
					newNode.cell = chosenNode.cell.neighborCells[i]
					newNode.g = 14
					#set its values
					#h value
					newNode.h = self.EstimateDestination(newNode)
					#g value
					#if x or z axis is equal to the chosen node cell, it is hor/ver movement, so it costs only 10
					if newNode.cell.position.x == chosenNode.cell.position.x or newNode.cell.position.y == chosenNode.cell.position.y:
						newNode.g = 10

					#we update the cost of the cell, being it inversely proportional of the amount of markers found inside it
					#this way, we can make cells with less markers to be costier (emulating obstacles)
					newNode.g += newNode.cell.qntMarkers - len(newNode.cell.markers)

					#f, just sums h with g
					newNode.f = newNode.h + newNode.g
					#set the parent node
					newNode.parent = chosenNode

					#add this node in the open list
					self.nodesToCheck.append(newNode)		

		#done with this one
		self.nodesChecked.append(chosenNode)
		self.nodesToCheck.remove(chosenNode)

	#estimate the h node value
	def EstimateDestination(self, checkingNode):
		manhattanWay = 0

		#since it is a virtual straight path, just sum up the differences in axis x and y
		differenceX = abs(self.destinationNode.cell.position.x - checkingNode.cell.position.x)
		differenceY = abs(self.destinationNode.cell.position.y - checkingNode.cell.position.y)

		#sum up and multiply by the weight (10)
		manhattanWay = int((differenceX + differenceY) * 10)

		return manhattanWay
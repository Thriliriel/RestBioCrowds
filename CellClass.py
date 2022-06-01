import math
import random
from Vector3Class import Vector3
from MarkerClass import MarkerClass

# Define Infinite (Using INT_MAX may cause overflow problems)
# Used to find out if a point is inside a polygon. Environment size can be used
INT_MAX = 1000

class CellClass:
	def __init__(self, id, position, cellRadius, density = 0.65, markers = []):
		self.id = id
		self.position = position
		self.markers:list[MarkerClass] = markers
		self.density = density
		self.markerRadius = 0.1
		self.cellRadius = cellRadius
		self.neighborCells = []
		self.qntMarkers = 0
		self.isWall = False

	def DartThrow(self, obstacles):
		#flag to break the loop if it is taking too long (maybe out of space)
		flag = 0
		#print("Qnt create: ", self.qntMarkers)
		i = 0
		while i < self.qntMarkers:
			x = random.uniform(self.position.x, self.position.x + self.cellRadius)
			y = random.uniform(self.position.y, self.position.y + self.cellRadius)

			#print(self.id, x, y)

			#check distance from other markers to see if can instantiante
			canInst = True
			for m in range (0, len(self.markers)):
				distance = Vector3.Distance(self.markers[m].position, Vector3(x, y, 0))
				if distance < self.markerRadius:
					canInst = False
					break

			#if i can inst, still need to check if it does not fall inside an obstacle
			if canInst:
				for it in range(0, len(obstacles)):
					inside = self.Is_inside_polygon(obstacles[it].points, Vector3(x, y, 0))
					if inside:
						canInst = False
						break

			#can i?
			if canInst:
				self.markers.append(MarkerClass(Vector3(x, y, 0)))
				flag = 0
			#else, try again
			else:
				flag += 1
				i -= 1

			#if flag is above qntMarkers (*2 to have some more), break;
			if flag > self.qntMarkers * 2:
				#reset flag
				flag = 0
				#print(self.id)
				break

			i += 1

	def CreateMarkers(self, obstacles):
		self.density *= (self.cellRadius) / (2.0 * self.markerRadius)
		self.density *= (self.cellRadius) / (2.0 * self.markerRadius)
		self.qntMarkers = math.floor(self.density)
		#print("Self - " + str(self.qntMarkers))
		self.DartThrow(obstacles)

		#if the ammount of markers is too low, declare as a wall
		if len(self.markers) < (self.qntMarkers/2):
			self.isWall = True

	#find the neighbor cells
	def FindNeighbor(self, allCells):
		#for each cell, check if the distance is lower or equal the hyp of the drawn square between the center of the cells
		for i in range(len(allCells)):
			distance = Vector3.Distance(self.position, allCells[i].position)

			#if distance is zero, it is the same cell, ignore it
			if distance > 0:
				#now, check if the distance is inside the boundaries 
				#(for example: cellRadius = 2, max distance = sqrt(8) = 2.sqrt(2))
				if distance <= 0.1 + math.sqrt(math.pow(self.cellRadius, 2) + math.pow(self.cellRadius, 2)):
					self.neighborCells.append(allCells[i])

		#print(self.id, len(self.neighborCells))

	#methods to check if point inside a polygon, from here:
	# https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/

	# Given three collinear points p, q, r, 
	# the function checks if point q lies
	# on line segment 'pr'
	def OnSegment(self, p:tuple, q:tuple, r:tuple) -> bool:
     
		if ((q.x <= max(p.x, r.x)) &
			(q.x >= min(p.x, r.x)) &
			(q.y <= max(p.y, r.y)) &
			(q.y >= min(p.y, r.y))):
			return True
         
		return False

	# To find orientation of ordered triplet (p, q, r).
	# The function returns following values
	# 0 --> p, q and r are collinear
	# 1 --> Clockwise
	# 2 --> Counterclockwise
	def Orientation(self, p:tuple, q:tuple, r:tuple) -> int:
     
		val = (((q.y - p.y) *
				(r.x - q.x)) -
				((q.x - p.x) *
				(r.y - q.y)))
            
		if val == 0:
			return 0
		if val > 0:
			return 1 # Collinear
		else:
			return 2 # Clock or counterclock

	def DoIntersect(self, p1, q1, p2, q2):     
		# Find the four orientations needed for 
		# general and special cases
		o1 = self.Orientation(p1, q1, p2)
		o2 = self.Orientation(p1, q1, q2)
		o3 = self.Orientation(p2, q2, p1)
		o4 = self.Orientation(p2, q2, q1)
 
		# General case
		if (o1 != o2) and (o3 != o4):
			return True
     
		# Special Cases
		# p1, q1 and p2 are collinear and
		# p2 lies on segment p1q1
		if (o1 == 0) and (self.OnSegment(p1, p2, q1)):
			return True
 
		# p1, q1 and p2 are collinear and
		# q2 lies on segment p1q1
		if (o2 == 0) and (self.OnSegment(p1, q2, q1)):
			return True
 
		# p2, q2 and p1 are collinear and
		# p1 lies on segment p2q2
		if (o3 == 0) and (self.OnSegment(p2, p1, q2)):
			return True
 
		# p2, q2 and q1 are collinear and
		# q1 lies on segment p2q2
		if (o4 == 0) and (self.OnSegment(p2, q1, q2)):
			return True
 
		return False
 
	# Returns true if the point p lies 
	# inside the polygon[] with n vertices
	def Is_inside_polygon(self, points:list, p:tuple) -> bool:
     
		n = len(points)
     
		# There must be at least 3 vertices
		# in polygon
		if n < 3:
			return False
         
		# Create a point for line segment
		# from p to infinite
		extreme = Vector3(INT_MAX, p.y, 0)
		count = i = 0
     
		while True:
			next = (i + 1) % n
         
			# Check if the line segment from 'p' to 
			# 'extreme' intersects with the line 
			# segment from 'polygon[i]' to 'polygon[next]'
			if (self.DoIntersect(points[i],
							points[next],
							p, extreme)):
                             
				# If the point 'p' is collinear with line 
				# segment 'i-next', then check if it lies 
				# on segment. If it lies, return true, otherwise false
				if self.Orientation(points[i], p,
								points[next]) == 0:
					return self.OnSegment(points[i], p,
										points[next])
                                  
				count += 1
             
			i = next
         
			if (i == 0):
				break
         
		# Return true if count is odd, false otherwise
		return (count % 2 == 1)
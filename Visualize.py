# importing the matplotlib library
import matplotlib.pyplot as plt
from ObstacleClass import ObstacleClass
from Vector3Class import Vector3
  
# values on x-axis
x = []
# values on y-axis
y = []

mapSizeX = 20
mapSizeY = 20

#read the config file to get the map size
lineCount = 1
for line in open("Input/config.txt", "r"):
	if '#' in line:
		continue
	elif lineCount == 4:
		#size of the scenario
		sp = line.split(',')
		mapSizeX = int(sp[0])
		mapSizeY = int(sp[1])
	lineCount += 1

#goals
for line in open("Input/goals.txt", "r"):
	if '#' in line:
		continue

	#create goal
	gl = line.split(',')
	x.append(float(gl[1]))
	y.append(float(gl[2]))

#open file to read
for line in open("resultFile.csv"):
    csv_row = line.split(';')
    x.append(float(csv_row[1]))
    y.append(float(csv_row[2]))
  
plt.axis([0, mapSizeX, 0, mapSizeY])

# naming the x and y axis
plt.xlabel('x - axis')
plt.ylabel('y - axis')

#obstacles
obstacles = []

#read the obstacles file
for line in open("Input/obstacles.txt", "r"):
	if '#' in line:
		continue

	#create obstacle
	ob = line.split(',')

	#if size is one, it is the id
	if len(ob) == 1:
		obstacles.append(ObstacleClass(int(ob[0])))
	#if size is three, it is one of the points
	elif len(ob) == 3:
		obstacles[len(obstacles)-1].AddPoint(Vector3(float(ob[0]), float(ob[1]), float(ob[2])))
	#else, something is wrong
	else:
		print("Error: input size is wrong!")
		exit

#draw obstacles
for obs in range(0, len(obstacles)):
	coord = []
	for pnt in range(0, len(obstacles[obs].points)):
		coord.append([obstacles[obs].points[pnt].x, obstacles[obs].points[pnt].y])
	coord.append(coord[0]) #repeat the first point to create a 'closed loop'
	xs, ys = zip(*coord) #create lists of x and y values
	plt.plot(xs,ys)
  
# plotting a line plot with it's default size
plt.plot(x, y, 'r*')
plt.show()
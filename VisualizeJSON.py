# importing the matplotlib library
import matplotlib.pyplot as plt
import argparse
import json
from ObstacleClass import ObstacleClass
from Vector3Class import Vector3


arg_parser = argparse.ArgumentParser(description="BioCrowds Python Visualization.")
arg_parser.add_argument('--f', metavar="F", type=str, default = '', help='Input File Name.')
args = vars(arg_parser.parse_args())

jsonInputFile = 'json_data.json'
#parse the JSON input
#if args['f'] == '':
#	#exit(1)

#jsonInputFile = args['f']
file = open(jsonInputFile,'r', encoding='utf8')
content = json.loads(file.read())


# values on x-axis
x = []
# values on y-axis
y = []

_terrain_size = content['terrains'][0]['terrain_size']
mapSizeX = int(_terrain_size[0])
mapSizeY = int(_terrain_size[2])

#goals
for _goal in content['goals']:
	_pos = _goal['position']
	x.append(_pos[0])
	y.append(_pos[2])

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

#obstacles
for _obstacles in content['obstacles']:
	obstacles.append(ObstacleClass(len(obstacles)))
	for _point in _obstacles['point_list']:
		obstacles[len(obstacles)-1].AddPoint(Vector3(float(_point[0]), float(_point[1]), float(_point[2])))

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
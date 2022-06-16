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
#	exit(1)

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

#open file to read
for line in open("markers.csv"):
    csv_row = line.split(';')

    #just one cell
    #if csv_row[0] != "0-0":
    #    continue

    x.append(float(csv_row[1]))
    y.append(float(csv_row[2]))
    
#x = [3, 1, 2, 5]
#y = [5, 2, 4, 7]

plt.plot(x, y, 'r*')
plt.axis([0, mapSizeX, 0, mapSizeY])

#for i, j in zip(x, y):
#   plt.text(i, j+0.5, '({}, {})'.format(i, j))

plt.show()
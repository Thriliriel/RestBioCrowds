# importing the matplotlib library
import matplotlib.pyplot as plt
  
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
# importing the matplotlib library
import matplotlib.pyplot as plt
import plotly.express as px

def visualize_markers(ip):
	# values on x-axis
	x = []
	# values on y-axis
	y = []

	mapSizeX = 30
	mapSizeY = 30

	#open file to read
	for line in open(f"OutputData/markers_{ip}.csv"):
		csv_row = line.split(';')

		#just one cell
		#if csv_row[0] != "0-0":
		#    continue

		x.append(float(csv_row[1]))
		y.append(float(csv_row[2]))
		
	#x = [3, 1, 2, 5]
	#y = [5, 2, 4, 7]

	fig = px.scatter(x=x, y=y)
	fig.show()
	# plt.axis([0, mapSizeX, 0, mapSizeY])

	# #for i, j in zip(x, y):
	# #   plt.text(i, j+0.5, '({}, {})'.format(i, j))

	# plt.show()

if __name__ == "__main__":
   visualize_markers("24131 PM586")
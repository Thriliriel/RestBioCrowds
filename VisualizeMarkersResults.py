import plotly.express as px

def visualize_markers(ip, simulation_id:int):
	# values on x-axis
	x = []
	# values on y-axis
	y = []

	#open file to read
	for line in open(f"OutputData/markers_{ip}.csv"):
		csv_row = line.split(';')
		x.append(float(csv_row[1]))
		y.append(float(csv_row[2]))
		
	fig = px.scatter(x=x, y=y)

	fig.update_layout(title = f"Marker Distribution - Sim {id}")
	fig.update_xaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')
	fig.update_yaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')

	fig.show()

if __name__ == "__main__":
   visualize_markers("24131 PM586", 1)
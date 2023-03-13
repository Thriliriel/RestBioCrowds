import os
from typing import TYPE_CHECKING
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import base64


if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass


def generate_trajectories(bio_crowds:'BioCrowdsClass', x_data, y_data):
    print("Generating Trajectories File")
    # Creating trajetories figure
    _map_size = bio_crowds.map_size
    if _map_size.x == _map_size.y:
        r_h = [0.0, 1.0, 0.0]
        c_w = [0.0, 1.0, 0.0]
    if _map_size.x > _map_size.y:
        _aspect = _map_size.y/_map_size.x
        r_h = [(1-_aspect)/2.0, _aspect, (1-_aspect)/2.0]
        c_w = [0.0, 1.0, 0.0]
    else:
        _aspect = _map_size.x/_map_size.y
        r_h = [0.0, 1.0, 0.0]
        c_w = [(1-_aspect)/2.0, _aspect, (1-_aspect)/2.0]

    figure = make_subplots(rows=3, cols=3,
                    row_heights=r_h,
                    column_widths=c_w,
                    horizontal_spacing = 0.0,
                    vertical_spacing = 0.0)
    trajectory_scatter = go.Scatter(x=x_data, 
                                y=y_data, 
                                mode='markers',  
                                name='Trajectory', 
                                marker=dict(size=4), 
                                marker_color="rgb(0,0,255)")
    figure.add_trace(trace=trajectory_scatter, row=2, col=2)

    axis_layout= {"range": [0, bio_crowds.map_size.x], 
                    "showgrid":True, 
                    "gridwidth":1, 
                    "gridcolor":'Gray',
                    "showline":True, 
                    "linewidth":1, 
                    "linecolor":'black', 
                    "mirror":True}
    figure.update_xaxes(axis_layout)
    axis_layout["range"] = [0, bio_crowds.map_size.y]
    figure.update_yaxes(axis_layout)

    # figTrajectories.update_layout(xaxis = dict(tickmode = 'linear', tick0 = 0))
    # figTrajectories.update_layout(yaxis = dict(tickmode = 'linear', tick0 = 0))
    

    #draw obstacles
    for obs in range(0, len(bio_crowds.obstacles)):
        coord = []
        for pnt in range(0, len(bio_crowds.obstacles[obs].points)):
            coord.append([bio_crowds.obstacles[obs].points[pnt].x, bio_crowds.obstacles[obs].points[pnt].y])
        coord.append(coord[0]) #repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord) #create lists of x and y values
        # plt.plot(xs,ys)
        figure.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False,),row=2, col=2)
            

    x_data = []
    y_data = []

    #goals
    for _goal in bio_crowds.goals:
        x_data.append(_goal.position.x)
        y_data.append(_goal.position.y)

    # plt.plot(x, y, 'bo', markersize=10, label = "Objetivo")
    goals_scatter = go.Scatter(x = x_data, 
                                y = y_data, 
                                mode = 'markers', 
                                name = 'Goals', 
                                marker = dict( size = 12), 
                                marker_color="rgb(255,0,0)")
    figure.add_trace(trace=goals_scatter, row=2, col=2)
    #print(figure)
    #figTrajectories.add_scatter(x = x_data, y = y_data, mode = 'markers', name = 'Goals', marker = dict( size = 12), marker_color="rgb(255,0,0)")
    
    figure.update_layout(
        template="simple_white",
        title = f"<b>Simulation {bio_crowds.simulation_id} - Agents' Trajectories</b>",
        width=700, height=600,
        title_x=0.5,
        title_font_size = 28,
        font_size = 18,
        legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # figTrajectories.update_layout()

    # plt.savefig("trajectories.png", dpi=75)
    # plt.savefig(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png", dpi=75)
    figure.write_image(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png")

    tj = []
    # with open("trajectories.png", "rb") as img_file:
    with open(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png", "rb") as img_file:
        tj = ["trajectories", base64.b64encode(img_file.read())]
    
    os.remove(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png")

    return tj
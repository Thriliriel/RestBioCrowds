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

    figTrajectories = make_subplots(rows=1, cols=1)
        
    figTrajectories.add_scatter(x=x_data, 
                                y=y_data, 
                                mode='markers', 
                                #name='Trajetória', 
                                name='Trajectory', 
                                marker=dict(size=4), 
                                marker_color="rgb(0,0,255)")

    # figTrajectories = px.scatter(x = x, y = y)

    major_ticks = np.arange(0, bio_crowds.map_size.x + 1, bio_crowds.cell_size)
    # ax.set_xticks(major_ticks)
    # ax.set_yticks(major_ticks)

    figTrajectories.update_xaxes(range = [0, bio_crowds.map_size.x], showgrid=True, gridwidth=1, gridcolor='Gray')
    figTrajectories.update_yaxes(range = [0, bio_crowds.map_size.y], showgrid=True, gridwidth=1, gridcolor='Gray')

    figTrajectories.update_layout(xaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))
    figTrajectories.update_layout(yaxis = dict(tickmode = 'linear', tick0 = 0, dtick = 2))

    figTrajectories.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
    figTrajectories.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True)
        

    #draw obstacles
    for obs in range(0, len(bio_crowds.obstacles)):
        coord = []
        for pnt in range(0, len(bio_crowds.obstacles[obs].points)):
            coord.append([bio_crowds.obstacles[obs].points[pnt].x, bio_crowds.obstacles[obs].points[pnt].y])
        coord.append(coord[0]) #repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord) #create lists of x and y values
        # plt.plot(xs,ys)
        figTrajectories.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False))
            

    x_data = []
    y_data = []

    #goals
    for _goal in bio_crowds.goals:
        x_data.append(_goal.position.x)
        y_data.append(_goal.position.y)

    # plt.plot(x, y, 'bo', markersize=10, label = "Objetivo")
    figTrajectories.add_scatter(x = x_data, y = y_data, mode = 'markers', name = 'Objetivo', marker = dict( size = 12), marker_color="rgb(255,0,0)")
        
    figTrajectories.update_layout(
        template="simple_white",
        title="Trajetórias dos Agentes",
        title_x=0.5,
        legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # plt.savefig("trajectories.png", dpi=75)
    # plt.savefig(self.outputDir + "/trajectories_" + self.ip.replace(":", "_") + ".png", dpi=75)
    figTrajectories.write_image(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png")

    tj = []
    # with open("trajectories.png", "rb") as img_file:
    with open(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png", "rb") as img_file:
        tj = ["trajectories", base64.b64encode(img_file.read())]
    
    os.remove(bio_crowds.output_dir + "/trajectories_" + bio_crowds.ip.replace(":", "_") + ".png")

    return tj
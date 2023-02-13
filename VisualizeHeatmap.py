import os
from typing import TYPE_CHECKING
import plotly.express as px
import numpy as np
import base64


#if TYPE_CHECKING:
from BioCrowds import BioCrowdsClass


def generate_heatmap():
    print("Generating Heatmap File")
    dataFig = []
    dataTemp = []
    output_dir = os.path.abspath(os.path.dirname(__file__)) + "/OutputData"
    ip = "54043 PM589"
    #open file to read
    # for line in open("resultCellFile.txt"):
    for line in open(output_dir + "/resultCellFile_" + ip + ".txt"):
        stripLine = line.replace('\n', '')
        strip = stripLine.split(',')
        dataTemp = []

        for af in strip:
            dataTemp.insert(0, float(af))

        dataFig.append(dataTemp)

    #datafig has all qnt of agents passed for each cell.
    heatmap = np.array(dataFig)
    heatmap = heatmap.transpose()

    figHeatmap = px.imshow(heatmap, 
            color_continuous_scale="Viridis", 
            labels=dict(color="Occupancy"),
            width=700, height=600)

    # Plotly configs

    figHeatmap.update_layout(
        template = "simple_white",
        #title = "Mapa de Densidades",
        title = "<b>Simulation 1 - Occupancy Map</b>",
        title_x=0.45,
        #legend_title = "Densidade"
        legend_title = "Occupancy",
        title_font_size = 28,
        font_size = 18
    )

    figHeatmap.update_xaxes(range=[-0.5, 30 - 0.5], visible = False)
    figHeatmap.update_yaxes(range=[-0.5, 30 - 0.5], visible = False)

    figHeatmap.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
    figHeatmap.update_layout(yaxis=dict(tickmode='linear', tick0=0, dtick=1))

    hm_output_file = output_dir + "/heatmap_" + ip.replace(":", "_") + ".png"

    figHeatmap.write_image(hm_output_file)
    figHeatmap.show()
    # hm = []
    # # with open("heatmap.png", "rb") as img_file:
    # with open(hm_output_file, "rb") as img_file:
    #     hm = ["heatmap", base64.b64encode(img_file.read())]
    
    # os.remove(hm_output_file)
    # return hm

if __name__ == "__main__":
   generate_heatmap()
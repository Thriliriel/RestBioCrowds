import os
from typing import TYPE_CHECKING
import plotly.express as px
import numpy as np
import base64


if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass


def generate_heatmap(bio_crowds:'BioCrowdsClass'):
    print("Generating Heatmap File")
    dataFig = []
    dataTemp = []

    #open file to read
    # for line in open("resultCellFile.txt"):
    for line in open(bio_crowds.output_dir + "/resultCellFile_" + bio_crowds.ip.replace(":", "_") + ".txt"):
        stripLine = line.replace('\n', '')
        strip = stripLine.split(',')
        dataTemp = []

        for af in strip:
            dataTemp.insert(0, float(af))

        dataFig.append(dataTemp)

    #datafig has all qnt of agents passed for each cell.
    heatmap = np.array(dataFig)
    heatmap = heatmap.transpose()

    figHeatmap = px.imshow(heatmap, color_continuous_scale="Viridis", labels=dict(color="Densidade"))

    # Plotly configs

    figHeatmap.update_layout(
        template = "simple_white",
        #title = "Mapa de Densidades",
        title = "Density Map",
        title_x=0.5,
        #legend_title = "Densidade"
        legend_title = "Density"
    )

    figHeatmap.update_xaxes(range=[-0.5, bio_crowds.map_size.x - 0.5], visible = False)
    figHeatmap.update_yaxes(range=[-0.5, bio_crowds.map_size.y - 0.5], visible = False)

    figHeatmap.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
    figHeatmap.update_layout(yaxis=dict(tickmode='linear', tick0=0, dtick=1))

    hm_output_file = bio_crowds.output_dir + "/heatmap_" + bio_crowds.ip.replace(":", "_") + ".png"

    figHeatmap.write_image(hm_output_file)

    hm = []
    # with open("heatmap.png", "rb") as img_file:
    with open(hm_output_file, "rb") as img_file:
        hm = ["heatmap", base64.b64encode(img_file.read())]
    
    os.remove(hm_output_file)
    return hm

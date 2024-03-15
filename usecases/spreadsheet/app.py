from flask import Flask, render_template, request, jsonify, send_file
import glob
import os
import sys
from pathlib import Path
module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(''))))

if module_path not in sys.path:
    sys.path.append(module_path)

# Create experimental setup folder
import datetime
current_directory = os.getcwd()
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
final_directory = os.path.join(current_directory, 'experimental_images', timestamp)
if not os.path.exists(final_directory):
    os.makedirs(final_directory)

# Load up specmetric
from specmetric.parser import ComputationTreeParser
from specmetric.computation_tree import ComputationNode
from specmetric.renderer import AltairRenderer

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chart.html")
def chart():
    list_of_files = glob.glob(os.path.join(final_directory, '*')) 
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    return send_file(latest_file)

@app.route("/berkeley.csv")
def berkeley():
    return send_file("berkeley_with_calculations.csv")

@app.route("/postSpecs", methods = ["POST"])
def getSpecs():
    nodes = request.get_json()['nodes']
    datadict = request.get_json()['datadict']
    rootName = request.get_json()['rootName']

    print("nodes: ", nodes)
    print("datadict:", datadict)
    # print("rootName:", rootName)

    specmetric_nodes = {}
    for n in nodes:
        parent = None
        if n['parent']:
            parent = specmetric_nodes[n['parent']]
        name = n['name']
        if len(name) == 1:
            name = name[0]
        else:
            print("NAME IS ", name)
        sn = ComputationNode(
            name, # name
            parent, # parent
            n['function'], # matched grammar rule
            input_data=n['input_data'],
            output_data=n['output_data']
            )

        specmetric_nodes[name] = sn

    root = specmetric_nodes[rootName]
    print("here, root is ", root)
    parser = ComputationTreeParser(root)
    parser.visualizeDFG()
    vis_containers = parser.visualization_containers
    print("vis_containers is ", vis_containers)
    r = AltairRenderer(vis_containers, datadict)
    charts = r.convert_to_charts()
    chart_timestamp_path = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.html")
    outpath = os.path.join(final_directory, chart_timestamp_path)
    charts.save(outpath, embed_options={'renderer':'svg'})

    return {'reload': True}

if __name__ == "__main__":
    app.run(debug=True)
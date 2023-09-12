from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from pathlib import Path
module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(''))))

if module_path not in sys.path:
    sys.path.append(module_path)

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
    return send_file("chart.html")

@app.route("/postSpecs", methods = ["POST"])
def getSpecs():
    nodes = request.get_json()['nodes']
    datadict = request.get_json()['datadict']
    rootName = request.get_json()['rootName']

    specmetric_nodes = {}
    for n in nodes:
        parent = None
        if n['parent']:
            parent = specmetric_nodes[n['parent']]
        name = n['name']
        if len(name) == 1:
            name = name[0]
        sn = ComputationNode(
            name, # name
            parent, # parent
            n['function'], # matched grammar rule
            input_data=n['input_data'],
            output_data=n['output_data']
            )

        specmetric_nodes[name] = sn

    root = specmetric_nodes[rootName]
    parser = ComputationTreeParser(root)
    parser.visualizeDFG()
    vis_containers = parser.visualization_containers
    r = AltairRenderer(vis_containers, datadict)
    charts = r.convert_to_charts()
    charts.save('chart.html', embed_options={'renderer':'svg'})

    return {'reload': True}

if __name__ == "__main__":
    app.run(debug=True)
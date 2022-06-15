from ast import AsyncFunctionDef
from flask import Flask, request, jsonify
import pandas as pd

#Base: Returns salesforce scraped data as a JSON object with each element being a node
#Layer 1: Filters and returns a JSON object of filtered/requested nodes
#Layer 2: Shit within a node

app = Flask(__name__)

df = pd.read_csv(r"C:\Users\akhil\OneDrive\Desktop\Apcela\sandbox\mapHostname\hostname_translation_data.csv")




@app.route('/nodes', methods = ['GET'])
def getDevices():
    nodesDict = df.to_dict('records') 
    args = request.args
    print(args)
    filteredNodes = filter(args, nodesDict)
    #filteredNodes = restrictiveFilter(args, nodesDict)

    return jsonify(filteredNodes)

#result is of a list of nodes matching criteria of any one filter NOT ALL FILTERS
def filter(args: dict, nodesDict: dict):
    if(args):
        filteredNodes = []
        nodeIndexes = set()
        """
        filters = args.keys()
        print(filters)
        for filter in filters:
            value = args.get(filter)
            print(value)
            indexes = df.index[df[filter] == value].tolist()
            for index in indexes:
                nodeIndexes.add(index)
        for index in nodeIndexes:
            filteredNodes.append(nodesDict[index])
        """
        arguments = request.args.to_dict(flat=False)
        for filter, values in arguments.items():
            print(filter)
            if filter == "Restrict":
                filteredNodes = restrictiveFilter(args, nodesDict)
                return filteredNodes
            else:
                for value in values:
                    indexes = df.index[df[filter] == value].tolist()
                    for index in indexes:
                        nodeIndexes.add(index)
        for index in nodeIndexes:
            filteredNodes.append(nodesDict[index])

    else:
        filteredNodes = nodesDict
    return filteredNodes

def restrictiveFilter(args, nodesDict):
    if(args):
        filteredNodes = []
        nodeIndexes = set()
        filters = args.keys()
        for filter in filters:
            if filter == "Restrict":
                pass
            else:
                value = args.get(filter)
                if(nodeIndexes):
                    for index in nodeIndexes.copy():
                        if(nodesDict[index][filter] == value):
                            pass
                        else:
                            nodeIndexes.remove(index)
                else:
                    indexes = df.index[df[filter] == value].tolist()
                    for index in indexes:
                        nodeIndexes.add(index)
        for index in nodeIndexes:
            filteredNodes.append(nodesDict[index])
        print(nodeIndexes)
    else:
        filteredNodes = nodesDict
    return filteredNodes

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port=105)


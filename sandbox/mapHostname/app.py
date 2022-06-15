from flask import Flask, request, jsonify
import pandas as pd

#Takes input of a location, returns all devices at that site

app = Flask(__name__)

df = pd.read_csv(r"C:\Users\akhil\OneDrive\Desktop\Apcela\sandbox\mapHostname\hostname_translation_data.csv")


@app.route('/<string:location>/', methods = ['GET', 'POST'])
def getDevices(location):
    devicesList = []
    nodeLength = len(df.index)
    for node in range(nodeLength):
        if(df.at[node, 'City'] == location):
            devicesList.append(df.at[node, 'Location Code'])
    return jsonify(devicesList)

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port=105)




#result is of a list of nodes matching every single filter
def restrictiveFilter(args, nodesDict):
    if(args):
        nodeIndexes = set()
        filters = args.keys()
        for filter in filters:
            value = args.get(filter)
            if(nodeIndexes):
                for index in nodeIndexes:
                    if(nodesDict[index][filter] == value):
                        pass
                    else:
                        nodeIndexes.remove(index)
            else:
                indexes = df.index[df[filter] == value].tolist()
                for index in indexes:
                    nodeIndexes.add(index)
        print(nodeIndexes)
    else:
        filteredNodes = nodesDict
    return filteredNodes
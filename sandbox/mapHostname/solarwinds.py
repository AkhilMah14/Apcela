import requests
from orionsdk import SwisClient

npm_server = 'sw.int.apcela.net'
username = 'cfnguest'
password = 'cfnpass'

verify = False
if not verify:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


swis = SwisClient(npm_server, username, password)

inputNode = input("Input an node abbreviation: ")

print("Query Test:")
nodes = swis.query("SELECT  NodeID, DisplayName, Location FROM Orion.Nodes WHERE DisplayName = @node", node = inputNode)

for node in nodes['results']:
    print("{DisplayName} has an NodeID of {NodeID} and is located at {Location}".format(**node))
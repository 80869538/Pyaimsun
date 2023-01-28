import os
import sys
import json

script_path = sys.argv[2]
 
# setting path
sys.path.insert(0,script_path)
from config import TEMPLATE_PATH
from core.aimsun import AimsunTemplate

# base_dir = os.path.dirname(os.path.realpath(__file__))

print('[load.py] Loading template ' + TEMPLATE_PATH)

model = AimsunTemplate(GKSystem, GKGUISystem)
model.load(TEMPLATE_PATH)
print("Hello From Aimsun")
replication_name = "Replication 86011"
replication = model.find_by_name(model.replications, replication_name)
if replication is None:
    print('[load.py] ERROR: Replication ' + replication_name +
          ' does not exist.')

model.run_replication(replication=replication, render=True)

# def load_network():
#     """Load the whole network into a dictionary and returns it.
#     """    
# path = os.path.join(base_dir, "Launch.bat")
# os.system(path) 

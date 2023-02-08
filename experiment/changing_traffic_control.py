import sys
sys.path.append("../")
from client import FlowAimsunAPI

NODE_ID = 423
PHASE_TO_CHANGE = 2
NEW_TIME = 16
previousPhase = None
timeLastChange = -100.0

api = FlowAimsunAPI(9999)
# api.stop_simulation()
api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()
# api.simulation_step()

# print(api.get_traffic_light_ids())
print(api.get_traffic_light_numbers(NODE_ID))
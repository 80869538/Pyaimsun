#This code will be executed inside the Aimsun.

import os
import sys
import json
import logging

from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *


logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)
logger.info("inside")
logger.info(sys.argv[0])
logger.info(sys.argv[1])
logger.info(sys.argv[2])

 
# setting path
project_path = sys.argv[2]
sys.path.insert(0, project_path)
from config import TEMPLATE_PATH, CONSOLE_MODE
from core.aimsun import AimsunTemplate

# HACK: Store port in author
port_string = sys.argv[1]


logger.info('[load.py] Loading template ' + TEMPLATE_PATH)


if not CONSOLE_MODE:
    model = AimsunTemplate(GKSystem, GKGUISystem)
    model.load(TEMPLATE_PATH)

else:
    model = AimsunTemplate(GKSystem)
    logger.info("Loading from the console")
    try:
        model.load(TEMPLATE_PATH)
    except Exception as e:
        logger.error(e, exc_info=True)




logger.info('[load.py] Loading Complete')
model.setAuthor(port_string)

logger.info("Hello From Aimsun")
replication_name = "Replication 86011"
replication = model.find_by_name(model.replications, replication_name)
if replication is None:
    logger.info('[load.py] ERROR: Replication ' + replication_name +
          ' does not exist.')
# Add API interactions
# experiment = replication.experiment
# scenario = experiment.scenario
# scenario_data = scenario.input_data
# scenario_data.add_extension(os.path.join(
#     project_path, 'core/utils/aimsun/run.py'), True)
model.run_replication(replication=replication, render=False)


"""Script used to interact with Aimsun's API during the simulation phase."""
import sys
import os


import AAPI as aimsun_api
from AAPI import *
from PyANGKernel import *
import socket
import struct
from _thread import start_new_thread
import core.constants as ac
import logging
logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)
logger.info("inside server")
logger.info(sys.argv[0])
logger.info(sys.argv[1])
logger.info(sys.argv[2])


model = GKSystem.getSystem().getActiveModel()
PORT = 9999
entered_vehicles = []
exited_vehicles = []

def send_message(conn, in_format, values):
    """Send a message to the client.

    If the message is a string, it is sent in segments of length 256 (if the
    string is longer than such) and concatenated on the client end.

    Parameters
    ----------
    conn : socket.socket
        socket for server connection
    in_format : str
        format of the input structure
    values : tuple of Any
        commands to be encoded and issued to the client
    """
    if in_format == 'str':
        packer = struct.Struct(format='i')
        values = values[0]
        logger.info(values)

        # when the message is too large, send value in segments and inform the
        # client that additional information will be sent. The value will be
        # concatenated on the other end
        while len(values) > 256:
            # send the next set of data
            conn.send(str.encode(values[:256]))
            values = values[256:]

            # wait for a reply
            data = None
            while data is None:
                data = conn.recv(2048)
                logger.info(data)

            # send a not-done signal
            packed_data = packer.pack(*(1,))
            logger.info("send packed data")
            logger.info(packed_data )
            conn.send(packed_data)

        # send the remaining components of the message (which is of length less
        # than or equal to 256)
        logger.info("connection sent")
        try:
            conn.send(str.encode(values))
        except Exception as e:
            logger.info(e)

        # wait for a reply
        data = None
        while data is None:
            data = conn.recv(2048)
            logger.info(data)
        logger.info("reply")
        logger.info(data)

        # send a done signal
        packed_data = packer.pack(*(0,))
        logger.info("packed_data")
        logger.info(packed_data)
        conn.send(packed_data)
    else:
        packer = struct.Struct(format=in_format)
        packed_data = packer.pack(*values)
        conn.send(packed_data)
def retrieve_message(conn, out_format):
    """Retrieve a message from the client.

    Parameters
    ----------
    conn : socket.socket
        socket for server connection
    out_format : str or None
        format of the output structure

    Returns
    -------
    Any
        received message
    """
    unpacker = struct.Struct(format=out_format)
    try:
        data = conn.recv(unpacker.size)
        unpacked_data = unpacker.unpack(data)
    finally:
        pass
    return unpacked_data


def threaded_client(conn):
    """Create a threaded process.

    This process is called every simulation step to interact with the aimsun
    server, and terminates once the simulation is ready to execute a new step.

    Parameters
    ----------
    conn : socket.socket
        socket for server connection
    """
    # send feedback that the connection is active
    conn.send(b'Ready.')

    done = False
    while not done:
        # receive the next message
        data = conn.recv(2048)

        if data is not None:
            # if the message is empty, search for the next message
            if data == '':
                continue

            # convert to integer
            if data != b'':
                data = int(data)

            # if the simulation step is over, terminate the ring and let
            # the step be executed
            if data == ac.SIMULATION_STEP:
                send_message(conn, in_format='i', values=(0,))
                done = True

            # Note that alongside this, the process is closed in Flow,
            # thereby terminating the socket connection as well.
            elif data == ac.SIMULATION_TERMINATE:
                send_message(conn, in_format='i', values=(0,))
                done = True

            elif data == ac.ADD_VEHICLE:
                send_message(conn, in_format='i', values=(0,))

                edge, lane, type_id, pos, speed, next_section = \
                    retrieve_message(conn, 'i i i f f i')

                # 1 if tracked, 0 otherwise
                tracking = 1

                veh_id = aimsun_api.AKIPutVehTrafficFlow(
                    edge, lane+1, type_id, pos, speed, next_section,
                    tracking
                )

                send_message(conn, in_format='i', values=(veh_id,))


                entered_vehicles = []


            elif data == ac.VEH_GET_LENGTH:
                send_message(conn, in_format='i', values=(0,))
                veh_id, = retrieve_message(conn, 'i')

                static_info = aimsun_api.AKIVehGetStaticInf(veh_id)
                output = static_info.length

                send_message(conn, in_format='f', values=(output,))

            elif data == ac.VEH_GET_STATIC:
                send_message(conn, in_format='i', values=(0,))
                veh_id, = retrieve_message(conn, 'i')

                static_info = aimsun_api.AKIVehGetStaticInf(veh_id)
                output = (static_info.report,
                          static_info.idVeh,
                          static_info.type,
                          static_info.length,
                          static_info.width,
                          static_info.maxDesiredSpeed,
                          static_info.maxAcceleration,
                          static_info.normalDeceleration,
                          static_info.maxDeceleration,
                          static_info.speedAcceptance,
                          static_info.minDistanceVeh,
                          static_info.giveWayTime,
                          static_info.guidanceAcceptance,
                          static_info.enrouted,
                          static_info.equipped,
                          static_info.tracked,
                          static_info.keepfastLane,
                          static_info.headwayMin,
                          static_info.sensitivityFactor,
                          static_info.reactionTime,
                          static_info.reactionTimeAtStop,
                          static_info.reactionTimeAtTrafficLight,
                          static_info.centroidOrigin,
                          static_info.centroidDest,
                          static_info.idsectionExit,
                          static_info.idLine)

                send_message(conn,
                             in_format='i i i f f f f f f f f f f i i i ? '
                                       'f f f f f i i i i',
                             values=output)


            elif data == ac.TL_GET_IDS:

                send_message(conn, in_format='i', values=(0,))

                data = None
                while data is None:
                    data = conn.recv(256)
                    logger.info(data)

                num_meters = aimsun_api.ECIGetNumberMeterings()
                logger.info(num_meters)
                if num_meters == 0:
                    output = '-1'
                else:
                    meter_ids = []
                    for i in range(1, num_meters + 1):
                        struct_metering = ECIGetMeteringProperties(i)
                        meter_id = struct_metering.Id
                        meter_ids.append(meter_id)
                    output = ':'.join([str(e) for e in meter_ids])
                send_message(conn, in_format='str', values=(output,))

            elif data == ac.TL_SET_STATE:
                send_message(conn, in_format='i', values=(0,))
                meter_aimsun_id, state = retrieve_message(conn, 'i i')
                time = AKIGetCurrentSimulationTime()  # simulation time
                sim_step = AKIGetSimulationStepTime()
                identity = 0
                ECIChangeStateMeteringById(
                    meter_aimsun_id, state, time, sim_step, identity)
                send_message(conn, in_format='i', values=(0,))

            
            elif data == ac.TL_GET_NM:
                logger.info("get traffic light")
                logger.info(data)
                try:
                    send_message(conn, in_format='i', values=(0,))
                    node_id, = retrieve_message(conn, 'i')
                    logger.info(node_id)
                    num_lights = ECIGetNumberSem(node_id)
                    send_message(conn, in_format='i',values=(num_lights,))
                except Exception as e:
                    logger.info(e)



            elif data == ac.TL_GET_STATE:
                send_message(conn, in_format='i', values=(0,))
                meter_aimsun_id = retrieve_message(conn, 'i')
                lane_id = 1  # TODO double check
                state = ECIGetCurrentStateofMeteringById(
                    meter_aimsun_id, lane_id)
                send_message(conn, in_format='i', values=(state,))

            elif data == ac.GET_EDGE_NAME:
                send_message(conn, in_format='i', values=(0,))

                # get the edge ID in flow
                edge = None
                while edge is None:
                    edge = conn.recv(2048)

                model = GKSystem.getSystem().getActiveModel()
                edge_aimsun = model.getCatalog().findByName(
                    edge, model.getType('GKSection'))

                if edge_aimsun:
                    send_message(conn, in_format='i',
                             values=(edge_aimsun.getId(),))
                else:
                    send_message(conn, in_format='i',
                            values=(int(edge),))

            # in case the message is unknown, return -1001
            else:
                send_message(conn, in_format='i', values=(-1001,))

    # close the connection
    conn.close()


def AAPILoad():
    """Execute commands while the Aimsun template is loading."""
    return 0


def AAPIInit():
    """Execute commands while the Aimsun instance is initializing."""
    # set the simulation time to be very large
    AKISetEndSimTime(2e6)
    return 0


def AAPIManage(time, timeSta, timeTrans, acycle):
    """Execute commands before an Aimsun simulation step."""
    # tcp/ip connection from the aimsun process
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', PORT))

    # connect to the Flow instance
    server_socket.listen(10)
    logger.info("Waiting for connection")
    print("Waiting for connection")
    c, address = server_socket.accept()

    # start the threaded process
    start_new_thread(threaded_client, (c,))

    return 0


def AAPIPostManage(time, timeSta, timeTrans, acycle):
    """Execute commands after an Aimsun simulation step."""
    return 0


def AAPIFinish():
    """Execute commands while the Aimsun instance is terminating."""
    return 0


def AAPIUnLoad():
    """Execute commands while Aimsun is closing."""
    return 0


def AAPIPreRouteChoiceCalculation(time, timeSta):
    """Execute Aimsun route choice calculation."""
    return 0


def AAPIEnterVehicle(idveh, idsection):
    """Execute command once a vehicle enters the Aimsun instance."""
    global entered_vehicles
    entered_vehicles.append(idveh)
    return 0


def AAPIExitVehicle(idveh, idsection):
    """Execute command once a vehicle exits the Aimsun instance."""
    global exited_vehicles
    exited_vehicles.append(idveh)
    return 0


def AAPIEnterPedestrian(idPedestrian, originCentroid):
    """Execute command once a pedestrian enters the Aimsun instance."""
    return 0


def AAPIExitPedestrian(idPedestrian, destinationCentroid):
    """Execute command once a pedestrian exits the Aimsun instance."""
    return 0


def AAPIEnterVehicleSection(idveh, idsection, atime):
    """Execute command once a vehicle enters the Aimsun instance."""
    return 0


def AAPIExitVehicleSection(idveh, idsection, atime):
    """Execute command once a vehicle exits the Aimsun instance."""
    return 0

# from _thread import start_new_thread
# import socket
# PORT = 9999

# print("Starting TCP server from the aimsun")
# while True:
#     # tcp/ip connection from the aimsun process
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     with server_socket:
#         server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         server_socket.bind(('localhost', PORT))

#         # connect to the Flow instance
#         server_socket.listen()
#         conn, address = server_socket.accept()

#         with conn:
#             print(f"Connected by {conn}")
#             while True:
#                 data = conn.recv(1024)
#                 if not data:
#                     break
#                 conn.sendall(data)

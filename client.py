"""Contains the Flow/Aimsun API manager."""
import socket
import logging
import struct

import core.constants as ac
import aimsun_struct

# this is used when identifying if a specific object is tracked
INFOS_ATTR_BY_INDEX = [
    'CurrentPos', 'distance2End', 'xCurrentPos', 'yCurrentPos', 'zCurrentPos',
    'xCurrentPosBack', 'yCurrentPosBack', 'zCurrentPosBack', 'CurrentSpeed',
    'TotalDistance', 'SectionEntranceT', 'CurrentStopTime', 'stopped',
    'idSection', 'segment', 'numberLane', 'idJunction', 'idSectionFrom',
    'idLaneFrom', 'idSectionTo', 'idLaneTo'
]



def create_client(port, print_status=False):
    """Create a socket connection with the server.

    Parameters
    ----------
    port : int
        the port number of the socket connection
    print_status : bool, optional
        specifies whether to print a status check while waiting for connection
        between the server and client

    Returns
    -------
    socket.socket
        socket for client connection
    """
    # create a socket connection
    if print_status:
        print('Listening for connection...', end=' ')

    stop = False
    while not stop:
        # try to connect
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', port))

            # check the connection
            data = None
            while data is None:
                data = s.recv(2048)
            stop = True

        except Exception as e:
            logging.debug('Cannot connect to the server: {}'.format(e))

        except socket.error:
            stop = False

    # print the return statement
    if print_status:
        print(data.decode('utf-8'))

    return s


class FlowAimsunAPI(object):
    """An API used to interact with Aimsun via a TCP connection.

    This is needed since Aimsun is written in Python 2.7.4, and may be
    deprecated in the future. An server/client connection is created between
    Flow and the Aimsun run script. The client is passed to this object and
    commands are accordingly provided to the Aimsun sever via this client.
    """

    def __init__(self, port):
        """Instantiate the API.

        Parameters
        ----------
        port : int
            the port number of the socket connection
        """
        self.port = port
        self.s = create_client(port, print_status=True)

    def _send_command(self, command_type, in_format, values, out_format):
        """Send an arbitrary command via the connection.

        Commands are sent in two stages. First, the client sends the command
        type (e.g. ac.REMOVE_VEHICLE) and waits for a conformation message from
        the server. Once the confirmation is received, the client send a
        encoded binary packet that the server will be prepared to decode, and
        will then receive some return value (either the value the client was
        requesting or a 0 signifying that the command has been executed. This
        value is then returned by this method.

        Parameters
        ----------
        command_type : flow.utils.aimsun.constants.*
            the command the client would like Aimsun to execute
        in_format : str or None
            format of the input structure
        values : tuple of Any or None
            commands to be encoded and issued to the server
        out_format : str or None
            format of the output structure

        Returns
        -------
        Any
            the final message received from the Aimsun server
        """
        # send the command type to the server
        self.s.send(str(command_type).encode())

        # wait for a response
        unpacker = struct.Struct(format='i')
        data = None
        while data is None:
            data = self.s.recv(unpacker.size)
          
        print(data)
        # send the command values
        if in_format is not None:
            if in_format == 'str':
                self.s.send(str.encode(values[0]))
            else:
                packer = struct.Struct(format=in_format)
                packed_data = packer.pack(*values)
                self.s.send(packed_data)
        else:
            # if no command is needed, just send a status response
            self.s.send(str.encode('1'))

        # collect the return values
        if out_format is not None:
            if out_format == 'str':
                done = False
                unpacked_data = ''
                while not done:
                    # get the next bit of data
                    data = None
                    while data is None or data == b'':
                        data = self.s.recv(256)
                        print(data)

                    # concatenate the results
                    unpacked_data += data.decode('utf-8')

                    # ask for a status check (just by sending any command)
                    self.s.send(str.encode('1'))

                    # check if done
                    unpacker = struct.Struct(format='i')
                    data = None
                    while data is None:
                        data = self.s.recv(unpacker.size)
                        print(data)
                    done = unpacker.unpack(data)[0] == 0
            else:
                unpacker = struct.Struct(format=out_format)
                data = None
                while data is None:
                    data = self.s.recv(unpacker.size)
                print(data)
                unpacked_data = unpacker.unpack(data)

            return unpacked_data

    def simulation_step(self):
        """Advance the simulation by one step.

        Since the connection is lost when this happens, this method also waits
        for and reconnects to the server.
        """
        self._send_command(ac.SIMULATION_STEP,
                           in_format=None, values=None, out_format=None)

        # reconnect to the server
        self.s = create_client(self.port)

    def stop_simulation(self):
        """Terminate the simulation.

        This will close the connection on both the client and server side.
        """
        # inform the simulation that it should terminate the simulation and the
        # server connection
        self._send_command(ac.SIMULATION_TERMINATE,
                           in_format=None, values=None, out_format=None)

        # terminate the connection
        self.s.close()

    def get_edge_name(self, edge):
        """Get the name of an edge in Aimsun.

        Parameters
        ----------
        edge : str
            name of the edge in Flow

        Returns
        -------
        int
            name of the edge in Aimsun
        """
        return self._send_command(ac.GET_EDGE_NAME,
                                  in_format='str',
                                  values=(edge,),
                                  out_format='i')[0]

    def add_vehicle(self, edge, lane, type_id, pos, speed, next_section):
        """Add a vehicle to the network.

        Parameters
        ----------
        edge : int
            name of the start edge
        lane : int
            start lane
        type_id : int or string
            vehicle type (id or name)
        pos : float
            starting position
        speed : float
            starting speed
        next_section : int
            the edge number the vehicle should move towards after the current
            edge it is one. If set to -1, the vehicle takes the next feasible
            route

        Returns
        -------
        int
            name of the new vehicle in Aimsun
        """
        # if type_id is a string, retrieve the id of the type
        if isinstance(type_id, str):
            type_id = self._send_command(ac.VEH_GET_TYPE_ID,
                                         in_format='str',
                                         values=(type_id,),
                                         out_format='i')[0]
        # TODO maybe put back the type conversion dict
        # to avoid useless API calls

        veh_id, = self._send_command(
            ac.ADD_VEHICLE,
            in_format='i i i f f i',
            values=(edge, lane, type_id, pos, speed, next_section),
            out_format='i')

        return veh_id

    def remove_vehicle(self, veh_id):
        """Remove a vehicle from the network.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        """
        self._send_command(ac.REMOVE_VEHICLE,
                           in_format='i',
                           values=(veh_id,),
                           out_format='i')

   

    def get_vehicle_static_info(self, veh_id):
        """Return the static information of the specified vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun

        Returns
        -------
        flow.utils.aimsun.struct.StaticInfVeh
            static info object
        """
        static_info = aimsun_struct.StaticInfVeh()

        (static_info.report,
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
         static_info.idLine) = self._send_command(
            ac.VEH_GET_STATIC,
            in_format='i',
            values=(veh_id,),
            out_format='i i i f f f f f f f f f f i i i ? f f f f f i i i i')

        return static_info

    def get_vehicle_tracking_info(self, veh_id, info_bitmap, tracked=True):
        """Return the tracking information of the specified vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        info_bitmap : str
            bitmap representing the tracking info to be returned
            (cf function make_bitmap_for_tracking in vehicle/aimsun.py)
        tracked : boolean (defaults to True)
            whether the vehicle is tracked in Aimsun.


        Returns
        -------
        flow.utils.aimsun.struct.InfVeh
            tracking info object
        """
        # build the output format from the bitmap
        out_format = ''
        for i in range(len(info_bitmap)):
            if info_bitmap[i] == '1':
                if i <= 12:
                    out_format += 'f '
                else:
                    out_format += 'i '
        if out_format == '':
            return
        else:
            out_format = out_format[:-1]

        # append tracked boolean and vehicle id to the bitmap
        # so that the command only has one parameter
        info_bitmap += "1" if tracked else "0"
        val = str(veh_id) + ":" + info_bitmap

        # retrieve the vehicle tracking info specified by the bitmap
        info = self._send_command(
            ac.VEH_GET_TRACKING,
            in_format='str',
            values=(val,),
            out_format=out_format)

        # place these tracking info into a struct
        ret = aimsun_struct.InfVeh()
        count = 0
        for map_index in range(len(INFOS_ATTR_BY_INDEX)):
            if info_bitmap[map_index] == '1':
                setattr(ret, INFOS_ATTR_BY_INDEX[map_index], info[count])
                count += 1

        return ret

 
    def get_traffic_light_ids(self):
        """Return the ids of all traffic lights in the network."""
        tl_ids = self._send_command(ac.TL_GET_IDS,
                                    in_format=None,
                                    values=None,
                                    out_format='str')

        if tl_ids == '-1':
            return []
        else:
            tl_ids = tl_ids.split(':')
            return [int(t) for t in tl_ids]

    def get_traffic_light_numbers(self, junction_id):
        """Return the numbers of all traffic lights on a junction."""
        tl_num = self._send_command(ac.TL_GET_NM,
                                    in_format='i',
                                    values=(junction_id,),
                                    out_format='i')

        return tl_num

    def get_traffic_light_state(self, tl_id):
        """Get the traffic light state of a specific set of traffic light(s).

        Parameters
        ----------
        tl_id : int
            name of the traffic light node in Aimsun

        Returns
        -------
        str
            traffic light state of each light on that node
        """
        res, = self._send_command(ac.TL_GET_STATE, values=(tl_id,),
                                  in_format='i',
                                  out_format='i')
        return res

    def set_traffic_light_state(self, tl_id, link_index, state):
        """Set the state of the specified traffic light(s).

        Parameters
        ----------
        tl_id : int
            name of the traffic light node in Aimsun
        link_index : TODO
            TODO
        state : str
            TODO
        """
        self._send_command(ac.TL_SET_STATE,
                           in_format='i i i',
                           values=(tl_id, link_index, state),
                           out_format=None)

    def set_vehicle_tracked(self, veh_id):
        """Set a vehicle as tracked in Aimsun.

        This thus allows for faster tracking information retrieval.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        """
        self._send_command(ac.VEH_SET_TRACKED,
                           in_format='i',
                           values=(veh_id,),
                           out_format=None)

    def set_vehicle_no_tracked(self, veh_id):
        """Set a tracked vehicle as untracked in Aimsun.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        """
        self._send_command(ac.VEH_SET_NO_TRACKED,
                           in_format='i',
                           values=(veh_id,),
                           out_format=None)
# # echo-client.py

# import socket

# HOST = "127.0.0.1"  # The server's hostname or IP address
# PORT = 9999  # The port used by the server

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     # s.sendall(b"Hello, world")
#     # data = s.recv(1024)

# # print(f"Received {data!r}")
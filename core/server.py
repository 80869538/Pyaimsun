"""Script used to interact with Aimsun's API during the simulation phase."""
import config
import sys
import os

sys.path.append(os.path.join(config.AIMSUN_NEXT_PATH,
                             'programming/Aimsun Next API/AAPIPython/Micro'))

import AAPI as aimsun_api
from AAPI import *
from PyANGKernel import *
import socket
import struct
from _thread import start_new_thread
import numpy as np

model = GKSystem.getSystem().getActiveModel()
PORT = int(model.getAuthor())
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

        # when the message is too large, send value in segments and inform the
        # client that additional information will be sent. The value will be
        # concatenated on the other end
        while len(values) > 256:
            # send the next set of data
            conn.send(values[:256])
            values = values[256:]

            # wait for a reply
            data = None
            while data is None:
                data = conn.recv(2048)

            # send a not-done signal
            packed_data = packer.pack(*(1,))
            conn.send(packed_data)

        # send the remaining components of the message (which is of length less
        # than or equal to 256)
        conn.send(values)

        # wait for a reply
        data = None
        while data is None:
            data = conn.recv(2048)

        # send a done signal
        packed_data = packer.pack(*(0,))
        conn.send(packed_data)
    else:
        packer = struct.Struct(format=in_format)
        packed_data = packer.pack(*values)
        conn.send(packed_data)
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

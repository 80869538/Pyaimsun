from _thread import start_new_thread
import socket
PORT = 9999

print("Starting TCP server from the aimsun")
while True:
    # tcp/ip connection from the aimsun process
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    with server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', PORT))

        # connect to the Flow instance
        server_socket.listen()
        conn, address = server_socket.accept()

        with conn:
            print(f"Connected by {conn}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# System modules
import socket
import sys
import threading
# Internal modules
from config_srv import CONFIGURATION
import client_http


def config():
    """
    Assigns a valid host name.
    Displays the current configuration
    :return: None
    :rtype: None
    """
    CONFIGURATION['Host'] = socket.gethostname()
    print("-------------")
    print("Host:", CONFIGURATION['Host'])
    print("Port :", CONFIGURATION['Port'])
    print("Path :", CONFIGURATION['Path'])
    return


def server_shutdown(sock):
    """
    Turns off the server/socket
    :type sock: socket.socket
    :return: None
    :rtype: None
    """
    print("The server is shutting down.")
    try:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        sys.exit(0)
    except OSError:
        print("Closing error.")
        sys.exit(1)


def listen(sock):
    """
    Allows the server socket to listen for incoming connections.
    Repeat the following sequence indefinitely:
        wait for a new incoming connection
        display a message on the console indicating this connection
        transmits the necessary parameters to the start function
    :type sock: socket.socket
    :return: None
    :rtype: None
    """
    try:
        sock.listen()
        while True:
            (client, address) = sock.accept()
            print("-------------" + "\n" + "Connection received from", address)
            start(client)
    except KeyboardInterrupt:
        print("Socket stopped manually")
    except OSError:
        print("Socket listening error")
    return


def start(sock):
    """
    Start a new thread to manage a new connection
    :t: thread
    :param sock: socket
    :return: None
    """
    try:
        t = threading.Thread(target=client_http.client_processing, args=[sock])
        t.start()
    except OSError:
        return None
    return


def main():
    config()
    host = "127.0.0.1"
    port = CONFIGURATION['Port']
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                print("-------------" + "\n" + "The server has started on the port: ", port)
            except PermissionError:
                print("Unauthorized port.")
            except OSError:
                print("Cannot attach the socket to this port.")
                server_shutdown(sock)
            listen(sock)
    except OSError:
        print("Socket creation failure.")


if __name__ == "__main__":
    main()

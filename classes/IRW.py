#!/usr/bin/env python

'''
Read lirc output, in order to sense key presses on an IR remote.

In order for commands to be read, a configuration file for your remote must exist in
your lirc directory at /etc/lirc/lircd.conf.d. Common remote configuration files can be
found and downloaded from http://lirc-remotes.sourceforge.net/remotes-table.html.

Based on pyirw.py by Akkana Peck, https://github.com/akkana/scripts/blob/master/rpi/pyirw.py
'''

import socket


class IRW:
    def __init__(self, _socket_path="/var/run/lirc/lircd"):
        self._socket_path = _socket_path
        # Automatically connect to a socket
        self._sock = self._connect()
        
    # Initialize and connect to the socket for reading IR commands
    def _connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self._socket_path)
        
        return sock
        
    # Check if an IR key is received and return either the command or None
    def get_key(self):
        data = self._sock.recv(128)
        data = data.strip()

        # If a key is received
        if data:
            # Decode the key command from the received data
            try:
                command = data.decode().split()[2]
                return command
            # If the data is somehow corrupted and can't be indexed
            except IndexError:
                return None


if __name__ == '__main__':
    irw = IRW()

    while True:
        command = irw.get_key()
        if command:
            print(command)
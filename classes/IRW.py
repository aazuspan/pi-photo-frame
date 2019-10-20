#!/usr/bin/env python

'''
Read lirc output, in order to sense key presses on an IR remote.

In order for commands to be read, a configuration file for your remote must exist in
your lirc directory at /etc/lirc/lircd.conf.d. Common remote configuration files can be
found and downloaded from http://lirc-remotes.sourceforge.net/remotes-table.html.

Based on pyirw.py by Akkana Peck, https://github.com/akkana/scripts/blob/master/rpi/pyirw.py
'''

import socket
import select


class IRW:
    def __init__(self, socket_path="/var/run/lirc/lircd", timeout=0.1, blocking=1):
        self._socket_path = socket_path
        # How long to look for data each call (longer values will slow down the rest of the program, but are less likely to miss commands)
        self._timeout = timeout
        # Should the socket block the rest of the program until data is received? Timeout must be None to enable blocking
        self._blocking = blocking
        # Automatically connect to a socket
        self._sock = self._connect()

        
    # Initialize and connect to the socket for reading IR commands
    def _connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(self._blocking)
        sock.settimeout(self._timeout)
        sock.connect(self._socket_path)
        
        return sock
        
    # Check if an IR key is received and return either the command or None
    def get_key(self):
        try:
            # Check if IR data is available on the socket
            data = self._sock.recv(128)
            data = data.strip()
            # Decode the key command from the received data
            try:
                command = data.decode().split()[2]
                return command
            # If the data is somehow corrupted and can't be indexed
            except IndexError:
                return None
        # If no data is received
        except Exception:
            return None

if __name__ == '__main__':
    irw = IRW()

    while True:
        print('test')
        command = irw.get_key()
        if command:
            print(command)
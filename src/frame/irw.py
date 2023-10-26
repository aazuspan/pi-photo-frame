import socket


class IRW:
    """
    Read lirc output, in order to sense key presses on an IR remote.

    In order for commands to be read, a configuration file for your remote must exist in
    your lirc directory at /etc/lirc/lircd.conf.d. Common remote configuration files can be
    found and downloaded from http://lirc-remotes.sourceforge.net/remotes-table.html.

    Based on pyirw.py by Akkana Peck, https://github.com/akkana/scripts/blob/master/rpi/pyirw.py
    """
    def __init__(self, socket_path="/var/run/lirc/lircd", timeout=0.01, blocking=False):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.setblocking(blocking)
        self._sock.settimeout(timeout)
        self._sock.connect(socket_path)

    def get_key(self):
        """Return a command if one is received."""
        try:
            data = self._sock.recv(128).strip()
            return data.decode().split()[2]
        except Exception:
            return None

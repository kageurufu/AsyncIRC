import sys
from functools import wraps
import socket
import ssl
import threading
import logging

if sys.hexversion < 0x03000000:
    #Python 2
    import Queue as queue
    BlockingIOError = socket.error
else:
    import queue

class IRCClient(object):
    """Provides real-time multithreaded IRC Client communication

    Provides multithreaded IRC connections for real-time communication
    using the IRC networks using threads and queues to handle communication
    with the server, and pseudo-asynchronous IO to the server


    host
      hostname or IP of the server to connect to

    port
      port the server is listening on

    nick
      your IRC nickname for the connection

    ident
      Your client identification string

    realname
      Your real name (not important, but required)

    password
      The IRC Server's password, if required
    """
    _socket = None
    _in_queue = None
    _out_queue = None
    _send_thread = None
    _recv_thread = None
    _stop_event = None

    host = None
    port = None
    nick = None
    ident = None
    realname = None
    password = None
    running = True

    def __init__(self, host, port=6667, nick='UNCONFIGURED', ident='PythonIRCClient', realname='PythonIRCClient',
                 password=None, use_ssl=False):
        """Create a new IRC Client instance

        :param host: required server host

        :param port=6667: required server port

        :param nick='UCONFIGURED': your IRC Nickname

        :param ident='PythonIRCClient': your ident string, set to the name of your program

        :param realname='PythonIRCClient': Your real name (pseudonym, etc)

        :param password=None: Password for the server
        """
        self.host = host
        self.port = port
        self.nick = nick
        self.password = password
        self.ident = ident
        self.realname = realname
        self.use_ssl = use_ssl

        self._in_queue = queue.Queue()
        self._out_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if use_ssl:
            self._regular_socket = self._socket
            self._socket = ssl.wrap_socket(self._regular_socket)


    def _async_send(self):
        logging.info("Send loop started")
        while not self._stop_event.is_set():
            try:
                msg = self._out_queue.get(timeout=1)
                if msg:
                    while True: #Retry sending until it succeeds
                        try:
                            self._socket.send(msg.encode("UTF-8"))
                            self._out_queue.task_done()
                        except BlockingIOError:
                            pass
                        else:
                            break
                    logging.debug(msg)
            except queue.Empty as e:
                pass
        logging.info("Send loop stopped")

    def _async_recv(self):
        """No raw bytes should escape from this, all byte encoding and
        decoding should be handling inside this function"""

        logging.info("Receive loop started")
        recbuffer = b""

        while not self._stop_event.is_set():
            try:
                recbuffer = recbuffer + self._socket.recv(1024)
                data = recbuffer.split(b'\r\n')
                recbuffer = data.pop()
                if data:
                    for line in data:
                        self._process_data(line.decode(encoding='UTF-8', errors='ignore'))
            except BlockingIOError as e:
                pass
        logging.info("Receive loop stopped")

    def _process_data(self, line):
        line = line.rstrip()
        line = line.split()
        if not line:
            #blank line, pass
            return
        elif line[0] == 'PING':
            self.send_raw('PONG {pong}'.format(pong=line[1]))
        else:
            self._in_queue.put(line)
        logging.debug(' '.join(line))

    def start(self):
        self._socket.connect((self.host, self.port))
        self._socket.setblocking(0)

        self.running = True

        self._send_thread = threading.Thread(target=self._async_send)
        self._recv_thread = threading.Thread(target=self._async_recv)

        self._send_thread.start()
        self._recv_thread.start()

        if self.password:
            self.send_raw("PASS {password}".format(password=self.password))
        self.send_raw("NICK {nick}".format(nick=self.nick))
        self.send_raw("USER {ident} {host} localhost :{realname}".format(
            ident=self.ident,
            host=self.host,
            realname=self.realname))


    def stop(self):
        self.running = False
        self.send_raw("QUIT")
        self._stop_event.set()
        self._send_thread.join()
        self._recv_thread.join()
        self.running = False

    def get_message(self, block=True, timeout=None):
        return self._in_queue.get(block, timeout)

    def send_raw(self, msg):
        if msg[-2:] != "\r\n":
            msg += "\r\n"
        self._out_queue.put(msg)

    def join(self, channel, key=None):
        if channel[0] != "#":
            channel = "#" + channel
        if key:
            self.send_raw("JOIN %s; %s" % (channel, key))
        else:
            self.send_raw("JOIN %s" % channel)

    def msg(self, channel, message):
        self.send_raw("PRIVMSG {channel} :{message}".format(channel=channel, message=message))

__all__ = ['IRCClient']
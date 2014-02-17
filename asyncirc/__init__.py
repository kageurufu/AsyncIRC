"""AsyncIRC

Asynchronous multithreaded IRC library
IRCClient is the core IRC Client library, utilizing `threading.Thread`, `threading.Event`, `queue.Queue`, and
`socket.socket` in order to provide safely buffered, non-blocking, asynchronous communication with an IRC Server.

 By instatiating multiple copies of `IRCClient` you can connect to multiple IRC Servers
"""

__author__ = 'Franklyn Tackitt'
__version__ = (0,0,3)

from .ircclient import IRCClient
from .ircbot import IRCBot

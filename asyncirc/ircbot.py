'''Todo:
* Add multiple thread support for async_process functions
* Potentially thread each handler function? idk
'''

import sys
import socket
import re
import threading
import logging
import time

if sys.hexversion < 0x03000000:
    #Python 2
    import Queue as queue
    BlockingIOError = socket.error
else:
    import queue

from .ircclient import IRCClient

#Somewhat complex regex that accurately matches nick!username@host, with named groups for easy parsing and usage
user_re = re.compile(r'(?P<nick>[\w\d<-\[\]\^\{\}\~\-]+)!(?P<user>[\w\d<-\[\]\^\{\}\~]+)@(?P<host>.+)')

class IRCBot(IRCClient):
    '''See `IRCClient` for basic client usage, here is usage for the bot system

    Handler notation:
    on_join(self, nick, host, channel)
    on_topic(self, nick, host, channel, topic)
    on_part(self, nick, host, channel, message)
    on_msg(self, nick, host, channel, message)
    on_privmsg(self, nick, host, message)
    on_chanmsg(self, nick, host, channel, message)
    on_notice(self, nick, host, channel, message)
    on_nick(self, nick, new_nick, host)
    '''

    _handlers = {
        'join': [],
        'part': [],
        'kick': [],
        'topic': [],
        'msg': [],
        'privmsg': [],
        'chanmsg': [],
        'notice': [],
        'nick': []
    }

    _process_thread = None

    def _async_process(self):
        while not self._stop_event.is_set():
            time.sleep(0.01)
            try:
                args = self._in_queue.get_nowait()
                #These "msg"s will be raw irc received lines, which have several forms
                # basically, we should be looking for
                # :User!Name@host COMMAND <ARGS>
                logging.debug(args)
                userhost = user_re.search(args[0][1:])

                if userhost:

                    nick, host, user = userhost.groups()

                    command = args[1]

                    if command == 'JOIN':
                        channel = args[2][1:] #JOIN Channels are : prefixed
                        for handler in self._handlers['join']:
                            handler(self, nick, host, channel)
                    elif command == 'TOPIC':
                        channel = args[2]
                        topic = ' '.join(args[3:])
                        for handler in self._handlers['topic']:
                            handler(self, nick, host, channel, topic)
                    elif command == 'PART':
                        channel = args[2]
                        message = ' '.join(args[3:])
                        for handler in self._handlers['part']:
                            handler(self, nick, host, channel, message)
                    elif command == 'PRIVMSG':
                        channel = args[2]
                        message = ' '.join(args[3:])[1:]
                        for handler in self._handlers['msg']:
                            handler(self, nick, host, channel, message)
                        if channel[0] == '#':
                            #this is a channel
                            for handler in self._handlers['chanmsg']:
                                handler(self, nick, host, channel, message)
                        else:
                            #private message
                            for handler in self._handlers['privmsg']:
                                handler(self, nick, host, message)
                    elif command == 'KICK':
                        channel = args[2]
                        kicked_nick = args[3]
                        reason = ' '.join(args[4:])[1:]
                        for handler in self._handlers['kick']:
                            handler(self, nick, host, channel, kicked_nick, reason)
                    elif command == 'NICK':
                        new_nick = args[2][1:]
                        for handler in self._handlers['nick']:
                            handler(self, nick, new_nick, host)
                    elif command == 'NOTICE':
                        #:nick!user@host NOTICE <userchan> :message
                        channel = args[2]
                        message = ' '.join(args[3:])
                        for handler in self._handlers['notice']:
                            handler(self, nick, host, channel, message)
                    else:
                        logging.warning("Unhandled command %s" % command)

                self._in_queue.task_done()
            except queue.Empty as e: pass
            except Exception as e:
                logging.debug(e.args)

    def start(self):
        IRCClient.start(self)
        self._process_thread = threading.Thread(target=self._async_process)
        self._process_thread.start()

    def on(self, type):
        '''Decorator function'''
        def decorator(self, func):
            '''decorated functions should be written as class methods
                @on('join')
                def on_join(self, channel):
                    print("Joined channel %s" % channel)
            '''
            self._handlers[type].append(func)
            return func

        return decorator

    def on_join(self, func):
        self._handlers['join'].append(func)
        return func

    def on_part(self, func):
        self._handlers['part'].append(func)
        return func

    def on_kick(self, func):
        self._handlers['kick'].append(func)
        return func

    def on_msg(self, func):
        self._handlers['msg'].append(func)
        return func

    def on_privmsg(self, func):
        self._handlers['privmsg'].append(func)
        return func

    def on_chanmsg(self, func):
        self._handlers['chanmsg'].append(func)
        return func

    def on_notice(self, func):
        self._handlers['notice'].append(func)
        return func

    def on_nick(self, func):
        self._handlers['nick'].append(func)
        return func

__all__ = ['IRCBot']

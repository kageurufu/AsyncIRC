import logging

from asyncirc.ircbot import IRCBot
import sys

if sys.hexversion > 0x03000000:
    raw_input = input

if len(sys.argv) < 4:
    print("Usage: %s <hostname> <port> <nickname>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)

irc = IRCBot(sys.argv[1], int(sys.argv[2]), sys.argv[3])

@irc.on_join
def on_join(self, nick, host, channel):
    self.msg(channel, 'Hello')

@irc.on_msg
def on_msg(self, nick, host, channel, message):
    if message.lower().startswith('!help'):
        self.msg(nick, 'some help, idk')

irc.start()

irc.join("#luna")

try:
    while irc.running:
        irc.send_raw(raw_input(""))
except KeyboardInterrupt:
    print("Received exit command")
finally:
    irc.stop()

#!/usr/bin/env python

import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from pyjabberbot import JabberBot, botcmd

class RoomBot(JabberBot):
    """ Roommate """
    def __init__(self, jid, password, res = None):
        super(RoomBot, self).__init__(jid, password, res)

    @botcmd
    def echo(self, msg, args):
        """Echo message back to the user"""
        return args

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'Usage: %s login@host password room' % sys.argv[0]
        sys.exit(1)

    bot = RoomBot(sys.argv[1], sys.argv[2])
    # to join room:
    bot.join_room(sys.argv[3])
    # to join with different nickname:
    #bot.join_room(sys.argv[3], username='Roommate')
    # to join passworded room use password argument:
    # bot.join_room(sys.argv[3], password='your_password')
    # to receive room history set history to None:
    # bot.join_room(sys.argv[3], history=None)

    bot.serve_forever()

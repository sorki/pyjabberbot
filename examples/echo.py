#!/usr/bin/env python

import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from pyjabberbot import JabberBot, botcmd

class EchoBot(JabberBot):
    """EchoBot"""
    def __init__(self, jid, password, res = None):
        super(EchoBot, self).__init__(jid, password, res)

    @botcmd
    def echo(self, msg, args):
        """Echo message back to the user"""
        return args

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s login@host password' % sys.argv[0]
        sys.exit(1)

    bot = EchoBot(sys.argv[1], sys.argv[2])
    bot.serve_forever()


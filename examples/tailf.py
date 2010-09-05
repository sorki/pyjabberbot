#!/usr/bin/env python

import os
import sys
import time 
import logging
import threading

logging.basicConfig(level=logging.DEBUG)

from pyjabberbot import SimpleBot, botcmd

class TailFBot(SimpleBot):
    """Tail -f over xmpp"""
    def __init__(self, jid, password, res = None):
        super(TailFBot, self).__init__(jid, password, res)

        self.users_threads = {}
        self.message_queue = {}

    @botcmd
    def tailf(self, msg, args):
        """Start watching the file supplied as an argument"""

        user = msg.getFrom()
        fpath = os.path.abspath(os.path.expanduser(args.strip()))
        if not os.path.isfile(fpath):
            return 'File %s does not exits' % fpath

        if not os.access(fpath, os.R_OK):
            return 'File %s not accessible' % fpath

        if user in self.users_threads:
            return 'Issue stop command before running another tailf'

        # start file monitoring thread for this user
        self.users_threads[user] = threading.Thread(
            target = self.watch_file, args = (user, fpath))
        self.users_threads[user].start()

        return 'Watching %s' % fpath

    @botcmd
    def stop(self, msg, args):
        """Stop watching file"""
        user = msg.getFrom()
        if user in self.users_threads:
            del self.users_threads[user]
            return 'Stopped'
        else:
            return 'Nothing to stop'

    def idle_proc(self):
        if not len(self.message_queue):
            return

        messages = self.message_queue
        self.message_queue = {}

        for user, messages in messages.iteritems():
            for message in messages:
                self.send(user, message)

    def watch_file(self, user, fpath):
        fh = open(fpath, 'r')

        while user in self.users_threads:
            msg = fh.read()
            if len(msg) > 0:
                if user in self.message_queue:
                    self.message_queue[user].append(msg)
                else:
                    self.message_queue[user] = [msg]
            time.sleep(1)

        fh.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s login@host password' % sys.argv[0]
        sys.exit(1)

    bot = TailFBot(sys.argv[1], sys.argv[2])
    bot.serve_forever()

    bot.users_threads = {}

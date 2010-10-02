#!/usr/bin/python

# JabberBot: A simple jabber/xmpp bot framework
# Copyright (c) 2007 Thomas Perl <thp@thpinfo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# This is an example JabberBot that serves as broadcasting server.
# Users can subscribe/unsubscribe to messages and send messages 
# by using "broadcast". It also shows how to send message from 
# outside the main loop, so you can inject messages into the bot 
# from other threads or processes, too.
#

import sys
import time 
import threading

from pyjabberbot import SimpleBot, botcmd

class BroadcastingBot(SimpleBot):
    """ This is a simple broadcasting client.
    Use "subscribe" to subscribe to broadcasts,
    "unsubscribe" to unsubscribe and
    "broadcast" + message to send out a broadcast message.
    Automatic messages will be sent out all 60 seconds.
    """

    def __init__(self, jid, password, res = None):
        super(BroadcastingBot, self).__init__(jid, password, res)

        self.users = []
        self.message_queue = []
        self.thread_killed = False

    @botcmd
    def subscribe(self, mess, args):
        """Subscribe to the broadcast list"""
        user = mess.getFrom()
        if user in self.users:
            return 'You are already subscribed.'
        else:
            self.users.append(user)
            return 'You are now subscribed.'

    @botcmd
    def unsubscribe(self, mess, args):
        """Unsubscribe from the broadcast list"""
        user = mess.getFrom()
        if not user in self.users:
            return 'You are not subscribed!'
        else:
            self.users.remove(user)
            return 'You are now unsubscribed.'

    @botcmd
    def broadcast(self, mess, args):
        """Sends out a broadcast, 
            supply message as arguments (e.g. broadcast hello)"""
        self.message_queue.append('broadcast: %s (from %s)' %
            (args, str(mess.getFrom()), ))

    def idle_proc(self):
        if not len(self.message_queue):
            return

        # copy the message queue, then empty it
        messages = self.message_queue
        self.message_queue = []

        for message in messages:
            for user in self.users:
                self.send(user, message)

    def thread_proc(self):
        while not self.thread_killed:
            self.message_queue.append('this is an automatic message,'
                ' sent all 60 seconds')
            for i in range(60):
                time.sleep(1)
                if self.thread_killed:
                    return

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s login@host password' % sys.argv[0]
        sys.exit(1)

    bot = BroadcastingBot(sys.argv[1], sys.argv[2])

    thread = threading.Thread(target = bot.thread_proc)
    bot.on_connect = lambda: thread.start()
    bot.serve_forever()
    bot.thread_killed = True


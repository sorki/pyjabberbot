#!/usr/bin/python

# JabberBot: A simple jabber/xmpp bot framework
# Copyright (c) 2007-2009 Thomas Perl <thpinfo.com>
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
# Homepage: http://thpinfo.com/2007/python-jabberbot/
#


import sys

try:
    import xmpp
except ImportError:
    print >>sys.stderr, 'You need to install xmpppy from http://xmpppy.sf.net/.'
    sys.exit(-1)
import inspect
import traceback

"""A simple jabber/xmpp bot framework

This is a simple bot framework around the "xmpppy" framework.
Copyright (c) 2007-2009 Thomas Perl <thpinfo.com>
"""

__author__ = 'Thomas Perl <thp@thpinfo.com>'
__version__ = '0.7'


def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""

    def decorate(func, hidden=False):
        setattr(func, '_jabberbot_command', True)
        setattr(func, '_jabberbot_hidden', hidden)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)


class JabberBot(object):
    AVAILABLE, AWAY, CHAT, DND, XA, OFFLINE = None, 'away', 'chat', 'dnd', 'xa', 'unavailable'

    MSG_AUTHORIZE_ME = 'Hey there. You are not yet on my roster. Authorize my request and I will do the same.'
    MSG_NOT_AUTHORIZED = 'You did not authorize my subscription request. Access denied.'

    def __init__( self, jid, password, res=None):
        """Initializes the jabber bot and sets up commands."""
        self.jid = xmpp.JID(jid)
        self.password = password
        self.res = (res or self.__class__.__name__)
        self.conn = None
        self.__finished = False
        self.__show = None
        self.__status = None
        self.__seen = {}
        self.__threads = {}

        self.commands = {}
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, '_jabberbot_command', False):
                self.debug('Registered command: %s' % name)
                self.commands[name] = value

################################

    def _send_status(self):
        self.conn.send(xmpp.dispatcher.Presence(show=self.__show, status=self.__status))

    def __set_status(self, value):
        if self.__status != value:
            self.__status = value
            self._send_status()

    def __get_status(self):
        return self.__status

    status_message = property(fget=__get_status, fset=__set_status)

    def __set_show(self, value):
        if self.__show != value:
            self.__show = value
            self._send_status()

    def __get_show(self):
        return self.__show

    status_type = property(fget=__get_show, fset=__set_show)

################################

    def debug(self, s):
        self.log(s)

    def log( self, s):
        """Logging facility, can be overridden in subclasses to log to file, etc.."""
        print self.__class__.__name__, ':', s

    def connect( self):
        if not self.conn:
            conn = xmpp.Client(self.jid.getDomain())
            
            if not conn.connect():
                self.log( 'unable to connect to server.')
                return None
            
            if not conn.auth( self.jid.getNode(), self.password, self.res):
                self.log( 'unable to authorize with server.')
                return None
            
            conn.RegisterHandler('message', self.callback_message)
            conn.RegisterHandler('presence', self.callback_presence)
            conn.sendInitPresence()
            self.conn = conn
            self.roster = self.conn.Roster.getRoster()
            self.log('*** roster ***')
            for contact in self.roster.getItems():
                self.log('  ' + str(contact))
            self.log('*** roster ***')

        return self.conn

    def quit( self):
        """Stop serving messages and exit.
        
        I find it is handy for development to run the 
        jabberbot in a 'while true' loop in the shell, so 
        whenever I make a code change to the bot, I send 
        the 'reload' command, which I have mapped to call
        self.quit(), and my shell script relaunches the 
        new version.
        """
        self.__finished = True

    def send(self, user, text, in_reply_to=None, message_type='chat'):
        """Sends a simple message to the specified user."""
        mess = xmpp.Message(user, text)

        if in_reply_to:
            mess.setThread(in_reply_to.getThread())
            mess.setType(in_reply_to.getType())
        else:
            mess.setThread(self.__threads.get(user, None))
            mess.setType(message_type)

        self.connect().send(mess)

    def status_type_changed(self, jid, new_status_type):
        """Callback for tracking status types (available, away, offline, ...)"""
        self.debug('user %s changed status to %s' % (jid, new_status_type))

    def status_message_changed(self, jid, new_status_message):
        """Callback for tracking status messages (the free-form status text)"""
        self.debug('user %s updated text to %s' % (jid, new_status_message))

    def broadcast(self, message, only_available=False):
        """Broadcast a message to all users 'seen' by this bot.

        If the parameter 'only_available' is True, the broadcast
        will not go to users whose status is not 'Available'."""
        for jid, (show, status) in self.__seen.items():
            if not only_available or show is self.AVAILABLE:
                self.send(jid, message)

    def callback_presence(self, conn, presence):
        jid, type_, show, status = presence.getFrom(), \
                presence.getType(), presence.getShow(), \
                presence.getStatus()

        if self.jid.bareMatch(jid):
            # Ignore our own presence messages
            return

        if type_ is None:
            # Keep track of status message and type changes
            old_show, old_status = self.__seen.get(jid, (self.OFFLINE, None))
            if old_show != show:
                self.status_type_changed(jid, show)

            if old_status != status:
                self.status_message_changed(jid, status)

            self.__seen[jid] = (show, status)
        elif type_ == self.OFFLINE and jid in self.__seen:
            # Notify of user offline status change
            del self.__seen[jid]
            self.status_type_changed(jid, self.OFFLINE)

        try:
            subscription = self.roster.getSubscription(str(jid))
        except KeyError, ke:
            # User not on our roster
            subscription = None

        if type_ == 'error':
            self.log(presence.getError())

        self.debug('Got presence: %s (type: %s, show: %s, status: %s, subscription: %s)' % (jid, type_, show, status, subscription))

        if type_ == 'subscribe':
            # Incoming presence subscription request
            if subscription in ('to', 'both', 'from'):
                self.roster.Authorize(jid)
                self._send_status()

            if subscription not in ('to', 'both'):
                self.roster.Subscribe(jid)

            if subscription in (None, 'none'):
                self.send(jid, self.MSG_AUTHORIZE_ME)
        elif type_ == 'subscribed':
            # Authorize any pending requests for that JID
            self.roster.Authorize(jid)
        elif type_ == 'unsubscribed':
            # Authorization was not granted
            self.send(jid, self.MSG_NOT_AUTHORIZED)
            self.roster.Unauthorize(jid)

    def callback_message( self, conn, mess):
        """Messages sent to the bot will arrive here. Command handling + routing is done in this function."""
        jid, text = mess.getFrom(), mess.getBody()
    
        # If a message format is not supported (eg. encrypted), txt will be None
        if not text:
            return

        # Ignore messages from users not seen by this bot
        if jid not in self.__seen:
            self.log('Ignoring message from unseen guest: %s' % jid)
            return

        # Remember the last-talked-in thread for replies
        self.__threads[jid] = mess.getThread()

        if ' ' in text:
            command, args = text.split(' ', 1)
        else:
            command, args = text, ''
    
        cmd = command.lower()
    
        if self.commands.has_key(cmd):
            try:
                reply = self.commands[cmd](mess, args)
            except Exception, e:
                reply = traceback.format_exc(e)
                self.log('An error happened while processing a message ("%s") from %s: %s"' % (text, jid, reply))
                print reply
        else:
            unk_str = 'Unknown command: "%s". Type "help" for available commands.<b>blubb!</b>' % cmd
            reply = self.unknown_command( mess, cmd, args) or unk_str
        if reply:
            self.send(jid, reply, mess)

    def unknown_command(self, mess, cmd, args):
        """Default handler for unknown commands

        Override this method in derived class if you 
        want to trap some unrecognized commands.  If 
        'cmd' is handled, you must return some non-false 
        value, else some helpful text will be sent back
        to the sender.
        """
        return None

    @botcmd
    def help( self, mess, args):
        """Returns a help string listing available options. Automatically assigned to the "help" command."""
        usage = '\n'.join(sorted(['%s: %s' % (name, command.__doc__ or '(undocumented)') for (name, command) in self.commands.items() if name != 'help' and not command._jabberbot_hidden]))

        if self.__doc__:
            description = self.__doc__.strip()
        else:
            description = 'Available commands:'

        return '%s\n\n%s' % ( description, usage, )

    def idle_proc( self):
        """This function will be called in the main loop."""
        pass

    def serve_forever( self, connect_callback = None, disconnect_callback = None):
        """Connects to the server and handles messages."""
        conn = self.connect()
        if conn:
            self.log('bot connected. serving forever.')
        else:
            self.log('could not connect to server - aborting.')
            return

        if connect_callback:
            connect_callback()

        while not self.__finished:
            try:
                conn.Process(1)
                self.idle_proc()
            except KeyboardInterrupt:
                self.log('bot stopped by user request. shutting down.')
                break

        if disconnect_callback:
            disconnect_callback()



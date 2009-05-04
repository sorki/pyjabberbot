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
    AWAY, CHAT, DND, XA = 'away', 'chat', 'dnd', 'xa'

    def __init__( self, jid, password, res=None):
        """Initializes the jabber bot and sets up commands."""
        self.jid = xmpp.JID(jid)
        self.password = password
        self.res = (res or self.__class__.__name__)
        self.conn = None
        self.__finished = False
        self.__show = None
        self.__status = None

        self.commands = { 'help': self.help_callback, }
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, '_jabberbot_command', False):
                print 'registered command: %s' % value
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

    def log( self, s):
        """Logging facility, can be overridden in subclasses to log to file, etc.."""
        print '%s: %s' % ( self.__class__.__name__, s, )

    def connect( self):
        if not self.conn:
            conn = xmpp.Client( self.jid.getDomain(), debug = [])
            
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
            for contact in self.roster.getItems():
                print contact

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

    def send( self, user, text, in_reply_to = None):
        """Sends a simple message to the specified user."""
        mess = xmpp.Message( user, text)
        if in_reply_to:
            mess.setThread( in_reply_to.getThread())
            mess.setType( in_reply_to.getType())
        
        self.connect().send( mess)

    def callback_presence(self, conn, presence):
        jid = presence.getFrom()
        try:
            subscription = self.roster.getSubscription(str(jid))
        except:
            subscription = None

        if subscription == 'from':
            self.roster.Subscribe(jid)

        if presence.getType() == 'subscribe':
            # Reply the subscription request (if the user is on our roster)
            if subscription == 'to':
                print 'sending subscribed response'
                self.roster.Authorize(jid)
                self.send(presence.getFrom(), 'subscribed - thanks :)')
                self._send_status()
            elif subscription is None or subscription == 'none':
                self.roster.Unauthorize(jid)
                self.send(presence.getFrom(), 'sorry, you are not yet on my roster. allow me to add you and then re-request')
                self.roster.Subscribe(jid)
        print 'Got presence: %s (type: %s, show: %s, status: %s, subscription: %s)' % (presence.getFrom(), presence.getType(),presence.getShow(), presence.getStatus(), subscription)

    def callback_message( self, conn, mess):
        """Messages sent to the bot will arrive here. Command handling + routing is done in this function."""
        text = mess.getBody()
    
        # If a message format is not supported (eg. encrypted), txt will be None
        if not text:
            return

        if ' ' in text:
            command, args = text.split(' ',1)
        else:
            command, args = text,''
    
        cmd = command.lower()
    
        if self.commands.has_key(cmd):
            try:
                reply = self.commands[cmd]( mess, args)
            except Exception, e:
                reply = traceback.format_exc(e)
                print reply
        else:
            unk_str = 'Unknown command: "%s". Type "help" for available commands.' % cmd
            reply = self.unknown_command( mess, cmd, args) or unk_str
        if reply:
            self.send( mess.getFrom(), reply, mess)

    def unknown_command( self, mess, cmd, args):
        """Default handler for unknown commands

        Override this method in derived class if you 
        want to trap some unrecognized commands.  If 
        'cmd' is handled, you must return some non-false 
        value, else some helpful text will be sent back
        to the sender.
        """
        return None

    def help_callback( self, mess, args):
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
                #conn.sendPresence()
                self.idle_proc()
            except KeyboardInterrupt:
                self.log('bot stopped by user request. shutting down.')
                break

        if disconnect_callback:
            disconnect_callback()



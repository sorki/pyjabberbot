# pyjabberbot: Stripped down version of JabberBot, jabber/xmpp bot framework
# Copyright (c) 2007-2010 Thomas Perl <thpinfo.com>
# Copyright (c) 2010 Richard Marko <rissko@gmail.com>
#
# Based on original JabberBot by Thomas Perl
# - repo: git://repo.or.cz/jabberbot.git
# - homepage: http://thpinfo.com/2007/python-jabberbot/
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

import re
import sys
import time

try:
    import xmpp
except ImportError:
    print >> sys.stderr, 'Install xmpppy from http://xmpppy.sf.net/.'
    sys.exit(-1)
import inspect
import logging
import traceback

from pyjabberbot import botcmd

class JabberBot(object):
    AVAILABLE, AWAY, CHAT = None, 'away', 'chat'
    DND, XA, OFFLINE = 'dnd', 'xa', 'unavailable'

    MSG_AUTHORIZE_ME = 'Please authorize me'
    MSG_NOT_AUTHORIZED = ('You did not authorize my subscription'
        ' request. Access denied.')

    def __init__(self, username, password, res=None):
        """Initializes the jabber bot and sets up commands."""
        self.__username = username
        self.__password = password
        self.__finished = False
        self.__status = None
        self.__seen = {}
        self.__threads = {}

        self.log = logging.getLogger(__name__)
        self.jid = xmpp.JID(self.__username)
        self.res = (res or self.__class__.__name__)
        self.conn = None
        self.roster = None
        self.commands = {}
        self.xmpp_debug = []
        self.reconnecting = False
        self.ignore_offline = False

        for name, value in inspect.getmembers(self):
            if (inspect.ismethod(value) and
                getattr(value, '_jabberbot_command', False)):

                name = getattr(value, '_jabberbot_command_name')
                self.log.debug('Registered command: %s' % name)
                self.commands[name] = value

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value):
        self.__status = value
        self.rawsend(xmpp.dispatcher.Presence(
            show=self.__status[0], status=self.__status[1]))

    def connect(self, handlers = None):
        if not self.conn:
            conn = xmpp.Client(self.jid.getDomain(), debug = self.xmpp_debug)
            conres = conn.connect()
            if not conres:
                self.log.error('unable to connect to server %s.'
                    % self.jid.getDomain())
                return None
            if conres != 'tls':
                self.log.warning('unable to establish secure'
                    'connection - TLS failed!')

            authres = conn.auth(self.jid.getNode(), self.__password,
                self.res)
            if not authres:
                self.log.error('unable to authorize with server.')
                return None
            if authres != 'sasl':
                self.log.warning('unable to perform SASL auth on %s.'
                    % self.jid.getDomain())
                self.log.warning('old authentication method used')

            conn.sendInitPresence()
            self.conn = conn
            self.roster = self.conn.Roster.getRoster()
            self.log.info('*** roster ***')
            for contact in self.roster.getItems():
                self.log.info('  %s' % contact)
            self.log.info('*** roster ***')

            if handlers is None:
                handlers = {'message': self.callback_message,
                    'presence': self.callback_presence}

            for (handler, callback) in handlers.iteritems():
                self.conn.RegisterHandler(handler, callback)

        return self.conn

    def reconnect(self):
        """Try to reconnect"""
        self.conn = None
        self.roster = None
        self.reconnecting = True
        self.log.debug('reconnecting')
        self.connect()
        if self.conn:
            self.log.info('bot reconnected')
        else:
            self.log.warn('reconnect failed, retrying in 5 seconds')
            time.sleep(5)
            self.reconnect()

        self.reconnecting = False

    def rawsend(self, stanza):
        """ Send stanza to server """
        if self.conn == None:
            if self.reconnecting:
                while self.reconnecting:
                    time.sleep(1)
            else:
                self.connect()

        if self.conn == None:
            return

        self.conn.send(stanza)

    def join_room(self, room, password=None, username=None,
            history={'maxchars': '0', 'maxstanzas': '1'}):
        """Join the specified multi-user chat room"""
        if username is None:
            username = self.jid.getNode()
        presence = xmpp.Presence(to='/'.join((room, username)))

        x = presence.setTag('x', namespace=xmpp.protocol.NS_MUC)
        if password is not None:
            x.setTagData('password', password)

        if history is not None:
            x.addChild('history', history)
        self.rawsend(presence)

    def quit(self):
        """Stop serving messages and exit.  """
        self.__finished = True

    def send_message(self, msg):
        """Send an XMPP message"""
        self.rawsend(msg)

    def send(self, to, text, typ='chat', in_reply_to=None):
        """Sends a message to the specified user or chat"""
        msg = self.build_message(text)
        msg.setTo(to)

        if in_reply_to:
            msg.setThread(in_reply_to.getThread())
            msg.setType(in_reply_to.getType())
        else:
            msg.setThread(self.__threads.get(to, None))
            msg.setType(typ)

        self.send_message(msg)

    def send_simple_reply(self, msg, text, private=False):
        """Send a simple response to a message"""
        self.send_message(self.build_reply(msg, text, private) )

    def build_reply(self, msg, text=None, private=False):
        """Build a message for responding to another message."""
        response = self.build_message(text)
        if private:
            response.setTo(msg.getFrom())
            response.setType('chat')
        else:
            response.setTo(msg.getFrom().getStripped())
            response.setType(msg.getType())
        response.setThread(msg.getThread())
        return response

    def build_message(self, text):
        """Builds an xhtml message without attributes."""
        text_plain = re.sub(r'<[^>]+>', '', text)
        msg = xmpp.protocol.Message(body=text_plain)
        if text_plain != text:
            html = xmpp.Node('html', {'xmlns':
                'http://jabber.org/protocol/xhtml-im'})
            try:
                html.addChild(node=xmpp.simplexml.XML2Node(
                    "<body xmlns='http://www.w3.org/1999/xhtml'>"
                    + text.encode('utf-8') + "</body>"))
                msg.addChild(node=html)
            except:
                self.log.error('exception: build_message (%s): %s' %
                    (text, sys.exc_info()[0]))
                msg = xmpp.protocol.Message(body=text_plain)
        return msg

    def get_sender_username(self, msg):
        """Extract the sender's user name from a message""" 
        typ = msg.getType()
        jid  = msg.getFrom()
        if typ == "groupchat":
            username = jid.getResource()
        elif typ == "chat":
            username  = jid.getNode()
        else:
            username = ""
        return username

    def broadcast(self, msg, only_available=False):
        """Broadcast a message to all users 'seen' by this bot.

        If the parameter 'only_available' is True, the broadcast
        will not go to users whose status is not 'Available'."""
        for jid, status in self.__seen.iteritems():
            if not only_available or status[0] is self.AVAILABLE:
                self.send(jid, msg)

    def callback_presence(self, conn, pre,
            status_type_changed = None, status_msg_changed = None):

        jid, typ, show, status = (pre.getFrom(), pre.getType(),
            pre.getShow(), pre.getStatus())

        if self.jid.bareMatch(jid):
            # Ignore our own presence messages
            return

        if typ is None:
            # Keep track of status message and type changes
            old_show, old_status = self.__seen.get(jid,
                (self.OFFLINE, None))
            if old_show != show:
                if status_type_changed:
                    status_type_changed(jid, show)

            if old_status != status:
                if status_msg_changed:
                    status_msg_changed(jid, status)

            self.__seen[jid] = (show, status)
        elif typ == self.OFFLINE and jid in self.__seen:
            # Notify of user offline status change
            del self.__seen[jid]
            if status_type_changed:
                status_type_changed(jid, self.OFFLINE)

        try:
            subscription = self.roster.getSubscription(str(jid))
        except KeyError:
            # User not on our roster
            subscription = None

        if typ == 'error':
            self.log.error(pre.getError())

        self.log.debug('got presence: %s (type: %s, show: %s, '
            'status: %s, subscription: %s)' %
            (jid, typ, show, status, subscription))

        if typ == 'subscribe':
            # Incoming presence subscription request
            if subscription in ('to', 'both', 'from'):
                self.roster.Authorize(jid)
                self.status = self.status

            if subscription not in ('to', 'both'):
                self.roster.Subscribe(jid)

            if subscription in (None, 'none'):
                self.send(jid, self.MSG_AUTHORIZE_ME)
        elif typ == 'subscribed':
            # Authorize any pending requests for that JID
            self.roster.Authorize(jid)
        elif typ == 'unsubscribed':
            # Authorization was not granted
            self.send(jid, self.MSG_NOT_AUTHORIZED)
            self.roster.Unauthorize(jid)

    def callback_message(self, conn, msg):
        """Messages sent to the bot will arrive here.
        Command handling + routing is done in this function."""

        jid, typ, props, text = (msg.getFrom(), msg.getType(),
            msg.getProperties(), msg.getBody())
        username = self.get_sender_username(msg)

        if typ not in ("groupchat", "chat"):
            self.log.debug("unhandled message type: %s" % type)
            return

        self.log.debug('got message: %s (type: %s, jid: %s, '
            'username: %s, properties: %s)' %
            (text, jid, typ, username, props))

        if self.ignore_offline:
            if xmpp.NS_DELAY in props:
                return

        # Ignore messages from myself + empty (e.g. encrypted) text
        if username == self.__username or not text:
            return

        # Ignore messages from users not seen by this bot
        if jid not in self.__seen:
            self.log.info('ignoring message from unseen guest: %s' %
                jid)
            return

        # Remember the last-talked-in thread for replies
        self.__threads[jid] = msg.getThread()

        if ' ' in text:
            command, args = text.split(' ', 1)
        else:
            command, args = text, ''
        cmd = command.lower()
        self.log.debug("*** cmd = %s" % cmd)

        if self.commands.has_key(cmd):
            try:
                reply = self.commands[cmd](msg, args)
            except Exception, ex:
                reply = traceback.format_exc(ex)
                self.log.debug('exception while processing msg'
                    '("%s") from %s: %s"' % (text, jid, reply))
        else:
            if typ == "groupchat":
                return
            reply = ('Unknown command: "%s". Type "help"'
                ' for available commands' % cmd)
        if reply:
            self.send_simple_reply(msg, reply)

    @botcmd
    def help(self, msg, args):
        """Returns a help string listing available options.

        Automatically assigned to the "help" command."""
        description = ''
        if self.__doc__:
            description = '%s\n' % self.__doc__.strip()

        description += 'Available commands:\n'

        cmdlist = []
        for name, command in self.commands.iteritems():
            if name == 'help' or command._jabberbot_hidden:
                continue

            doc = ''
            if command.__doc__:
                doc = ': ' + command.__doc__.strip()
            cmdlist.append('- %s %s' % (name, doc))

        usage = '\n'.join(sorted(cmdlist))
        return '%s%s' % (description, usage)

    def serve_forever(self, connect_callback = None,
            disconnect_callback = None):
        """Connects to the server and handles messages."""
        self.connect()
        if self.conn:
            self.log.info('bot connected. serving forever.')
        else:
            self.log.warn('could not connect to server - aborting.')
            return

        if connect_callback:
            connect_callback()

        while not self.__finished:
            try:
                state = self.conn.Process(1)
                if state == None:
                    self.log.error('IOError occurred')
                    time.sleep(2)
                    self.log.info('trying to reconnect')
                    conn = self.reconnect()
                    continue
                if hasattr(self, 'idle_proc'):
                    self.idle_proc()
            except KeyboardInterrupt:
                self.log.info('stopping by user request')
                break
            except:
                self.log.error('unexpected error: %s' %
                    traceback.format_exc())
                time.sleep(2)
                self.log.info('trying to reconnect')
                conn = self.reconnect()

        if disconnect_callback:
            disconnect_callback()

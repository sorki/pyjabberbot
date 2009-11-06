
# TwitterBot: Example Twitter but using python-jabberbot
# Copyright (c) 2008 Thomas Perl <thpinfo.com>
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

import twitter
import jabberbot

botcmd = jabberbot.botcmd

# Configure your Jabber and Twitter authentication and secret phrase
JABBERBOT_USER = 'jabberbot@example.com'
JABBERBOT_PASS = 'jabberbotpassword'
TWITTER_USERNAME = 'yourtwitterusername'
TWITTER_PASSWORD = 'yourtwitterpassword'
SECRETPHRASE = 'HelloMyTwitterBot!'

class TwitterBot(jabberbot.JabberBot):
    """
    This is a JabberBot that can interface with the Twitter webservice.
    Just set up a Jabber account for your Bot (set the JABBERBOT_USER and
    JABBERBOT_PASS variables accordingly) and then add your Twitter
    authentication data to TWITTER_USERNAME and TWITTER_PASSWORD.

    You can select a SECRETPHRASE that you will have to say to identify
    yourself to your JabberBot, so it will take commands from you.

    Additional requirements: python-twitter
    """

    denied = "Just what do you think you're doing, Dave?"
    himaster = "Good afternoon, gentlemen. I am a HAL 9000 computer."
    twitteruser = JABBERBOT_USER
    twitterpass = JABBERBOT_PASS

    def __init__(self, username, password, secret):
        jabberbot.JabberBot.__init__(self, self.twitteruser, self.twitterpass)
        self.master = ''
        self.secret = secret
        self.api = twitter.Api(username=username, password=password)

    def callback_message(self, conn, mess):
        # This is an example how you can set a "master" to listen to:
        if mess.getBody() == self.secret:
            self.master = mess.getFrom().getStripped()
            self.send(mess.getFrom(), self.himaster, mess)
            return
        if mess.getFrom().getStripped() != self.master:
            self.send(mess.getFrom(), self.denied, mess)
        else:
            return jabberbot.JabberBot.callback_message(self, conn, mess)

    @botcmd
    def friends(self, mess, args):
        """Return the friends"""
        return ', '.join([u.name for u in self.api.GetFriends()])

    @botcmd
    def post(self, mess, args):
        """Post a message to twitter"""
        posting = self.api.PostUpdate(args)
        return 'http://twitter.com/'+posting.GetUser().GetScreenName()+'/status/'+str(posting.GetId())


if __name__ == '__main__':
    bot = TwitterBot(TWITTER_USERNAME, TWITTER_PASSWORD, SECRETPHRASE)
    bot.serve_forever()


# Tunes: Example XEP-0118 (User Tune) user.
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

"""
When the bot is connected, use commands like:

set artist Metallica
set title Bad Seed

The bot will update its tune and log the outgoing packet to stdout.
"""

import sys
from jabberbot import JabberBot, botcmd

class Tunes(JabberBot):
    def __init__(self, username, password):
        JabberBot.__init__(self, username, password)
        self.track = { 'file': 'test.mp3' }

    @botcmd
    def set(self, message, args):
        'set track properties'
        args = args.strip().split(' ')
        if len(args) < 2 or args[0] not in ('artist', 'title', 'album', 'source', 'pos', 'track', 'time', 'uri'):
            return 'Usage: set {artist|title|album|source|pos|track|time|uri} value'
        self.track[args[0]] = ' '.join(args[1:])
        self.send_tune(self.track, True)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s login@host password' % sys.argv[0]
        sys.exit(1)
    bot = Tunes(sys.argv[1], sys.argv[2])
    bot.serve_forever()


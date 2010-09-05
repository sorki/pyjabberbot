import sys
import logging

from pyjabberbot import PersistentBot, botcmd
logging.basicConfig(level=logging.DEBUG)

class PersistentBotDemo(PersistentBot):
    """ PersistentBot demo, this bot will try to reconnect when
    specified number of timeouts occur """


    @botcmd
    def reconnects(self, msg, args):
        """ Get number of reconnects ocurred """
        return 'Reconnects: %s' % self.reconnects

    @botcmd
    def threshold(self, msg, args):
        """ Get number of timeouts until reconnect """
        return 'Threshold: %s' % self.threshold

    @botcmd
    def interval(self, msg, args):
        """ Get availabilty check interval """
        return 'Interval: %s' % self.syn_interval

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s login@host password' % sys.argv[0]
        sys.exit(1)

    bot = PersistentBotDemo(sys.argv[1], sys.argv[2])
    # show syn/ack messages
    bot.debug_heartbeat = True
    # configure
    bot.syn_interval = 5
    bot.threshold = 2

    bot.serve_forever()

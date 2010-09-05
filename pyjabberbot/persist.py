#!/usr/bin/env python

import time
import logging
import threading


from pyjabberbot import SimpleBot, botcmd

class PersistentJabberBot(SimpleBot):
    """PersistentBot - SimpleBot + connection monitoring, reconnects after 
    number of timeouts reached in a row. """
    def __init__(self, jid, password, res = None):
        super(PersistentJabberBot, self).__init__(jid, password, res)

        self.alive_running = True
        self.alive_paused = False
        self.alive_thread = threading.Thread(target=self.alive_proc)
        self.syn = True
        self.ack = True
        self.syn_interval = 2
        self.threshold = 3
        self.timeouts = 0
        self.incident = False


        self.reconnects = 0

    @botcmd
    def reconnects(self, msg, args):
        """Number of reconnects ocurred"""
        return 'Reconnects: %s' % self.reconnects

    def alive_proc(self):
        time.sleep(self.syn_interval)
        while self.alive_running:
            self.syn = True
            if self.ack == False:
                logging.debug('| !!! timeout')
                self.timeouts += 1
                if self.timeouts == self.threshold:
                    self.incident = True
                    self.alive_paused = True
                    while self.alive_paused:
                        time.sleep(1)
                        if not self.alive_running:
                            return
            else:
                self.timeouts = 0
            self.ack = False

            for i in range(self.syn_interval):
                time.sleep(1)
                if not self.alive_running:
                    return

    def idle_proc(self):
        if self.incident:
            logging.error('Threshold reached, trying to reconnect')
            self.reconnects += 1
            self.reconnect()
            self.incident = False
            self.alive_paused = False

        if self.syn:
            logging.debug('| syn')
            self.send(self.jid, 'syn')
            self.syn = False

    def callback_message(self, conn, msg):
        jid = msg.getFrom().getStripped()
        txt = msg.getBody()
        if  jid == self.jid and txt == 'syn':
            logging.debug('| ^^^ ack')
            self.ack = True
            return

        return super(PersistentJabberBot, self).callback_message(conn, msg)



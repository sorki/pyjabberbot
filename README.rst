pyjabberbot
============

IMPORTANT: this fork is no longer maintained as the original project (`python-jabberbot <http://thpinfo.com/2007/python-jabberbot/>`_) 
implemented all of the features of this fork. Please migrate to python-jabberbot - this fork will be deleted in few months.

Xmpp/jabber bot framework makes implementation of your jabber bot
straightforward and quick.

pyjabberbot is a fork of `python-jabberbot <http://thpinfo.com/2007/python-jabberbot/>`_
with focus on overall stability and availability of the bot.

Features:
-----------
 - fault tolerance
 - connection monitoring, auto-reconnect
 - command handling

Requirements:
--------------
 - python 2.6+
 - xmpppy

Installation:
--------------
 - from python package index

   easy_install pyjabberbot

 - or download the package and run

   python setup.py install

Usage:
-------
 - subclass either `SimpleBot` (or `PersistentBot` if you want connection
   monitoring and auto-reconnect features)
 - decorate your custom methods with `botcmd` decorator, these methods will
   then serve as command handlers
 - create an instance of your new class, supplying jid and password
 - issue commands to your new bot

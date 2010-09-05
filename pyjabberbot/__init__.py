# Definition of botcmd decorator and proxy classess

def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""

    def decorate(func, hidden=False, name=None):
        setattr(func, '_jabberbot_command', True)
        setattr(func, '_jabberbot_hidden', hidden)
        setattr(func, '_jabberbot_command_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)


# proxy classess
from pyjabberbot.bot import JabberBot
class SimpleBot(JabberBot):
    pass

from pyjabberbot.persist import PersistentJabberBot
class PersistentBot(PersistentJabberBot):
    pass

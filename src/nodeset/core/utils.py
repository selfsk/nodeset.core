from nodeset.core import config

def catch(ev):
    """
    Node methods decorator, an easy way to mark method as a handler for specified event
    """
    def _inner(fn, *args, **kw):
        fn.__event_handler__ = [ev, args, kw]
        return fn
    
    return _inner


def setDefaultOptions():
    c = config.Configurator()
    c._config = {'dispatcher-url': 'pbu://localhost:5333/dispatcher',
                     'listen': 'localhost:5444',
                     'dht-nodes': None,
                     'dht-port': None,
                     'verbose': None,
                     }
        
    # minor hack to avoid 'xmpp' subCommand failures
    c.subCommand = None



def DynamicNode(cls):
    """
    Node class creation decorator, searching for 'catch'es in methods
    """
    cls.__events__ = {}
    for item in cls.__dict__.itervalues():
        if hasattr(item, '__event_handler__'):
            ev_name, args, kw = getattr(item, '__event_handler__')
            cls.__events__[ev_name] = [item, args, kw]
            
    return cls

def catch(ev):
    """
    Node methods decorator, an easy way to mark method as a handler for specified event
    """
    def _inner(fn, *args, **kw):
        fn.__event_handler__ = [ev, args, kw]
        return fn
    
    return _inner
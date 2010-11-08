from zope.interface import implements


from nodeset.core import interfaces

class NodeMonitor:
    implements(interfaces.heartbeat.INodeMonitor)
    
    """
    Special class for handling heartbeat monitor and its callbacks and errbacks
    """
    
    def __init__(self, node):
        self.node = node
        self.__ok = []
        self.__fails = []
        
    def heartbeat(self):
        d = self.node.callRemote('heartbeat')
        
        for callable, args, kwargs in self.__ok:
            d.addCallback(callable, *args, **kwargs)
        
        for callable, args, kwargs in self.__fails:
            d.addErrback(callable, *args, **kwargs)
            
    def onOk(self, callable, *args, **kwargs):
        """
        @param callable: callable instance which will be added addCallback for callRemote defer
        @param *args: additional arguments
        @param **kwargs: additional kw arguments
        @return: L{NodeMonitor}
        """
        self.__ok.append((callable, args, kwargs))
    
        return self
    
    def onFail(self, callable, *args, **kwargs):
        """
        @param callable: callable instance which will be added by addErrback for callRemote defer
        @param *args: additional args for errback
        @param **kwargs: additional kw args for errback
        @return: L{NodeMonitor}
        """
        self.__fails.append((callable, args, kwargs))
        
        return self
    
    
class NodeHeartBeat:
    implements(interfaces.heartbeat.INodeHeartBeat)
    
    def __init__(self, dispatcher):
        self.monitors = set()
        self.dispatcher = dispatcher
        self.delayed = None
        
    def cancel(self):
        if self.delayed and self.delayed.active():
            self.delayed.cancel()
        
    def _lookup(self, node):
        """
        Do lookup for heartbeat monitor for node
        @param node: Node
        @type node: L{Node}
        @raise: KeyError
        @return: L{NodeMonitor}
        """
        for m in self.monitors:
            if m.node == node:
                return m
        raise KeyError("Unknown node %s" % node)

    def has(self, node):
        """
        Check if node has heartbeat monitor
        @param node: Node
        @type node: L{Node}
        @return: True or False
        """
        try:
            m = self._lookup(node)
            return True
        except KeyError, e:
            return False
    
    def add(self, node):
        """
        Add heartbeat monitor for node
        @param node: Node
        @type node: L{Node}
        @return: L{NodeMonitor}
        """

        # if node has its own specific monitor callbacks, use them before dispatchers one
        monitor = node.monitor or NodeMonitor(node)
        self.monitors.add(monitor)
        
        return monitor
    
    def remove(self, node):
        """
        Removes heartbeat monitor for node
        @param node: Node
        @type node: L{Node}
        @return: L{NodeMonitor}
        """
        
        monitor = node.monitor or self._lookup(node) 
        self.monitors.remove(monitor)
        
        return monitor
    
    def schedule(self, delay=5):
        """
        Schedules heartbeating
        """
        from twisted.internet import reactor
        self.delayed = reactor.callLater(delay, self._do_heartbeat)
        
    def _do_heartbeat(self):
        """
        Do actual heartbeat
        """
        # copy monitors list, set can be changed through iteration
        monitors = self.monitors.copy()
        
        for m in monitors:
            m.heartbeat()
            
        del monitors
        
        self.schedule()

            
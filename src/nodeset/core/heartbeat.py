from twisted.internet import reactor, defer

class NodeMonitor:
    
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
        self.__ok.append((callable, args, kwargs))
    
        return self
    
    def onFail(self, callable, *args, **kwargs):
        self.__fails.append((callable, args, kwargs))
        
        return self
    
    
class NodeHeartBeat:
    
    def __init__(self, dispatcher):
        self.monitors = set()
        self.dispatcher = dispatcher
        
    def _lookup(self, node):
        for m in self.monitors:
            if m.node == node:
                return m
        raise KeyError("Unknown node %s" % node)

    def has(self, node):
        try:
            m = self._lookup(node)
            return True
        except KeyError, e:
            return False
    
    def add(self, node):
        monitor = NodeMonitor(node)
        self.monitors.add(monitor)
        
        return monitor
    
    def remove(self, node):
        monitor = self._lookup(node) 
        self.monitors.remove(monitor)
        
        return monitor
    
    def schedule(self, delay=5):
        reactor.callLater(delay, self._do_heartbeat)
        
    def _do_heartbeat(self):
        print self.monitors
        print self.dispatcher.routing.entries
        
        # copy monitors list, set can be changed through iteration
        monitors = self.monitors.copy()
        
        for m in monitors:
            m.heartbeat()
            
        del monitors
        self.schedule()

            
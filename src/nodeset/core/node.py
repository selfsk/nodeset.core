from foolscap.api import Referenceable, Tub, Copyable, UnauthenticatedTub
from uuid import uuid4

class NodeEvent(Copyable):
    pass
    
class EventDispatcher(Referenceable):
    
    def __init__(self):
        self._subscribers = {}
        self.tub = UnauthenticatedTub()
        self.tub.listenOn('tcp:5333')
        self.tub.setLocation('localhost:5333')
        self.tub.registerReference(self, 'dispatcher')
        
    def remote_publish(self, event_name, event):
        
        for s in self._subscribers[event_name]:
            print "publishing %s to %s" % (event_name, s)
            s.callRemote('event', event)
    
    def remote_subscribe(self, event_name, node):
        print "subscription to %s by %s" % (event_name, node)
        if self._subscribers.has_key(event_name):
            self._subscribers[event_name].append(node) 
        else:
            self._subscribers[event_name] = [node]
                    
    
#eventDispatcher = EventDispatcher()
  
class Node(Referenceable):
    
    def __init__(self, port, name=None):
        self.tub = Tub()
        self.tub.listenOn('tcp:%d' % port)
        self.tub.setLocation('localhost:%d' % port)
        self.name = name
        
        if not self.name:
            self.name = str(uuid4())
            
        self.tub.registerReference(self, self.name)
        
        self.dispatcher = None
        
        d = self.tub.getReference('pbu://localhost:5333/dispatcher')
        d.addCallback(self._gotDispatcher).addErrback(self._error)
        
    def _gotDispatcher(self, remote):
        self.dispatcher = remote
        
    def _error(self, failure):
        print "error - %s" % str(failure)
          
    def publish(self, name, event):
        self.dispatcher.callRemote('publish', name, event)
        #tcher._publish(name, event)
        #for s in self._subscribers:
        #    s.tub.callRemote('event', event)
    
    def subscribe(self, name):
        self.dispatcher.callRemote('subscribe', name, self)
        
    def onEvent(self, event):
        print "event %s" % event
    
    def remote_event(self, event):
        self.onEvent(event)
 

   
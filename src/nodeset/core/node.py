from foolscap.api import Referenceable, Tub, Copyable, UnauthenticatedTub, RemoteCopy
from uuid import uuid4

from nodeset.core import routing

class NodeEvent(Copyable, RemoteCopy):
    """
    Copyable object for events, for safe objects exchange between nodes
    """
    
    """
    @ivar typeToCopy: hardcoded 'node-event-0xdeadbeaf'  
    @ivar copytype: hardcoded 'node-event-0xdeadbeaf'
    """
    typeToCopy = copytype = 'node-event-0xdeadbeaf'
    
    def __init__(self, name, payload):
        """
        @param name: event name
        @param payload: any object
        """
        self.name = name
        self.payload = payload
    
    
class EventDispatcher(Referenceable):
    """ 
    EventDispatcher instance is running on each host as separate process. Remote Nodes can subscribe for events
    on this dispatcher, too. Nodes are exchanging events through dispatcher.
    """
    def __init__(self):
        self.routing = routing.RoutingTable() 
        self.tub = UnauthenticatedTub()
        self.tub.listenOn('tcp:5333')
        self.tub.setLocation('localhost:5333')
        self.tub.registerReference(self, 'dispatcher')
        
    def remote_publish(self, event_name, event):
        
        for s in self.routing.get(event_name):
            print "publishing %s to %s" % (event_name, s)
            s.getNode().callRemote('event', event)
    
    def remote_unsubscribe(self, event_name, node):
        print "unsubscription to %s by %s" % (event_name, node)
        
        self.routing.remove(event_name, node)

            
    def remote_subscribe(self, event_name, node):
        print "subscription to %s by %s" % (event_name, node)
        self.routing.add(event_name, node)
  
class Node(Referenceable):
    """
    Main atom of NodeSet framework, communication is build on top of simple interface:
     - publish
     - subscribe
    """
   
    def __init__(self, port, name=None):
        """ 
        @param port: listen port for Tub
        @param name: create named Tub, otherwise UUID will be generated
        """
        
        """
        @ivar tub: foolscap's Tub (Authorized)
        @ivar name: name of Node, will UUID in case of missing name
        @ivar dispatcher: EventDispatcher remote reference
        """
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
        """
        publish event with name and event object (NodeEvent)
        @param name: event name (str node@host/event)
        @param event: object
        @type event: NodeEvent
        @return: None
        """
        self.dispatcher.callRemote('publish', name, event)
  
    def subscribe(self, name):
        """
        subscribe to specified event
        @param name: event name
        @return: None
        """
        self.dispatcher.callRemote('subscribe', name, self)
    
    
    def unsubscribe(self, name):
        """
        unsubscribe from specified event
        @param name: event name
        @return: None
        """
        self.dispatcher.callRemote('unsubscribe', name, self)
        
        
    def onEvent(self, event):
        """
        default callback for event
        @param event: object
        @type event: NodeEvent
        """
        print "event %s" % event
    
   
    def remote_event(self, event):
        """
        foolscap's method, will be called by EventDispatcher on event publishing. By default it calls onEvent(event),
        you can implement it in subclass to perform various events handling
        @param event: object
        @type event: NodeEvent
        @return: None
        """
        self.onEvent(event)
 

   
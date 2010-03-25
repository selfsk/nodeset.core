from foolscap.api import Referenceable, Tub, Copyable, UnauthenticatedTub, RemoteCopy 
from foolscap.ipb import DeadReferenceError
from uuid import uuid4

from twisted.internet import reactor, defer
from twisted.python import log

from nodeset.core import routing, heartbeat
import logging
import signal

class NodeEventBuilder:
    """
    We can't pass any arguments to NodeEvent, due to foolscap limitations 
    (i.e U{RemoteCopy<http://foolscap.lothar.com/docs/api/foolscap.copyable.RemoteCopy-class.html>}). This factory
    should be used for NodeEvent creation and configuration (Builder pattern)
    """
    
    def createEvent(self, name, payload):
        """
        create empty NodeEvent object, and then set name and payload values
        @param name: event name
        @param payload: payload
        @return NodeEvent
        """
        event = NodeEvent()
        event.name = name
        event.payload = payload
        
        return event
    
class NodeEvent(Copyable, RemoteCopy):
    """
    Copyable object for events, for safe objects exchange between nodes
    """
    
    """
    @ivar typeToCopy: hardcoded 'node-event-0xdeadbeaf'  
    @ivar copytype: hardcoded 'node-event-0xdeadbeaf'
    """
    typeToCopy = copytype = 'node-event-0xdeadbeaf'
    
    def __init__(self):
        """
        @param name: event name
        @param payload: any object
        """
        self.name = None
        self.payload = None
   
    def getStateToCopy(self):
        return {'name': self.name, 'payload': self.payload}

    def setCopyableState(self, state):
        self.name = state['name']
        self.payload = state['payload']
        
    def __str__(self):
        return str("%s<%s>" % (self.name, self.payload))
    

  
class Node(Referenceable):
    """
    Main atom of NodeSet framework, communication is build on top of simple interface:
     - publish
     - subscribe
     - unsubscribe
    """
   
    """
    @ivar monitor: HeartBeat monitor
    @type monior: L{NodeMonitor}
    """
    monitor = None
    parent = None
    
    def __init__(self, port=None, name=None, dispatcher_url=None):
        """ 
        @param port: listen port for Tub
        @param name: create named Tub, otherwise UUID will be generated
        """
        
        """
        @ivar tub: foolscap's Tub (Authorized)
        @ivar name: name of Node, will UUID in case of missing name
        @ivar dispatcher: EventDispatcher remote reference
        """

        self.port = port
        self.name = name
        
        # internal state of subscriptions, useful for re-establish connection to dispatcher
        self.__subscribes = []
        
        if not self.name:
            self.name = str(uuid4())
        
        self.dispatcher_url = dispatcher_url or 'pbu://localhost:5333/dispatcher'
        self.dispatcher = None
   
    def _handle_signal(self, signo, bt):
        print "signal %d" % signo
        print "bt %s" % bt
        
        reactor.callLater(0.1, self._restart, 2)
        
    def start(self, timeout=0):
        self.tub = Tub()
        self.tub.listenOn('tcp:%d' % self.port)
        self.tub.setLocation('localhost:%d' % self.port)
        
        self.tub.registerReference(self, self.name)
        
        self._establish(timeout)
        
    def _establish(self, timeout=0, application=None):
        d = self.tub.getReference(self.dispatcher_url)
        d.addCallback(self._gotDispatcher).addErrback(self._error, timeout)
        
        return d
    
    def getApplication(self):
        return self.tub
    
    def _gotDispatcher(self, remote):
        log.msg("got dispatcher %s" % remote)
        
        self.dispatcher = remote

        # in case if we're reinitializing connection to dispatcher
        for e in self.__subscribes:
            self.subscribe(name, self)
            
        return remote
    
    def _error(self, failure, timeout):
        log.msg("error - %s" % str(failure), logLevel=logging.ERROR)
        self.dispatcher = None
        self._restart(timeout+2)
        
    def _restart(self, timeout):
        """
        re-initialize Node, if dispatcher was restarted
        """
        if timeout > 4:
            log.msg("stop trying to reconnect after %d" % timeout, logLevel=logging.ERROR)
            return
        
        reactor.callLater(timeout, self._establish, timeout)
        log.msg("re-initializing connection dispatcher in %d seconds" % timeout, logLevel=logging.ERROR)
     
    def publish(self, event):
        """
        publish event with name and event object (NodeEvent)
        @param event: NodeEvent instance 
        @type event: L{NodeEvent}
        @return: deferred
        """
        if self.dispatcher:
            d = self.dispatcher.callRemote('publish', self, event)
            return d
  
    def subscribe(self, name):
        """
        subscribe to specified event
        @param name: event name
        @return: None
        """
        
        if self.parent:
            return self.parent.subscribe(name, self)
        
        if self.dispatcher:
            d = self.dispatcher.callRemote('subscribe', name, self)
            self.__subscribes.append(name)
            return d
    
    def unsubscribe(self, name):
        """
        unsubscribe from specified event
        @param name: event name
        @return: None
        """
        if self.parent:
            return self.parent.unsubscribe(name, self)
            
        if self.dispatcher:
            d = self.dispatcher.callRemote('unsubscribe', name, self)
            self.__subscribes.remove(name)
        
            return d
        
    def onEvent(self, event):
        """
        default callback for event
        @param event: object
        @type event: NodeEvent
        """
        pass
    
 
    def onError(self, error):
        """
        default callback for errors
        @param error: NodeEventError
        @type error: NodeEventError
        """
        pass
    
    def remote_event(self, event):
        """
        foolscap's method, will be called by EventDispatcher on event publishing. By default it calls onEvent(event),
        you can implement it in subclass to perform various events handling
        @param event: object
        @type event: L{NodeEvent}
        @return: None
        """
        return self.onEvent(event)
 
    
    def remote_error(self, error):
        """
        foolscap's method, will be called by EventDispatcher in case of error on rcpt side. 
        @param error: error object
        @type error: L{NodeEventError}
        """
        return self.onError(error)

    def remote_heartbeat(self):
        """
        dispatcher sends periodical heartbeat to Node, in reply return True for now 
        (DeadReferences are handled by dispacher automatically)
        """
        log.msg("someone is heartbeating me")
        return True
    

class NodeCollection(Node):
    """
    Node which contain group of node, to avoid running each node as separate process
    @ivar nodes: list of L{Node}s
    """
    
    events = {}
    
    def addEvent(self, event_name, node):
        if self.events.has_key(event_name):
            self.events[event_name].append(node)
        else:
            self.events[event_name] = [node]
        
        return len(self.events[event_name])

    def removeEvent(self, event_name, node):
        if self.events.has_key(event_name):
            self.events[event_name].remove(node)
    
        # return size of subscriptions for event, if 0 - completely unsubscribe from dispatcher
        return len(self.events[event_name])
    
    def addNode(self, node):
        node.parent = self
        
    def removeNode(self, node):
        node.parent = None

    def eventloop(self, node, event):
        return node.onEvent(event)
        
    def remote_event(self, event):
        for n in self.events[event.name]:
            reactor.callLater(0, self.eventloop, n, event)
        
        #for n in self.events[event.name]:
        #    n.onEvent(event)
    
    def subscribe(self, name, node):
        if self.dispatcher:
            # if we already subscribed to this event, don't send callRemote again
            if self.addEvent(name, node) == 1:
                self.dispatcher.callRemote('subscribe', name, self)
        
    def unsubscribe(self, name, node):
        if self.dispatcher:
            # if there are no nodes awaiting this event, unsubscribe multi node itself
            if not self.removeEvent(name, node) == 0:
                self.dispatcher.callRemote('unsubscribe', name, self)
            
class StreamNode(Node):
    """
    Special case of Node, which supports streaming of any data
    """
    
    def remote_stream(self, stream):
        pass
    
    def stream(self):
        pass
    
def _create_node(stub, kNode, *args, **kwargs):
    return kNode(*args, **kwargs)

class DeferNodeFactory:
    
    node = Node
    
    def createNode(self, *args, **kwargs):
        d = defer.Deferred()
        
        d.addCallback(_create_node, self.node, *args, **kwargs)
        
        return d
   
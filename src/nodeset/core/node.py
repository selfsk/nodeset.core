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

        self.heartbeat = heartbeat.NodeHeartBeat(self)
        self.heartbeat.schedule(10)
        
    def _dead_reference(self, fail, node):
        """
        Errback for DeadReference exception handling
        @param fail: twisted failure object
        @type fail: twisted.failure.Falure
        @param node: node object
        @type node: L{Node}
        """
        fail.trap(DeadReferenceError)
        log.msg("dead reference %s, drop it" % node, logLevel=logging.WARNING)
        self.routing.remove(None, node)
        self.heartbeat.remove(node)
        
    def _failure(self, fail, node):
        """
        Handling of any other exception, in case of failure on rcpt node.
        Do callRemote('error') on src node, to deliver failure
        @param fail: failure
        @type fail: twisted.failure.Failure
        @param node: src node
        @type node: Node
        """
        log.msg("Unresolved failure %s" % str(fail), logLevel=logging.ERROR)
        node.callRemote('error', NodeEventBuilder().createEvent('error', fail))
        
    def remote_publish(self, src, event):
        """
        callRemote('publish', src, event)
        @param src: src reference
        @type src: L{Node}
        @param event: event object
        @type event: L{NodeEvent}
        """
        log.msg("publishing %s" % (event), logLevel=logging.INFO)
        #print "--> publishing %s" % event.name
        
        for s in self.routing.get(event.name):
            print "publishing %s to %s" % (event.name, s)
            s.getNode().callRemote('event', event).addErrback(self._dead_reference, s).addErrback(self._failure, src)

    
    def remote_unsubscribe(self, event_name, node):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        #print "unsubscription to %s by %s" % (event_name, node)
        
        self.routing.remove(event_name, node)
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)
            
    def remote_subscribe(self, event_name, node):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
        
        self.routing.add(event_name, node)
        if not self.heartbeat.has(node):
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, node)
        
  
class Node(Referenceable):
    """
    Main atom of NodeSet framework, communication is build on top of simple interface:
     - publish
     - subscribe
     - unsubscribe
    """
   
    def __init__(self, port, name=None, dispatcher_url=None):
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
        
        # internal state of subscriptions, useful for re-establish connection to dispatcher
        self.__subscribes = []
        
        if not self.name:
            self.name = str(uuid4())
            
        self.tub.registerReference(self, self.name)
        
        self.dispatcher_url = dispatcher_url or 'pbu://localhost:5333/dispatcher'
        self.dispatcher = None
   
    def _handle_signal(self, signo, bt):
        print "signal %d" % signo
        print "bt %s" % bt
        
        reactor.callLater(0.1, self._restart, 2)
        
    def start(self, timeout=0, application=None):
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
        
        reactor.callLater(timeout, self.start, timeout)
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
        self.onEvent(event)
 
    
    def remote_error(self, error):
        """
        foolscap's method, will be called by EventDispatcher in case of error on rcpt side. 
        @param error: error object
        @type error: L{NodeEventError}
        """
        self.onError(error)

    def remote_heartbeat(self):
        """
        dispatcher sends periodical heartbeat to Node, in reply return True for now 
        (DeadReferences are handled by dispacher automatically)
        """
        log.msg("someone is heartbeating me")
        return True
    
def _create_node(stub, kNode, *args, **kwargs):
    return kNode(*args, **kwargs)

class DeferNodeFactory:
    
    node = Node
    
    def createNode(self, *args, **kwargs):
        d = defer.Deferred()
        
        d.addCallback(_create_node, self.node, *args, **kwargs)
        
        return d
   
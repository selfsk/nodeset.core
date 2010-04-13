from foolscap.api import Referenceable, Tub, Copyable, UnauthenticatedTub, RemoteCopy 
from foolscap.ipb import DeadReferenceError
from uuid import uuid4

from twisted.internet import reactor, defer
from twisted.python import log, components

from nodeset.core import routing, heartbeat, interfaces, stream
import logging
import signal

from zope.interface import implements 

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
    implements(interfaces.INode)
    
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
    builder = NodeEventBuilder()
    
    def __init__(self, port=None, host=None, name=None, dispatcher_url=None):
        """ 
        @param port: listen port for Tub
        @param name: create named Tub, otherwise UUID will be generated
        """
        
        """
        @ivar tub: foolscap's Tub (Authorized)
        @ivar name: name of Node, will UUID in case of missing name
        @ivar dispatcher: EventDispatcher remote reference
        """

        self.host = host or 'localhost'
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
        self.tub.setLocation('%s:%d' % (self.host, self.port))
        
        self.tub.registerReference(self, self.name)
        
        return self._establish(timeout)
        
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
            
        return self
    
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
     
    def publish(self, uri_or_event, *args):
        """
        publish event with name and event object (NodeEvent)
        @param uri_or_event: NodeEvent instance 
        @type event: L{NodeEvent} or L{str}
        @param *args: additional arguments for builder.createEvent()
        @return: deferred
        """

        if self.dispatcher:
            
            if isinstance(uri_or_event, NodeEvent):
                event = uri_or_event
            else:
                event = self.builder.createEvent(uri_or_event, *args)    
            
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
   
    def onStream(self, stream):
        """
        default callback for stream events
        @param stream: StreamEvent
        @type stream: L{StreamEvent}
        """
        pass
     
    def remote_stream(self, data, formatter):
        """
        foolscap's method, will be called directly by StreamNode (which will push data to Node)
        @param data: encoded stream data
        @param formatter: formatter instance
        @type formatter: L{Formatter}
        """
        return self.onStream(data, formatter)
    
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
    
class StreamNode(Node):
    implements(interfaces.IStreamNode)
    
    """
    Special case of Node, which supports streaming of any data
    @ivar streamClass: Stream handling class
    @type streamClass: L{stream.Stream}
    """
    
    streamClass = stream.Stream
        
    def getRemoteNode(self, stream_name):
        """
        Gets list of remote references for direct foolscap calls. Dispatcher will return list
        instead of forwarding event to rcpt nodes
        @param stream_name: eventURI 
        """
        return self.dispatcher.callRemote('stream', stream_name)
    
    def buildStream(self, peers=None):
        """
        Called when getRemoteNode() returns list of peers
        """
        s = self.streamClass(self, peers)
        
        return s

    def streamError(self, failure):
        print "streamError: %s" % failure
        
    def stream(self, stream_name):
        """
        Called to get L{Stream} instance with appropriate peers for this stream
        @param stream_name: the same as eventURI
        @param stream_name: L{str}
        """
        return self.getRemoteNode(stream_name).addCallback(self.buildStream).addErrback(self.streamError)
        
    
class NodeCollection(Node):
    
    implements(interfaces.INodeCollection)
    
    """
    Node which contain group of node, to avoid running each node as separate process
    @ivar events: dict for event_name -> list of L{Node}s
    """
    
    events = {}
    
    def addEvent(self, event_name, node):
        """
        Add node to events under event_name
        @param event_name: event name
        @param node: node for event delivering
        @type node: L{Node}
        """
        if self.events.has_key(event_name):
            self.events[event_name].append(node)
        else:
            self.events[event_name] = [node]
        
        return len(self.events[event_name])

    def removeEvent(self, event_name, node):
        """
        Remove node from events under event_name
        @param event_name: event name
        @param node: node for event delivering
        @type node: L{Node}
        """
        if self.events.has_key(event_name):
            self.events[event_name].remove(node)
    
        # return size of subscriptions for event, if 0 - completely unsubscribe from dispatcher
        return len(self.events[event_name])
    
    def adapt(self, node):
        """
        Adapts Node to NodeCollection pub/sub interface
        """
        adapted = interfaces.INodeCollection(node)
        adapted.collection = self

        print "node %s, adapted %s" % (node, adapted)
        return adapted
    
    def eventloop(self, node, event, defer):
        """
        do onEvent
        """
        try:
            defer.callback(node.onEvent(event))
        except Exception, e:
            defer.errback(e)
        
    def remote_event(self, event):
        """
        Do scheduling of event delivering through reactor
        """
        nodes = self.events[event.name]
        defers = []
        
        for n in nodes:
            d = defer.Deferred()
            reactor.callLater(0, self.eventloop, n, event, d)

            # if more nodes to come, do DeferredList instead
            if len(nodes):
                defers.append(d)
                

        del nodes
        if len(defers) > 1:
            return defer.DeferredList(defers)
        else:
            d = defers.pop()
            return d
        
    
class CollectionAdapter:
    """
    INode -> INodeCollection adaptor
    """
    def __init__(self, original):
        self.original = original
        self.original.publish = self.publish
        self.original.subscribe = self.subscribe
        self.original.unsubscribe = self.unsubscribe
        
    def publish(self, event):
        if self.collection.dispatcher:
            # if is a message between nodes in collection - do direct message handling
            if event.name in self.collection.events:
                return self.collection.remote_event(event)
            else:
                return self.collection.dispatcher.callRemote('publish', self.collection, event)
        
    def subscribe(self, name):
        if self.collection.dispatcher:
            # if we already subscribed to this event, don't send callRemote again
            if self.collection.addEvent(name, self.original) == 1:
                self.collection.dispatcher.callRemote('subscribe', name, self.collection)
        
    def unsubscribe(self, name):
        if self.collection.dispatcher:
            # if there are no nodes awaiting this event, unsubscribe multi node itself
            if not self.collection.removeEvent(name, self.original) == 0:
                self.collection.dispatcher.callRemote('unsubscribe', name, self.collection)

# adapt Node to INodeCollection interface with CollectionAdapter factory
components.registerAdapter(CollectionAdapter, Node, interfaces.INodeCollection)
          

    
def _create_node(stub, kNode, *args, **kwargs):
    return kNode(*args, **kwargs)

class DeferNodeFactory:
    
    node = Node
    
    def createNode(self, *args, **kwargs):
        d = defer.Deferred()
        
        d.addCallback(_create_node, self.node, *args, **kwargs)
        
        return d
   
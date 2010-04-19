from foolscap.api import Referenceable, Tub, Copyable, UnauthenticatedTub, RemoteCopy 
from foolscap.ipb import DeadReferenceError
from uuid import uuid4

from twisted.internet import reactor, defer
from twisted.python import log, components

from nodeset.core import routing, heartbeat, interfaces, stream, message
import logging
import signal

from zope.interface import implements 

class NodeMessageBuilder:
    """
    We can't pass any arguments to NodeMessage, due to foolscap limitations 
    (i.e U{RemoteCopy<http://foolscap.lothar.com/docs/api/foolscap.copyable.RemoteCopy-class.html>}). This factory
    should be used for NodeMessage
    """
    
    def __init__(self, klass):
        self.message = klass
    
    def createEvent(self, **kwargs):
        """
        create NodeMessage object, kwargs sets attributes in message
        @param name: event name
        @param payload: payload
        @return L{NodeMessage}
        """
        msg = self.message()
        
        #print msg.attrs
        
        # create message to pass to other side
        _msg = message._Message()
        _msg.attrs = msg.attrs
        #_msg.setAttrs(msg.attrs)
        
        #_msg.setCopyableState = msg.setCopyableState
        #_msg.getStateToCopy = msg.getStateToCopy
        
        for k,v in kwargs.items():
            _msg.set(k, v)
        
        return _msg

  
class Node(Referenceable):
    """
    Main atom of NodeSet framework, communication is build on top of simple interface:
     - publish
     - subscribe
     - unsubscribe

    """

    implements(interfaces.INode)
    
    """
    @ivar monitor: HeartBeat monitor
    @type monior: L{NodeMonitor}
    @ivar builder: Message builder
    @type builder: L{NodeMessageBuilder}
    @ivar message: message class (by default NodeMessage)
    @type message: class
    """
    
    monitor = None
    message = message.NodeMessage
    builderClass = NodeMessageBuilder
    
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
   
        self.builder = self.builderClass(self.message)
        
    def _handle_signal(self, signo, bt):
        print "signal %d" % signo
        print "bt %s" % bt
        
        reactor.callLater(0.1, self._restart, 2)
        
    def start(self, timeout=0):
        self.tub = Tub()
        self.tub.listenOn('tcp:%d' % self.port)
        self.tub.setLocation('%s:%d' % (self.host, self.port))
        
        self.tub.registerReference(self, self.name)
        
        # this defer will be called only after _gotDispatcher call
        self.startDeferred = defer.Deferred()
        
        self._establish(timeout)
        return self.startDeferred
        
    def _establish(self, timeout=0, deferred=None):
        d = self.tub.getReference(self.dispatcher_url)
        d.addCallback(self._gotDispatcher).addErrback(self._error, timeout)
    
        return deferred
    
    def getApplication(self):
        return self.tub
    
    def _gotDispatcher(self, remote):
        log.msg("got dispatcher %s" % remote)
        
        self.dispatcher = remote

        # in case if we're reinitializing connection to dispatcher
        for e in self.__subscribes:
            self.subscribe(name, self)
        
        # fire startDeferred 
        self.startDeferred.callback(self)
    
    def _error(self, failure, timeout=1):
        failure.trap(Exception)
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
     
    def publish(self, event_uri, **kwargs):
        """
        publish event with message (fields are **kwargs)
        @param uri_or_event: eventURI 
        @type event: L{str}
        @param **kwargs: additional arguments for builder.createEvent()
        @return: deferred
        """

        if self.dispatcher:
            msg = self.builder.createEvent(**kwargs)    
            d = self.dispatcher.callRemote('publish', self, event_uri, msg)
            
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
        
    def onEvent(self, event, msg):
        """
        default callback for event
        @param event: event name
        @type event: L{str}
        @param msg: NodeMessage
        @type msg: L{NodeMessage}
        """
        pass
    
   
    def onStream(self, stream, formatter):
        """
        default callback for stream events
        @param stream: StreamEvent
        @type stream: L{StreamEvent}
        @param formatter: Formatter
        @type formatter: L{Formatter}
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
    
    def remote_event(self, event, msg):
        """
        foolscap's method, will be called by EventDispatcher on event publishing. By default it calls onEvent(event),
        you can implement it in subclass to perform various events handling
        @param event: event name 
        @type event: L{str}
        @param msg: NodeMessage instance
        @type msg: L{NodeMessage}
        @return: None
        """
        return self.onEvent(event, msg)
 

    def remote_heartbeat(self):
        """
        dispatcher sends periodical heartbeat to Node, in reply return True for now 
        (DeadReferences are handled by dispacher automatically)
        """
        log.msg("someone is heartbeating me")
        return True
    
class StreamNode(Node):
    """
    Special case of Node, which supports streaming of any data
    @ivar streamClass: Stream handling class
    @type streamClass: L{stream.Stream}
    """
    implements(interfaces.IStreamNode)
    
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
    """
    Node which contain group of node, to avoid running each node as separate process
    @ivar events: dict for event_name -> list of L{Node}s
    """
     
    implements(interfaces.INodeCollection)
    
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
    
    def eventloop(self, node, event, msg, defer):
        """
        do onEvent
        """
        try:
            defer.callback(node.onEvent(event, msg))
        except Exception, e:
            defer.errback(e)
        
    def remote_event(self, event, msg):
        """
        Do scheduling of event delivering through reactor
        """
        nodes = self.events[event]
        defers = []
        
        for n in nodes:
            d = defer.Deferred()
            reactor.callLater(0, self.eventloop, n, event, msg, d)

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
        
    def publish(self, event, **kwargs):
        if self.collection.dispatcher:
            # if is a message between nodes in collection - do direct message handling
            
            m = self.original.builder.createEvent(**kwargs)
            
            if event in self.collection.events:
                return self.collection.remote_event(event, m)
            else:
                return self.collection.dispatcher.callRemote('publish', self.collection, event, m)
        
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
   
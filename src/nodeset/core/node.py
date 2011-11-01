"""
Base classes for Nodes, use them as base class for your Nodes
"""
from foolscap.api import Referenceable, Tub

from uuid import uuid4

from twisted.application import service
from twisted.internet import defer
from twisted.python import components

from nodeset.core import interfaces, stream, message, config, utils
#from nodeset.common.log import setLogger
from nodeset.common import log
import logging

from zope.interface import implements 
import copy

class MessageBuilder(object):
    """
    We can't pass any arguments to NodeMessage, due to foolscap limitations 
    (i.e U{RemoteCopy<http://foolscap.lothar.com/docs/api/foolscap.copyable.RemoteCopy-class.html>}). This factory
    should be used for NodeMessage
    """
    __slots__ = ['createMessage']
    
    def createMessage(self, klass, **kwargs):
        """
        create NodeMessage object, kwargs sets attributes in message
        @param klass: message class (i.e. message.NodeMessage)
        @param kwargs: fields of message
        @return L{NodeMessage}
        """
        log.msg("building message for %s" % klass)
        msg = klass()
        
        # create message to pass to other side, kind of stub
        _msg = message._Message()
        # save attrs, otherwise set() raise exception
        # we can't simply assign here, to avoid static members update, using deepcopy
        _msg.attrs = copy.deepcopy(msg.attrs)
        
        for k,v in kwargs.items():
            _msg.set(k, v)
        
        #log.msg("message klass(%s), fields(%s), msg(%s), _msg(%s)" \
        #        % (klass, kwargs, msg.attrs.items(), _msg.attrs.items()), logLevel=logging.DEBUG)
        
        return _msg

  
class _Node(Referenceable, service.Service):
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
    @type builder: L{MessageBuilder}
    @ivar message: message class (by default NodeMessage)
    @type message: class
    """
    
    monitor = None
    message = message.NodeMessage
    builderClass = MessageBuilder
    
    def __init__(self, port=None, name=None, host=None, dispatcher_url=None):
        """ 
        @param port: listen port for Tub
        @param name: create named Tub, otherwise UUID will be generated
        @param host: Tub's listen address
        @param dispatcher_url: dispatcher's FURL
        
        All these params has priority to cmdline arguments, be careful!
        """
        
        """
        @ivar tub: foolscap's Tub (Authorized)
        @ivar name: name of Node, will UUID in case of missing name
        @ivar dispatcher: EventDispatcher remote reference
        """

        # internal state of subscriptions, useful for re-establish connection to dispatcher
        self.__subscriptions = []
        self.name = name or str(uuid4())
        
        self.dispatcher_url = dispatcher_url
        self.host = host or 'localhost'
        self.port = port or 0
        
        self.dispatcher = None

        self.config = config.Configurator()
        self.builder = self.builderClass()
        
        self.connector = None
        
        self.cold_start = False # if true .start() was called
        
    def getSubscriptions(self):
        return self.__subscriptions
    
    def startService(self):
        # if we're not started yet
        if not self.cold_start:
            self.start()

        if not self.dispatcher_url:
            self.dispatcher_url = self.config['dispatcher-url']
        if self.config.has_key('listen') and not self.port:
            self.host, self.port = self.config['listen'].split(':')
        
        self.tub = Tub()
        self.tub.listenOn('tcp:%d' % int(self.port))
        self.tub.setLocation('%s:%d' % (self.host, int(self.port)))
        self.tub.registerReference(self, self.name)
        
        self.tub.startService()
        
        self._createConnector()

        
    def stopService(self):
        self.tub.stopService()
        
        
    def _handle_signal(self, signo, bt):
        log.msg("Handling signal %d, initiate re-connecting" % signo)
        
        if self.connector:
            self.connector.reset()
        
    def start(self):
        self.cold_start = True
        
        # this defer will be called only after _gotDispatcher call
        self.startDeferred = defer.Deferred()
        return self.startDeferred
        
    def getApplication(self):
        return self.tub
    
    def _createConnector(self, verbose=True):
        """
        Initialized Reconnector instance. Should be called after tub is initialized
        """
        from foolscap.reconnector import Reconnector 
        
        Reconnector.verbose = verbose
        self.connector = Reconnector(self.dispatcher_url, self._gotDispatcher, (), {})
        self.connector.maxDelay = 300
        self.connector.startConnecting(self.tub)
      
    def _dropConnector(self):
        if self.connector._active:
            self.connector.stopConnecting()  
            
    def _gotDispatcher(self, remote):
        log.msg("got dispatcher %s" % remote)
        
        self.dispatcher = remote

        # in case if we're reinitializing connection to dispatcher
        for name in self.getSubscriptions():
            log.msg("re-subscribing to %s" % name)
            self.subscribe(name)
        
        # fire startDeferred only on first time
        if not self.startDeferred.called: 
            self.startDeferred.callback(self)
    
    def publishMessage(self, event_uri, msg):
        """
        publish already built message
        @param event_uri: eventURI
        @param msg: message instance
        """
        
        if self.dispatcher:
            d = self.dispatcher.callRemote('publish', event_uri, msg)
            
            return d
        
    def publish(self, event_uri, msgClass=None, **kwargs):
        """
        publish event with message (fields are **kwargs)
        @param uri_or_event: eventURI 
        @type event: L{str}
        @param **kwargs: additional arguments for builder.createEvent()
        @return: deferred
        """

        if self.dispatcher:
            if not msgClass:
                msgClass = self.message
            msg = self.builder.createMessage(msgClass, **kwargs)
            d = self.dispatcher.callRemote('publish', event_uri, msg)
            
            return d
  
    def subscribe(self, name):
        """
        subscribe to specified event
        @param name: event name
        @return: None
        """
        
        if self.dispatcher:
            d = self.dispatcher.callRemote('subscribe', name, self, self.name)
            
            if name not in self.__subscriptions:
                self.__subscriptions.append(name)
            return d
    
    def unsubscribe(self, name):
        """
        unsubscribe from specified event
        @param name: event name
        @return: None
        """
            
        if self.dispatcher:
            d = self.dispatcher.callRemote('unsubscribe', name, self, self.name)
            self.__subscriptions.remove(name)
        
            return d
        
    def issubscribed(self, name):
        """
        Check does node already subscribed to event
        @param name: event name
        @return bool
        """
        return name in self.__subscriptions
    
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
    
    def remote_event(self, event, msg, bubble=False):
        """
        foolscap's method, will be called by EventDispatcher on event publishing. By default it calls onEvent(event),
        you can implement it in subclass to perform various events handling
        @param event: event name 
        @type event: L{str}
        @param msg: NodeMessage instance
        @type msg: L{NodeMessage}
        @param bubble: remote side can set to True to get exceptions from this node, otherwise suppress it
        @type bubble: L{boolean}
        @return: None
        """
        try:
            return self.onEvent(event, msg)
        except Exception, e:
            if not bubble:
                log.err(e)
                
            else:
                raise e
 

    def remote_heartbeat(self):
        """
        dispatcher sends periodical heartbeat to Node, in reply return True for now 
        (DeadReferences are handled by dispacher automatically)
        """
        #log.msg("someone is heartbeating me")
        return True
  
class Node(_Node):
    
    def __new__(cls, *args, **kw):
        """
        Customizing Node subclass creation. Catching method decorators
        """
        
        # creating new instance (cls is just a Class)
        self = super(Node, cls).__new__(cls)
        
        # will handle our event handlers here
        self.__events__ = {}
        
        # loop over cls (not instance, instance's __init__ has not been called yet)
        for item in cls.__dict__.values():
            if hasattr(item, '__event_handler__'):
                ev_name = getattr(item, '__event_handler__')
                ev_name, args, kw = getattr(item, '__event_handler__')
                # our handlers could have args and kwargs as well
                self.__events__[ev_name] = [item, args, kw]
            
        return self
    
    def remote_event(self, event, msg, bubble=False):
        # doing usual stuff, but maybe someone want to .catch(event)
        super(Node, self).remote_event(event, msg, bubble)

        if self.__events__.has_key(event):
            log.msg("__dyn_event[%s] = %s" % (event, self.__events__[event]), logLevel=logging.DEBUG)
            callable, args, kwargs = self.__events__[event]
    
            return callable(self, msg, *args, **kwargs)

        return
     
class StreamNode(_Node):
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
        
        log.msg("peers=%s" % peers)
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
        d = self.getRemoteNode(stream_name)
        d.addCallback(self.buildStream).addErrback(self.streamError)
        
        return d
        
    
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
            defer.callback(node.remote_event(event, msg))
        except Exception, e:
            defer.errback(e)
        
    def remote_event(self, event, msg):
        """
        Do scheduling of event delivering through reactor
        """
        nodes = self.events[event]
        defers = []
        
        from twisted.internet import reactor
        
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
        
    def publish(self, event, msgClass=None, **kwargs):
        if self.collection.dispatcher:
            # if is a message between nodes in collection - do direct message handling
            
            if not msgClass:
                msgClass = self.original.message
                
            m = self.original.builder.createMessage(msgClass, **kwargs)
            
            if event in self.collection.events:
                return self.collection.remote_event(event, m)
            else:
                return self.collection.dispatcher.callRemote('publish', event, m)
        
    def subscribe(self, name):
        if self.collection.dispatcher:
            # if we already subscribed to this event, don't send callRemote again
            if self.collection.addEvent(name, self.original) == 1:
                self.collection.dispatcher.callRemote('subscribe', name, self.collection, self.original.name)
        
    def unsubscribe(self, name):
        if self.collection.dispatcher:
            # if there are no nodes awaiting this event, unsubscribe multi node itself
            if not self.collection.removeEvent(name, self.original) == 0:
                self.collection.dispatcher.callRemote('unsubscribe', name, self.collection, self.original.name)

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

class ShellNode(Node):
    """
    Special purspose node, provides interactive shell to nodeset environment, you
    can use this node to perform:
     * subscribing/publishing
     * getting internal information
     * etc.
    """

    def setShell(self, shell):
        self.shell = shell
        self.shell.namespace['node'] = self
        
    def register(self, name, callbable):
        """
        Register callable in shell's namespace
        """
        assert(self.shell)
        
        self.shell.namespace[name] = callable

    def unregister(self, name):
        """
        Unregister callable in shell's namespace
        """
        assert(self.shell)
        del self.shell.namespace[name]
        
    def switch(self, URL):
        """
        Switch to another dispatcher (by FURL)
        """
        self.dispatcher_url = URL
        
        self._dropConnector()
        self._createConnector()

        
        
    
    
        
    

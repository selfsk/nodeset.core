from foolscap.api import Referenceable, UnauthenticatedTub, Tub
from foolscap.ipb import DeadReferenceError

from twisted.internet import defer
from twisted.python import log
import logging

from nodeset.core import routing, heartbeat


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
        
        node.monitor = None
        
        self.heartbeat.remove(node)
       
    def remote_stream(self, stream_name):
        """
        @param stream_name: event_URI
        """
    
        log.msg("Getting list of route entries for stream(%s) delivering" % stream_name)
        return [x.getNode() for x in self.routing.get(stream_name)]
      
    def remote_publish(self, src, event):
        """
        callRemote('publish', src, event)
        @param src: src reference
        @type src: L{Node}
        @param event: event object
        @type event: L{NodeEvent}
        """
        log.msg("publishing %s" % (event), logLevel=logging.INFO)
        #print "--> publishing %s rcpt %s" % (event, self.routing.get(event.name))
        
        defers = []
        for s in self.routing.get(event.name):
            print "publishing %s to %s" % (event.name, s)
            
            d = s.getNode().callRemote('event', event).addErrback(self._dead_reference, s.getNode())
            
            defers.append(d)
            
        
        if len(defers) > 1:
            return defer.DeferredList(defers)
        else:
            return defers.pop()

    def remote_unsubscribe(self, event_name, node):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        
        self.routing.remove(event_name, node)
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)
            
    def remote_subscribe(self, event_name, node):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
        
        self.routing.add(event_name, node)
        if not self.heartbeat.has(node):
            #FIXME: workaround for missing monitor, foolscap does not pass ivars
            node.monitor = None
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, node)
            

                
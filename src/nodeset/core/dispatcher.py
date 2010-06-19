"""
EventDispatcher's code, use this code to write your own dispatchers
"""
from foolscap.api import Referenceable, UnauthenticatedTub, Tub
from foolscap.ipb import DeadReferenceError

from twisted.application import service
from twisted.internet import defer

import logging
import hashlib

from nodeset.core import routing, heartbeat, config
from nodeset.common import log

# entangled DHT stuff
from nodeset.core.dht import NodeSetDHT

class EventDispatcher(Referenceable, service.Service):
    """ 
    EventDispatcher instance is running on each host as separate process. Remote Nodes can subscribe for events
    on this dispatcher, too. Nodes are exchanging events through dispatcher.
    """
    def __init__(self, dispatcher_url='pbu://localhost:5333/dispatcher'):
        self.routing = routing.RoutingTable() 
        self.tub = UnauthenticatedTub()
        
        host, port, refname = self._split(dispatcher_url)
        
        self.dispatcher_url = dispatcher_url
        self.host = host
        self.port = port
        
        self.tub.listenOn('tcp:%d' % port)
        self.tub.setLocation('%s:%d' % (host, port))
        self.tub.registerReference(self, refname)
        self.heartbeat = heartbeat.NodeHeartBeat(self)
        self.heartbeat.schedule(10)
    
        self.knownNodes = []
        self.dht = None
        
    def _neighbour(self):
        if Configurator['neighbour']:
            pass
        
    def _split(self, url):
        
        schema, rest = url.split('://')
        location, ref = rest.split('/')
        
        host, port = location.split(':')
        
        return host, int(port), ref
    
    def initDHT(self):
        
        c = config.Configurator()
        
        if c['dht-nodes']:
            self.knownNodes = [x.split(':') \
                               for x in c['dht-nodes'].split(',')]
            self.knownNodes = map(lambda x: (x[0], int(x[1])), self.knownNodes)
                                  
        self.dht = NodeSetDHT(udpPort=c['dht-port'])
        self.dht.setTub(self)
        self.dht.joinNetwork(self.knownNodes)
        
    def startService(self):
        self.tub.startService()
        self.initDHT()
        
    def stopService(self):
        self.heartbeat.cancel()
        self.tub.stopService()

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
      
    def _prepare(self, event_uri):
        
        node_name, host, event = self.routing._split_uri(event_uri)
        
        if host == self.host:
            host = 'localhost'
            
        return "%s@%s/%s" % (node_name, host, event)
    
    def remote_publish(self, event_name, msg):
        """
        callRemote('publish', event)
        @param src: src reference
        @type src: L{Node}
        @param event: event object
        @type event: L{NodeEvent}
        """
        log.msg("publishing %s(msg=%s)" % (event_name, msg), logLevel=logging.INFO)
        #print "--> publishing %s rcpt %s" % (event, self.routing.get(event.name))
        
        defers = []
        for s in self.routing.get(self._prepare(event_name)):
            log.msg("publishing %s to %s" % (event_name, s), logLevel=logging.DEBUG)
            
            method = 'event'
            
            if isinstance(s, routing.RemoteRouteEntry):
                method = 'publish'
                
            d = s.getNode().callRemote(method, event_name, msg).addErrback(self._dead_reference, s.getNode())
            
            defers.append(d)

            if msg._delivery_mode != 'all':
                break
        
        if len(defers) > 1:
            return defer.DeferredList(defers)
        elif len(defers) == 1:
            return defers.pop()
        else:
            return
        
    def remote_unsubscribe(self, event_name, node, node_name=None):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        node.name = node_name
        self.routing.remove(event_name, node)
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)

        host_name = 'localhost'
        event_uri = self.get_event_uri(node_name, host_name, event_name)
        
        self.dht.iterativeDelete(self.hash_key(event_uri))
                                 
    def hash_key(self, key):
        h = hashlib.sha1()
        h.update(key)
        
        return h.digest()
        
    def get_event_uri(self, node_name, host_name, event_name):
        return "%s@%s/%s" % (node_name, host_name, event_name)
    
    def remote_subscribe(self, event_name, node, node_name=None):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
        
        node.name = node_name
        # store data about node, host and event into DHT
        host_name = 'localhost'
        event_uri = self.get_event_uri(node_name, self.host, event_name)
        
        self.dht.iterativeStore(self.hash_key(event_uri),
                                (event_uri, self.dispatcher_url))
        
        self.routing.add(event_name, node)
        if not self.heartbeat.has(node):
            #FIXME: workaround for missing monitor, foolscap does not pass ivars
            node.monitor = None
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, node)
            

                
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
        self.routing = routing.RoutingTable(self) 
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
      
    
    def _debug_print(self, data):
        print "<-> %s" % data
        
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
        for s in self.routing.get(event_name):
            if isinstance(s, defer.Deferred):
                print "delayed..."
                # re-schedule remote_publish when we'll got everything we need
                s.addCallback(lambda _: self.remote_publish(event_name, msg))
            else:
                log.msg("publishing %s to %s" % (event_name, s), logLevel=logging.DEBUG)
            
                method = 'event'
                err_back = self._dead_reference
                if isinstance(s, routing.RemoteRouteEntry):
                    method = 'publish'
                    err_back = lambda _: None
                    
                d = s.getNode().callRemote(method, event_name, msg).addErrback(err_back, s.getNode())
            
                defers.append(d)

                if msg._delivery_mode != 'all':
                    break
        
        if len(defers) > 1:
            return defer.DeferredList(defers)
        elif len(defers) == 1:
            return defers.pop()
        else:
            return
       
    def buildUri(self, nname, ename):
        return "%s@localhost/%s" % (nname, ename)
     
    def remote_unsubscribe(self, event_name, node, name):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        node.name = name
        self.routing.remove(self.buildUr(node.name, event_name), node)
        
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)
                                 
    def remote_subscribe(self, event_name, node, name):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
        node.name = name
        self.routing.add(self.buildUri(node.name, event_name), node)
        
        if not self.heartbeat.has(node):
            #FIXME: workaround for missing monitor, foolscap does not pass ivars
            node.monitor = None
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, node)
            

                
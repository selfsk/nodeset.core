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
from nodeset.core.dht import NodeSetDHT, NodeSetDataStore

class EventDispatcher(Referenceable, service.Service):
    """ 
    EventDispatcher instance is running on each host as separate process. Remote Nodes can subscribe for events
    on this dispatcher, too. Nodes are exchanging events through dispatcher.
    """
    def __init__(self, listen='pbu://localhost:5333/dispatcher'):
        self.routing = routing.RoutingTable(self) 
        self.tub = UnauthenticatedTub()
        
        host, port, refname = self._split(listen)
        
        self.listen_url = listen
        self.host = host
        self.port = port
        
        self.tub.listenOn('tcp:%d' % port)
        self.tub.setLocation('%s:%d' % (host, port))
        self.tub.registerReference(self, refname)
        
        self.heartbeat = heartbeat.NodeHeartBeat(self)
        self.heartbeat.schedule(10)
    
    def _split(self, url):
        schema, rest = url.split('://')
        location, ref = rest.split('/')
        
        host, port = location.split(':')
        
        return host, int(port), ref
    
 
        
    def startService(self):
        self.tub.startService()
        
        if config.Configurator['dht-port']:
            self.dht = NodeSetDHT(config.Configurator['dht-port'], dataStore=NodeSetDataStore())
            self.routing.dht = self.dht
            
            def publishToDHT(eventDict, listen_url):
                dht_key = "%s@%s" % (eventDict['parsed_uri'].eventName, eventDict['parsed_uri'].nodeName)
                 
                print "publishing to DHT key(%s), value(%s)" % (dht_key, listen_url)
                self.dht.publishData(dht_key, listen_url)
              
            def removeFromDHT(eventDict, listen_url):
                dht_key = "%s@%s" % (eventDict['parsed_uri'].eventName, eventDict['parsed_uri'].nodeName)
                print "Removing from DHT key(%s),value(%s)" % (dht_key, listen_url)
                
                self.dht.removeData(dht_key)
                
            self.routing.addObserver('add', publishToDHT, self.listen_url)
            self.routing.addObserver('remove', removeFromDHT, self.listen_url)
            
            if config.Configurator['dht-nodes']:
                snodes = config.Configurator['dht-nodes']
                ntuple = [x.split(':') for x in snodes.split(',')]
                
                
                ntuple = [(x[0], int(x[1])) for x in ntuple]
                
                print ntuple
                
                self.dht.joinNetwork(ntuple)
            
    def stopService(self):
        self.heartbeat.cancel()
        self.tub.stopService()
        
    def _dead_reference(self, fail, event_uri, node):
        """
        Errback for DeadReference exception handling
        @param fail: twisted failure object
        @type fail: twisted.failure.Falure
        @param node: node object
        @type node: L{Node}
        """
        fail.trap(DeadReferenceError)
        log.msg("dead reference %s, drop it" % node, logLevel=logging.WARNING)
        self.routing.remove(event_uri, node)
        
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
        
    def _do_publish(self, entries, event_name, msg):
        print "---> %s" % entries
        defers = []
        for n in entries:
            method = 'event'
            err_back = self._dead_reference
            args = (n.getNode(),)
             
            if isinstance(n, routing.RemoteRouteEntry):
                method = 'publish'
                err_back = lambda _: None
                args = ()
                
            d = n.getNode().callRemote(method, event_name, msg).addErrback(err_back, *args)
            
            defers.append(d)
            if msg._delivery_mode != 'all':
                break
            
        if len(defers) > 1:
            return defer.DeferredList(defers)
        elif len(defers) == 1:
            return defers.pop()
        else:
            return
        
    def gotRemoteRoute(self, remote, eventUri, msg):
        self.routing._add({'parsed_uri': eventUri, 'instance': remote})
        
        return remote.callRemote('publish', "%s@localhost/%s" % (eventUri.nodeName, eventUri.eventName), msg)
        
    def getRemote(self, furl, eventUri, msg):
        if furl:
            for f in furl:
                print "Doing remote publishing to %s to %s" % (eventUri.eventName, f)
                self.tub.getReference(f).addCallback(self.gotRemoteRoute, eventUri, msg)
         
    def remote_publish(self, event_name, msg):
        log.msg("publishing %s(msg=%s)" % (event_name, msg), logLevel=logging.INFO)
        
        for d in self.routing.get(event_name):
            d.addCallback(self._do_publish, event_name, msg)\
                  .addErrback(self.routing.onFailure, routing.NoSuchEntry, self.getRemote, msg)
                  
       
    def remote_unsubscribe(self, event_name, node, name):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        self.routing.remove(event_name, node)
        
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)
                                 
    def remote_subscribe(self, event_name, node, name):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
        self.routing.add(event_name, node, name)
        
        if not self.heartbeat.has(node):
            #FIXME: workaround for missing monitor, foolscap does not pass ivars
            node.monitor = None
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, event_name, node)
            

                
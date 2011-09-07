"""
EventDispatcher's code, use this code to write your own dispatchers
"""
from foolscap.api import Referenceable, UnauthenticatedTub
from foolscap.ipb import DeadReferenceError

from twisted.application import service

import logging
import simplejson

from nodeset.core import routing, config, message
from nodeset.common import log

class DispatcherStats(object):
    
    def __init__(self):
        self.pubs = 0
        self.subs = 0

    def toJSON(self):
        return simplejson.dumps({"subs": self.subs, "pubs": self.pubs})
    
class EventDispatcher(Referenceable, service.Service):
    """ 
    EventDispatcher instance is running on each host as separate process. Remote Nodes can subscribe for events
    on this dispatcher, too. Nodes are exchanging events through dispatcher.
    """
    def __init__(self, listen='pbu://localhost:5333/dispatcher'):
        self.routing = routing.RoutingTable() 
        self.tub = UnauthenticatedTub()
        
        host, port, refname = self._split(listen)
        
        self.listen_url = listen
        self.host = host
        self.port = port
        self.stats = DispatcherStats()
        
        self.tub.listenOn('tcp:%d' % port)
        self.tub.setLocation('%s:%d' % (host, port))
        self.tub.registerReference(self, refname)
        
    
    def _split(self, url):
        schema, rest = url.split('://')
        location, ref = rest.split('/')
        
        host, port = location.split(':')
        
        return host, int(port), ref

 
        
    def startService(self):
        self.tub.startService()
        
        from nodeset.core import heartbeat
        self.heartbeat = heartbeat.NodeHeartBeat(self)
        self.heartbeat.schedule(10)
        
        if config.Configurator.subCommand == 'xmpp':
            
            from nodeset.core.pubsub import agent
            
            jidname = config.Configurator.subOptions['jidname']
            pwd = config.Configurator.subOptions['passwd']
            xmpp_srv = config.Configurator.subOptions['server']
            xmpp_fqdn = config.Configurator.subOptions['fqdn']
            xmpp_pubsub = config.Configurator.subOptions['pubsub']
        
            xmpp_host =  xmpp_fqdn or xmpp_srv
            xmpp_port = config.Configurator.subOptions['port']
               
            jid = "%s@%s/nodeset" % (jidname, xmpp_host)

            log.msg("XMPP support enabled, jid(%s)" % jid)            
            xmpp = agent.XmppAgent(xmpp_srv, jid, pwd, xmpp_port)
            #xmpp.setServiceParent(self)
            xmpp.startService()
            
            def on_event(msg):
                log.msg("on_event")
                items = xmpp.getEventItems(msg)
                for item in items:
                    #body = item.children[0]
                    json = simplejson.loads(item.body.children[0])
                    
                    if json['host'] ==  jidname:
                        log.msg("Event json %s" % json)
                        _msg = message._Message()
                        _msg.fromJson(json['msg'])
                    
                        print _msg.attrs
                        eventURI = '%s@localhost/%s' % (json['node'], json['event_name'])
                    
                        self.remote_publish(eventURI, _msg)
                    else:
                        log.msg("Event for another node %s" % json)
                    
            xmpp.gotEvent = on_event
            
            def subscription_add(eventDict, xmpp):
                uri = eventDict['parsed_uri']
                
                xmpp.hasNode(xmpp_pubsub, uri.eventName)\
                    .addErrback(lambda _: 
                                    xmpp.createNodeAndConfigure(xmpp_pubsub, uri.eventName))\
                                    .addCallback(lambda _: xmpp.subscribe(xmpp_pubsub, uri.eventName))
                                                                                  
                
                #xmpp.subscribe(xmpp_pubsub, uri.getEventName)
                
            #def subscription_drop(eventDict, xmpp):
            #    pass

            def publish_fail(eventDict, xmpp):
                uri = eventDict['parsed_uri']
                msg = eventDict['args'][0]
                
                payload = {'event_name': uri.eventName, 'node': uri.nodeName, 'host': uri.hostName}
                payload['msg'] = msg.toJson()
                
                log.msg("publish fail %s, %s, %s" % (eventDict, xmpp, payload))
                
                xmpp.publish(xmpp_pubsub, xmpp.jid.userhost(), uri.eventName, simplejson.dumps(payload))
                
            
            
            self.routing.addObserver('add', subscription_add, xmpp)
            #self.routing.addObserver('remove', subscription_drop, xmpp)
            #self.routing.addObserver('get', subscription_find, xmpp)
            self.routing.addObserver('fail', publish_fail, xmpp)
            
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
      
    
    def remote_get_stats(self):
        """
        Foolscap RPC method, returns current stats for dispatcher
        """
        return self.stats.toJSON()
    
    def _debug_print(self, data):
        print "<-> %s" % data
        
    def _do_publish(self, entries, event_name, msg):
        for n in entries:
            method = 'event'
            err_back = self._dead_reference
            args = (None, n.getNode(),)
             
            #TODO: implement call() in Node
            n.getNode().callRemote(method, event_name, msg).addErrback(err_back, *args)
            self.stats.pubs += 1
            
            if msg._delivery_mode != 'all':
                break
         
    def remote_publish(self, event_name, msg):
        log.msg("publishing %s(msg=%s)" % (event_name, msg), logLevel=logging.INFO)
        
        for d in self.routing.get(event_name):
            d.addCallback(self._do_publish, event_name, msg)\
                  .addErrback(self.routing.onFailure, routing.NoSuchEntry, msg)
                  

        return True
    
    def remote_unsubscribe(self, event_name, node, name):
        log.msg("unsubscribe for %s by %s" % (event_name, node), logLevel=logging.INFO)
        self.routing.remove(event_name, node, name)
        
        if self.heartbeat.has(node):
            self.heartbeat.remove(node)
                                 
    def remote_subscribe(self, event_name, node, name):
        log.msg("subscription to %s by %s" % (event_name, node), logLevel=logging.INFO)
  
        self.routing.add(event_name, node, name)
        self.stats.subs += 1
        
        if not self.heartbeat.has(node):
            #FIXME: workaround for missing monitor, foolscap does not pass ivars
            node.monitor = None
            m = self.heartbeat.add(node).onOk(lambda _: None).onFail(self._dead_reference, event_name, node)
            

                
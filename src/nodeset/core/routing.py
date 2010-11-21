"""
Dispatcher's routing classes
"""
from zope.interface import implements

from nodeset.core import interfaces, config
from nodeset.common import log

from nodeset.core.observer import Observer, ObserverCarousel

class RREntrySet(list):
    """
    Subclass of list for routing table entries. This class provides to additional methord (to list).
    """
    def order(self):
        """
        re-order items in list (in this case it's round robin)
        """
        try:
            e = self.pop(0)
            self.append(e)
        except IndexError, e:
            pass
    
    def add(self, item):
        """
        the same as for set(), if try to add already available item, exception will be raised
        """
        try:
            self.index(item)
            
            raise IndexError("Dup entry")
        except ValueError, e:
            self.append(item)
            
class NoSuchEntry(Exception):
    
    def __init__(self, eventUri):
        self.eventUri = eventUri

class EventURI:
    def __init__(self, event_uri):
        self.eventName = None
        self.nodeName = None
        self.hostName = None
        self.raw = event_uri
    
        if event_uri:
            self._split_uri(event_uri)
        
    def __str__(self):
        return str("%s@%s/%s" % (self.nodeName, self.hostName, self.eventName))
    
    def _split_uri(self, event_uri):
        """
        Parsing of event URI (i.e. node@host/event)
        @param event_uri: event URI
        @return: triplet of (host, node, event)
        @raise: Exception(Invalid Addressing)
        """
        host = node = event = None

        # split URI node@host/event
        # by / first -> list, if not found - only event name was provided
        # list[0] split by '@' if not - only host was specified, otherwise node and host
        
    
        items = event_uri.split('/')
        
        if len(items) == 2:
            tt = items[0].split('@')
        
            if len(tt) == 2:
                self.nodeName, self.hostName = tt
            else:
                self.hostName = items[0]
                
            self.eventName = items[1]
        else:
            self.eventName = items[0]

        # in case of missing host -> localhost
        # in case of missing node -> *
        if not self.hostName:
            self.hostName = 'localhost'
        if not self.nodeName:
            self.nodeName = '*'

        # event is mandatory, if missing - invalid addressing
        if not self.eventName:
            raise Exception("Invalid addressing %s" % event_uri)
        
        #return EventURI(node, host, event)
    
class RoutingTable:
    """
    Routing table container
    @ivar entries: dict of RouteEntry instances 'event_name' -> [RouteEntry, RouteEntry,...]
    """
    
    def __init__(self):
        self.entries = {}
        self.factory = RouteEntryFactory()
       
        # default observers for routing table actions (add, get, remove and failure)
        self.observers = {'add': [Observer(self._add)],
                          'remove': [Observer(self._remove)],
                          'get': [Observer(self._get)],
                          'fail': [Observer(lambda _: None)]}
     
        self.carousel = ObserverCarousel()
        
    def addObserver(self, name, callbable, *args, **kwargs):
        ob = Observer(callbable, *args, **kwargs)
        
        if ob not in self.observers[name]:
            self.observers[name].append(ob)
    
        return ob
    
    def removeObserver(self, name, observer):
        self.observers[name].remove(observer)
           
    def _lookup(self, event_uri, node=None):
        """
        return list of destination nodes
        """
        if config.Configurator['verbose']:
            log.msg("Looking up %s(instance=%s)" % (event_uri, node))
        
        ev = EventURI(event_uri)
        
        # return empty list if we don't know about such event
        # observers should do the rest (i.e. get data from DHT)
        if not self.entries.has_key(ev.eventName):
            raise NoSuchEntry(ev)
        
        # first lookup only by event name
        ns = self.entries[ev.eventName]
    
        # change order of entries for next calls
        self.entries[ev.eventName].order()
        
        #ns = [x for x in self.entries if x.getEventName() == name]
        
        
        # then lookup by hostname
        if ev.hostName:
            ns = RREntrySet([x for x in ns if x.getHost() == ev.hostName])

        
                
        # and then lookup by node_name, but avoid check if node is wildcard
        if ev.nodeName and ev.nodeName != '*':
            ns = RREntrySet([x for x in ns if x.getName() == ev.nodeName])
            
        # and then lookup by object instance
        if node:
            return RREntrySet([x for x in ns if x.getNode() == node])

        # anyway, if we didn't find any route entries for this eventURI and hostname is not localhost
        # try to get this data from DHT
        if len(ns) == 0 and ev.hostName != 'localhost':
            raise NoSuchEntry(ev)
        
        return ns
        
    def _lookupByNode(self, node):
        rlist = []
        for k in self.entries.values():
            t = [x for x in k if x.getNode() == node]
            if len(t):
                rlist += t
                
        return rlist
        
    def _get(self, eventDict):
        return self._lookup(eventDict['uri'])
     
    def get(self, event_uri):
        """
        Get recepients for event_uri
        @param event_uri: event URI
        @return: L{RouteEntry}
        @raise: KeyError
        """
        d = {'uri': event_uri,
             'parsed_uri': EventURI(event_uri)}
        
        return self.carousel.twist(self.observers['get'], d)


    def onFailure(self, fail, klass, *args):
        fail.trap(klass)
        
        # don't know how to get exception instance from L{Failure}
        try:
            fail.raiseException()
        except klass, e:
            eventUri = e.eventUri
        
            #print eventUri.hostName
            
            # if it's not for localhost, twist the carousel
            if eventUri.hostName != 'localhost':
                return self.carousel.twist(self.observers['fail'], {'parsed_uri': eventUri,
                                                                'args':  args})
    
    #    if self.dht:
    #        dht_key = "%s@%s" % (eventUri.eventName, eventUri.nodeName)
    #        log.msg("looking in DHT key(%s)" % dht_key)
    #        return self.dht.searchData(dht_key).addCallback(self.dht.onData, eventUri, cb, *args)
        
        return []
        
    def _add(self, eventDict):
        
        parsed = eventDict['parsed_uri']
                
        if not self.entries.has_key(parsed.eventName):
            self.entries[parsed.eventName] = RREntrySet()
           
        if config.Configurator['verbose']: 
            log.msg("Adding route entry for %s" % str(parsed))
        
        self.entries[parsed.eventName]\
                 .add(self.factory.getEntry(parsed.hostName, parsed.eventName, 
                                            eventDict['instance'], parsed.nodeName))
            
    def add(self, event_uri, node, node_name=None):
        """
        Add new recepient for event
        @param event_uri: event URI
        @param node: recepient node
        @type node: L{Node}
        """
        
        #key = "%s@%s/%s" % (node_name, host, name)
        #log.msg("Adding %s to routing table" % key)
        
        parsedUri = EventURI(event_uri)
        
        if parsedUri.nodeName == '*':
            parsedUri.nodeName = node_name
            
        d = {'uri': event_uri,
             'parsed_uri': parsedUri,
             'instance': node}
             
        
        return self.carousel.twist(self.observers['add'], d)
        
    def remove(self, event_uri, node, node_name=None):
        
        parsedUri = EventURI(event_uri)
        if parsedUri.nodeName == '*':
            parsedUri.nodeName = node_name
            
        d = {'uri': event_uri,
             'parsed_uri': parsedUri,
             'instance': node}
        
        return self.carousel.twist(self.observers['remove'], d)
        
    def _remove(self, eventDict):
        """
        Remove recepient for event
        @param event_uri: event URI
        @param node: recepient
        @raise: KeyError
        """
        
        if eventDict['uri']:
            nodes = self._lookup(eventDict['uri'], eventDict['instance'])
        else:
            if isinstance(eventDict['instance'], RouteEntry):
                #node.alive = False
                nodes = [eventDict['instance']]
            else:
                #print node
                nodes = self._lookupByNode(eventDict['instance'])
        
        #XXX actual removing maybe could be pushed to background
        for n in nodes:
            key = "%s@%s/%s" % (n.getName(), n.getHost(), n.getEventName())
            if config.Configurator['verbose']:
                log.msg("Removing %s from routing table" % key)
            self.entries[n.getEventName()].remove(n)
            
            
class RouteEntry:
    """
    Routing table entry, contains event name and subscribed nodes to such event
    @ivar name: event name
    @ivar node: Node instance
    @ivar host: Node's host
    """
    implements(interfaces.routing.IRouteEntry)
    
    name = None
    node = None
    host = None
    alive = True
    weight = 1
    
    def __init__(self, host, event_name, node, node_name):
        """
        @param host: host part of eventURI
        @param event_name: event name
        @param node: foolscap's node (L{RemoteReference})
        @param node_name: node name
        """
        self.name = event_name
        self.node = node
        self.host = host
        self.node_name = node_name
        
    def getNode(self):
        return self.node
    
    def getName(self):
        return self.node_name
    
    def getHost(self):
        return self.host
    
    def getEventName(self):
        return self.name
    
    def __str__(self):
        return str("%s@%s/%s (alive=%s)" % (self.node_name, self.host, self.name, self.alive))
    
    def __eq__(self, obj):
        if self.getNode() != obj.getNode() or \
            self.getHost() != obj.getHost() or \
            self.getName() != obj.getName() or \
            self.getEventName() != obj.getEventName():
            return False
        
        return True
            
            
class RemoteRouteEntry(RouteEntry):
    """
    Routing entry for remote Nodes
    """
    pass

    
class LocalRouteEntry(RouteEntry):
    """
    Routing entries for local Nodes
    """
    pass

class RouteEntryFactory:
    
    def getEntry(self, host, event, node, node_name):
        if host == 'localhost':
            return LocalRouteEntry(host, event, node, node_name)
        else:
            return RemoteRouteEntry(host, event, node, node_name)
        
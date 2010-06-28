"""
Dispatcher's routing classes
"""
from zope.interface import implements

from nodeset.core import interfaces, dht
from nodeset.common import log

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
            
    
class RoutingTable:
    """
    Routing table container
    @ivar entries: dict of RouteEntry instances 'event_name' -> [RouteEntry, RouteEntry,...]
    """
    
    def __init__(self, dispatcher):
        self.entries = {}
        self.factory = RouteEntryFactory()
        self.dispatcher = dispatcher
       
        self.dht = None
        self.knownNodes = []
        
    def initDHT(self, port, nodes):
        self.dht = dht.NodeSetDHT(udpPort=port)
        if nodes:
            self.knownNodes = [x.split(':') \
                               for x in nodes.split(',')]
            self.knownNodes = map(lambda x: (x[0], int(x[1])), self.knownNodes)
            self.dht.joinNetwork(self.knownNodes)
             
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
                node, host = tt
            else:
                host = items[0]
                
            event = items[1]
        else:
            event = items[0]

        # in case of missing host -> localhost
        # in case of missing node -> *
        if not host or host == self.dispatcher.host:
            host = 'localhost'
        if not node:
            node = '*'

        # event is mandatory, if missing - invalid addressing
        if not event:
            raise Exception("Invalid addressing %s" % event_uri)
        
        return (node, host, event)
    
    def _lookup(self, event_uri, node=None):
        """
        return list of destination nodes
        """
        log.msg("Looking up %s(%s)" % (event_uri, node))
        
        node_name, host, name = self._split_uri(event_uri)
        
        # first lookup only by event name
        ns = self.entries[name]
    
        # change order of entries for next calls
        self.entries[name].order()
        
        #ns = [x for x in self.entries if x.getEventName() == name]
        
        # then lookup by hostname
        if host:
            ns = RREntrySet([x for x in ns if x.getHost() == host])
        
        # and then lookup by node_name, but avoid check if node is wildcard
        if node_name and node_name != '*':
            ns1 = RREntrySet([x for x in ns if x.getName() == node_name])
            
        # and then lookup by object instance
        if node:
            return RREntrySet([x for x in ns if x.getNode() == node])

        return ns
        
    def _lookupByNode(self, node):
        rlist = []
        for k in self.entries.values():
            t = [x for x in k if x.getNode() == node]
            if len(t):
                rlist += t
                
        return rlist
        
    def _gotRem(self, remote, event_uri):
        self.add(event_uri, remote, '*', dht=False)
            
    def _handle_DHT(self, data, event_uri):
        log.msg("DHT: raw data %s" % data)
        dispatcher_url = ''.join(data)
        if len(data):
            log.msg("dispatcher URL from DHT %s" % dispatcher_url)
            return self.dispatcher.tub.getReference(dispatcher_url).addCallback(self._gotRem, event_uri)
        
        
    def get(self, event_uri):
        """
        Get recepients for event_uri
        @param event_uri: event URI
        @return: L{RouteEntry}
        @raise: KeyError
        """
        try:
            return self._lookup(event_uri)
        except KeyError, e: # unkown URI, ignore it
            log.msg("Searching in DHT... %s" % event_uri)
            return [self.dht.searchData(event_uri).addCallback(self._handle_DHT, event_uri)]
        
    def add(self, event_uri, node, node_name=None, dht=True):
        """
        Add new recepient for event
        @param event_uri: event URI
        @param node: recepient node
        @type node: L{Node}
        """
        node_name, host, name = self._split_uri(event_uri)
        key = "%s@%s/%s" % (node_name, host, name)
        log.msg("Adding %s to routing table" % key)
        
        if dht and self.dht:
            dht_key = "%s@%s/%s" % (node_name, self.dispatcher.host, name)
            self.dht.publishData(dht_key, self.dispatcher.listen_url)
        
        if not self.entries.has_key(name):
            self.entries[name] = RREntrySet()
            
        self.entries[name].add(self.factory.getEntry(host, name, node, node_name))
        
    def remove(self, event_uri, node):
        """
        Remove recepient for event
        @param event_uri: event URI
        @param node: recepient
        @raise: KeyError
        """
        
        if event_uri:
            nodes = self._lookup(event_uri, node)
        else:
            if isinstance(node, RouteEntry):
                #node.alive = False
                nodes = [node]
            else:
                #print node
                nodes = self._lookupByNode(node)
        
        #XXX actual removing maybe could be pushed to background
        for n in nodes:
            key = "%s@%s/%s" % (n.getName(), n.getHost(), n.getEventName())
            log.msg("Removing %s from routing table" % key)
            self.entries[n.getEventName()].remove(n)
            if dht:
                self.dht.removeData(key)
            
            
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
        self.name = event_name
        self.node = node
        self.host = host
        self.node_name = node_name
        
    def getNode(self):
        return self.node
    
    def getName(self):
        return self.name
    
    def getHost(self):
        return self.host
    
    def getEventName(self):
        return self.name
    
    def __str__(self):
        return str("%s@%s/%s (alive=%s)" % (self.node, self.host, self.name, self.alive))
    
    def __eq__(self, obj):
        if self.getNode() != obj.getNode() or \
            self.getHost() != obj.getHost() or \
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
        
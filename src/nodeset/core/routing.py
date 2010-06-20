"""
Dispatcher's routing classes
"""
from zope.interface import implements

from nodeset.core import interfaces

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
        print "looking up %s(%s)" % (event_uri, node)
        
        node_name, host, name = self._split_uri(event_uri)
        
        # first lookup only by event name
        ns = self.entries[name]
    
        # change order of entries for next calls
        self.entries[name].order()
        
        print "do we have such event %s" % ns
        #ns = [x for x in self.entries if x.getEventName() == name]
        
        # then lookup by hostname
        if host:
            ns = RREntrySet([x for x in ns if x.getHost() == host])
        
        print "do we have such host %s" % ns
        
        # and then lookup by node_name, but avoid check if node is wildcard
        if node_name and node_name != '*':
            ns1 = RREntrySet([x for x in ns if x.getNode().name == node_name])
            
        # and then lookup by object instance
        if node:
            return RREntrySet([x for x in ns if x.getNode() == node])

        print ns
        
        return ns
        
    def _lookupByNode(self, node):
        rlist = []
        for k in self.entries.values():
            t = [x for x in k if x.getNode() == node]
            if len(t):
                rlist += t
                
        return rlist
        
    def _gotRem(self, remote, event_uri):
        #n, h, e = self._split_uri(event_uri)
        remote.name = '*'
        self.add(event_uri, remote, dht=False)
            
    def _handle_DHT(self, data, event_uri):
        dispatcher_url = ''.join(data)
        if len(data):
            print "dispatcher URL from DHT %s" % dispatcher_url
            return self.dispatcher.tub.getReference(dispatcher_url).addCallback(self._gotRem, event_uri)
        
        
    def get(self, event_uri):
        """
        Get recepients for event_uri
        @param event_uri: event URI
        @return: L{RouteEntry}
        @raise: KeyError
        """
        try:
            ns = self._lookup(event_uri)
            
            #if not len(ns):
            #    print "Searching in DHT"
                
            #    self.dispatcher.dht.searchForKeywords(event_uri).addCallback(self._dht_results)
                
            return ns
        except KeyError, e: # unkown URI, ignore it
            print "Searching in DHT... %s" % event_uri
            return [self.dispatcher.dht.searchForKeywords(event_uri).addCallback(self._handle_DHT, event_uri)]
            #return []
        
    def add(self, event_uri, node, dht=True):
        """
        Add new recepient for event
        @param event_uri: event URI
        @param node: recepient node
        @type node: L{Node}
        """
        node_name, host, name = self._split_uri(event_uri)
        key = "%s@%s/%s" % (node_name, host, name)
        print "--> adding %s" % key
        
        if dht:
            #if host == 'localhost':
            #    host = self.dispatcher.host
            
            dht_key = "%s@%s/%s" % (node_name, self.dispatcher.host, name)
            self.dispatcher.dht.publishData(dht_key, self.dispatcher.dispatcher_url)
        #self.dispatcher.dht.iterativeStore(self.dispatcher.dht.hash_key(key),
        #                                   (key, self.dispatcher.dispatcher_url))
        
        if not self.entries.has_key(name):
            self.entries[name] = RREntrySet()
            
        self.entries[name].add(self.factory.getEntry(host, name, node))
        
        print self.entries
        
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
            key = "%s@%s/%s" % (n.getNode().name, n.getHost(), n.getEventName())
            print "--> remove key %s" % key
            self.entries[n.getEventName()].remove(n)
            self.dispatcher.dht.removeData(key)
            #self.dispatcher.dht.iterativeDelete(self.dispatcher.dht.hash_key(key))
        
            
            
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
    
    def __init__(self, host, event_name, node):
        self.name = event_name
        self.node = node
        self.host = host
        
    def getNode(self):
        return self.node
    
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
    
    def getEntry(self, host, event, node):
        if host == 'localhost':
            return LocalRouteEntry(host, event, node)
        else:
            return RemoteRouteEntry(host, event, node)
        
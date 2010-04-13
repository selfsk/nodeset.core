from zope.interface import implements

from nodeset.core import interfaces
 
class RoutingTable:
    """
    Routing table container
    @ivar entries: list of RouteEntry instances
    """
    
    entries = {}
    #nodes = {}
    #hosts = {}
    #events = {}
    
    def __init__(self):
        self.factory = RouteEntryFactory()
        
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
        if not host:
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
        node_name, host, name = self._split_uri(event_uri)
        
        # first lookup only by event name
        ns = self.entries[name]
        
        #ns = [x for x in self.entries if x.getEventName() == name]
        
        # then lookup by hostname
        if host:
            ns = [x for x in ns if x.getHost() == host]
        
        # and then lookup by node_name, but avoid check if node is wildcard
        if node_name and node_name != '*':
            ns = [x for x in ns if x.getNode().name == node_name]
            
        # and then lookup by object instance
        if node:
            return [x for x in ns if x.getNode() == node]
        
        return ns 
        
            
    def get(self, event_uri):
        """
        Get recepients for event_uri
        @param event_uri: event URI
        @return: L{RouteEntry}
        @raise: KeyError
        """
        
        return self._lookup(event_uri)
        
    def add(self, event_uri, node):
        """
        Add new recepient for event
        @param event_uri: event URI
        @param node: recepient node
        @type node: L{Node}
        """
        node_name, host, name = self._split_uri(event_uri)

        if not self.entries.has_key(name):
            self.entries[name] = []
            
        self.entries[name].append(self.factory.getEntry(host, name, node))
        
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
                nodes = [node]
            else:
                nodes = [x for x in self.entries if x.getNode() == node]
        
        #XXX actual removing maybe could be pushed to background        
        #for n in nodes:
        #    self.entries.remove(n)
        
class RouteEntry:
    implements(interfaces.routing.IRouteEntry)
    """
    Routing table entry, contains event name and subscribed nodes to such event
    @ivar name: event name
    @ivar node: Node instance
    @ivar host: Node's host
    """
    name = None
    node = None
    host = None
    
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
        
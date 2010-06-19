# entangled DHT stuff
from entangled.node import EntangledNode
from entangled.kademlia import node


class NodeSetDHT(EntangledNode):
    
    def __init__(self, *args, **kwargs):
        EntangledNode.__init__(self, *args, **kwargs)
        self.nodeset = None
        
        
    def setTub(self, nodeset):
        self.nodeset = nodeset
        
    
    def _gotReference(self, remote, event_uri):
        self.nodeset.routing.add(event_uri, remote)
        
    def _err(self, failure):
        print failure
        
    @node.rpcmethod
    def store(self, key, value, originalPublisherID=None, age=0, **kwargs):
        super(EntangledNode, self).store(key, value, originalPublisherID, age, **kwargs)
    
        event_uri, dispatcher_url = value
        
        self.nodeset.tub.getReference(dispatcher_url).addCallback(self._gotReference, event_uri).addErrback(self._err)
        
        print "--> %s" % str(value)
        
        return 'OK'
            
    @node.rpcmethod
    def delete(self, key, **kwargs):
        super(EntangledNode, self).delete(key, **kwargs)
        
        print "---> delete %s" % kwargs
        
        return 'OK'
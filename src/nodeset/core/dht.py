# entangled DHT stuff
from entangled.node import EntangledNode
from entangled.kademlia import node

import hashlib

class NodeSetDHT(EntangledNode):
    
    def __init__(self, *args, **kwargs):
        EntangledNode.__init__(self, *args, **kwargs)
        self.nodeset = None
        self.keywordSplitters = []
        
    def setTub(self, nodeset):
        self.nodeset = nodeset
    
    def _err(self, failure):
        print failure
        
    def hash_key(self, key):
        h = hashlib.sha1()
        h.update(key)
        
        return h.digest()


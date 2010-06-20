# entangled DHT stuff
from entangled.node import EntangledNode
from entangled.kademlia import node

import hashlib

class NodeSetDHT(EntangledNode):
    
    def __init__(self, *args, **kwargs):
        EntangledNode.__init__(self, *args, **kwargs)
        self.nodeset = None
        self.keywordSplitters = [',']
        
    def searchData(self, name):
        
        key = self.hash_key(name)
        
        def checkResults(results):
            print "DHT res; %s" % str(results)
            
            if type(results) == dict:
                return results[key]
            else:
                return None
            
        df = self.iterativeFindValue(key)
        df.addCallback(checkResults)
        
        return df
    
    def setTub(self, nodeset):
        self.nodeset = nodeset
    
    def _err(self, failure):
        print failure
        
    def hash_key(self, key):
        h = hashlib.sha1()
        h.update(key)
        
        return h.digest()


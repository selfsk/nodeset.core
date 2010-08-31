# entangled DHT stuff
from entangled.node import EntangledNode
from entangled.kademlia import datastore

from nodeset.common import log

import hashlib

class NodeSetDataStore(datastore.DictDataStore):
    
    def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherID):
        if self._dict.has_key(key):
            self._dict[key].append((value, lastPublished, originallyPublished, originalPublisherID))
        else:
            self._dict[key] = [(value, lastPublished, originallyPublished, originalPublisherID)]
            
    def __getitem__(self, key):
        return [x[0] for x in self._dict[key]]
    
class NodeSetDHT(EntangledNode):
    
    def __init__(self, *args, **kwargs):
        EntangledNode.__init__(self, *args, **kwargs)
        self.nodeset = None
        self.keywordSplitters = [',']
        
    #def _gotRem(self, remote, eventUri):
    #    self.routing.add(eventUri.eventName, remote, eventUri.nodeName)
            
    def onData(self, data, eventUri, cb, *args):
        if not data:
            return None
        
        log.msg("DHT: raw data %s" % data)
        if len(data):
            return cb(data, eventUri, *args)
        
    
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


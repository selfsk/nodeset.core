"""
Stream handling (encoding/decoding) base classes for StreamNodes
"""
from twisted.internet import defer

from nodeset.common import log

class Formatter:
    """
    Plain stream formatter, provides encode/decode routines
    """
    
    def encode(self, data):
        """
        Encode stream data before sending
        """
        return data
    
    def decode(self, data):
        """
        Decode stream data on receiving
        """
        return data
    

class Stream:
    """
    Streaming class for StreamNode
    @ivar formatterClass: stream formatter class, provides encode/decode
    """
    
    formatterClass = Formatter
    
    def __init__(self, node, peers=None):
        self.node = node
        self.peers = peers
        self.formatter = self.formatterClass()
        
    def push(self, data):
        """
        Push new data to stream
        """
        defers = []

        log.msg("Pushing data to peers=%s" % self.peers)
        
        for peer in self.peers:
            d = peer.callRemote('stream', self.formatter.encode(data), self.formatter)

            defers.append(d)
            
        if len(defers) > 1:
            return defer.DeferredList(defers)
        
        return defers.pop()

    
    
    
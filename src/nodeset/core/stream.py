from twisted.internet import defer

class Formatter:
    """
    Stream formatter, provides encode/decode routins
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
    Abstract Streaming class for StreamNode
    """
    
    def __init__(self, node, name):
        self.node = node
        self.name = name
        self.remote = None
        
    def _getPeer(self, peers):
        self.remote = peers

    def _error(self, failure):
        print "failure %s" % failure
        
    def getRemoteNode(self):
        """
        Gets remote reference for direct foolscap calls
        """
        return self.node.dispatcher.callRemote('stream', self.name).addCallback(self._getPeer).addErrback(self._error)
    
    def push(self, data):
        """
        Push new data to stream
        """
        defers = []

        for r in self.remote:
            d = r.callRemote('stream', self.node.formatter.encode(data))
            defers.append(d)
            
        if len(defers) > 1:
            return defer.DeferredList(defers)
        
        return defers.pop()
    

    
    
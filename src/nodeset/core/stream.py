
class Stream:
    """
    Abstract Streaming class for StreamNode
    """
    
    def __init__(self, node):
        self.node = node
        
    def getRemoteNode(self):
        """
        Gets remote reference for rctp node
        """
        pass
    
    def push(self, data):
        """
        Push new data to stream
        """
        pass
    
    

class YamlStream(Stream):
    """
    Class for Yaml Streaming, to perform massive event execution
    """
    def push(self, event):
        pass
    
    
class BinaryStream(Stream):
    """
    Class for binary streaming
    """
    
    def push(self, chunk):
        pass
    
    
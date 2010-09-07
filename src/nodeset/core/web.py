from nodeset.core import node

from twisted.web import server

class WebBridgeNode(node.Node):
    """
    Special purpose Node, which should work in coop with NodeSetSite object, to perform publish/subscribe via HTTP
    """
    
    events = {}
    def onEvent(self, event, msg):
        #try:
        m, args, kw = self.events[event]
        m(msg, *args, **kw)
     
    def subscribe(self, event, cb, *args, **kwargs):
        self.events[event] = (cb, args, kwargs)
        super(WebBridgeNode, self).subscribe(event)
               
    def unsuscribe(self, event):
        del self.events[event]
        super(WebBridgeNode, self).unsubscribe(event)
         
class NodeSetSite(server.Site):
    """
    Site class for Web resources handling with support of Node
    """
    
    def __init__(self, resource, node, **kw):
        server.Site.__init__(self, resource, **kw)
        
        self.node = node
        
    def setNode(self, node):
        self.node = node

    def getNode(self):
        return self.node
    
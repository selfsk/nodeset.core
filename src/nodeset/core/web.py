from nodeset.core import node

from twisted.web import server
import uuid

class WebBridgeNode(node.Node):
    """
    Special purpose Node, which should work in coop with NodeSetSite object, to perform publish/subscribe via HTTP
    """
    
    events = {}

    def onEvent(self, event, msg):
        for item in self.events[event]:
            subId = item[0]
            m, args, kw = item[1]
            
            m(msg, subId, *args, **kw)
     
    def subscribe(self, event, cb, *args, **kwargs):
        subscriptionId = str(uuid.uuid4())
        
        if self.events.has_key(event):
            self.events[event].append((subscriptionId,  (cb, args, kwargs)))
        else:
            self.events[event] = [(subscriptionId, (cb, args, kwargs))]
            
        if not self.issubscribed(event):
            super(WebBridgeNode, self).subscribe(event)

        return subscriptionId
    
    def unsubscribe(self, event, subscriptionId):
        
        for idx, item in enumerate(self.events[event]):
            subId = item[0]
            
            if subId == subscriptionId:
                t = self.events[event].pop(idx)
                del t
                
        if len(self.events[event]) == 0:
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
    
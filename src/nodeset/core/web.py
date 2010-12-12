from nodeset.core import node, message

from twisted.web import server, resource
import uuid
import simplejson

class WebMessageBuilder(node.MessageBuilder):
    """
    Builder class for web messages from JSON
    """
    def createMessage(self, klass, json):
        j = simplejson.loads(json)
        _msg = super(WebMessageBuilder, self).createMessage(klass)
        
        for k,v in j.items():
            _msg.setAttribute(k, v)
            
        return _msg
    
class WebBridgeNode(node.Node):
    """
    Special purpose Node, which should work in coop with NodeSetSite object, to perform publish/subscribe via HTTP
    """
    
    events = {}
    builderClass = WebMessageBuilder
    
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

class NodeSetSubscribe(resource.Resource):
    
    def render_GET(self, request):  
        n = request.site.getNode()
        verifier = request.site.getVerifier()
        
        use_key = request.getHeader('x-verify-key')
        is_verified = True
        try:
            signature = request.args['signature'].pop()
            timestamp = request.args['timestamp'].pop()
        
            
            if verifier:
                is_verified = verifier.verify(use_key, timestamp, signature)
        except KeyError:
            pass
        
        if not is_verified:
            return resource.ForbiddenResource("Signature invalid")
        
        def generic_handler(msg, subId, request):
            request.setHeader('content-type', 'application/json')
            request.write(msg.toJson())
            request.write("\r\n")
            
            if request.clientproto == "HTTP/1.0":
                request.finish()
            
        for ev in request.args['event']:
            n.subscribe(ev, generic_handler, request)
        
        
        return server.NOT_DONE_YET
    
    render_POST = render_GET
    

    
class NodeSetPublish(resource.Resource):
    
    def render_POST(self, request):
        node = request.site.getNode()
        verifier = request.site.getVerifier()
        
        msg = request.args['message'].pop()             
        ev = request.args['event'].pop()

        # by default all messages are verified
        is_verified = True
        
        try:
            signature = request.args['signature'].pop()
            if verifier:
                is_verified = verifier.verify(ev, msg, signature)
        except KeyError:
            pass
            
        if is_verified:
            node.publish(ev, msgClass=message.NodeMessage, json=msg).addCallback(lambda _: request.finish())
        
        request.write("\r\n")
        return server.NOT_DONE_YET

    render_GET = render_POST
    
class NodeSetSite(server.Site):
    """
    Site class for Web resources handling with support of Node
    """
    
    def __init__(self, resource, node, **kw):
        server.Site.__init__(self, resource, **kw)
        
        self.node = node
        # we need to verify that publish/subscribe are coming from permitted users
        self.verifier = None
        
    def getVerifier(self):
        return self.verifier
    
    def setVerifier(self, verifier):
        self.verifier = verifier
        
    def setNode(self, node):
        self.node = node

    def getNode(self):
        return self.node
    
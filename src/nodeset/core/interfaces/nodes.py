from zope import interface


class INode(interface.Interface):
    """ Node interface """
    name = interface.Attribute("Node name")
    port = interface.Attribute("Node listen port")
    dispatcher = interface.Attribute("Dispatcher remote ref")
    monitor = interface.Attribute("heartbeat monitor")
    builder = interface.Attribute("NodeEventBuilder instance")
    tub = interface.Attribute("foolscap's Tub")
    
    __subscribers = interface.Attribute("Node's subscriptions")
    
    
    
    def start(timeout):
        """ start routing for Node """
        
    # foolscaps callRemote callbacks
    def remote_event(event):
        """ foolscap's callRemote() callback """
    
    def remote_stream(data, formatter):
        """ callRemote('stream') callback """
        
    def remote_heartbeat():
        """ callRemote('heartbeat') callback """
        
    def remote_error(error):
        """ callRemote('error') callback """
     
    def onStream(data, formatter):
        """ default handler for stream data """
           
    def onError(error):
        """ default handler for error passed from dispatcher """
        
    def onEvent(event):
        """ default event handler for node """
        
    def publish(event):
        """ publish event to dispatcher """
        
    def subscribe(name):
        """ subscribe to event (name) onto dispatcher """
        
    def unsubscribe(name):
        """ unsubscribe from event (name) onto dispatcher """
        
        
class INodeCollection(interface.Interface):
    """ NodeCollection interface """
    
    events = interface.Attribute("events dict of lists")
    
    def addEvent(event_name, node):
        """ add node to event_name subscriptions """
        
    def removeEvent(event_name, node):
        """ remove node from subscriptions to event name """
        
    def eventloop(node, event, defer):
        """ do node.onEvent() callback and fire defer """
        
        
class IStreamNode(INode):
    """ Streaming Node interface """

    streamClass = interface.Attribute("stream class name, called to build stream")
    
    def getRemoteNode(stream_name):
        """ gets list of rcps nodes for stream name """
        
    def buildStream(peers):
        """ callback to build L{Stream} instance """
        
    def stream():
        """ stream interface """
        
from nodeset.core import dispatcher
from nodeset.core import node, config, message, utils

from twisted.trial import unittest
from twisted.internet import defer, reactor

class NodeTestCase(unittest.TestCase):
    
    def setUp(self):
        c = config.Configurator()
        c._config = {'dispatcher-url': 'pbu://localhost:5333/dispatcher',
                     'listen': 'localhost:5444',
                     'dht-nodes': None,
                     'dht-port': None,
                     'verbose': None,
                     }
        
        # minor hack to avoid 'xmpp' subCommand failures
        c.subCommand = None

        
        self.dispatcher = dispatcher.EventDispatcher()
        self.dispatcher.startService()
       
        def _err(fail):
            print fail
            
        self.dynnode = TestDynNode(name='dyn', port=5222)
        dy = self.dynnode.start().addCallback(lambda _: None).addErrback(_err)
        
        
        self.node = TestNode(5111)
        self.node.dqueue = defer.DeferredQueue()
         
        d = self.node.start().addCallback(lambda _: self.node.subscribe('event_name'))
        
        self.node.startService()
        self.dynnode.startService()
        
        self.dl = defer.DeferredList([dy, d])
        
        return self.dl
        
                                  
    def tearDown(self):
        self.dynnode.stopService()
        self.node.stopService()
            
        self.dispatcher.stopService()
            
        d = defer.Deferred()
        
        # doing a nasty thing! somehow reactor could have a delayedcall still, so use stupid sleep 
        reactor.callLater(1, d.callback, None)
        
        return d
        #self.nodeSub.stopService()
        
class TestNode(node.Node):
    """ Special node for testing functionality, onEvent stores last value, to perform check """
    
    def onEvent(self, event, msg):
        self.dqueue.put((event, msg))

class TestDynNode(node.Node):

    @utils.catch('event_one')
    def handleEventOne(self, msg):
        if self._ev_defs.has_key('event_one'):
            self._ev_defs['event_one'](msg)
    
    @utils.catch('event_two')
    def handleEventTwo(self, msg):
        if self._ev_defs.has_key('event_two'):
            self._ev_defs['event_two'](msg)
            
    @utils.catch('event_three')
    def handleEventThree(self, msg):
        if self._ev_defs.has_key('event_three'):
            self._ev_defs['event_three'](msg)
    
    def startService(self):
        node.Node.startService(self)
        self._ev_defs = {}
        
    def subscribe_t(self, event, d):
        self._ev_defs[event] = d.callback
        return node.Node.subscribe(self, event)
        
        
        
class TestMessage(message.NodeMessage):
    
    def __init__(self):
        message.NodeMessage.__init__(self)
        
        message.Attribute('payload')
        
from nodeset.core import dispatcher
from nodeset.core import node, config, message

from twisted.python import log
from twisted.trial import unittest
from twisted.internet import defer

class NodeTestCase(unittest.TestCase):
    
    def setUp(self):
        c = config.Configurator()
        c._config = {'dispatcher-url': 'pbu://localhost:5333/dispatcher',
                     'listen': 'localhost:5444',
                     'dht-nodes': None,
                     'dht-port': None}
        
        self.dispatcher = dispatcher.EventDispatcher()
        self.dispatcher.startService()
       
        self.node = TestNode(5111)
        self.node.dqueue = defer.DeferredQueue()
         
        d = self.node.start().addCallback(lambda _: self.node.subscribe('event_name'))
        self.node.startService()
        
        #print self.dispatcher.routing.entries
        
        return d
                                  
    def tearDown(self):
        self.dispatcher.stopService()
        self.node.stopService()
        #self.nodeSub.stopService()
        
class TestNode(node.Node):
    """ Special node for testing functionality, onEvent stores last value, to perform check """
    
    def onEvent(self, event, msg):
        self.dqueue.put((event, msg))

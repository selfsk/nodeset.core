#from twisted.trial import unittest
from twisted.python import log

from nodeset.core import message

from common import NodeTestCase, TestMessage
     
       
class PublishSubscribeTestCase(NodeTestCase):
    
    def checkReceivedData(self, data, w_event, w_attr, w_attr_val):
        event, msg = data
        v = getattr(msg, w_attr)
        
        self.assertTrue(v != None)
        self.assertEqual(event, w_event)
        self.assertEqual(v, w_attr_val)
        
    def testSubscribe(self):
        # on setUp node do subscribe('event_name')
        self.assertTrue('event_name' in self.node.getSubscriptions())
        self.assertTrue(len(self.dispatcher.routing.get('event_name')) == 1)
        
    def testPublish(self):
        log.msg("dispatcher %s" % self.node.dispatcher)

        d = self.node.dqueue.get()
        d.addCallback(self.checkReceivedData, 'event_name', 'payload', 'test-publish')
        
        self.node.publish('event_name', msgClass=TestMessage, payload='test-publish')
        
        return d
    
    def testPublishWithCustomMessage(self):
        class TMsg(message.NodeMessage):
            
            def __init__(self):
                message.NodeMessage.__init__(self)
                message.Attribute('custom_field')
        
        d = self.node.dqueue.get()        
        self.node.publish('event_name', TMsg, custom_field='custom')
        
        d.addCallback(self.checkReceivedData, 'event_name', 'custom_field', 'custom')
        
        return d

   
    
        
        
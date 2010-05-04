from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.python import log

from nodeset.core import message, node

from common import NodeTestCase
     
       
class PublishSubscribeTestCase(NodeTestCase):
    
    def checkReceivedData(self, data, node, event_name, message):
        self.assertEqual(node.event, event_name)
        self.assertEqual(node.msg, message)
        
    def testSubscribe(self):
        # on setUp node do subscribe('event_name')
        self.assertTrue('event_name' in self.node.getSubscriptions())
        self.assertTrue(len(self.dispatcher.routing.get('event_name')) == 1)
        
    def testPublish(self):
        log.msg("dispatcher %s" % self.node.dispatcher)
        m = self.node.builder.createMessage(self.node.message, payload='test-publish')
        d = self.node.publish('event_name', payload='test-publish')
        d.addCallback(self.checkReceivedData, self.node, 'event_name', m)
        
        return d
    
    def testPublishWithCustomMessage(self):
        class TMsg(message.NodeMessage):
            
            def __init__(self):
                message.Attribute('custom_field')
                
        m = self.node.builder.createMessage(TMsg, custom_field='custom')
        d = self.node.publish('event_name', TMsg, custom_field='custom')
        d.addCallback(self.checkReceivedData, self.node, 'event_name', m)
        
        return d

   
    
        
        
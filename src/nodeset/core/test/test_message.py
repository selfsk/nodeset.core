from twisted.trial import unittest
from twisted.internet import defer

from nodeset.core import message, node

class MessageTest(unittest.TestCase):
    
    def setUp(self):
        self.builder = node.MessageBuilder()
        
    def testBuildMessage(self):
        m = self.builder.createMessage(message.NodeMessage)
        
        self.assertTrue(isinstance(m, message._Message))
                        
    def testMessageUpdate(self):
        m = self.builder.createMessage(message.NodeMessage)
        
        self.assertTrue(m.payload == None)
        
        m.payload = 'payload#1'
        
        self.assertTrue(m.payload == 'payload#1')
        
    def testMessagePayloadTypes(self):
        m = self.builder.createMessage(message.NodeMessage, payload=1)
        
        self.assertTrue(m.payload == 1)
        m.payload = float(1.0)
        
        self.assertTrue(m.payload == 1.0)
        
        m.payload = ['1','2','3']
        self.assertTrue(m.payload == ['1', '2', '3'])
        
        m.payload = (1, 2, 3)
        self.assertTrue(m.payload == (1,2,3))
        
        m.payload = {'key': 'value'}
        self.assertTrue(m.payload == {'key': 'value'})
        
    def testMessageDeliveryMode(self):
        m = self.builder.createMessage(message.NodeMessage)
        
        self.assertTrue(m._delivery_mode in ['all', 'direct'])
        
    def testCustomMessage(self):
        class TMsg(message.NodeMessage):
            def __init__(self):
                message.Attribute('field1')
                message.Attribute('field2', 'value2')
                
        m = self.builder.createMessage(TMsg, field1='value1')
            
        self.assertTrue(m.field1 == 'value1')
        self.assertTrue(m.field2 == 'value2')
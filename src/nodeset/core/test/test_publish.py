#from twisted.trial import unittest
from twisted.python import log
from twisted.internet import defer

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

        def _err(failure):
            print failure
            
        d = self.node.dqueue.get()
        d.addCallback(self.checkReceivedData, 'event_name', 'payload', 'test-publish').addErrback(_err)
        
        self.node.publish('event_name', msgClass=TestMessage, payload='test-publish')
        
        return d
    
    def dynCheckReceivedData(self, msg, evname, fieldname, fieldval):
        v = getattr(msg, fieldname)
        
        self.assertTrue(v != None)
        self.assertEqual(v, fieldval)
        
    def testPublishWithDynEvents(self):
        class TMsg(message.NodeMessage):
            
            def __init__(self):
                message.NodeMessage.__init__(self)
                message.Attribute('param')
        
        defers = []
        
        sub_defs = []
        for evname in ['event_one', 'event_two', 'event_three']:
            d = defer.Deferred()
            d.addCallback(self.dynCheckReceivedData, evname, 'param', evname)
            
            ds = self.dynnode.subscribe_t(evname, d)
            sub_defs.append(ds)
            defers.append(d)
         
        self.dynnode.publish('event_one', TMsg, param='event_one')
        self.dynnode.publish('event_two', TMsg, param='event_two')
        self.dynnode.publish('event_three', TMsg, param='event_three')
           
        return defer.DeferredList(defers)
    
    def testPublishWithCustomMessage(self):
        class TMsg(message.NodeMessage):
            
            def __init__(self):
                message.NodeMessage.__init__(self)
                message.Attribute('custom_field')
        
        d = self.node.dqueue.get()        
        self.node.publish('event_name', TMsg, custom_field='custom')
        
        d.addCallback(self.checkReceivedData, 'event_name', 'custom_field', 'custom')
        
        return d

   
    
        
        
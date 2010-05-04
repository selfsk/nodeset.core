from nodeset.core import node
from nodeset.common import log

from twisted.trial import unittest
from twisted.internet import defer

from common import NodeTestCase

class TStreamNode(node.StreamNode):
    def onStream(self, data, formatter):
        self.formatter = formatter
        self.data = data
        

class StreamNodeTestCase(NodeTestCase):
    
    def setUp(self):
        NodeTestCase.setUp(self)
        self.sender = TStreamNode(port=6111)
        self.receiver = TStreamNode(port=6112)
        
        d = [] 
        d.append(self.receiver.start().addCallback(lambda _: self.receiver.subscribe('stream_name')))
        d.append(self.sender.start())
        
        self.receiver.startService()
        self.sender.startService()
        
        return defer.DeferredList(d)
    
    def tearDown(self):
        NodeTestCase.tearDown(self)
        
        self.sender.stopService()
        self.receiver.stopService()
        
        
    def testStreamNode(self):
        #import twisted
        #twisted.internet.base.DelayedCall.debug = True
        
        dl = []
        d = defer.Deferred()
        d.addCallback(lambda _: None)
        def checkStreamData(push_ret):
            log.msg("%s" % push_ret)
            self.assertTrue(self.receiver.formatter.decode(self.receiver.data) == 'data_packet#1')
            
            d.callback(None)
            
        def gotStream(stream):
            stream.push('data_packet#1').addCallback(checkStreamData)
        
        d2 = self.sender.stream('stream_name').addCallback(gotStream)
        dl.append(d2)
        dl.append(d)
        
        return defer.DeferredList(dl)
    

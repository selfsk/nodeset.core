from nodeset.core import node

from twisted.internet import defer

from common import NodeTestCase

class TStreamNode(node.StreamNode):
    def onStream(self, data, formatter):
        self.formatter = formatter
        self.data = data
        

class StreamNodeTestCase(NodeTestCase):
    
    def skip(self):
        return "Stream interface is not defined yet"
    
    def setUp(self):
        NodeTestCase.setUp(self)
        self.sender = TStreamNode(port=6111)
        self.receiver = TStreamNode(port=6112)
        
        #d = []
        d1 = self.receiver.start()
        d1.addCallback(lambda n: n.subscribe('stream_name'))
        d2 = self.sender.start()
        d2.addCallback(lambda _: None)
        
        #d.append(d1)
        #d.append(d2)
        
        self.receiver.startService()
        self.sender.startService()
        
        return defer.DeferredList([d1, d2])
    
    def tearDown(self):
        NodeTestCase.tearDown(self)
        
        self.receiver.stopService()
        self.sender.stopService()
        
        
        
    def testStreamNode(self):
        def checkStreamData(push_ret, rcv):
            print push_ret
            print rcv.formatter.decode(rcv.data)
            #self.failUnlessTrue(self.receiver.formatter.decode(self.receiver.data) == 'data_packet#1')
            
            
        def gotStream(stream):
            return stream.push('data_packet#1')
        
        d2 = self.sender.stream('stream_name').addCallback(gotStream).addCallback(checkStreamData, self.receiver).addCallback(lambda _: None)
        
        return d2
        #dl.append(d2)
        #dl.append(d)
        
        #self.fail
        #return defer.DeferredList(dl)
    

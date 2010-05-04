from nodeset.core import node, routing, interfaces, heartbeat

from twisted.trial import unittest
from zope.interface import verify

class InterfacesTest(unittest.TestCase):
    
    def testNodeIface(self):
        self.assertTrue(verify.verifyClass(interfaces.INode, node.Node, 1))
        
    def testStreamNodeIface(self):
        self.assertTrue(verify.verifyClass(interfaces.IStreamNode, node.StreamNode))
        self.assertTrue(verify.verifyClass(interfaces.INode, node.StreamNode))
        
    def testNodeCollectionIface(self):
        self.assertTrue(verify.verifyClass(interfaces.INodeCollection, node.NodeCollection))
        
    def testRouteEntryIface(self):
        self.assertTrue(verify.verifyClass(interfaces.IRouteEntry, routing.RouteEntry))
        self.assertTrue(verify.verifyClass(interfaces.IRouteEntry, routing.LocalRouteEntry))
        self.assertTrue(verify.verifyClass(interfaces.IRouteEntry, routing.RemoteRouteEntry))
        
    def testNodeMonitorIface(self):
        self.assertTrue(verify.verifyClass(interfaces.INodeMonitor, heartbeat.NodeMonitor))
        
    def testNodeHeartBeatIface(self):
        self.assertTrue(verify.verifyClass(interfaces.INodeHeartBeat, heartbeat.NodeHeartBeat))
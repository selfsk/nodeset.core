from common import NodeTestCase, TestNode

class Node(NodeTestCase):
    
    def setUp(self):
        self.node = TestNode(port=4311, name='test-node', dispatcher_url='pbu://localhost:5333/dispatcher')
        
    def testName(self):
        self.assertEqual(self.node.name, 'test-node')
        
    def testPort(self):
        self.assertEqual(self.node.port, 4311)
        
    def testDispatcherURL(self):
        self.assertEqual(self.node.dispatcher_url, 'pbu://localhost:5333/dispatcher')

    def tearDown(self):
        pass
        
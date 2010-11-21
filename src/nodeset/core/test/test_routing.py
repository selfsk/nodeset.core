from twisted.trial import unittest

from nodeset.core import routing, dispatcher, config

class RoutingTest(unittest.TestCase):
    
    def setUp(self):
        c = config.Configurator()
        c._config = {'dispatcher-url': 'pbu://localhost:5333/dispatcher',
                     'listen': 'pbu://localhost:5333/dispatcher',
                     'dht-nodes': None,
                     'dht-port': None, 
                     'verbose': None}
       
        c.subCommand = None
         
        self.dispatcher = dispatcher.EventDispatcher()
        self.dispatcher.startService()
       
        #self.node = TestNode(5111)
        
        #d = self.node.start().addCallback(lambda _: self.node.subscribe('event_name'))
        #self.node.startService()

        self.routing = self.dispatcher.routing
        
    def tearDown(self):
        
        return self.dispatcher.stopService()

    def testRREntryDuplicate(self):
        entry = routing.RREntrySet()
        
        entry.add(1)
        entry.add(2)
        entry.add(3)
        
        self.failUnlessRaises(IndexError, entry.add, 1)
        self.failUnlessRaises(IndexError, entry.add, 2)
        self.failUnlessRaises(IndexError, entry.add, 3)
        
    def testRREntryIter(self):
        entry = routing.RREntrySet([1,2,3,4])
        
        start = 12
        
        for i in range(start, 0, -1):
            v = entry[0]

            # when i % len(entry) and i > 1, we already goes through all of entryset
            # now start from 4, instead of 8
            if (start - i) != 0 and i % len(entry) == 0:
                start -= len(entry)
            
            self.assertEqual(v, (start - i + 1))
            
            entry.order()
            
    def testRREntryRemove(self):
        entry = routing.RREntrySet([1,2,3,4])
        
        entry.remove(4)
        
        self.failUnlessRaises(ValueError, entry.index, 4)
        
    def testRoutingAddLocal(self):
        self.routing.add('event_name', None)
        
        self.assertTrue(len(self.routing.get('event_name')) == 1)
        
    def testRoutingAddInvalidAddressing(self):
        self.failUnlessRaises(Exception, self.routing.add, 'node@host')
        
    #def testRoutingAddRemote(self):
    #    self.node = node.Node(name='node_name') 
    #    self.routing.add('event_name', self.node, self.node.name)
    #
    #    self.assertTrue(len(self.routing.get('node_name@host/event_name')) == 1)
        
    def testRoutingRemoveLocal(self):
        self.testRoutingAddLocal()
        self.routing.remove('event_name', None)
        
        def _cb(entries, length):
            self.assertTrue(len(entries) == length)
        
        self.routing.get('event_name')[0].addCallback(_cb, 0)
        
        #self.assertTrue(len(self.routing.get('event_name')) == 0)
        
    #def testRoutingRemoveRemote(self):
    #    self.testRoutingAddRemote()
    #    self.routing.remove('node_name@host/event_name', self.node)
    #    
    #    self.assertTrue(len(self.routing.get('node_name@host/event_name')) == 0)
        
    def testRoutingMultiple(self):
        self.routing.add('event_name1', None)
        self.routing.add('event_name2', None)
        self.routing.add('event_name3', None)
        
        self.routing.remove('event_name1', None)
        
        def _cb(entries, length):
            self.assertTrue(len(entries) == length)
        
        self.routing.get('event_name2')[0].addCallback(_cb, 1)
        self.routing.get('event_name3')[0].addCallback(_cb, 1)
        self.routing.get('event_name1')[0].addCallback(_cb, 0)
           
        #self.assertTrue(len(self.routing.get('event_name2')) == 1)
        #self.assertTrue(len(self.routing.get('event_name3')) == 1)
        #self.assertTrue(len(self.routing.get('event_name1')) == 0)
        
    def testRoutingAddDupilcate(self):
        self.routing.add('event_name1', None)
        dl = self.routing.add('event_name1', None)
        
        self.failUnlessFailure(dl[0], IndexError)
        #self.failUnlessRaises(IndexError, self.routing.add, 'event_name1', None)

    #def testRoutingAddDuplicateRemote(self):
    #    n = node.Node(name='node_name')
    #    self.routing.add('node_name@host_name/event_name', n)
        
    #    self.failUnlessRaises(IndexError, self.routing.add, 'node_name@host_name/event_name', n)
        
        
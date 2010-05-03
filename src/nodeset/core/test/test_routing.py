from twisted.trial import unittest

from nodeset.core import routing, node

class RoutingTest(unittest.TestCase):
    
    def setUp(self):
        self.routing = routing.RoutingTable()
        
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
        
    def testRoutingAddRemote(self):
        self.node = node.Node(name='node_name') 
        self.routing.add('node_name@host/event_name', self.node)

        self.assertTrue(len(self.routing.get('node_name@host/event_name')) == 1)
        
    def testRoutingRemoveLocal(self):
        self.testRoutingAddLocal()
        self.routing.remove('event_name', None)
        
        self.assertTrue(len(self.routing.get('event_name')) == 0)
        
    def testRoutingRemoveRemote(self):
        self.testRoutingAddRemote()
        self.routing.remove('node_name@host/event_name', self.node)
        
        self.assertTrue(len(self.routing.get('node_name@host/event_name')) == 0)
        
    def testRoutingMultiple(self):
        self.routing.add('event_name1', None)
        self.routing.add('event_name2', None)
        self.routing.add('event_name3', None)
        
        self.routing.remove('event_name1', None)
        
        self.assertTrue(len(self.routing.get('event_name2')) == 1)
        self.assertTrue(len(self.routing.get('event_name3')) == 1)
        self.assertTrue(len(self.routing.get('event_name1')) == 0)
        
    def testRoutingAddDupilcate(self):
        self.routing.add('event_name1', None)
        self.failUnlessRaises(IndexError, self.routing.add, 'event_name1', None)

    def testRoutingAddDuplicateRemote(self):
        n = node.Node(name='node_name')
        self.routing.add('node_name@host_name/event_name', n)
        
        self.failUnlessRaises(IndexError, self.routing.add, 'node_name@host_name/event_name', n)
        
        
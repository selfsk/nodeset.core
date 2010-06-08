from twisted.trial import unittest
from nodeset.core.stats import metric, types

class MetricStoreTest(unittest.TestCase):
    
    def setUp(self):
        self.m = metric.Metric('counter1', types.Counter)
        
    def test_StoreGet(self):
        self.m.update()
        
        self.assertTrue(self.m.get() == 1)
        
        om = metric.Store.get('counter1')
        
        self.assertTrue(om.get() == 1)
        
    def test_StoreUpdate(self):
        om = metric.Store.get('counter1')
        om.update()
        
        #om is the same as self.m
        self.assertTrue(self.m.get() == 1)
        
        
    def test_StoreMetric(self):
        om = metric.Store.get('counter1')
        self.assertTrue(self.m == om)
        

        
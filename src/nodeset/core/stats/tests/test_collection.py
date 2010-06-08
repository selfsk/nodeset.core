from twisted.trial import unittest

from nodeset.core.stats import metric, types, format

class TestMetricCollection(unittest.TestCase):
    
    def setUp(self):
        self.c = metric.MetricCollection(format.Dict())
        
        self.c.add(metric.Metric('counter1', types.Counter))
        self.c.add(metric.Metric('counter2', types.Counter))
        
    def test_CollectionUpdate(self):
        
        c2 = metric.Store.get('counter2')
        c2.update()
        
        self.assertTrue(self.c.get()['counter2'] == 1)
        
    def test_CollectionMetricRemove(self):

        c2 = metric.Store.get('counter2')
        
        self.c.remove(c2)
        
        self.assertFalse(self.c.get().has_key('counter2'))
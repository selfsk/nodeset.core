from twisted.trial import unittest
from nodeset.core.stats import metric, types

class MetricTypesTest(unittest.TestCase):
    
    def test_Counter(self):
        c = metric.Metric('counter', types.Counter)
        c.update()
        
        self.assertTrue(c.get() == 1)
        
        c.update()
        self.assertTrue(c.get() == 2)
        
        c.update()
        self.assertTrue(c.get() == 3)
        
    def test_Absolute(self):
        m = metric.Metric('abs', types.Absolute)
        
        m.update()
        m.update()
        
        self.assertTrue(m.get() == 2)
        self.assertTrue(m.get() == 0)
        
    def test_Gauge(self):
        m = metric.Metric('gauge', types.Gauge)
        
        m.update()
        
        self.assertTrue(m.get() == 0.0)
        
        m.update(15.4)
        self.assertTrue(m.get() == 15.4)
        
    def test_Derive(self):
        m = metric.Metric('derive', types.Derive)
        
        m.update()
        self.assertTrue(m.get() == 1)
        m.update()
        self.assertTrue(m.get() == 2)
        
        m.update(1231)
        self.assertTrue(m.get() == 3)
         
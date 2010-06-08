from twisted.trial import unittest

from nodeset.core.stats import metric, types, format

import simplejson

class TestMetricFormat(unittest.TestCase):
    
    def setUp(self):
        self.c = metric.MetricCollection()
        self.c.add(metric.Metric('counter1', types.Counter))
        self.c.add(metric.Metric('counter2', types.Counter))
        self.c.add(metric.Metric('gauge1', types.Gauge))
        
    def test_DictFormat(self):
        self.c.formatter = format.Dict()
        
        self.assertTrue('counter1' in self.c.get().keys())
        self.assertTrue('counter2' in self.c.get().keys())
        self.assertTrue('gauge1' in self.c.get().keys())
        
    def test_JsonFormat(self):
        self.c.formatter = format.Json()
        
        self.assertTrue(isinstance(self.c.get(), str))
        
        d = simplejson.loads(self.c.get())
        
        self.assertTrue(d['counter1'] == 0)
        self.assertTrue(d['counter2'] == 0)
        self.assertTrue(d['gauge1'] == 0.0)

        
        
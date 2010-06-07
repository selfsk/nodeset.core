"""
Metric API for Nodes
"""

from nodeset.core.stats import types

class MetricStore:
    """
    Global table of metrics, should be available everywhere
    """
    
    def __init__(self):
        self.__metrics = {}
        
    def add(self, metric):
        self.__metrics[metric.name] = metric
    
    def get(self, name):
        return self.__metrics[name]
       
try: 
    Store
except NameError, e:
    Store = MetricStore()

class Metric:
    """
    Base class for metrics
    """
    
    def __init__(self, name, mtype):
        self.name = name
        self.mtype = mtype
        self.data = self.mtype()
        
        Store.add(self)
        
    def update(self, value=0):
        """
        How to update metric
        """
        if isinstance(self.data, types.Gauge):
            self.data = self.mtype(value)
        else:
            # other types could be only increased
            self.data += 1
    
    def get(self):
        if isinstance(self.data, types.Absolute):
            v = self.data
            self.data = self.mtype()
            
            return v
        else:
            return self.data
        
    
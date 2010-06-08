"""
Metric API for Nodes
"""

from nodeset.core.stats import types, format

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
        
class MetricCollection:
    
    def __init__(self, formatter=None):
        self.__metrics = set()
        
        if not formatter:
            self.fmt = format.Base()
        else:
            self.fmt = formatter
    
    def _get_fmt(self):
        return self.fmt
    def _set_fmt(self, fmt):
        self.fmt = fmt
                
    formatter = property(_get_fmt, _set_fmt)
    
    def add(self, metric):
        self.__metrics.add(metric)
    
    def remove(self, metric):
        self.__metrics.remove(metric)
        
    def get(self):
        return self.formatter.get(self.__metrics)
    
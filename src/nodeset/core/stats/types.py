"""
Metric types, similar to RRD's
"""

class Base:
    
    def returnValue(self, klass, obj):
        if not isinstance(obj, klass):
            obj = klass(obj)
            
        return obj
        
class Counter(Base, long):
    def __add__(self, obj):
        return Counter(long(self).__add__(self.returnValue(Counter, obj)))

    def __sub__(self, obj):
        raise Exception("Not permitted")
    
class Gauge(Base, float):
    def __add__(self, obj):
        return Gauge(float(self).__add__(self.returnValue(Gauge, obj)))
    
    def __sub__(self, obj):
        return Gauge(float(self).__sub__(self.returnValue(Gauge, obj)))

class Absolute(Counter, long):
    
    def __add__(self, obj):
        return Absolute(long(self).__add__(self.returnValue(Absolute, obj)))
    
class Derive(Counter):
    pass
"""
Common classes for benchmark suite
"""

import simplejson
import time

import pprint

class Message:
    
    def __init__(self, **kwargs):
        self.attrs = {}

        self._setattrs(kwargs)
        
    def _setattrs(self, attrs):
        for k,v in attrs.items():
            self.attrs[k] = v
            
            
    def toString(self):
        return str(simplejson.dumps(self.attrs))
    
    def fromString(self, str):
        obj = simplejson.loads(str)
        
        self._setattrs(obj)
        
        
class Stats:
    
    def __init__(self):
        self._stats = {'msgcount': 0,
                       'latency': {'min': 0.0, 'max': 0.0, 'avg': 0.0},
                       'stime': None,
                       'etime': None}
        
        
    def start(self):
        self._stats['msgcount'] = 0
        self._stats['stime'] = time.time()
        
    def stop(self):
        self._stats['etime'] = time.time()
        
    def msgcount(self):
        self._stats['msgcount'] += 1
        
    def _update(self, what, msgcount, cur, val):
        if what == 'max':
            return max([cur, val])
        elif what == 'min':
            if cur == 0.0:
                return val
            
            return min([cur, val])
        elif what == 'avg':
            return (cur + val) / float(msgcount)
            
        else:
            return cur
        
    def updateLatency(self, val):
        cnt = self._stats['msgcount']
        
        for l,v in self._stats['latency'].items():
            self._stats['latency'][l] = self._update(l, cnt, v, val)
       
    def __str__(self):
        return str(pprint.pprint(self._stats))
     
        
        
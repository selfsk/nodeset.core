from twisted.internet import defer

from nodeset.common import log
from nodeset.core import config
 
class Observer(object):
    
    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        
        #print "-- %s, %s" % (self.args, self.kwargs)
        self.assertfunc = lambda x: True
        
    def setAssert(self, assertfunc):
        self.assertfunc = assertfunc
        
    def run(self, *args, **kwargs):
        a = tuple(list(args) + list(self.args))
        kw = dict(kwargs.items() + self.kwargs.items())
        
        return self.callable(*a, **kw)
        
        
class ObserverCarousel(object):
    
    def twist(self, observers, eventDict): 
        defers = []

        if config.Configurator['verbose']:
            log.msg("twist carousel %s, %s" % (observers, eventDict))
                
        for i in observers:
            defers.append(defer.maybeDeferred(i.run, eventDict))
                     
        return defers

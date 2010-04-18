from foolscap.api import Copyable, RemoteCopy

import sys

class Attribute:
    """
    Helper class to define Message attributes, to make easy for foolscap to build Copyable objects
    """
    
    def __init__(self, name):
        
        f = sys._getframe(1)
        
        msg = f.f_locals['self']
        msg._attrs[name] = self
            
        self.name = name
        self.value = None

        
class NodeMessage(Copyable, RemoteCopy):
    """
    Base class for NodeSet messages
    """
    
    typeToCopy = copytype = 'node-message-0xdeadbeaf'
    
    """
    @ivar _attrs: dict of message attributes
    """
    _attrs = {}
    
    def __init__(self):
        Attribute('name')
        Attribute('payload')
        
    def __getattr__(self, name):
        if self._attrs.has_key(name):
            return self._attrs[name].value
        
        return self.__dict__[name]
        
    def __setattr__(self, name, value):
        if self._attrs.has_key(name):
            self._attrs[name].value = value
            
        elif self.__dict__.has_key(name):
            self.__dict__[name] = value
            
        else:
            raise KeyError("Class %s has no property %s" % (self, name))
            
    def getStateToCopy(self):
        d = {}
        for k, v in self._attrs.items():
            d[v.name] = v.value

        return d

    def setCopyableState(self, state):
        for k,v in state.items():
            item = Attribute(k)
            item.value = v
            
    
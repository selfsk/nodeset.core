from foolscap.api import Copyable, RemoteCopy

import sys

class Attribute:
    """
    Helper class to define Message attributes, to make easy for foolscap to build Copyable objects
    """
    
    def __init__(self, name, value=None):
        try:
            f = sys._getframe(1)
            
            msg = f.f_locals['self']
            msg.attrs[name] = self
        except KeyError, e:
            pass
        
        self.name = name
        self.value = value

class _Message(Copyable, RemoteCopy):
    typeToCopy = copytype = 'node-message-0xdeadbeaf'
    
    def __init__(self):
        self.attrs = {}
    
    def __getattr__(self, name):
        if self.attrs.has_key(name):
            return self.attrs[name].value
        elif self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            raise KeyError("getattr() - Class %s has no property %s" % (self, name))
        
    def set(self, name, value):
        self.attrs[name].value = value
           
    def getStateToCopy(self):
        d = {}
        for k, v in self.attrs.items():
            d[v.name] = v.value

        return d

    def setCopyableState(self, state):
        for k,v in state.items():
            item = Attribute(k)
            item.value = v
            
class NodeMessage:
    """
    Base class for NodeSet messages
    """
    
    """
    @ivar _attrs: dict of message attributes
    """
    attrs = {'_delivery_mode': Attribute('_delivery_mode', 'all')}
    
    def __init__(self):
        Attribute('payload')
        Attribute('name')
        
    def __getattr__(self, name):
        if self.attrs.has_key(name):
            return self.attrs[name].value
        elif self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            raise KeyError("getattr() - Class %s has no property %s" % (self, name))
        
    def __setattr__(self, name, value):
        if self.attrs.has_key(name):
            Attribute(name, value)
        elif self.__dict__.has_key(name):
            self.__dict__[name] = value
        else:
            raise KeyError("setattr() - Class %s has no property %s" % (self, name))    
        
            
    
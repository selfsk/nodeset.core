"""
Base classes for Messages, provides NodeMessage (base class for message), and Attribute - message attribute descriptor
"""
from foolscap.api import Copyable, RemoteCopy

import sys
import simplejson

class Attribute(object):
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

    def __ne__(self, obj):
        if not isinstance(obj, Attribute):
            value = obj
        else:
            value = obj.value
            
        return self.value != value
    
    
    def __eq__(self, obj):
        if not isinstance(obj, Attribute):
            value = obj
        else:
            value = obj.value
            
        return self.value == value
    
    def __float__(self):
        return float(self.value)
    
    def __repr__(self):
        return repr(self.value)
    
    def __getitem__(self, name):
        return self.value[name]
    
    def __str__(self):
        return str(self.value)
    
    def getValue(self):
        """
        Return value of Attribute
        """
        return self.value
    
class _BaseMessage(object):
    """
    Base class for message: _Message and NodeMessage
    """
    def __init__(self):
        # NodeMessage will call __setattr__ on __init__, self.attrs raise KeyError
        self.__dict__['attrs'] = {}
            
    def set(self, name, value):
        self.attrs[name].value = value
    
    def setAttribute(self, name, value):
        Attribute(name, value)
        
    def toJson(self):
        d = {}
        
        for k,v in self.attrs.items():
            # ignore all hidden fields
            if not k.startswith('_'):
                d[k] = v.getValue()
            
        return simplejson.dumps(d)

    def fromJson(self, json):
        d = simplejson.loads(json)
        for k,v in d.items():
            Attribute(k, v)
    
    
class _Message(_BaseMessage, Copyable, RemoteCopy):
    """
    Foolscap message description, we're trying to wrap any NodeSet message into this one
    """
    typeToCopy = copytype = 'node-message-0xdeadbeaf'
    
    def __getattr__(self, name):
        if self.attrs.has_key(name):
            return self.attrs[name]
        elif self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            raise KeyError("getattr() - Class %s has no property %s" % (self, name))
        

    def getStateToCopy(self):
        d = {}
        for k, v in self.attrs.items():
            d[str(v.name)] = v.value

        return d

    def setCopyableState(self, state):
        for k,v in state.items():
            item = Attribute(k)
            item.value = v

    def __eq__(self, obj):
        for k,v in self.attrs.items():
            try:
                i = getattr(obj, k)
                if i != v:
                    return False
                
            except KeyError, e:
                return False
            
        return True
            
            
class NodeMessage(_BaseMessage):
    """
    Base class for NodeSet messages
    """
    
    """
    @ivar _attrs: dict of message attributes
    """
    #attrs = {'_delivery_mode': Attribute('_delivery_mode', 'all')}
     
    def __init__(self):
        _BaseMessage.__init__(self)
        
        Attribute('_delivery_mode', 'all')
      
    def __str__(self):
        return str(self.__class__)
              
    def __repr__(self):
        return repr(self.__class__)
    
    def __getattr__(self, name):
        if self.__dict__.has_key('attrs') and self.attrs.has_key(name):
            return self.attrs[name]
        elif self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            raise KeyError("getattr() - Class %s has no property %s" % (self, name))
        
    def __setattr__(self, name, value):
        if self.__dict__.has_key('attrs') and self.attrs.has_key(name):
            Attribute(name, value)
        elif self.__dict__.has_key(name):
            self.__dict__[name] = value
        else:
            raise KeyError("setattr() - Class %s has no property %s" % (self, name))    
        
    
    
def _singleton(klass):
    """ singelton creater, can be used as decorator """
    
    if not klass._instance:
        klass._instance = klass()
        
    return klass._instance

class Configurator(object):
    """ Has only one instance all the time, and provides access to twisted usage.Options
    
    @ivar _instance: Configurator instance, will be retruned that one instead of creating
    """
    
    _instance = None
    
    def __call__(self):
        """ return the same instance if we're already configured. executed in case of call Configurator() """
        if not self._instance:
            self._instance = self()
            
        return self._instance
        
    def __init__(self):
        self.__dict__['_config'] = {}
        
    def __getattr__(self, k):
        """ delegate to self._config """
        if hasattr(self._config, k):
            return getattr(self._config, k)
        else:
            return self.__dict__[k]
        
    def __setattr__(self, k, v):
        """ delegate to self._config """
        if hasattr(self._config, k):
            setattr(self._config, k, v)
        else:
            self.__dict__[k] = v
    
    def __getitem__(self, k):
        """ delegate to self._config """ 
        return self._config[k]
    
    def __setitem__(self, k, v):
        """ delegate to self._config """
        self._config[k] = v
        
# to make it work for python v.2.5
Configurator = _singleton(Configurator)
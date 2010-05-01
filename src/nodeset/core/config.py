def _singleton(klass):
    
    if not klass._instance:
        klass._instance = klass()
        
    return klass._instance

@_singleton
class Configurator(object):
    
    _instance = None
    
    def __call__(self):
        """ return the same instance if we're already configured """
        return self._instance
        
    def __init__(self):
        self.__dict__['_config'] = {}
        
    def __getattr__(self, k):
        if hasattr(self._config, k):
            return getattr(self._config, k)
        else:
            return self.__dict__[k]
        
    def __setattr__(self, k, v):
        if hasattr(self._config, k):
            setattr(self._config, k, v)
        else:
            self.__dict__[k] = v
    
    def __getitem__(self, k):
        return self._config[k]
    
    def __setitem__(self, k, v):
        self._config[k] = v
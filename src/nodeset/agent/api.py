class AgentAPI(object):
    
    def __init__(self):
        self._services = {}
        
    def getServices(self):
        return self._services
    
    def getService(self, name):
        return self._services[name]
    
    """ 
    handling of register of agent's services instances
    @param service: agent's service object  
    """
    def register(self, service):
        pass
    
    """ 
    unregister agent's services
    @param service: agent's service object 
    """
    def unregister(self, service):
        pass
    
    
    
    
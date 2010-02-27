class AgentAPI(object):
    
    def __init__(self):
        self._services = {}
        
    def hasService(self, name):
        return name in self._services.keys()
    
    def getServices(self):
        return self._services
    
    def getService(self, name):
        return self._services[name]
    
    """ 
    handling of register of agent's services instances
    @param service: agent's service object  
    """
    def register(self, service):
        print "registering service %s" % dir(service)
        self._services[service.name] = service
    
    """ 
    unregister agent's services
    @param service: agent's service object 
    """
    def unregister(self, service):
        del self._service[service.name]
    
    
    
    
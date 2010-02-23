from foolscap.api import Referenceable
from nodeset.agent.api import AgentAPI

class ApiProxy(Referenceable):
    
    def __init__(self):
        self.agent_api = AgentAPI()
        
    def remote_getList(self):
        return self.agent_api.getServices()
    
    def remote_getItem(self, name):
        return self.agent_api.getService(name)
    
    def remote_registerService(self, item):
        self.agent_api.register(item)
        
    def remote_unregisterService(self, item):
        self.agent_api.unregister(item)
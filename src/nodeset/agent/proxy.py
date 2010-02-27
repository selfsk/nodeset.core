from foolscap.api import Referenceable, RemoteCopy
from nodeset.agent.api import AgentAPI

import random

class ApiProxy(Referenceable):
    
    def __init__(self):
        self.agent_api = AgentAPI()
        
    def remote_getRandomPortFor(self, name):
        if self.agent_api.hasService(name):
            raise Exception("Such service(%s) already running" % name)
        else:
            # TODO: do check for random port somehow
            return random.randint(32678, 65353)
    
    def remote_getList(self):
        return self.agent_api.getServices()
    
    def remote_getItem(self, name):
        return self.agent_api.getService(name)
    
    def remote_registerService(self, item):
        self.agent_api.register(item)
        
    def remote_unregisterService(self, item):
        self.agent_api.unregister(item)
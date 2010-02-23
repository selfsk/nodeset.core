from foolscap.api import Tub

class AgentService:
    
    def __init__(self, name):
        self.name = name
        # get Tub for foolscap calls
        self.tub = Tub()
        
    """ start service instance and register it to agent through foolscap RPC
    
    @return: IService 
    """
    def serviceStart(self):
        pass
    
    def serviceStop(self):
        pass
    
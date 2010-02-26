
import api
import proxy

from foolscap.api import Tub
from twisted.application import service

from proxy import ApiProxy
from nodeset.common.twistedapi import run

class AgentInstance(object):
    
    def __init__(self, config):
        pass

def run_agent():
    tub = Tub()
    tub.listenOn('tcp:5333')
    tub.setLocation('localhost:5333')
    tub.registerReference(ApiProxy(), 'api')
    tub.registerReference(AgentInstance, 'agent')
    
    application = service.Application("nodeset-agent")
    tub.setServiceParent(application)

    
    return run(application)



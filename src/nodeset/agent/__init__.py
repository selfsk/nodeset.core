
import api
import proxy

from foolscap.api import UnauthenticatedTub
from twisted.application import service as ts

from proxy import ApiProxy
from nodeset.common.twistedapi import run
from nodeset.agent.service import AgentService

class AgentInstance(object):
    
    def __init__(self, config):
        pass

def run_agent():
    tub = UnauthenticatedTub()
    tub.listenOn('tcp:5333')
    tub.setLocation('localhost:5333')

    url = tub.registerReference(ApiProxy(), 'api')
    print "FURL %s" % url
    url = tub.registerReference(AgentInstance, 'agent')
    print "FURL 2 %s" % url
    application = ts.Application("nodeset-agent")
    tub.setServiceParent(application)

    
    return run(application)


def run_service():
    s = AgentService('simple_service')
    
    
    application = ts.Application('nodeset-service')
    s.tub.setServiceParent(application)
    
    return run(application)
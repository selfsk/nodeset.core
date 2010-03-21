
import api
import proxy

from foolscap.api import UnauthenticatedTub, Tub
from twisted.application import service as ts
from twisted.internet import reactor

from proxy import ApiProxy
from nodeset.common.twistedapi import run
from nodeset.agent.service import AgentService

from nodeset.core import node


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
    tub = Tub()
    s = AgentService('simple_service', tub)
    application = ts.Application('nodeset-service')
    s.tub.setServiceParent(application)
    
    return run(application)

def run_dispatcher():
    d = node.EventDispatcher()
    application = ts.Application('nodeset-dispatcher')
    d.tub.setServiceParent(application)
    
    return run(application)

def run_node():
    n = node.Node(5334)
    application = ts.Application('nodeset-node')
    n.tub.setServiceParent(application)
    n.start()
    reactor.callLater(1, n.subscribe, 'simple_event')
    return run(application)

def run_node1():
    n = node.Node(5335)
    application = ts.Application('nodeset-node')
    n.tub.setServiceParent(application)   
    ev = node.NodeEventBuilder().createEvent('simple_event', 'hello world')
    n.start()
    reactor.callLater(3, n.publish, ev)
    return run(application)

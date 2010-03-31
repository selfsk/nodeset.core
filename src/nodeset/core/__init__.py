from twisted.application import service as ts
from twisted.internet import reactor

from nodeset.common.twistedapi import run
from nodeset.core import node, dispatcher

def run_dispatcher():
    d = dispatcher.EventDispatcher()
    application = ts.Application('nodeset-dispatcher')
    d.tub.setServiceParent(application)
    
    return run(application)

def run_node_sub():
    n = node.Node(5334)
    application = ts.Application('nodeset-node-subscriber')

    n.start()
    reactor.callLater(1, n.subscribe, 'simple_event')
    n.tub.setServiceParent(application)
    
    return run(application)

def run_node_pub():
    n = node.Node(5335)
    application = ts.Application('nodeset-node-publisher')
    n.start()
    
    n.tub.setServiceParent(application)   
    ev = node.NodeEventBuilder().createEvent('simple_event', 'hello world')
    
    reactor.callLater(3, n.publish, ev)

    return run(application)

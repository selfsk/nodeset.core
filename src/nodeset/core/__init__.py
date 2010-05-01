from twisted.application import service as ts
from twisted.internet import reactor
from twisted.python import usage

from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.core import node, dispatcher, slicers

class DispatcherOptions(NodeSetAppOptions):
    
    optParameters = [
                     ['heartbeat', None, None, 'heartbeat period', int]
                     ]
    
def run_dispatcher():
    
    config = DispatcherOptions()
    application = ts.Application('nodeset-dispatcher')
    
    try:
        config.parseOptions()
        
        d = dispatcher.EventDispatcher(config['dispatcher-url'])
        d.setServiceParent(application)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)
    
def run_node_sub():
    n = node.Node(5334)
    application = ts.Application('nodeset-node-subscriber')

    
    def _print(e, m):
        print m
        
    n.onEvent = _print
    
    n.start()
    reactor.callLater(1, n.subscribe, 'simple_event')
    n.setServiceParent(application)
    
    return run(application)

def run_node_pub():
    n = node.Node(5335)
    application = ts.Application('nodeset-node-publisher')
    n.start()

    
    n.setServiceParent(application)   
    reactor.callLater(3, n.publish, 'simple_event', payload='hello world')

    return run(application)

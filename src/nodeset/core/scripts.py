from twisted.application import service as ts
from twisted.internet import reactor
from twisted.python import usage
from twisted.python.log import ILogObserver

from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.common import log
from nodeset.core import node, dispatcher, slicers

class DispatcherOptions(NodeSetAppOptions):
    
    optParameters = [
                     ['dht-port', None, 4000, 'DHT listen port', int],
                     ['dht-nodes', None, None, 'known nodes addresses (ip:port,ip2:port)']
                     ]
    
import os
def run_dispatcher():
    
    config = DispatcherOptions()
    application = ts.Application('nodeset-dispatcher')
    
    
    try:
        config.parseOptions()
        
        d = dispatcher.EventDispatcher(config['listen'])
        d.setServiceParent(application)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)
    
def run_node_sub():
    n = node.Node(5334, name='simple-subscriber')
    application = ts.Application('nodeset-node-subscriber')

    
    def _print(e, m):
        print m
        
    n.onEvent = _print
    
    n.start()
    reactor.callLater(1, n.subscribe, '%s@%s/simple_event' % (n.name, n.host))
    n.setServiceParent(application)
    
    return run(application)

def run_node_pub():
    n = node.Node(5335)
    application = ts.Application('nodeset-node-publisher')
    n.start()

    
    n.setServiceParent(application)   
    reactor.callLater(3, n.publish, 'simple_event', payload='hello world')

    return run(application)

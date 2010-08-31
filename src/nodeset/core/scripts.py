from twisted.application import service as ts, internet
from twisted.internet import reactor
from twisted.python import usage


from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.core import node, dispatcher

class DispatcherOptions(NodeSetAppOptions):
    
    optParameters = [
                     ['dht-port', None, 4000, 'DHT listen port', int],
                     ['dht-nodes', None, None, 'known nodes addresses (ip:port,ip2:port)'],
                     ['listen', None, 'pbu://localhost:5333/dispatcher', 'dispatcher listen FURL']
                     ]
  
def run_shell():
    from twisted.manhole.telnet import ShellFactory
    
    application = ts.Application('nodeset-shell')
    n = node.ShellNode()
    n.setServiceParent(application)
    
    
    sfactory = ShellFactory()
    #sfactory.namespace['node'] = n
    #sfactory.namespace['service'] = application
    
    n.setShell(sfactory)
        
    shell = internet.TCPServer(10331, sfactory)
    shell.setServiceParent(application)
    
    run(application)
      
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
    n = node.Node(5335, name='simple-subscriber1')
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

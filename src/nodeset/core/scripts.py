from twisted.application import service as ts, internet
from twisted.internet import reactor
from twisted.python import usage


from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.core import node, dispatcher

from nodeset.core import web
from twisted.web import static, server, script

class DispatcherXmppOptions(usage.Options):
    
    optParameters = [
                     ['jidname', None, None, 'host name or any name suitable for JID <user> part'],
                     ['passwd', None, None, 'password'],
                     ['server', None, None, 'XMPP server address'],
                     ['fqdn', None, None, 'XMPP host part, default xmpp-server value'],
                     ['pubsub', None, None, 'pubsub service name']
                     ] 
    
class DispatcherOptions(NodeSetAppOptions):
    
    subCommands = [
                    ['xmpp', None, DispatcherXmppOptions, 'xmpp pubsub, required for inter-host communication']
                    ]
    
    optParameters = [
                     ['listen', None, 'pbu://localhost:5333/dispatcher', 'dispatcher listen FURL'],
                  
                     ]


class WebBridgeOptions(usage.Options):
    
    optParameters = [
                     ['path', None,'/var/www/rpy', '.rpy files path'],
                     ['port', None, 8080, 'web listen port', int]
                     ] 

class WebNodeOptions(NodeSetAppOptions):
    subCommands = [['web', None, WebBridgeOptions, 'web bridge options']]
    
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
    n.start().addCallback(lambda _: n.publish('simple_event', payload='helloworld_xyz'))

    
    n.setServiceParent(application)   


    return run(application)

def run_web_node():
    
    config = WebNodeOptions()
    application = ts.Application('nodeset-web-node')
    #sc = ts.IServiceCollection(application)
      
    try:
        config.parseOptions()

        n = web.WebBridgeNode()
        n.setServiceParent(application)
     
        n.start()
        root = static.File(config.subOptions['path'])
        root.ignoreExt(".rpy")
        root.processors = {'.rpy': script.ResourceScript}
        
        site = web.NodeSetSite(root, n)

        webservice = internet.TCPServer(config.subOptions['port'], site)
        webservice.setServiceParent(application)
        
        #d = dispatcher.EventDispatcher(config['listen'])
        #d.setServiceParent(application)
    except usage.error, ue:
        #print config
        print ue
    else:
        runApp(config, application)
    
    #n.start()
    #n.setServiceParent(Application)
    
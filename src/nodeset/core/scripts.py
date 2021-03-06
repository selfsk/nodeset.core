from twisted.application import service as ts, internet
from twisted.python import usage


from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.common import log
import logging

class PubSubOptions(usage.Options):
    optParameters = [
                     ['event', None, 'simple_event', 'eventURI'],
                     ['payload', None, None, 'event payload (for publishing)']
                     ]
    
    
class ExampleNodeOptions(NodeSetAppOptions):
    
    subCommands = [
                   ['subscriber', None, PubSubOptions, 'subscriber options'],
                   ['publisher', None, PubSubOptions, 'publisher options']
                   ]
    
class DispatcherXmppOptions(usage.Options):
    
    optParameters = [
                     ['jidname', None, None, 'host name or any name suitable for JID <user> part'],
                     ['passwd', None, None, 'password'],
                     ['server', None, None, 'XMPP server address'],
                     ['fqdn', None, None, 'XMPP host part, default xmpp-server value'],
                     ['pubsub', None, None, 'pubsub service name'],
                     ['port', None, 5222, "XMPP server's port"]
                     ] 
    
class DispatcherOptions(NodeSetAppOptions):
    
    subCommands = [
                    ['xmpp', None, DispatcherXmppOptions, 'xmpp pubsub, required for inter-host communication']
                    ]
    
    optFlags = [['verbose', None, 'enable verbose logging']]
    
    optParameters = [
                     ['listen', None, 'pbu://localhost:5333/dispatcher', 'dispatcher listen FURL'],
                     
                     ]


class WebBridgeOptions(usage.Options):
    
    optParameters = [
                     ['path', None,'/var/www/rpy', '.rpy files path'],
                     ['port', None, 8080, 'web listen port', int],
                     ['logfile', None, 'nodeset-web.log', 'HTTP requests logfile']
                     ] 

class WebNodeOptions(NodeSetAppOptions):
    subCommands = [['web', None, WebBridgeOptions, 'web bridge options']]
   
def run_shell():
    from twisted.manhole.telnet import ShellFactory
    from nodeset.core import node
    
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

        from nodeset.core import dispatcher
        
        d = dispatcher.EventDispatcher(config['listen'])
        d.setServiceParent(application)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)


   
def run_example_node():
    
    application = ts.Application('nodeset-node')
    config = ExampleNodeOptions()
    
    try:
        config.parseOptions()
        
        from nodeset.core import node, message
   
        class CustomMessage(message.NodeMessage):
            
            def __init__(self):
                message.NodeMessage.__init__(self)
                message.Attribute('payload')
                 
        n = node.Node(name='simple-%s' % config.subCommand)
        
        if config.subCommand == 'subscriber':
            # subscriber node
            def _print(e, m):
                log.msg("Message arrived")
                log.msg("JSON: %s" % m.toJson(), logLevel=logging.DEBUG)
                
            n.onEvent = _print
            n.start().addCallback(lambda _: n.subscribe(config.subOptions['event']))
        else:
            # publisher node
            n.start().addCallback(lambda _: n.publish(config.subOptions['event'], 
                                                      msgClass=CustomMessage, payload=config.subOptions['payload']))
            
        n.setServiceParent(application)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)

def run_web_node():
    
    config = WebNodeOptions()
    application = ts.Application('nodeset-web-node')
    #sc = ts.IServiceCollection(application)
      
    try:
        config.parseOptions()


        from twisted.web import static, script, resource

        from nodeset.core import web
        n = web.WebBridgeNode()
        n.setServiceParent(application)
     
        n.start()
        
        if config.subOptions.has_key('path'):
            root = static.File(config.subOptions['path'])
            root.ignoreExt(".rpy")
            root.processors = {'.rpy': script.ResourceScript}
        else:
            root = resource.Resource()
        
        site = web.NodeSetSite(root, n, logPath=config.subOptions['logfile'])

        root.putChild('subscribe', web.NodeSetSubscribe())
        root.putChild('publish', web.NodeSetPublish())
        
        webservice = internet.TCPServer(config.subOptions['port'], site)
        webservice.setServiceParent(application)
        
        #d = dispatcher.EventDispatcher(config['listen'])
        #d.setServiceParent(application)
    except usage.error, ue:
        #print config
        print ue
    else:
        runApp(config, application)
    
if __name__ == '__main__':
    run_dispatcher()

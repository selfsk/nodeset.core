from twisted.python import usage
from twisted.application import service
#from twisted.internet import reactor

from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp

from nodeset.core.pubsub.agent import XmppAgent

class XmppOptions(usage.Options):
    
    optParameters = [
                     ['server', 's', None, 'XMPP server address'],
                     ['jid', 'j', None, 'JID address'],
                     ['password', 'p', None, 'password'],
                     ['node', 'n', None, 'node name'],
                     ['publish', None, None, 'publish entry'],
                     ['rcpt', None, None, 'rcpt node (for publish)'],
                     ['subId', None, None, 'subscription Id (for unsubscribe)'],
                     ['pubsub', None, None, 'pubsub jabber service name']
                     ]
    
    optFlags = [
                ['subscriptions', None, 'subscription list'],
                ['unsubscribe', None, 'unsubscribe by node'],
                ['subscribe', None, 'subscribe to node'],
                ['delete', None, 'delete node']
                ]

class XmppAppOptions(NodeSetAppOptions):
    
    subCommands = [['xmpp', None, XmppOptions, 'XMPP options']]
    
def run_sub():
    
    config = XmppAppOptions()
    application = service.Application('xmpp')
    
    try:
        config.parseOptions()

        bot = XmppAgent(config.subOptions['server'], config.subOptions['jid'], config.subOptions['password'])
        
        bot.setServiceParent(application)
        d = bot.start()
        
        #print config.subOptions['publish']
        #print config.subOptions['subscriptions']
        
        if config.subOptions['publish']:
            d.addCallback(lambda _: bot.publish(config.subOptions['pubsub'], config.subOptions['rcpt'], config.subOptions['node'], config.subOptions['publish']))
        elif config.subOptions['subscriptions']:
            d.addCallback(lambda _: bot.subscriptions(config.subOptions['pubsub'], config.subOptions['node']))
        elif config.subOptions['unsubscribe']:
            d.addCallbac(lambda _: bot.unsubscribe(config.subOptions['pubsub'], config.subOptions['node'], config.subOptions['subId']))
        elif config.subOptions['subscribe']:
            d.addCallback(lambda _: bot.subscribe(config.subOptions['pubsub'], config.subOptions['node']))
        elif config.subOptions['delete']:
            d.addCallback(lambda _: bot.deleteNode(config.subOptions['pubsub'],config.subOptions['node']))
            
        def _err(fail):
            print fail
            
        d.addErrback(_err)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)
        

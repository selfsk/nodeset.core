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
                     ['subId', None, None, 'subscription Id (for unsubscribe)']
                     ]
    
    optFlags = [
                ['subscriptions', None, 'subscription list'],
                ['unsubscribe', None, 'unsubscribe by node']
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

        print config.subOptions['publish']
        print config.subOptions['subscriptions']
        
#        if config.subOptions['publish']:
#            reactor.callLater(3, bot.publish, 'pubsub.su-msk.dyndns.org', config.subOptions['rcpt'], config.subOptions['node'], config.subOptions['publish'])
#        elif config.subOptions['subscriptions']:
#            reactor.callLater(3, bot.subscriptions, 'pubsub.su-msk.dyndns.org', config.subOptions['node'])
#        elif config.subOptions['unsubscribe']:
#            reactor.callLater(3, bot.unsubscribe, 'pubsub.su-msk.dyndns.org', config.subOptions['node'], config.subOptions['subId'])
#        else:
            
            reactor.callLater(3, bot.subscribe, 'pubsub.su-msk.dyndns.org', config.subOptions['node'])
        
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)
        

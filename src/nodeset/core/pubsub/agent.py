from twisted.words.protocols.jabber import client, jid
from twisted.words.protocols.jabber import xmlstream
from twisted.words.xish import xpath

from twisted.application import service, internet

from twisted.internet import defer
#from twisted.python import log
from nodeset.common.twistedapi import log

from nodeset.core.pubsub.common import * 
#import XmppInstance, IQMessage, SubscribeMessage, \
#                            PublishMessage, UnsubscribeMessage, SubscriptionsMessage, \
#                            Message
                            
#from kiss.trmng import TransactionClient, XmlStreamDebug

#log.startLogging(sys.stdout)

class XmlStreamJabber(xmlstream.XmlStream):
    
    def __init__(self, auth):
        xmlstream.XmlStream.__init__(self, auth)
        
        # dict for pending responses
        self._pending = {}
        
    def _dispatcher(self, xs):
        """
        Dispatch XmppAgent level observers
        """
        cb = self.factory.client.getObserver("/%s" % xs.name)
        
        cb(self, xs)

    def send(self, obj):
        """
        Do default xmlstream.send, but put obj[id] to _pending response dict
        """
        
        d = None
        if isinstance(obj, IQMessage):        
            try:
                
                log.msg("Sending %s" % obj['id'])
                d = defer.Deferred()
                self._pending[obj['id']] = d
                
            except KeyError:
                pass
            
        xmlstream.XmlStream.send(self, obj)
        

        return d
    
class XmppAgent(XmppInstance, service.Service):

    def __init__(self, host, jid_str, pswd, port=5222):
        XmppInstance.__init__(self)
        
        self.jid = jid.JID(jid_str)
        self.pwd = pswd
        self.host = host
        self.port = port
        
        self.service = None
        self.xmlstream = None
        self.start_defer = defer.Deferred()
        
    def start(self):
        return self.start_defer
    
    def startService(self):
        
        a = client.BasicAuthenticator(self.jid, self.pwd)
        self.factory = xmlstream.XmlStreamFactory(a)
        self.factory.protocol = XmlStreamJabber
        self.factory.client = self
         
        self.factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.clientAuth)
       
        self.addObserver('/message', self.gotMessage)
        self.addObserver('/iq', self.gotIq)

        self.service = internet.TCPClient(self.host, self.port, self.factory)
        self.service.startService()
        
    
    def stopService(self):
        if self.service:
            self.service.stopService()
            
    def clientAuth(self, xmlstream):

        presence = domish.Element(('jabber:client', 'presence'))
        presence.addElement('status').addContent('Online')
      
        xmlstream.send(presence)
        log.msg("clientAuth: presense sent") 
        # add a callback for the messages
        for observer in self.getObserverNames():
            xmlstream.addObserver(observer, xmlstream._dispatcher)
           
        self.xmlstream = xmlstream
        
        self.start_defer.callback(xmlstream)
        
        #xmlstream.addObserver('/message', self.gotMessage)
        log.msg("clientAuth: finished")
    
    def subscribe(self, jid_to, node):
        assert(self.xmlstream!=None)
        
        submsg = SubscribeMessage(jid_to, self.jid.userhost(), node)
        log.msg("Subscribing to node(%s), msg(%s)" % (node, submsg.toXml()))
        
        self.xmlstream.send(submsg)
        
    def publish(self, jid_to, jid_from, node, payload):
        assert(self.xmlstream != None)
    
        pubmsg = PublishMessage(jid_to, jid_from, node)
        
        
        pubmsg.addPayload(payload)
        log.msg("Publishing node(%s), msg(%s)" % (node, pubmsg.toXml()))
        
        self.xmlstream.send(pubmsg)
        
    def unsubscribe(self, jid_to, node, subId=None):
        assert (self.xmlstream != None)
        
        unsub = UnsubscribeMessage(jid_to, self.jid.userhost(), node, subId)
        log.msg("Unsubscribing %s from node %s" % (self.jid.userhost(), node))
        
        self.xmlstream.send(unsub)
        
    def subscriptions(self, jid_to, node=None):
        assert(self.xmlstream != None)
        
        subs = SubscriptionsMessage(jid_to, self.jid.userhost(), node)
        
        log.msg("Retriving subscriptions to node %s" % subs.toXml())
        
        self.xmlstream.send(subs)
     
    def nodes(self, jid_to):
        assert(self.xmlstream != None)
        
        iqnode = IQMessage(jid_to, self.jid.userhost(), 'get', ns=None)
        iqnode.addChild(Message('query', ns='http://jabber.org/protocol/disco#items'))
        
        log.msg("Requesting available nodes %s" % iqnode.toXml())
        
        return self.xmlstream.send(iqnode)#.addCallback(self._dmsg).addErrback(self._err)
        
    def hasNode(self, pubsub, node):
        
        return self.nodes(pubsub).addCallback(self._findNode, node)
        
    def _findNode(self, message, node):
        query = xpath.XPathQuery('/iq/query/item[@node="%s"]' % node)
        
        items = query.queryForNodes(message)
        
        if not items:
            raise Exception("node %s, not found" % node)
            
    
    def createNode(self, pubsub, node, configure=None):
        assert(self.xmlstream != None)
        
        create = CreateNodeMessage(pubsub, self.jid.userhost(), node)
        
        if configure:
            create.pubsub.addChild(configure)
            
        log.msg("Creating node %s" % create.toXml())
         
        return self.xmlstream.send(create)
     
    def deleteNode(self, pubsub, node):
        assert(self.xmlstream != None)
        
        delete = DeleteNodeMessage(pubsub, self.jid.userhost(), node)
    
        log.msg("Deleting node %s" % delete.toXml())
            
        return self.xmlstream.send(delete)
    
    def createNodeAndConfigure(self, pubsub, node):
        """
        Defautl configuration for node
        """
        configure = ConfigureMessage()
        configure.addOption('pubsub#persist_items', 0)
        configure.addOption('pubsub#publish_model', 'open')
        configure.addOption('pubsub#send_last_published_item', 'never')
        return self.createNode(pubsub, node, configure)
    
    def getEventItems(self, message):
        query = xpath.XPathQuery('/message/event/items/item')
        
        items = query.queryForNodes(message)
        
        return items or []
       
    def gotEvent(self, message):
        log.msg("Incoming message %s" % message.toXml())
        
    def gotMessage(self, stream, message):
        log.msg("Got XMPP message %s" % message.toXml())
        
        try:
            #TODO: do initial parsing, on <error> run errback
            d = stream._pending[message['id']]
            d.callback(message)
            
            del stream._pending[message['id']]
        except KeyError:
            # looks like it's event message from XMPP
            self.gotEvent(message)
            
    def gotIq(self, stream, message):
            
        log.msg("Got IQ message - %s" % message.toXml())
        iq_id = message.getAttribute('id')
        
        log.msg("_pending %s" % stream._pending)
        try:
            d = stream._pending[iq_id]
            d.callback(message)#.addErrback(_errIq)
            
            del stream._pending[iq_id]
        except KeyError:
            pass
        

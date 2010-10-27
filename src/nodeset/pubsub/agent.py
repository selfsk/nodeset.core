from twisted.words.protocols.jabber import client, jid
from twisted.words.protocols.jabber import xmlstream
from twisted.words.xish import domish

from twisted.application import service, internet

#from twisted.internet import reactor
#from twisted.python import log
from nodeset.common.twistedapi import log

from nodeset.pubsub.common import XmppInstance, SubscribeMessage, PublishMessage, UnsubscribeMessage, SubscriptionsMessage
#from kiss.trmng import TransactionClient, XmlStreamDebug

#log.startLogging(sys.stdout)

class XmlStreamJabber(xmlstream.XmlStream):
    
    def _dispatcher(self, xs):
        cb = self.factory.client.getObserver("/%s" % xs.name)
        
        cb(self, xs)

class XmppBot(XmppInstance, service.Service):

    def __init__(self, host, jid_str, pswd):
        XmppInstance.__init__(self)
        
        self.jid = jid.JID(jid_str)
        self.pwd = pswd
        self.host = host
        
        self.service = None
        self.xmlstream = None
        
    def startService(self):
        
        a = client.BasicAuthenticator(self.jid, self.pwd)
        self.factory = xmlstream.XmlStreamFactory(a)
        self.factory.protocol = XmlStreamJabber
        self.factory.client = self
         
        self.factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.clientAuth)
       
        self.addObserver('/message', self.gotMessage)
        self.addObserver('/iq', self.gotIq)

        self.service = internet.TCPClient(self.host, 5222, self.factory)
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
        
    def gotMessage(self, stream, message):
        print u"gotMessage: received message %s" % message.toXml()

    def gotIq(self, stream, message):
        log.msg("Got IQ message - %s" % message.toXml())
        

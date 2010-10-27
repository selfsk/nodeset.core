from twisted.words.xish import domish, xmlstream
from uuid import uuid4

import time, types

class XmppInstance(object):
    
    def __init__(self):
        self._observers = {}
        
    def addObserver(self, elem, cb):
        self._observers[elem] = cb
        
    def removeObserver(self, elem):
        del self._observer[elem]
    
    def getObserverNames(self):
        return self._observers.keys()
    
    def getObserver(self, elem):
        return self._observers[elem]
    
class XmlHelper(object):
    def __init__(self, item, inf=unicode, outf=unicode):
        self.item = item
        self.inf = inf
        self.outf = outf
    
    def get(self):
        return self.outf(unicode(self.item))

    def set(self, val):
        
        if isinstance(val, domish.Element):
            self.item.children = []
            return XmlHelper(self.item.addChild(val))
        else:
            if len(self.item.children):
                self.item.children = []
            self.item.addContent(self.inf(val))

def convert(object, msgtype):
    
    t = msgtype()
    for child in object.children:
        #print "filter %s" % filter(lambda x: isinstance(x, (str, int)), child.children)
        #if isinstance(child, Message) \
        #    and len(child.children):
        #    t.setter(child.name, convert(child, msgtype))
        #else:
        #    print "child %s %s" % (child.name, child)
         
        #val = str(child)
        #print "val %s" % val
        t.setter(child.name, unicode(child))

    return t

class Message(domish.Element):
    
    def __init__(self, name, ns=''):
        #domish.Element.__init__(*args, **kwargs)
        domish.Element.__init__(self, (ns, name))
        
        self['id'] = str(uuid4())
        self.fields = {}

    
    def __unicode__(self):
        for n in self.children:
            if isinstance(n, types.StringTypes): return unicode(n, "utf-8")
        return u""
    
    # to avoid encoding problems with toXml method (str internal use)
    __str__ = __unicode__
    
    def setter(self, k, val):
        self.fields[k].set(val)
        
    def getter(self, k):
        return self.fields[k].get()

class JabberMessage(Message):
    
    def __init__(self):
        Message.__init__(self, 'message', 'jabber:client')
        
        self.fields = {'body': XmlHelper(self.addElement('body'))}
        
class IQMessage(Message):
    
    def __init__(self, jid_to, jid_from, iq_type, ns):
        Message.__init__(self, 'iq', ns)
        
        self['to'] = jid_to
        self['from'] = jid_from
        self['type'] = iq_type
        
class PubSubMessage(IQMessage):
    
    def __init__(self, jid_to, jid_from, iq_type, ns='http://jabber.org/protocol/pubsub'):
        IQMessage.__init__(self, jid_to, jid_from, iq_type, None)
        
        self.pubsub = Message('pubsub', ns)
        del self.pubsub['id']
        
        self.addChild(self.pubsub)

class SubscriptionsMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node=None):
        PubSubMessage.__init__(self, jid_to, jid_from, 'get', ns='http://jabber.org/protocol/pubsub#owner')
        
        subs = Message('subscriptions', None)

        if node:        
            subs['node'] = node
             
        del subs['id']
        
        self.pubsub.addChild(subs)
                
class PublishMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node):
        PubSubMessage.__init__(self, jid_to, jid_from, 'set')
        
        self.pub = Message('publish', None)
        self.pub['node'] = node
        
        del self.pub['id']
        
        self.pubsub.addChild(self.pub)
            
    def addPayload(self, payload):
        item = Message('item', None)
        body = Message('body', None)
        body.addContent(payload)
        
        item.addContent(body)
        
        item['id'] = str(uuid4())
        self.pub.addChild(item)
        

          
class SubscribeMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node):
        PubSubMessage.__init__(self, jid_to, jid_from, 'set')
        
        self.sub = Message('subscribe', None)
        
        self.sub['node'] = node
        self.sub['jid'] = jid_from
        
        del self.sub['id']
        
        self.pubsub.addChild(self.sub)
        
class UnsubscribeMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node, subId=None):
        PubSubMessage.__init__(self, jid_to, jid_from, 'set')
        
        unsub = Message('unsubscribe', None)
        unsub['node'] = node
        unsub['jid'] = jid_from
        
        if subId:
            unsub['subid'] = subId
            
        self.pubsub.addChild(unsub)
        
class CreateNodeMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node):
        PubSubMessage.__init__(self, jid_to, jid_from, 'set')
        
        create = Message('create', None)
        create['node'] = node
        
        self.pubsub.addChild(create)
        
class DeleteNodeMessage(PubSubMessage):
    
    def __init__(self, jid_to, jid_from, node):
        PubSubMessage.__init__(self, jid_to, jid_from, 'set')
        
        delete = Message('delete', None)
        delete['node'] = node
        
        self.addChild(delete)
        
class TransactionMessage(Message):
    
    def __init__(self):
        Message.__init__(self, 'transaction')
        self.fields = {
                         'type': XmlHelper(self.addElement('type')),
                         'amount': XmlHelper(self.addElement('amount'), outf=int),
                         'ts': XmlHelper(self.addElement('ts')), 
                         'currency': XmlHelper(self.addElement('currency')),
                         'desc': XmlHelper(self.addElement('desc')),
                         'direction': XmlHelper(self.addElement('direction')),
                         'from': XmlHelper(self.addElement('from'))}

    
        
class AcknowledgeMessage(Message):
    
    def __init__(self):
        Message.__init__(self, 'acknowledge')
        self.status = XmlHelper(self.addElement('status'))
        
    def failure(self, msg):
        t = self.status.set(domish.Element(('', 'failure')))
        t.set(msg)
        
    def success(self, msg):
        t = self.status.set(domish.Element(('', 'success')))
        t.set(msg)

    
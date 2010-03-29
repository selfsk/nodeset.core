from nodeset.core import node
from nodeset.common.twistedapi import run

from twisted.application import service
from twisted.internet import reactor

import time
class SimpleNode(node.Node):
    
    def onEvent(self, event):
        print "Got event %s" % (event)
        return "return event_%s" % event.name
    

class SimpleNode1(node.Node):
    
    def _print(self, data):
        print "In node return %s" % data
        
    def onEvent(self, event):
        print "%s, #1 got event %s" % (self, event)
        #raise Exception("#1 exception")
        
        self.publish(self.builder.createEvent('event_2', 'payload_inmulti')).addCallback(self._print)
        self.publish(self.builder.createEvent('remote_event', 'payload')).addCallback(self._print)
        
        return "#1 return"
    
class SimpleBlockNode(node.Node):
    def onEvent(self, event):
        print "Blocking event %s" % event
        #return "return event_%s" % event.name
        
        time.sleep(5)
        print "Go ahead!"
        #raise Exception("Block exception")
        return "block_%s" % event.name

def listen_main():
    multi = node.NodeCollection(5788)
    
    nn = SimpleNode()
    n1 = multi.add(nn)
    
    #n1.subscribe('event_1')
    
    n2 = multi.add(SimpleNode())
    n3 = multi.add(SimpleNode())
    ns = multi.add(SimpleNode1())
    nb = multi.add(SimpleBlockNode())
    
    #print n1.subscribe
    reactor.callLater(2, n1.subscribe, 'event_1')
    reactor.callLater(2, ns.subscribe, 'event_1')
    reactor.callLater(2, nb.subscribe, 'event_block')
    reactor.callLater(3, n2.subscribe, 'event_2')
    reactor.callLater(4, n3.subscribe, 'event_3')
    
    multi.start()
    
    application = service.Application('multi-node')
    
    #n.addNode(node.Node()
    multi.tub.setServiceParent(application)
    
    
    return run(application)
    
    
if __name__ == '__main__':
    listen_main()
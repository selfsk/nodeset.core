from nodeset.core import node, utils
from nodeset.common.twistedapi import run

from twisted.application import service
from twisted.internet import reactor

import time
class SimpleNode(node.Node):
    
    def onEvent(self, event, msg):
        print "Got event %s, msg %s" % (event, msg)
        return "return event_%s" % event
    

class SimpleNode1(node.Node):
    
    def _print(self, data):
        print "In node return %s" % data
        
    def onEvent(self, event, msg):
        print "%s, #1 got event %s, msg %s" % (self, event, msg)
        #raise Exception("#1 exception")
        
        #self.publish('event_2', payload='payload_inmulti').addCallback(self._print)
        #self.publish('remote_event', payload='payload').addCallback(self._print)
        
        return "#1 return"
    
class SimpleBlockNode(node.Node):
    
    @utils.catch('event_block')
    def handleEvent(self, msg):
        #print "Blocking event %s" % event_name
        #return "return event_%s" % event.name
        print "block"
        time.sleep(5)
        print "Go ahead!"
        #raise Exception("Block exception")
        #return "block_%s" % event_name

def listen_main():
    multi = node.NodeCollection(5788)
    
    nn = SimpleNode()
    n1 = multi.adapt(nn)
    
    #n1.subscribe('event_1')
    
    n2 = multi.adapt(SimpleNode())
    n3 = multi.adapt(SimpleNode())
    ns = multi.adapt(SimpleNode1())
    nb = multi.adapt(SimpleBlockNode())
    
    #print n1.subscribe
    reactor.callLater(2, n1.subscribe, 'event_1')
    reactor.callLater(2, ns.subscribe, 'event_1')
    reactor.callLater(2, nb.subscribe, 'event_block')
    reactor.callLater(3, n2.subscribe, 'event_2')
    reactor.callLater(4, n3.subscribe, 'event_3')
    
    multi.start()
    
    application = service.Application('multi-node')
    
    #n.addNode(node.Node()
    multi.setServiceParent(application)
    
    
    return run(application)
    
    
if __name__ == '__main__':
    listen_main()

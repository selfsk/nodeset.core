from nodeset.core import node
from nodeset.common.twistedapi import run

from twisted.application import service
from twisted.internet import reactor

import time
class SimpleNode(node.Node):
    
    def onEvent(self, event):
        print "Got event %s" % (event)

class SimpleBlockNode(node.Node):
    def onEvent(self, event):
        print "Blocking event %s" % event
        
        time.sleep(5)
        print "Go ahead!"

def listen_main():
    multi = node.NodeCollection(5788)
    
    n1 = SimpleNode()
    n2 = SimpleNode()
    n3 = SimpleNode()
    nb = SimpleBlockNode()
    
    #print n1.subscribe
    multi.addNode(n1)
    multi.addNode(n2)
    multi.addNode(n3)
    multi.addNode(nb)
    
    #print n1.subscribe
    reactor.callLater(2, n1.subscribe, 'event_1')
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
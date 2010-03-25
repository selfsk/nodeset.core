from nodeset.core import node
from nodeset.common.twistedapi import run

from twisted.application import service
from twisted.internet import reactor

def publish_main():
    n = node.Node(5688)
    application = service.Application('mnode-publish')

    reactor.callLater(2, n.publish, node.NodeEventBuilder().createEvent('event_1', 'payload_1'))
    reactor.callLater(2, n.publish, node.NodeEventBuilder().createEvent('event_block', 'blocking'))
    reactor.callLater(3, n.publish, node.NodeEventBuilder().createEvent('event_2', 'payload_2'))
    reactor.callLater(4, n.publish, node.NodeEventBuilder().createEvent('event_3', 'payload_3'))
    
    n.start()
    n.tub.setServiceParent(application)
    
    run(application)
    
    
if __name__ == '__main__':
    publish_main()
    
from nodeset.core import node
from nodeset.common.twistedapi import run

from twisted.application import service
from twisted.internet import reactor

class SimpleNode(node.Node):
    
    def onEvent(self, event_name, msg):
        return "On event %s, msg %s" % (event_name, msg)
    
def _print(rval):
    print rval
    
def _publish(n, name, payload):
    n.publish(name, payload=payload).addCallback(_print)
    
def publish_main():
    n = SimpleNode(5688)
    application = service.Application('mnode-publish')

    reactor.callLater(1, n.subscribe, 'remote_event')
    reactor.callLater(2, _publish, n, 'event_1', 'payload_1')
    reactor.callLater(2, _publish, n, 'event_block', 'blocking')
    #reactor.callLater(3, n.publish, node.NodeEventBuilder().createEvent('event_2', 'payload_2'))
    reactor.callLater(4, _publish, n, 'event_3', 'payload_3')
    
    n.start()
    n.setServiceParent(application)
    
    run(application)
    
    
if __name__ == '__main__':
    publish_main()
    
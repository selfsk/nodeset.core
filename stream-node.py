from nodeset.core import node
from nodeset.core import stream

from nodeset.common.twistedapi import run

from twisted.internet import reactor
from twisted.application import service

class StreamNodeExample(node.StreamNode):
   
    def onStream(self, data, formatter):
        print "%s" % formatter
        print "%s" % formatter.decode(data)
        return "formatted"
    
def _print(push_res):
    print push_res
    
def _gotStream(stream):
    stream.push('hello world #1').addCallback(_print)

def getStream(pubNode, name):
    
    pubNode.stream(name).addCallback(_gotStream)
    
def main():
    pub = StreamNodeExample(5556)
    sub = StreamNodeExample(5557)
    
    reactor.callLater(1, sub.subscribe, 'stream_name')
    reactor.callLater(2, getStream, pub, 'stream_name')
    
    pub.start()
    sub.start()
    
    application = service.Application('streaming')
    
    #n.addNode(node.Node()
    pub.tub.setServiceParent(application)
    sub.tub.setServiceParent(application)
    
    return run(application)

if __name__ == '__main__':
    main()
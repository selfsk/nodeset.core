from nodeset.core import node
from nodeset.core import stream

from nodeset.common.twistedapi import run

from twisted.internet import reactor
from twisted.application import service

class StreamNodeExample(node.StreamNode):
    #streamFactory = stream.BinaryStream
    
    #formater = stream.Formater()
    
    def stream(self, stream_name):
        return stream.Stream(self, stream_name)
    
    def onStream(self, stream):
        print "%s" % self.formater.decode(stream)
        return "formatted"
    
def _print(push_res):
    print push_res
    
def pushStream(s):
    s.push('hello stream #1').addCallback(_print)
    
def main():
    pub = StreamNodeExample(5556)
    sub = StreamNodeExample(5557)
    
    
    s = pub.stream('stream_name')
    reactor.callLater(1, sub.subscribe, 'stream_name')
    reactor.callLater(2, s.getRemoteNode)
    reactor.callLater(3, pushStream, s)

    pub.start()
    sub.start()
    
    application = service.Application('streaming')
    
    #n.addNode(node.Node()
    pub.tub.setServiceParent(application)
    sub.tub.setServiceParent(application)
    
    return run(application)

if __name__ == '__main__':
    main()
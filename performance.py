from nodeset.core import node
from nodeset.common.twistedapi import run

from twisted.internet import reactor, defer
from twisted.application import service

import time

class Stats:
    
    def __init__(self):
        self.msg_num = 0
        self.start_date = 0
        self.end_date = 0
        self.rtt = []
        
    def __str__(self):
        return str("msg(%d) in %f(rtt avg:%f max:%f min:%f)" % \
                   (self.msg_num, self.end_date - self.start_date,
                    sum(self.rtt)/len(self.rtt), max(self.rtt), min(self.rtt)))
    
class Publisher(node.StreamNode):

    def update(self, rval):
        flag, d = rval
        now = time.time()
        
        if flag:
            self.stats.msg_num += 1
            if not self.stats.start_date:
                self.stats.start_date = time.time()
            self.stats.end_date = time.time()
            self.stats.rtt.append(now - d)
            
class Subscriber(node.StreamNode):
    
    def onStream(self, stream, formatter):
        ev = self.builder.createEvent('#dumb', stream['payload'])
        
        return self.onEvent(ev)
    
        #return (True, time.time())
    
    def onEvent(self, event):
        n = time.time()
        if event.name == 'show_stats':
            print "Subscriber stats(%s)" % self.stats
        else:
            delta = n - event.payload
           
            self.stats.rtt.append(delta)
            
            self.stats.msg_num += 1
            if not self.stats.start_date:
                self.stats.start_date = time.time()
                
            self.stats.end_date = time.time()

        return (True, n)


    
#def do_subscribe(sub, event_name, defer):
    
def show_stats(none, publisher):
    publisher.publish(publisher.builder.createEvent('show_stats', 'payload'))
    print "Publisher stats(%s)" % publisher.stats
        

def do_publishing(publisher, event_name, msg_num):
    
   
    defers = []
    for i in range(msg_num):
        d = publisher.publish(publisher.builder.createEvent(event_name, time.time()))\
                .addCallback(publisher.update)
                
        defers.append(d)

    defer.DeferredList(defers).addCallback(show_stats, publisher)
        
    

def do_streaming(stream, msg_count):
    
    #builder = node.NodeEventBuilder()
    
    defers = []
    #print stream.peers
    for i in range(msg_count):
        #stream.push(time.time()).addCallback(stream.node.update)
        
        d = stream.push({'payload': time.time()}).addCallback(stream.node.update)
        defers.append(d)
        
        
    defer.DeferredList(defers).addCallback(show_stats, stream.node)
     
def gotStream(pub, stream_name, msg_count):
    
    pub.stream(stream_name).addCallback(do_streaming, msg_count)
    
                    
def main():
    
    pub = Publisher(5443)#, 'pub', 'pbu://su-msk.dyndns.org:5333/dispatcher')
    sub = Subscriber(5444)#, 'sub', 'pbu://su-msk.dyndns.org:5333/dispatcher')
    pub.stats = Stats()
    sub.stats = Stats()
    
    pub.start()
    sub.start()
    
    #stream = pub.stream('stream_name')
    
    #defer = defer.Deferred()
    
    reactor.callLater(1, sub.subscribe, 'event_name')
    reactor.callLater(1, sub.subscribe, 'show_stats')
    reactor.callLater(1, sub.subscribe, 'stream_name')
    
    #reactor.callLater(2,do_publishing, pub, 'event_name', 3000)
    reactor.callLater(3, gotStream, pub, 'stream_name', 3000)
    application = service.Application('performance-test')
    
    
    pub.tub.setServiceParent(application)
    sub.tub.setServiceParent(application)
    
    return run(application)

if __name__ == '__main__':
    main()
    

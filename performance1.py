from nodeset.core import node
from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp

from twisted.internet import reactor, defer
from twisted.application import service
from twisted.python import usage
import time

class PerfOptions(NodeSetAppOptions):
    
    optFlags = [
                ['publisher', None, 'start publisher'],
                ['subscriber', None, 'start subscriber']
                ]
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
    
class Publisher(node.Node):

    def update(self, rval):
        if not isinstance(rval, list):
            rval = [(True, rval)]
            
        for flag, d in rval:
            now = time.time()
        
            if flag:
                self.stats.msg_num += 1
                if not self.stats.start_date:
                    self.stats.start_date = time.time()
                self.stats.end_date = time.time()
            
            self.stats.rtt.append(now - d)
            
        return self

class Subscriber(node.Node):
    
    def onStream(self, stream, formatter):
        ev = self.builder.createEvent('#dumb', payload=stream['payload'])
        
        return self.onEvent(ev)
    
        #return (True, time.time())
    
    def onEvent(self, event_name, msg):
        n = time.time()
        if event_name == 'show_stats':
            print "Subscriber stats(%s)" % self.stats
        else:
            delta = n - msg.payload
           
            self.stats.rtt.append(delta)
            
            self.stats.msg_num += 1
            if not self.stats.start_date:
                self.stats.start_date = time.time()
                
            self.stats.end_date = time.time()

        return n


    
#def do_subscribe(sub, event_name, defer):
    
def show_stats(none, publisher):
    publisher.publish('show_stats')
    
    print "Publisher stats(%s)" % publisher.stats
        

def do_publishing_iter(publisher, event_name, msg_num):
    
    defers = []
    for i in range(msg_num):
        n = time.time()
        d = publisher.publish(event_name, payload=n, _delivery_mode='direct').addCallback(publisher.update)
        
        defers.append(d)
        
    defer.DeferredList(defers).addCallback(show_stats, publisher)
    
def do_publishing(publisher, event_name, msg_num):
   
    #print "msg_num=%d" % msg_num
    if msg_num <= 0:
        show_stats(None, publisher)
        return

    d = publisher.publish(event_name, payload=time.time(), _delivery_mode='direct')\
              	.addCallback(publisher.update).addCallback(do_publishing, event_name, msg_num - 1)
                  

    
def do_subscribe(node):
    
    node.subscribe('event_name')
    node.subscribe('show_stats')
                  
def main():
    application = service.Application('performance-test')
    config = PerfOptions()
    
    try:
        config.parseOptions()
        
        if config['publisher']:
            pub = Publisher(5443, dispatcher_url=config['dispatcher-url'])
            pub.stats = Stats()
            
            pub.start()
            reactor.callLater(1, do_publishing, pub, 'event_name', 3000)
            
            pub.tub.setServiceParent(application)
        if config['subscriber']:
            sub = Subscriber(5444, dispatcher_url=config['dispatcher-url'])
            sub2 = Subscriber(5445, dispatcher_url=config['dispatcher-url'])
            sub.stats = Stats()
            sub2.stats = Stats()
            
            sub.start().addCallback(do_subscribe)
            sub2.start().addCallback(do_subscribe)
            
            sub.tub.setServiceParent(application)
            sub2.tub.setServiceParent(application)
            
    except usage.error, ue:
        print config
        print "%s: %s" % (sys.argv[0], ue)
    else:
        runApp(config, application)


if __name__ == '__main__':
    main()
    

from twisted.internet import reactor, protocol, defer
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

class DumbProto(protocol.Protocol):
    
    isSrv = True
    waiting = False
    
    def dataReceived(self, data):
        
        #print data
        if data == 'EOF':
            print "Receviver %s" % self.stats
            return 
            #reactor.stop()
            
        s_date = float(data)
        n = time.time()
        
        self.stats.msg_num += 1
        self.stats.end_date = time.time()
        
        self.stats.rtt.append(n - s_date)
        
        if self.isSrv:
            if not self.stats.start_date:
                self.stats.start_date = time.time()
                
            self.transport.write(str(n))
        else:
            self.queue.put(self)
            
    def sendMsg(self, msg):
        #if self.waiting:
        #    return
        
        if not self.stats.start_date:
            self.stats.start_date = time.time()

        
        self.transport.write(str(msg))
        #self.waiting = True
        
        return self.queue.get()

class DumbFactory(protocol.Factory):
    
    proto = DumbProto
    
    def buildProtocol(self, addr):
        p = self.proto()
        p.stats = Stats()
        
        return p
    
def sendAnother(proto, msg_num):
    
    msg = time.time()
    
    if msg_num == 0:
        print "Sender stats(%s)" % proto.stats
        msg = "EOF"
    
        proto.sendMsg(msg)
        return 
    
    proto.sendMsg(msg).addCallback(sendAnother, msg_num - 1)
    
def gotProtocol(proto, stats, msg_num):
    #print "Got proto (%d) " % msg_num
    
    msg = time.time()
    
    proto.isSrv = False    
    proto.stats = stats
    proto.queue = defer.DeferredQueue()
    #for i in range(msg_num):
    proto.sendMsg(msg).addCallback(sendAnother, msg_num - 1)

        
def client():
    
    stats = Stats()
    c = protocol.ClientCreator(reactor, DumbProto)
    c.connectTCP("localhost", 5333).addCallback(gotProtocol, stats, 3000)     
     
    reactor.run()
    
def srv():
    
    f = DumbFactory()
    f.stats = Stats()
    
    print "listen on 5333"
    reactor.listenTCP(5333, f)
    reactor.run()
    
    
if __name__ == '__main__':
    
    import sys
    
    if sys.argv[1] == 'srv':
        srv()
    else:
        client()

from nodeset.common.twistedapi import runApp, NodeSetAppOptions
from nodeset.common import log

from nodeset.core import node, message

from twisted.application import service, internet
from twisted.python import usage

from common import Message, Stats

import time

class CustomMessage(message.NodeMessage):
    
    def __init__(self):
        message.NodeMessage.__init__(self)
        
        message.Attribute('ts')
        message.Attribute('seq')
  
class ReplyMessage(CustomMessage):
    
    def __init__(self):
        CustomMessage.__init__(self)
        
        message.Attribute('o_ts')
        
class CustomCmd(message.NodeMessage):
    
    def __init__(self):
        message.NodeMessage.__init__(self)
        
        message.Attribute('cmd')
          
class BenchOptions(usage.Options):
    
    optParameters = [
                     ['msgcount', 'm', None, 'msg count', int],
                     ['event', 'e', None, 'event name']
                     ]

class BenchAppOptions(NodeSetAppOptions):
    
    subCommands = [
                  ['publisher', None, BenchOptions, 'publisher options'],
                  ['subscriber', None, BenchOptions, 'subscribe options']
                  ]

    
class MyNode(node.Node):
    
    def __init__(self, *args, **kwargs):
        node.Node.__init__(self, *args, **kwargs)
        
        self.started = False
        self.stats = None
        
    def onEvent(self, event, msg):
        m = Message()
        m.fromString(msg.toJson())
        
        print str(msg.toJson())
        
        if event == 'reply':
            r_ts = m.attrs['ts']
            o_ts = m.attrs['o_ts']
            
            latency = r_ts - o_ts
             
            self.stats.msgcount()
            self.stats.updateLatency(latency)
        elif event == 'teststop':
            print str(self.stats)
        
        else:
            if m.attrs.has_key('cmd'):
                if m.attrs['cmd'] == 'start':
                    self.stats.start()
                    self.started = True
                elif m.attrs['cmd'] == 'stop':
                    self.stats.stop()
                
                    print str(self.stats)
                    self.publish('teststop')
                    
            # these code handled by subscriber
            elif m.attrs.has_key('ts'):
                recv_ts = time.time()

                self.publish('reply', msgClass=ReplyMessage, ts=recv_ts, o_ts=m.attrs['ts'], seq=m.attrs['seq'])
            
                latency = recv_ts - m.attrs['ts']
            
                self.stats.msgcount()
                self.stats.updateLatency(latency)
    
def main():
    
    application = service.Application('benchmark')
    config = BenchAppOptions()
    
      
    def _err(fail):
        print fail
        
    try:
        config.parseOptions()
        
        n = MyNode(name='simple-%s' % config.subCommand)
        n.stats = Stats()
        
        if config.subCommand == 'subscriber':
            n.start().addCallback(lambda _: n.subscribe(config.subOptions['event'])).addErrback(_err)
        else:
            # publisher node
          
                
            def iterate(node, event):
                node.subscribe('reply')
                node.subscribe('teststop')
                node.publish(event, msgClass=CustomCmd, cmd='start')
                
                for i in range(config.subOptions['msgcount']):
                    print "publishing %s" % event
                    node.publish(event, msgClass=CustomMessage, ts=time.time(), seq=i).addErrback(_err)
                
                node.publish(event, msgClass=CustomCmd, cmd='stop')
                    
            n.start().addCallback(iterate, config.subOptions['event']).addErrback(_err)
            
            #n.start().addCallback(lambda _: n.publish(config.subOptions['event'], payload=config.subOptions['payload']))
            
        n.setServiceParent(application)
    except usage.error, ue:
        print config
        print ue
    else:
        runApp(config, application)
        
if __name__ == '__main__':
    main()
    

from nodeset.common.twistedapi import runApp, NodeSetAppOptions
from nodeset.common import log

from nodeset.core import node, message, config

from twisted.application import service, internet
from twisted.python import usage
from twisted.python.log import ILogObserver#, StdioOnnaStick#, FileLogObserver, msg
from common import Message, Stats

from twisted.internet import reactor

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
    
    optFlags = [
                ['reply', 'r', 'if want to measure the round-trip time for message']
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
        
        #print str(msg.toJson())
        
        if event == 'reply':
            r_ts = m.attrs['ts']
            o_ts = m.attrs['o_ts']
            
            latency = r_ts - o_ts
             
            self.stats.msgcount()
            self.stats.updateLatency(latency)
        elif event == 'teststop':
            from twisted.internet import reactor
            
            print str(self.stats)
            reactor.stop()
        else:
            if m.attrs.has_key('cmd'):
                if m.attrs['cmd'] == 'start':
                    self.stats.start()
                    self.started = True
                elif m.attrs['cmd'] == 'stop':
                    self.stats.stop()
                
                    print (str(self.stats))
             
                    from twisted.internet import reactor
                           
                    #print str(self.stats)
                    self.publish('teststop').addCallback(lambda _: reactor.stop())
                    
                    
            # these code handled by subscriber
            elif m.attrs.has_key('ts'):
                recv_ts = time.time()

                if config.Configurator().subOptions['reply']:
                    self.publish('reply', msgClass=ReplyMessage, ts=recv_ts, o_ts=m.attrs['ts'], seq=m.attrs['seq'])
            
                latency = recv_ts - m.attrs['ts']
            
                self.stats.msgcount()
                self.stats.updateLatency(latency)
                
                
                    
    
def main():
    
    application = service.Application('benchmark')
    config = BenchAppOptions()
    
    import sys

    # dirty hack to print data to stdout    
    application.setComponent(ILogObserver, log.NodeSetLogStdout(sys.stdout).emit)
    def _err(fail):
        log.msg(fail)
        
    try:
        config.parseOptions()

        # disable forking
        config['nodaemon'] = True
        
        print "Creating node simple-%s" % config.subCommand
                 
        n = MyNode(name='simple-%s' % config.subCommand)
        n.stats = Stats()
        
        if config.subCommand == 'subscriber':
            if config['listen'] == 'localhost:5444':
                config['listen'] = 'localhost:5788'
            if config['pidfile'] == 'twistd.pid':
                config['pidfile'] = '/tmp/s_XXX.pid'
                
            print "Subscribing to %s" % config.subOptions['event']
            n.start().addCallback(lambda _: n.subscribe(config.subOptions['event']).addErrback(_err)).addErrback(_err)
            print "Waiting for messages"
        else:
            if config['listen'] == 'localhost:5444':
                config['listen'] = 'localhost:5789'
            if config['pidfile'] == 'twistd.pid':
                config['pidfile'] = '/tmp/p_XXX.pid'
            
            def continue_publish(dummy, node, event, init_count, msgcount):
                #log.msg("msgcount %s" % msgcount)
                msgcount -= 1
                seq = init_count - msgcount
                
                if not config.subOptions['reply']:
                        n.stats.msgcount()
                        
                if msgcount < 0:
                    n.stats.stop()
                    node.publish(event, msgClass=CustomCmd, cmd='stop')
                else:
                    node.publish(event, msgClass=CustomMessage, ts=time.time(), seq=seq)\
                        .addCallback(continue_publish, node, event, init_count, msgcount)\
                        .addErrback(_err)
                
            # publisher node
            def iterate(node, event):
                if config.subOptions['reply']:
                    node.subscribe('reply')
                    node.subscribe('teststop')
                    
                node.publish(event, msgClass=CustomCmd, cmd='start')
                n.stats.start()
                
                
                #for i in range(config.subOptions['msgcount']):
                node.publish(event, msgClass=CustomMessage, ts=time.time(), seq=0)\
                    .addCallback(continue_publish, node, event, 
                                 int(config.subOptions['msgcount']), int(config.subOptions['msgcount']))\
                    .addErrback(_err)
                                    
                    # count published message if no --reply specified, otherwise waiting for replies
                

                
             
            print "Start publishing %d message(s) to event %s" % (config.subOptions['msgcount'], config.subOptions['event'])    
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
    

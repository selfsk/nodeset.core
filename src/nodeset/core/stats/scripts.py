from nodeset.core import node, message

from twisted.application import service
from twisted.python import usage

from nodeset.common.twistedapi import run, NodeSetAppOptions, runApp
from nodeset.common import log

class MonitorMessage(message.NodeMessage):
    
    def __init__(self):
        message.Attribute('stats')
        message.Attribute('node')
1
class MonitorOptions(NodeSetAppOptions):
    optParameters = [
                     ['rrdsrv', None, None, 'rrdsrv address']
                     ]
    
class MonitorNode(node.Node):
    
    def onEvent(self, msg):
        print msg
        

def main():
    
    config = MonitorOptions()
    app = service.Application('nodeset-monitor') 
    
    try:
        config.parseOptions()
        
        mon = MonitorNode(55430)
        
        mon.start().addCallback(lambda n: n.subscribe('notify'))
        mon.setServiceParent(app)
        
    except usage.error, ee:
        print ee
        print config
    else:
        runApp(config, app)
        
        
        
    
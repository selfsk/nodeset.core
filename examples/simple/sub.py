from nodeset.core import utils
from core import SimpleNode

def do_subscribe(node, event_name):
   print "Subscribing for %s event" % event_name
   node.subscribe(event_name)
 
def _err(failure):
   print failure

from twisted.internet import reactor

utils.setDefaultOptions()

node = SimpleNode(name='nodeAbc', port=6555)
node.start().addCallback(do_subscribe, 'some_event').addErrback(_err)
node.startService()

reactor.run()

from nodeset.core import utils
from core import SimpleMessage, SimpleNode

def do_publish(node, event_name, **kw):
   print "Publishing msg(%s) for %s event" % (kw, event_name)
   node.publish(event_name, SimpleMessage, **kw)
 
def _err(failure):
   print failure

from twisted.internet import reactor

utils.setDefaultOptions()

node = SimpleNode(name='nodeAbc', port=6553)
node.start().addCallback(do_publish, 'some_event', field1='value1').addErrback(_err)
node.startService()

reactor.run()

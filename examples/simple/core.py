from nodeset.core import message, node, utils

class SimpleMessage(message.NodeMessage):

   def __init__(self):
      message.NodeMessage.__init__(self)
      message.Attribute('field1')


class SimpleNode(node.Node):

   @utils.catch('some_event')
   def callbackForWhatever(self, msg):
       print "EVENT: %s" % msg.toJson()



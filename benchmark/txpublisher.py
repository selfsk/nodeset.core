from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, task
from twisted.internet.protocol import ClientCreator
from twisted.python import log
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.content import Content
import txamqp.spec

from common import Message, Stats
import time


@inlineCallbacks
def gotConnection(conn, username, password, body, count=1):
    print "Connected to broker."
    yield conn.authenticate(username, password)

    print "Authenticated. Ready to send messages"
    chan = yield conn.channel(1)
    yield chan.channel_open()
    stats = Stats()
    
    def send_messages():
        stats.start()
        
        cmd = Message(cmd='start')
        msg = Content(cmd.toString())
        msg['delivery mode'] = 2
        chan.basic_publish(exchange='txmaqp-test-exchange', content=msg, routing_key='txamqp_test')
        
        print "Starting publishing messages"
        def message_iterator():
            for i in range(count):
                pubm = Message(ts=time.time(), seq=i)
                #print pubm.attrs
                #content = body + "-%d" % i
                msg = Content(pubm.toString())
                msg["delivery mode"] = 2
                chan.basic_publish(exchange='txmaqp-test-exchange', content=msg, routing_key="txamqp_test")
                
                #print msg
                                
                stats.msgcount()
                
                yield None
                
            stats.stop()
            
        return task.coiterate(message_iterator())

    yield send_messages()
    
    m = Message(cmd='stop')
    
    msg = Content(m.toString())
    msg["delivery mode"] = 2
    chan.basic_publish(exchange="txmaqp-test-exchange", content=msg, routing_key="txamqp_test")
    print "Stopping"

    yield chan.channel_close()

    chan0 = yield conn.channel(0)
    yield chan0.connection_close()
    
    reactor.stop()
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 8:
        print "%s host port vhost username password path_to_spec content [count]" % sys.argv[0]
        print "e.g. %s localhost 5672 / guest guest ../../specs/standard/amqp0-8.stripped.xml hello 1000" % sys.argv[0]
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    vhost = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]

    spec = txamqp.spec.load(sys.argv[6])

    content = sys.argv[7]
    try:
        count = int(sys.argv[8])
    except:
        count = 1

    delegate = TwistedDelegate()

    d = ClientCreator(reactor, AMQClient, delegate=delegate, vhost=vhost,
        spec=spec).connectTCP(host, port)

    d.addCallback(gotConnection, username, password, content, count)

    def whoops(err):
        if reactor.running:
            log.err(err)
            reactor.stop()

    d.addErrback(whoops)

    reactor.run()

from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.python import log

from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate

import txamqp.spec

from common import Message, Stats

import time

@inlineCallbacks
def gotConnection(conn, username, password):
    print "Connected to broker."
    yield conn.authenticate(username, password)

    print "Authenticated. Ready to receive messages"
    chan = yield conn.channel(1)
    yield chan.channel_open()

    yield chan.queue_declare(queue="txamqp-test-queue", durable=False, exclusive=False, auto_delete=True)
    yield chan.exchange_declare(exchange="txmaqp-test-exchange", type="direct", durable=False, auto_delete=True)
    yield chan.queue_bind(queue="txamqp-test-queue", exchange="txmaqp-test-exchange", routing_key="txamqp_test")

    yield chan.basic_consume(queue='txamqp-test-queue', no_ack=True, consumer_tag="testtag")

    queue = yield conn.queue("testtag")
    #m = Message()
    stats = Stats()
    started = False
    
    print "Waiting for messages"
    while True:
        msg = yield queue.get()
        m = Message()
        m.fromString(msg.content.body)

        if m.attrs.has_key('cmd'):
            if m.attrs['cmd'] == 'start':
                started = True
                stats.start()
            elif m.attrs['cmd'] == 'stop' and started:
                stats.stop()
                break
            
        elif m.attrs.has_key('ts') and started:
            now = time.time()
            latency = now - m.attrs['ts']
            
            stats.msgcount()
            stats.updateLatency(latency)
            
    yield chan.basic_cancel("testtag")

    yield chan.channel_close()

    chan0 = yield conn.channel(0)

    yield chan0.connection_close()

    print str(stats)
    print "Msg rate: %f" % ((float(stats._stats['etime']) - float(stats._stats['stime'])) / float(stats._stats['msgcount'])) 
    reactor.stop()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 7:
        print "%s host port vhost username password path_to_spec" % sys.argv[0]
        print "e.g. %s localhost 5672 / guest guest ../../specs/standard/amqp0-8.stripped.xml" % sys.argv[0]
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    vhost = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]

    spec = txamqp.spec.load(sys.argv[6])

    delegate = TwistedDelegate()

    d = ClientCreator(reactor, AMQClient, delegate=delegate, vhost=vhost,
        spec=spec).connectTCP(host, port)

    d.addCallback(gotConnection, username, password)

    def whoops(err):
        if reactor.running:
            log.err(err)
            reactor.stop()

    d.addErrback(whoops)

    reactor.run()

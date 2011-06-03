# Framework

Pub/Sub framework for distributed services, nodeset.core is based on [Foolscap][1] RPC and [twisted][2]. 
Each "node" is a separate unix process, and all events delivering are performed by *dispatcher*, 
the special unix process (also based on foolscap RPC).

# Features

* Distributed -  nodes and dispatcher(s) could be anywhere in network. 
* Stateless
     *  dispatcher is completely stateless (after crash/restart the state of dispatcher will be the same as before).
     * nodes share nothing between each other, and restores all subscriptions after dispatcher reconnect
* HTTP support - nodeset-web helps to implement HTTP API based on nodeset.core pub/sub framework
* Monitoring - built in monitoring support [WiP]


# nodeset.core components:
* dispatcher - runs on its own, just listen for incoming foolscap RPC calls, and trace which nodes are available,
    and its health.
* node - Each Node can act as publisher, as well as subscribers. 
 * node collection - group nodes under one listen port

# Install (easy_install based)

python setup.py install (or develop for development)

# Examples

There are few examples of NodeSet framework usage:

 * examples/node.py - example of NodeCollection, as well as Node usage. Subscription example
 * examples/mnode_publish.py - example of publishing

To run any of example, first you must run dispatcher:

 * nodeset-dispatcher [options]

## Node usage example
  - nodeset-node [options]
  - nodeset-node publisher [options]
  - nodeset-node subscriber [options]
 
## Web node usage example
  - nodeset-web web [options]

  Options for call is similar to twistd tool in twisted framework, base code was taken from twisted, just use --help to
find out available options.

### Links:
[1]: http://foolscap.lothar.com/trac
[2]: http://twistedmatrix.com


from foolscap.api import Tub, Referenceable, Copyable, RemoteCopy

class AgentObserver:
    
    def dispatch(self, event, *args, **kwargs):
        print "dispatching event=%s with args(%s)" % (event, str(args))
    
class RAgentService(RemoteCopy):
    copytype = 'nodeset-agent-service-instance'
    def __init__(self):
        pass
    
class AgentService(Copyable):
    typeToCopy = copytype = 'nodeset-agent-service-instance'
    
    def __init__(self, name):
        self.name = name

        # get Tub for foolscap calls
        self.tub = Tub()

        #self.tub.startService()
        self.observers = []
        
        d = self.tub.getReference("pbu://localhost:5333/api")

        d.addCallback(self._gotAgentApi).addErrback(self._errCb)
        self.remote = None
        
        #self.tub.startService()
    def getStateToCopy(self):
        d = {'name': self.name,
             'tubId': self.tub.getTubID(),
             'methods': ['start', 'stop']}
        
        return d
    
    def _initListenTub(self, port):
        self.tub.listenOn('tcp:%d' % port)
        self.tub.setLocation('localhost:%d' % port)
        url = self.tub.registerReference(self, self.name)
        print "FURL %s" % url
        
    def _gotAgentApi(self, remote):
        self.remote = remote
        d = self.remote.callRemote("getRandomPortFor", self.name)
        d.addCallback(self._initListenTub).addErrback(self._errCb).addCallback(self.start)
        
    def _errCb(self, failure):
        print "Error %s" % str(failure)
        
    def start(self, stub):
        # register self on agent and perform remain job for service starting
        self.remote.callRemote("registerService", self)
        
        # delegate event to observer
        self.onEvent('start', self)
    
    def stop(self):
        self.remote.callRemote("unregisterService", self)
        self.onEvent('stop', self)
    
    def status(self):
        return self.onEvent('status', self)
        
    def onEvent(self, event, *args, **kwargs):
        """ i.e. launcher start of any program dispatch event, i.e. "start"
        """
        
        for o in self.observers:
            o.dispatch(event, *args, **kwargs)
            
    def addObserver(self, observer):
        self.observers.append(observer)
    
    def removeObserver(self, observer):
        self.observers.remove(observer)
    
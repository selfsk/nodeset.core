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
    
    def __init__(self, tub, name):
        self.name = name
        self.furl = None
        
        # agent's remote reference
        self.remote = None
        
        self.observers = []
        
        #d = tub.getReference("pbu://localhost:5333/api")
        #d.addCallback(self._gotAgentApi).addErrback(self._errCb)
        
        
        #self.tub.startService()
    def getStateToCopy(self):
        d = {'name': self.name,
             'furl': self.furl}
        
        return d
    
    def _initListenTub(self, port):
        self.port = port
        
        # create listen Tub() for events from agent
        tub = Tub()
        tub.listenOn('tcp:%d' % self.port)
        tub.setLocation('localhost:%d' % self.port)
        url = tub.registerReference(self, self.name)

        self.furl = url
        
    def _gotAgentApi(self, remote):
        d = self.remote.callRemote("getRandomPortFor", self.name)
        d.addCallback(self._initListenTub).addErrback(self._errCb)
        
    def _errCb(self, failure):
        print "Error %s" % str(failure)
        
    def start(self):
        # register self on agent and perform remain job for service starting
        #self.remote.callRemote("registerService", self)
        
        # delegate event to observer
        self.onEvent('start', self)
    
    def stop(self):
        #self.remote.callRemote("unregisterService", self)
        self.onEvent('stop', self)
    
    def status(self):
        return self.onEvent('status', self)
        
    def onEvent(self, event, *args, **kwargs):
        """ i.e. launcher start of any program dispatch event, i.e. "start"
        """
        
        for o in self.observers:
            o.dispatch(event, self, *args, **kwargs)
            
    def addObserver(self, observer):
        self.observers.append(observer)
    
    def removeObserver(self, observer):
        self.observers.remove(observer)
    
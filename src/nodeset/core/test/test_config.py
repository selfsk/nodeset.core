from twisted.trial import unittest
from twisted.internet import defer

from nodeset.core import config
from nodeset.common.twistedapi import NodeSetAppOptions

class ConfigurationTest(unittest.TestCase):
    
    def setUp(self):
        cfg = NodeSetAppOptions()
        cfg.parseOptions(['-n', '--listen', 'localhost:4333', 
                          '--dispatcher-url', 'pbu://localhost:5333/dispatcher'])
        
        self.config = config.Configurator()
        self.config._config = cfg
        
    def testListenParam(self):
        self.assertTrue(self.config['listen'] == 'localhost:4333')
        
    def testDispatcherParam(self):
        self.assertTrue(self.config['dispatcher-url'] == 'pbu://localhost:5333/dispatcher')
        
    def testAnotherInstance(self):
        c = config.Configurator()
        self.assertTrue(c['listen'] == 'localhost:4333')
        
    def testUpdate(self):
        self.config['new_option'] = 'value'
        
        self.assertTrue(self.config['new_option'] == 'value')
        
    def testAnotherRoutine(self):
        def anotherRoutine(d):
            c = config.Configurator()
            
            self.assertTrue(c['listen'] == 'host.name.com:4111')
        
        self.config['listen'] = 'host.name.com:4111'
        

        d = defer.Deferred()
        d.addCallback(anotherRoutine)
        
        d.callback(None)
        
    def testPassingAsArgument(self):
        def routine(conf):
            c = config.Configurator()
            
            self.assertTrue(c == conf)
            
        d = defer.Deferred()
        d.addCallback(routine)
        
        d.callback(config.Configurator())
        
    def tearDown(self):
        del self.config
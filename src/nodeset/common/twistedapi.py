
from twisted.application import app
from twisted.python import usage
#from twisted.python.log import ILogObserver, startLoggingWithObserver
from twisted.application import internet
from twisted.python.util import uidFromString, gidFromString
#from twisted.python.runtime import platformType

#from twisted.internet import reactor

import sys, os

from twisted.scripts._twistd_unix import \
            UnixApplicationRunner as _SomeApplicationRunner, _umask, UnixAppLogger
    
from nodeset.core.config import Configurator
from nodeset.common import log
from nodeset.core import copyright

import logging

import syslog as py_syslog

from twisted.python import syslog


def _logLevel(val):
    if val.upper() not in ['INFO', 'DEBUG', 'WARN', 'CRIT', 'NOTICE']:
        raise ValueError("invalid logLevel %s" % val.upper())
    
    return val.upper()

def _checkSyslogFacility(val):
    
    vu = val.upper()
    
    if hasattr(py_syslog, vu):
        return getattr(py_syslog, vu)
    else:
        raise ValueError("invalid syslog(3) facility")
    
def _checkSyslogOptions(val):
    
    d = []
    for i in val.split(","):
        d.append(_checkSyslogFacility(i))
        
    bitfield_opts = 0
    for i in d:
        bitfield_opts |= i
        
    return bitfield_opts

class NodeSetAppOptions(usage.Options, app.ReactorSelectionMixin):
    """
    Copy of U{ServerOptions<http://twistedmatrix.com/documents/9.0.0/api/twisted.application.app.ServerOptions.html>}, 
    but without all twistd options.
    """
    
    optFlags = [['nodaemon','n',  "don't daemonize, don't use default umask of 0077"],
                ['savestats', None,
                 "save the Stats object rather than the text output of "
                 "the profiler."],
                ['quiet', 'q', "No-op for backwards compatibility."],
                ['originalname', None, "Don't try to change the process name"],
                ['syslog', None,   "Log to syslog, not to file"],
                ['euid', '',
                 "Set only effective user-id rather than real user-id. "
                 "(This option has no effect unless the server is running as "
                 "root, in which case it means not to shed all privileges "
                 "after binding ports, retaining the option to regain "
                 "privileges in cases such as spawning processes. "
                 "Use with caution.)"],
               ]
     
    optParameters = [
                     ['facility', None, syslog.DEFAULT_FACILITY, 'syslog facility', _checkSyslogFacility],
                     ['options', None, syslog.DEFAULT_OPTIONS, 'syslog options', _checkSyslogOptions],
                     ['prefix', None,'twisted',
                      "use the given prefix when syslogging"],
                     ['pidfile','','twistd.pid',
                      "Name of the pidfile"],
                     ['chroot', None, None,
                      'Chroot to a supplied directory before running'],
                     ['uid', 'u', None, "The uid to run as.", uidFromString],
                     ['gid', 'g', None, "The gid to run as.", gidFromString],
                     ['umask', None, None,
                      "The (octal) file creation mask to apply.", _umask],
                     ['logfile','l', None,
                      "log to a specified file, - for stdout"],
                     ['loglevel', None, 'info', 'logLevel, one of (info,warn,debug,crit etc.)', _logLevel],
                     ['rundir','d','.',
                      'Change to a supplied directory before running'],
                       ['profile', 'p', None,
                      "Run in profile mode, dumping results to specified file"],
                     ['profiler', None, "hotshot",
                      "Name of the profiler to use (%s)." %
                      ", ".join(app.AppProfiler.profilers)],
                     ['dispatcher-url', None, 'pbu://localhost:5333/dispatcher', "Dispatcher's URL"],
                     ['listen', None, 'localhost:5444',  "Node's listen address (i.e. host:port)"],
                     ['manhole', None, None, 'run manhole service on specified port', int]
                     ]



    def __init__(self, *a, **kw):
        self['debug'] = False
        usage.Options.__init__(self, *a, **kw)
        
        # set some twisted option to default values
        self['no_save'] = True
        
    def opt_version(self):
        print "nodeset.core version: %s" % copyright.version
        super(NodeSetAppOptions, self).opt_version()
       
class NodeSetAppLogger(UnixAppLogger):
    
    def __init__(self, options):
        UnixAppLogger.__init__(self, options)
        
        self._syslogOptions = options.get('options', syslog.DEFAULT_OPTIONS)
        self._syslogFacility = options.get('facility', syslog.DEFAULT_FACILITY)
        
        
    def _getLogObserver(self):
        
        if self._syslog:
            return syslog.SyslogObserver(self._syslogPrefix, self._syslogOptions, self._syslogFacility).emit
        
        if self._nodaemon:
            stream = sys.stdout
        else:
            if not self._logfilename:
                self._logfilename = 'nodeset-core.log'
                
            stream = log.NodeSetLog(os.path.basename(self._logfilename), os.path.dirname(self._logfilename) or '.')
            
        lvl = getattr(logging, Configurator['loglevel'].upper())
        
        return log.NodeSetLogObserver(stream, lvl).emit
    
class NodeSetApplicationRunner(_SomeApplicationRunner):
    """
    Adoption of U{UnixApplicationRunner<http://twistedmatrix.com/documents/9.0.0/api/twisted.scripts._twistd_unix.UnixApplicationRunner.html>} 
    for NodeSet, createOrGetApplication redefined only
    """
    
    loggerFactory = NodeSetAppLogger
    
    def createOrGetApplication(self):
        """
        Modified to return application instance, early defined
        """
        return self.application
    
def runApp(config, application):
    """
    twistd runApp modified, added second argument application
    @param config: run option (--option i.e.)
    @type config: NodeSetAppOptions
    @param applicatin: application instance
    @type application: Application
    """
    runner = NodeSetApplicationRunner(config)
    runner.application = application
    
    if config['manhole']:
        from twisted.manhole.telnet import ShellFactory
        
        sfactory = ShellFactory()
        #sfactory.namespace['node'] = n
        #sfactory.namespace['service'] = application
    
        #n.setShell(sfactory)
        sfactory.setService(application)
        sfactory.namespace['services'] = []
        for v in application._adapterCache.values():
            
            if hasattr(v, 'services'):
                for s in v.services:
                    if s not in sfactory.namespace['services']:
                        sfactory.namespace['services'].append(s)
            
        shell = internet.TCPServer(config['manhole'], sfactory)
        shell.setServiceParent(application)
        
    #level = getattr(logging, config['loglevel'])
    
    #if config['logfile']:
    #    import os
    #    logfile = log.NodeSetLog(os.path.basename(config['logfile']), os.path.dirname(config['logfile']) or '.')
    #    application.setComponent(ILogObserver, log.NodeSetLogObserver(logfile, level).emit)

        
    Configurator._config = config
    
    runner.run()

def _run(runApp, application, ServerOptions=NodeSetAppOptions):
    """
    instead of run, to handle additional option
    @param runApp: runApp func
    @param ServerOptions: class for options parsing
    @type ServerOptions: NodeSetAppOptions
    """
    config = ServerOptions()
    #config['no_save'] = False
    try:
        config.parseOptions()
    except usage.error, ue:
        print config
        print "%s: %s" % (sys.argv[0], ue)
    else:
        application.config = config
        runApp(config, application)
        
def run(application, options=NodeSetAppOptions):
    """
    wrapper for _run, application instance added
    @param application: Application instance
    @type application: Application
    """
    _run(runApp, application, options)
   
__all__ = ['run', 'runApp']


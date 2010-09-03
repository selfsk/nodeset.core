
from twisted.application import app
from twisted.python import usage
from twisted.python.log import ILogObserver
from twisted.python.util import switchUID, uidFromString, gidFromString
#from twisted.python.runtime import platformType

from twisted.internet import reactor

import sys

from twisted.scripts._twistd_unix import ServerOptions, \
            UnixApplicationRunner as _SomeApplicationRunner, _umask
    
from nodeset.core.config import Configurator
from nodeset.common import log
from nodeset.core import copyright

class NodeSetAppOptions(usage.Options, app.ReactorSelectionMixin):
    """
    Copy of U{ServerOptions<http://twistedmatrix.com/documents/9.0.0/api/twisted.application.app.ServerOptions.html>}, 
    but without all twistd options.
    """
    
    optFlags = [['nodaemon','n',  "don't daemonize, don't use default umask of 0077"],
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
                     ['rundir','d','.',
                      'Change to a supplied directory before running'],
                       ['profile', 'p', None,
                      "Run in profile mode, dumping results to specified file"],
                     ['profiler', None, "hotshot",
                      "Name of the profiler to use (%s)." %
                      ", ".join(app.AppProfiler.profilers)],
                     ['dispatcher-url', None, 'pbu://localhost:5333/dispatcher', "Dispatcher's URL"],
                     ['listen', None, 'localhost:port',  "Node's listen address (i.e. host:port)"]
                     ]



    def __init__(self, *a, **kw):
        self['debug'] = False
        usage.Options.__init__(self, *a, **kw)
        
        # set some twisted option to default values
        self['no_save'] = True
        
    def opt_version(self):
        print "nodeset.core version: %s" % copyright.version
        super(NodeSetAppOptions, self).opt_version()
       
class NodeSetApplicationRunner(_SomeApplicationRunner):
    """
    Adoption of U{UnixApplicationRunner<http://twistedmatrix.com/documents/9.0.0/api/twisted.scripts._twistd_unix.UnixApplicationRunner.html>} 
    for NodeSet, createOrGetApplication redefined only
    """
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
    
    if config['logfile']:
        import os
        logfile = log.NodeSetLog(os.path.basename(config['logfile']), os.path.dirname(config['logfile']) or '.')
        application.setComponent(ILogObserver, log.NodeSetLogObserver(logfile).emit)

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


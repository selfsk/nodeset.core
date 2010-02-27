
from twisted.application import app
from twisted.python import usage
from twisted.python.util import switchUID, uidFromString, gidFromString
#from twisted.python.runtime import platformType

import sys

from twisted.scripts._twistd_unix import ServerOptions, \
            UnixApplicationRunner as _SomeApplicationRunner, _umask
    

class NodeSetAppOptions(usage.Options, app.ReactorSelectionMixin):
    
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
                       
                     ]


    def __init__(self, *a, **kw):
        self['debug'] = False
        usage.Options.__init__(self, *a, **kw)
        
        # set default twisted option to default values
        self['no_save'] = True
        
class NodeSetApplicationRunner(_SomeApplicationRunner):
    
    def createOrGetApplication(self):
        return self.application
    
def runApp(config, application):
       runner = NodeSetApplicationRunner(config)
       runner.application = application
   
       runner.run()

def _run(runApp, ServerOptions, application):
    config = ServerOptions()
    #config['no_save'] = False
    try:
        config.parseOptions()
    except usage.error, ue:
        print config
        print "%s: %s" % (sys.argv[0], ue)
    else:
        runApp(config, application)
        
def run(application):
       _run(runApp, NodeSetAppOptions, application)
   
   
__all__ = ['run', 'runApp']


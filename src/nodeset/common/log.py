from twisted.python import log, logfile, context
import ctypes

class NodeSetLog(logfile.DailyLogFile):
    """ Special class for log rotation, always return True on shouldRotate(),
    on SIGUSR1, handler checks shouldRotate() value
    """
    def __init__(self, *args, **kwargs):
        logfile.DailyLogFile.__init__(self, *args, **kwargs)
        
    def shouldRotate(self):
        return True
    
class NodeSetLogObserver(log.FileLogObserver):
    
    def __init__(self, *args, **kwargs):
        log.FileLogObserver.__init__(self, *args, **kwargs)

def msg(message, *args, **kwargs):
    try:
        import sys
        f = sys._getframe(1)
            
        r = f.f_locals['self']
        instance = '%s@%s' % (r.__class__.__name__, hex(id(r)))
    except KeyError, e:
        instance = '-'
    
    log.callWithContext({'system': instance}, log.msg, message, *args, **kwargs)
    


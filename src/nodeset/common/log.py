from twisted.python import log, logfile, util

import logging

logLevel = {logging.DEBUG: 'DEBUG',
            logging.ERROR: 'ERROR',
            logging.INFO: 'INFO',
            logging.WARN: 'WARN',
            logging.CRITICAL: 'CRITICAL'}

import sys

class NodeSetLog(logfile.DailyLogFile):
    """ Special class for log rotation, always return True on shouldRotate(),
    on SIGUSR1, handler checks shouldRotate() value
    """
    def __init__(self, *args, **kwargs):
        logfile.DailyLogFile.__init__(self, *args, **kwargs)
        
    def shouldRotate(self):
        return True
class NodeSetLogStdout(log.FileLogObserver):
        
    def emit(self, eventDict):
        text = log.textFromEventDict(eventDict)
        
        if eventDict['system'] == '-':
            self.write("%s\n" % text)
            self.flush()
        
class NodeSetLogObserver(log.FileLogObserver):
    
    def __init__(self, *args, **kwargs):
        log.FileLogObserver.__init__(self, *args, **kwargs)

    def emit(self, eventDict):
        text = log.textFromEventDict(eventDict)
        if text is None:
            return
        
        if not eventDict.has_key('logLevel'):
            eventDict['logLevel'] = 'INFO'
        elif logLevel.has_key(eventDict['logLevel']):
            eventDict['logLevel'] = logLevel[eventDict['logLevel']]
            
        timeStr = self.formatTime(eventDict['time'])
        fmtDict = {'system': eventDict['system'], 'text': text.replace("\n", "\n\t"),
                   'logLevel': eventDict['logLevel']}
        msgStr = log._safeFormat("[%(logLevel)s] [%(system)s] %(text)s\n", fmtDict)

        util.untilConcludes(self.write, timeStr + " " + msgStr)
        util.untilConcludes(self.flush)  # Hoorj!
        
def _get_instance():
    try:
        import sys
        f = sys._getframe(2)
         
        r = f.f_locals['self']
        c = f.f_code.co_name
        #l = f.f_code.co_firstlineno
        return "%s.%s" % (r.__class__.__name__, c)
        #return '%s@%s' % (r.__class__.__name__, hex(id(r)))
    except KeyError, e:
        return '-'
         
def msg(message, *args, **kwargs):
   
    instance = _get_instance()
    
    log.callWithContext({'system': instance}, log.msg, message, *args, 
                         **kwargs)
    
def err(_stuff=None, _why=None, loglevel=logging.ERROR, **kw):
    instance = _get_instance()
    
    log.err(_stuff, _why, system=instance, logLevel=loglevel, **kw)

crit = err
warn = err

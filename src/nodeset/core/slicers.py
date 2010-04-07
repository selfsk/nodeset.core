from nodeset.core import stream

from foolscap import slicer
import pickle

class FormatterSlicer(slicer.BaseSlicer):
    """
    Slicer for formatter instance
    """
    opentype = ('Formatter',)
    slices = stream.Formatter
    trackReferences = True
    
    def sliceBody(self, streamable, banana):
        yield  pickle.dumps(self.obj.encode)
        yield  pickle.dumps(self.obj.decode)

    
class StreamEventUnslicer(slicer.BaseUnslicer):
    """
    Unslicer for formatter instance
    """
    opentype = ('Formatter',)

    def __init__(self):
        self.obj = stream.Formatter()
        
    def receiveChild(self, obj, ready_deferred=None):
        o = pickle.loads(obj)
        setattr(self.obj, o.__name__, o)
        
    def receiveClose(self):
        return self.obj, None
    
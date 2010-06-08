import simplejson

class Base(object):
    def get(self, metrics):
        d = [(m.name, m.get()) for m in metrics]
        
        return d
    

class Dict(Base):
    
    def get(self, metrics):
        d = super(Dict, self).get(metrics)
        
        return dict(d)
    

class Json(Dict):
    
    def get(self, metrics):
        d = super(Json, self).get(metrics)
        
        return simplejson.dumps(d)

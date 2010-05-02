from twisted.trial.runner import TestLoader
from twisted.scripts.trial import Options, _makeRunner, _getSuite

import sys

class TrialTestLoader(TestLoader):
    
    def loadTestsFromNames(self, test_suite, wtf):
        config = Options()
        config.parseOptions(test_suite)
                                
        trialRunner = _makeRunner(config)
        suite = _getSuite(config)
        if config['until-failure']:
            test_result = trialRunner.runUntilFailure(suite)
        else:
            test_result = trialRunner.run(suite)
        if config.tracer:
            sys.settrace(None)
            results = config.tracer.results()
            results.write_results(show_missing=1, summary=False,
                                  coverdir=config.coverdir)
            
        sys.exit(not test_result.wasSuccessful())
        

from setuptools import setup, find_packages

setup(
    name = "nodeset",
    version = "0.99.0",
    packages = find_packages('src'),
    package_dir = {'': 'src'},

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['twisted>=9.0.0', 'foolscap>=0.5.0', 'pyyaml'],
    
    package_data = {
        # If any package contains *.txt and .yml files
        '': ['*.txt', '*.rst', '*.yml'],
    },

    entry_points = {
                    'console_scripts': [
                                        'nodeset-agent = nodeset.agent:run_agent', 
                                        'nodeset-service = nodeset.agent:run_service',
                                        'nodeset-dispatcher = nodeset.agent:run_dispatcher',
                                        'nodeset-node-subscribe = nodeset.agent:run_node',
                                        'nodeset-node-publish = nodeset.agent:run_node1']},
    
    # metadata for upload to PyPI
    description = "NodeSet framework",

    # could also include long_description, download_url, classifiers, etc.
)

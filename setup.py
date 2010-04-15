from setuptools import setup, find_packages

setup(
    name = "nodeset",
    version = "0.99.4",
    packages = find_packages('src'),
    package_dir = {'': 'src'},

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['twisted>=9.0.0', 'foolscap>=0.5.0', 'pyopenssl'],
    
    package_data = {
        # If any package contains *.txt and .yml files
        '': ['*.txt', '*.rst', '*.yml'],
    },

    entry_points = {
                    'console_scripts': [
                                        'nodeset-dispatcher = nodeset.core:run_dispatcher',
                                        'nodeset-node-subscribe = nodeset.core:run_node_sub',
                                        'nodeset-node-publish = nodeset.core:run_node_pub']},
    
    # metadata for upload to PyPI
    description = "NodeSet framework",

    # could also include long_description, download_url, classifiers, etc.
)

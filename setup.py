from setuptools import setup, find_packages


setup(
    name = "nodeset",
    version = "0.99.8",
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    author = 'Sergei Kononov',
    author_email = 'self.sik@gmail.com',
    url = 'http://github.com/selfsk/nodeset.core',
    
    install_requires = ['twisted>=9.0.0', 'foolscap>=0.5.0', 'pyopenssl'],
    
    package_data = {
        # If any package contains *.txt and .yml files
        '': ['*.txt', '*.rst', '*.yml'],
    },

    entry_points = {
                    'console_scripts': [
                                        'nodeset-dispatcher = nodeset.core.scripts:run_dispatcher',
                                        'nodeset-node-subscribe = nodeset.core.scripts:run_node_sub',
                                        'nodeset-node-publish = nodeset.core.scripts:run_node_pub',
                                        'nodeset-monitor = nodeset.core.stats.scripts:main',
                                        'nodeset-shell = nodeset.core.scripts:run_shell',
                                        'nodeset-web = nodeset.core.scripts:run_web_node']},
    
    # metadata for upload to PyPI
    description = "NodeSet framework",

    test_suite = 'nodeset.core',
    test_loader = 'nodeset.core.test:TrialTestLoader',
    
    namespace_packages = ['nodeset']
    # could also include long_description, d,wnload_url, classifiers, etc.
)

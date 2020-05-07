import sys
import os

extensions = [
    'sphinxcontrib.httpdomain',
    'sphinx_tabs.tabs',
    'sphinx.ext.autodoc'
]
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../'))

master_doc = 'index'

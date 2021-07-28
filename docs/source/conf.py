#!/usr/bin/env python3

import sys
import os
import time

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']

master_doc = 'index'

project = 'Python.org Website'
copyright = '%s, Python Software Foundation' % time.strftime('%Y')

# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0'

pygments_style = 'sphinx'

try:
    import sphinx_rtd_theme
except ImportError:
    html_theme = 'default'
else:
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

htmlhelp_basename = 'PythonorgWebsitedoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  ('index', 'PythonorgWebsite.tex', 'Python.org Website Documentation',
   'Python Software Foundation', 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'pythonorgwebsite', 'Python.org Website Documentation',
     ['Python Software Foundation'], 1)
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'PythonorgWebsite', 'Python.org Website Documentation',
   'Python Software Foundation', 'PythonorgWebsite', '',
   'Miscellaneous'),
]

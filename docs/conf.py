# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os


# У список sys.path додається абсолютний шлях до батьківської директорії з поточної директорії. 
# Це необхідно для того, щоб Sphinx міг знаходити модулі Python, що перебувають поза 
# директорією проєкту документації:
sys.path.append(os.path.abspath('..'))
project = 'pva Rest API'
copyright = '2023, Denys'
author = 'Denys'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
# html_theme = 'alabaster'
# шлях до директорії зі статичними файлами (наприклад, зображеннями), які будуть використовуватися в документації:
html_static_path = ['_static']

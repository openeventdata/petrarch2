.. PETRARCH documentation master file, created by
   sphinx-quickstart on Fri Jun  6 11:40:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PETRARCH's documentation!
====================================

The Python Engine for Text Resolution And Related
Coding Hierarchy (PETRARCH) coder is the next-generation successor to the
`TABARI <http://eventdata.parusanalytics.com/software.dir/tabari.html>`_ event-data coding software. More information about the differences
between PETRARCH and TABARI can be found on the `Notes <current.html>`_ page.

Installing
----------

It is now possible to install the program. It is highly recommended that you
install within a virtual environment. This is alpha software, so things will
change moving forward. Seriously, install in a virtual environment.

To install (you're in a virtual environment, right?):

1) Clone the repo

  - For example, download the zip file into ``~/Downloads``.
  - This will put the repo into something like ``~/Downloads/petrarch``.

2) Run ``pip install -e ~/Downloads/petrarch``


This will install the program with a command-line hook. You can now run the program using:

``petrarch <COMMAND NAME> [OPTIONS]``

You can get more information using:

``petrarch -h``

**StanfordNLP:**

If you plan on using StanfordNLP for parsing within the program you will also
need to download that program. PETRARCH uses StanfordNLP 3.2.0, which can be
obtained from `Stanford <http://www-nlp.stanford.edu/software/stanford-corenlp-full-2013-06-20.zip>`_. 
PETRARCH's default configuration file assumes that this is unzipped and located
in the user's home directory in a directory named ``stanford-corenlp/``, e.g., ``~/stanford-corenlp``.

The program is stable enough that it is probably useable. The main thing that's
going to change are the underlying dictionaries and some organization of the
code. It's not *that* likely that there will be large changes in the API. 

Running
-------

Currently, you can run PETRARCH using the following command if installed:

``petrarch parse -i <INPUT FILE> -o <OUTPUT FILE>``

If not installed:

``python petrarch.py parse -i data/text/GigaWord.sample.PETR.xml -o test_output.txt``

There's also the option to specify a configuration file using the ``-c <CONFIG
FILE>`` flag, but the program will default to using ``PETR_config.ini``.

When you run the program, a ``PETRARCH.log`` file will be opened in the current
working directory. This file will contain general information, e.g., which
files are being opened, and error messages.


Contents:
---------

.. toctree::
   :maxdepth: 2

   current.rst
   petrarch.rst
   dictionaries.rst
   inputs.rst
   contributing.rst
   modules.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


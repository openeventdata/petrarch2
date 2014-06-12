.. PETRARCH documentation master file, created by
   sphinx-quickstart on Fri Jun  6 11:40:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

A Python Engine for Text Resolution And Related Coding Hierarchy.

PETRARCH is a natural language processing tool for machine-coding events data.
It is designed to process fully-parsed news summaries in Penn Treebank format,
from which 'whom-did-what-to-whom' relations are extracted. 

PETRARCH is the next-generation successor to the `TABARI
<http://eventdata.parusanalytics.com/software.dir/tabari.html>`_ event-data
coding software. More information about the key differences between PETRARCH
and TABARI can be be found `here <current.html>`_ .

This software is MIT Licensed (MIT) Copyright &copy; 2014 Open Event Data Alliance


Events Data
-----------

Over the last few decades, computational and social scientists have refined a
process of systematically coding events from news summaries and event
descriptions referred to as “event data.” This process consists of two
component parts:

 1. First, is the collection of raw unstructured text including information
     about relevant events. For this step we have developed a web scraper that
     automatically pulls news stories form a white list of RSS feeds. Scraped
     stories are then stored in a MongoDB instance for easy future retrieval.

 2. **Second in this process is the extraction of structured data from scraped
     unstructured texts using an event data coding system. This was
     traditionally done using the TABARI system, but will soon be replaced with
     PETRARCH which works with fully-parsed inputs.**

The output of this process, event observations identified and extracted in a
'who-did-what-to-whom' format, is what we refer to as event data. At this most
fundamental event event data consists of three component parts,
``{SOURCE_ACTOR, ACTION_TYPE, TARGET_ACTOR}`` as well as general attributes
``{DATE_TIME, LOCATION}``:

Sample Raw Event Data Output:

::

    | Date     | Source | CAMEO Code | Target | Cameo Event |
    |:--------:|:------:|:----------:|:------:|:--------------------------------:
    | 19980312 | ISRMIL | 190        | PALINS | (Use conventional military face) |

For more information on event data as well as event data related research see: http://eventdata.parusanalytics.com/

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

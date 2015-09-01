PETRARCH
========

Code for the new Python Engine for Text Resolution And Related Coding Hierarchy (PETRARCH) 
event data coder. The coder now has all of the functions from the older TABARI coder 
and the new CAMEO.verbpatterns.140609.txt dictionary incorporates both parser-based matching 
and extensive synonym sets. The program coded 60,000 AFP sentences from the GigaWord corpus 
without crashing, using the included dictionaries.

For more information, please visit the (work-in-progress)
[documentation](http://petrarch.readthedocs.org/en/latest/#).
##First, a note.

It is possible to run PETRARCH as a stand-alone program. Most of our
development work has gone into incorporating PETRARCH into a full pipeline of
utilities, though, e.g., the [Phoenix pipeline](https://github.com/openeventdata/phoenix_pipeline).
There's also a RESTful wrapper around PETRARCH and CoreNLP named
[hypnos](https://github.com/caerusassociates/hypnos). It's probably worthwhile
to explore those options before trying to use PETRARCH as a stand-alone.

##Installing

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

There was a time where Stanford CoreNLP was incorporated directly into Petrarch, but due
to operating system differences that we don't want to deal with, this is no longer the case.
We recommend [this dockerized API](http://github.com/chilland/ccnlp) if you need to incorporate
a CoreNLP parse into a script, or the Stanford website has a nice [web app](http://nlp.stanford.edu:8080/corenlp/), where if you select the "Pretty Print," output option, it'll give you the 
syntactic parse in Treebank form. Or if you're not looking to edit Petrarch itself and just
use its functionality, [hypnos](https://github.com/caerusassociates/hypnos) is an easier option.


##Running

Currently, you can run PETRARCH using the following command if installed:

``petrarch batch [-i <INPUT FILE> ] [-o [<OUTPUT FILE>]``

If not installed:

``python petrarch.py batch -i <INPUT FILE> -o <OUTPUT FILE>``

There's also the option to specify a configuration file using the ``-c <CONFIG
FILE>`` flag, but the program will default to using ``PETR_config.ini``.

When you run the program, a ``PETRARCH.log`` file will be opened in the current
working directory. This file will contain general information, e.g., which
files are being opened, and error messages.

##Unit tests

Commits should always successfully complete the PyTest command

``py.test``

Naturally you need PyTest installed for this to work. Commits will be tested
by TravisCI upon Pull Request to the master directory, and will tell us whether
the version has passed the tests. If for whatever reason you need to change the 
tests or add cases to the test file, state that in the PR description. 


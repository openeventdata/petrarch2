PETRARCH
========

[![Join the chat at https://gitter.im/openeventdata/petrarch2](https://badges.gitter.im/openeventdata/petrarch2.svg)](https://gitter.im/openeventdata/petrarch2?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Documentation Status](https://readthedocs.org/projects/petrarch2/badge/?version=latest)](http://petrarch2.readthedocs.org/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/openeventdata/petrarch2.svg?branch=master)](https://travis-ci.org/openeventdata/petrarch2)
[![Code Health](https://landscape.io/github/openeventdata/petrarch2/master/landscape.svg?style=flat)](https://landscape.io/github/openeventdata/petrarch2/master)

[![Caerus logo](http://caerusassociates.com/wp-content/uploads/2012/03/Caerus_logo.png)](http://caerusassociates.com/wp-content/uploads/2012/03/Caerus_logo.png)

Code for the new Python Engine for Text Resolution And Related Coding Hierarchy (PETRARCH) 
event data coder. The coder now has all of the functions from the older TABARI coder 
and the new CAMEO.2.0.txt verb dictionary incorporates more syntactic information and is far
simpler than the previous version.


For more information, please read the Petrarch2.pdf file in this directory and visit the (work-in-progress)
[documentation](http://petrarch2.readthedocs.org/en/latest/#).

##First, a note.

It is possible to run PETRARCH as a stand-alone program. Most of our
development work has gone into incorporating PETRARCH into a full pipeline of
utilities, though, e.g., the [Phoenix pipeline](https://github.com/openeventdata/phoenix_pipeline).
There's also a RESTful wrapper around PETRARCH and CoreNLP named
[hypnos](https://github.com/caerusassociates/hypnos). It's probably worthwhile
to explore those options before trying to use PETRARCH as a stand-alone.

##Installing
If you do decide you want to work with Petrarch as a standalone program, it is possible to install:


``pip install git+https://github.com/openeventdata/petrarch2.git``


This will install the program with a command-line hook. You can now run the program using:

``petrarch <COMMAND NAME> [OPTIONS]``

You can get more information using:

``petrarch -h``

**StanfordNLP:**

There was a time where Stanford CoreNLP was incorporated directly into Petrarch, but due
to operating system differences that we don't want to deal with, this is no longer the case.
We recommend [this dockerized API](http://github.com/chilland/ccnlp) if you need to incorporate
a CoreNLP parse into a script, or the Stanford website has a nice [web app](http://nlp.stanford.edu:8080/corenlp/),
 where if you select the "Pretty Print," output option, it'll give you the 
syntactic parse in Treebank form. Or if you're not looking to edit Petrarch itself and just
use its functionality, [hypnos](https://github.com/caerusassociates/hypnos) is an easier option.


##Running

Currently, you can run PETRARCH using the following command if installed:

``petrarch2 batch [-i <INPUT FILE> ] [-o [<OUTPUT FILE>]``

If not installed:

``python petrarch2.py batch -i <INPUT FILE> -o <OUTPUT FILE>``

You can see a sample of the input/output by running (assuming you're in the
PETRARCH2 directory):

``petrarch2 batch -i ./petrarch2/data/text/GigaWord.sample.PETR.xml -o test.txt``

This will return a file named `evts.test.txt`.

There's also the option to specify a configuration file using the ``-c <CONFIG
FILE>`` flag, but the program will default to using ``PETR_config.ini``.

When you run the program, a ``PETRARCH.log`` file will be opened in the current
working directory. This file will contain general information, e.g., which
files are being opened, and error messages.

But seriously, you should probably use [hypnos](https://github.com/caerusassociates/hypnos) rather than run PETRARCH as a standalone program.

##Unit tests

Commits should always successfully complete the PyTest command

``py.test``

Naturally you need PyTest installed for this to work. Commits will be tested
by TravisCI upon Pull Request to the master directory, and will tell us whether
the version has passed the tests. If for whatever reason you need to change the 
tests or add cases to the test file, state that in the PR description. 


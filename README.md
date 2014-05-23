PETRARCH
========

Current development for the new Python Engine for Text Resolution And Related
Coding Hierarchy (PETRARCH) coder.

See the header of PETR_coder.py for details on the current state of the program. In a 
nutshell, this works -- it coded 60,000 AFP sentences from the GigaWord corpus without 
crashing, using the included dictionaries -- but the pattern matching is only partially 
implemented and the CAMEO dictionary still uses the old TABARI-style stemming which does 
not work in PATRARCH, which is to say there are a *lot* of patterns that no longer work. 
However, it now has almost all of the features of the TABARI coder.

Documentation could also use a little work (really??) but is fairly complete, though 
scattered in """...""" blocks throughout the program.

##Installing

It is possible to install the program. **It is highly recommended that you install within
a virtual environment.** This is alpha software, so things will change
moving forward. Seriously, install in a virtual environment.

To install (you're in a virtual environment, right?):

1) Clone the repo
2) cd into the cloned repository
3) Run `pip install -e .`

This will install the program with a command-line hook. You can now run the
program using:

    petrarch <COMMAND NAME> [OPTIONS]

You can get more information using:

    petrarch -h

It's not really adviseable to install the program at the current moment,
though.

##Running

Currently, you can run PETRARCH using the following command:

    python petrarch.py parse -i data/text/GigaWord.sample.PETR.txt -o test_output.txt

There's also the option to specify a configuration file using the `-c <CONFIG
FILE>` flag, but the program will default to using `PETR_config.ini`.

You can get help with the program by running

    python petrarch.py -h

##Unit tests

Commits should always successfully complete 

	python petrarch.py validate

This command defaults to the `PETR.UnitTest.records.txt` file included with the
program. Alternative files can be indicated using the `-i` option. For example
(this is equivalent to the default command):


	python PETR.coder.py validate -i data/text/PETR.UnitTest.records.txt

The final record should read

	Sentence: FINAL-RECORD [ DEMO ]
	ALL OF THE UNIT TESTS WERE CODED CORRECTLY. 
	No events should be coded
	No events were coded
	Events correctly coded in FINAL-RECORD
	Exiting: <Stop> record 


##Compatibilities with TABARI dictionaries

PETRARCH has a much richer dictionary syntax than TABARI, which will eventually accommodate 
the WordNet-enhanced dictionaries developed at Penn State as well as reducing the level 
of redundancy in the existing dictionaries. While the initial version of the program 
could use existing TABARI dictionaries, this compatibility will decline with further 
developments and only the PETRARCH-specific dictionaries can be used

15-Nov-2013: Requires TABARI 0.8 indented date restrictions, not older in-line format

23-Apr-2014: PETRARCH-formatted agents dictionary required

12-May-2014: Disjunctive phrases no longer recognized in the .verbs dictionary

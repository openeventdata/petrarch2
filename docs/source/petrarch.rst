PETRARCH
========

This page contains some general notes about PETRARCH such as how the data is
stored internally, how the configuration file is organized, and an outline of
how PETRARCH differs from the previous-generation coder, TABARI.

Miscellaneous Operating Details
-------------------------------

While PETRARCH is able to handle chunks of text as input, such as the first
four sentences of a news story, the functional processing unit is the
individual sentence. As can be seen in the section below, the data *is*
organized within the program at the story level, but both the StanfordNLP and
event coding process occurs stricly at the sentence level.


Internal Data Structures
------------------------

The main data format within PETRARCH is a Python dictionary that is structured
around unique story IDs as the keys for the dictionary and another dictionary
as the value. The value dictionary contains the relevant information for the
sentences within the story, and the meta information about the story such as
the date and source. The broad format of this internal dictionary is:

::

    {story_id: {'sents': {0: {'content': 'String of content', 'parsed': 'StanfordNLP parse tree',
                              'coref': 'Optional list of corefs', 'events': 'List of coded events',
                              'issues': 'Optional list of issues'},
                          1: {'content': 'String of content', 'parsed': 'StanfordNLP parse tree',
                              'coref': 'Optional list of corefs', 'events': 'List of coded events',
                              'issues': 'Optional list of issues'}
                          }
                'meta': {'date': 'YYYYMMDD', 'other': "This is the holding dict for misc info."}
            },
     story_id: {'sents': {0: {'content': 'String of content', 'parsed': 'StanfordNLP parse tree',
                              'coref': 'Optional list of corefs', 'events': 'List of coded events',
                              'issues': 'Optional list of issues'},
                          1: {'content': 'String of content', 'parsed': 'StanfordNLP parse tree',
                              'coref': 'Optional list of corefs', 'events': 'List of coded events',
                              'issues': 'Optional list of issues'}
                          }
                'meta': {'date': 'YYYYMMDD', 'other': "This is the holding dict for misc info."}
            },
    }

This consistent internal format allows for the easy extension of the program
through external hooks. 

Configuration File
------------------

The configuration file for PETRARCH currently has three sections:
``Dictionaries``, ``Options``, and ``StanfordNLP``. An example config file is
outlined below. This is the same setup as the default configuration used within
PETRARCH.

::

    [Dictionaries]
    # See the PETRreader.py file for the purpose and format of these files
    verbfile_name    = CAMEO.091003.master.verbs
    #actorfile_list   = Phoenix.Countries.140227.actors.txt, Phoenix.Internatnl.140130.actors.txt, Phoenix.MNSA.140131.actors.txt
    actorfile_list  = Phoenix.Countries.140227.actors.txt
    agentfile_name   = Phoenix.140422.agents.txt
    discardfile_name = Phoenix.140227.discards.txt
    issuefile_name   = Phoenix.issues.140225.txt

    [Options]
    # textfile_list is a comma-delimited list of text files to code. This list has priority if 
    #               both a textfile_list and textfile_name are present
    textfile_list = GigaWord.sample.PETR.txt
    #textfile_list = AFP0808-01.txt, AFP0909-01.txt, AFP1210-01.txt
    # textfile_name is the name of a file containing a list of names of files to code, one 
    # file name per line.
    #textfile_name  = PETR.textfiles.benchmark.txt

    # eventfile_name is the output file for the events
    eventfile_name = events.PETR-Devel.txt


    # INTERFACE OPTIONS: uncomment to activate
    # Default: set all of these false, which is equivalent to an A)utocode in TABARI

    # code_by_sentence: show events after each sentence has been coded; default is to 
    #                   show events after all of the sentences in a story have been coded
    code_by_sentence = True
    # pause_by_sentence: pause after the coding of each sentence. Entering 'Return' will 
    #                    cause the next sentence to be coded; entering any character will 
    #                    cause the program to exit. Default is to code without any pausing. 
    pause_by_sentence = True
    # pause_by_story: pause after the coding of each story. 
    #pause_by_story = True

    
    # CODING OPTIONS: 
    # Defaults are more or less equivalent to TABARI

    # new_actor_length: Maximum length for new actors extracted from noun phrases if no 
    #                   actor or agent generating a code is found. To disable and just 
    #                   use null codes "---", set to zero; this is the default. 
    #                   Setting this to a large number will extract anything found in a (NP
    #                   noun phrase, though usually true actors contain a small number of words 
    #                   This must be an integer.                       
    new_actor_length = 0

    # require_dyad: Events require a non-null source and target: setting this false is likely
    #               to result in a very large number of nonsense events. As happened with the 
    #               infamous GDELT data set of 2013-2014. And certainly no one wants to see 
    #               that again.
    require_dyad = True

    # stop_on_error: If True, parsing errors causing the program to halt; typically used for 
    #                debugging. With the default [false], the error is written to the error 
    #                file, record is skipped, and processing continues. 
    stop_on_error = False

    # commas: These adjust the length (in words) of comma-delimited clauses that are eliminated 
    #         from the parse. To deactivate, set the max to zero. 
    #         Defaults, based on TABARI, are in ()
    #         comma_min :  internal clause minimum length [2]
    #         comma_max :  internal clause maximum length [8]
    #         comma_bmin : initial ("begin") clause minimum length [0]
    #         comma_bmax : initial clause maximum length [0 : deactivated by default]
    #         comma_emin : terminal ("end") clause minimum length [2]
    #         comma_emax : terminal clause maximum length [8]
    comma_min = 2
    comma_max = 8
    comma_bmin = 0
    comma_bmax = 0
    comma_emin = 2
    comma_emax = 8

    [StanfordNLP]
    stanford_dir = ~/stanford-corenlp/

Differences from TABARI
-----------------------

1. Requires a Penn TreeBank parsed version of the sentence as input and
   Stanford NLP coreferences -- see further discussion below

2. There is no stemming: if you need a stem, use a synset, but meanwhile noun
   and verb forms are more extensively incorporated into the system than they
   were in the earlier version of TABARI (which are the versions where most of
   the dictionary development had been done)

3. Only named entities (NE) can match actors

4. Matching following the verb is restricted to the actual verb phrase(!!).
   Matching prior to the verb is probably more or less equivalent to what
   TABARI did

5. The text input format is considerably more complex and contains embedded
   XML.

6. The dictionary format has changed substantially and will not be compatible
   with TABARI in either direction.

TreeBank parsing is clearly the core difference, and it is substantial in at
least three ways. First, because TABARI was a pattern-based shallow parser, it
could get the right answer for the wrong reason, and at least some of the
dictionary entries -- in particular those treating nouns as if they were verbs,
depend on this. This became very apparent as I was going through the unit
tests, many of which had to be discarded because they used only patterns, not
grammatically-correct constructions. Which are also a lot harder to
construct. PETR does not allow this: for starters, it only matches true verbs
--- (VP (VB in the parse tree --- and if a parser is given a ungrammatical
sentence, results can be unpredictable.

Which leads to the second issue: parsed input is typically less robust than
pattern- based input, since the addition or deletion of words that seem trivial
to a native speaker (or at least this native speaker) will sometimes change the
parse (which is, of course, itself a very complex program). This probably has
two implications. First, it means that PETR will be more conservative than TAB,
which again seems to be what people want. Second, probably a lot of work is
going to need to be done getting the dictionaries adapted to this. That said,
there have also been some pleasant surprises where features that had to be
dealt with as special cases in TAB are taken care of automatically in PETR, and
the full parts-of-speech markup should simplify the dictionaries.

Third, switching to an open-source parser means that we are relegating the
parsing to the linguists, and more generally to the very large community that
develops parser that can produce TreeBank output. I had originally expected
that this would simplify the code but it does not really seem to have done so,
since the quirks of a full parse are, if anything, more complex than those of a
pattern-based shallow parse. And the parse doesn't take care of everything: for
example comma-delimited clause deletion and passive voice detection are
essentially done the same way as in TAB, but now with the added complexity of
requiring the tags in the tree to remain balanced. This is also essentially
just an extension of TAB, which already tagged a number of phrases and clauses:
the difference is that TreeBank tags all of them.}  One thing that may result
from this will be the ability to easily adapt PETR to other languages. TAB
had been adapted to Spanish a couple of times, and KEDS to German and Spanish.
since the TreeBank format is standard across many languages. It will still be
necessary to adjust for some of the phrase and word-ordering rules, but because
of the complete markup, and the fact that the system works *only* with this
markup, modification for other languages should be easier.

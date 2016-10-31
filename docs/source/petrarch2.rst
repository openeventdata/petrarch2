PETRARCH2
=========

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

Command Line Interface
----------------------

**Primary options**

``batch``
  Run the PETRARCH parser with all options specified in the config file. If combined with 
  ``-c``, configuration will be read from that file; default config file is  ``PETR_config.ini``.

``parse``
  **NOTE:** This command is deprecated in PETRARCH2.
  Run the PETRARCH parser specifying files in the command line
  

The following options can be used in the command line


-i, --inputs    File, or directory of files, to parse.

-o, --output    Output file for parsed events

-P, --parsed    Input has already been parsed: all input records contain  StanfordNLP-parsed  <Parse>...</Parse> block. Defaults to ``False``.

-c, --config    Filepath for the PETRARCH configuration file. Defaults to ``PETR_config.ini``.



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

    # write_actor_root: If True, the event record will include the text of the actor root: 
    #                   The root is the text at the head of the actor synonym set in the 
    #                   dictionary. Default is False
    write_actor_root = False

    # write_actor_text: If True, the event record will include include the complete text of 
    #                   the noun phrase that was used to identify the actor.  Default is False
    write_actor_text = False

    # require_dyad: Events require a non-null source and target: setting this false is likely
    #               to result in a very large number of nonsense events. As happened with the 
    #               infamous GDELT data set of 2013-2014. And certainly no one wants to see 
    #               that again.
    require_dyad = True

    # stop_on_error: If True, parsing errors causing the program to halt; typically used for 
    #                debugging. With the default [false], the error is written to the error 
    #                file, record is skipped, and processing continues. 
    stop_on_error = False


    [StanfordNLP]
    stanford_dir = ~/stanford-corenlp/


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


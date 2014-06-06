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

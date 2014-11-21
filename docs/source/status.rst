Status of the program 21-November-2014
======================================

PETARCH now has virtually all of the functionality of TABARI except for the following:

* Coding of multiple clauses is not quite implemented at the TABARI level: the
  source in the first phrase is not forwarded

* The simple pronoun resolution rules of TABARI have not been implemented

The program has now been operational for about four months, both in real time coding 
and batch coding: we recently completed a batch coding run involving several million 
sentences for a thirty-year time span and the program did not crash. It will occasionally
log errors -- for example the 60,000 AFP stories from the
GigaWord we use as a test suite generates 3 [trapped] bugs -- but these involve fairly esoteric constructions, often cases where the CoreNLP parse is off. 

TABARI *.agent* and *.verbs* dictionaries are no longer compatible with the program; 
the *.actor* dictionaries still are -- assuming these us TABARI 0.8 indented date restrictions, not the older in-line format -- but this might change in the future.

*NEW FEATURES NOT IN TABARI:*

1.  There is a new agents dictionary format which can automatically generate word forms

2.   PETRARCH can pull out noun phrases which correspond to actors not in the
     dictionary: this is controlled by the parameter ``new_actor_length`` in
     *PETR_config.ini* (see that file for description of this feature)

3. The *.verbs* dictionary is now organized around WordNet synonym sets and involves a new format; 
this substantially reduces the level of redundancy in the existing dictionaries. See the comments
in PETRwriter.read_verb_dictionary() for an extended discussion of these issues.
     
4.  The ``write_actor_root`` and ``write_actor_text`` options in the config file add to the 
    output record the actor 
    'root' -- the phrase that begins a list of synonyms -- and the full text in the 
    noun phrase used to code the actor. 
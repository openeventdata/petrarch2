Some Notes
==========

Notes pulled from the head of `petrarch.py` and some other places.


Status of the program 12-May-2014
---------------------------------

This now has most of the functionality of TABARI except for the following:

* % tokens in patterns

* Coding of multiple clauses is not quite implemented at the TABARI level: the
  source in the first phrase is not forwarded

* The simple pronoun resolution rules of TABARI have not been implemented

I'm now down to only 3 [trapped] bugs in coding 60,000 AFP stories from the
GigaWord, and these are fairly esoteric constructions.  The system now codes
243 of the TABARI unit-test records, which is most of them, plus some new
records specific to PETR.

So, those remaining functions, the debugging of the compounds, handling a
few more noun-related tags (specifically (NML and (NP-TMP)  and a few
additional unimplemented features scattered through the code are what is
left, and I may be able to get to those in the next couple of weeks, and
certainly before the end of the month.  At the point of completing those,
I'll probably shift to getting the WordNet-based verb dictionaries into the
system.

Despite the nearly full implementation, this still seems to be getting a
substantially lower yield of event compared to TABARI: this needs further
exploration, though may be in part a feature of GigaWord, but it is probably
also very strongly affected by the stemming in the existing CAMEO
dictionary.

*NEW FEATURES NOT IN TABARI WHICH HAVE BEEN IMPLEMENTED:*

1.  There is a new agents dictionary format: this is the first of the format
    changes that will modify these to the point where they are not compatible
    for TABARI dictionaries

2.   Program can pull out noun phrases which correspond to actors not in the
     dictionary: this is controlled by the parameter new_actor_length in
     config.ini (see that file for description of this feature)


Compatibilities with TABARI dictionaries
----------------------------------------

PETRARCH has a much richer dictionary syntax than TABARI, which will eventually
accommodate the WordNet-enhanced dictionaries developed at Penn State as well
as reducing the level of redundancy in the existing dictionaries. While the
initial version of the program could use existing TABARI dictionaries, this
compatibility will decline with further developments and only the
PETRARCH-specific dictionaries can be used

15-Nov-2013: Requires TABARI 0.8 indented date restrictions, not older in-line format

23-Apr-2014: PETRARCH-formatted agents dictionary required

12-May-2014: Disjunctive phrases no longer recognized in the .verbs dictionary


Notes for the manual
--------------------

1. There are an assortment of comments that contain the string '???' which
   indicate points that need to be clarified when re-writing the TABARI manual.


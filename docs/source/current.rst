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


[What the heck is TABARI??: `http://eventdata.parusanalytics.com/software.dir/tabari.html <http://eventdata.parusanalytics.com/software.dir/tabari.html>`_]



Differences from TABARI
-----------------------

[which will be of little interest unless you are one of the fifty or so people
in the world who actually worked with TABARI, but it is possible that you've
got an old TABARI dictionary and some of this might be relevant.]

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
depend on this \fn{This became very apparent as I was going through the unit
tests, many of which had to be discarded because they used only patterns, not
grammatically-correct constructions. Which are also a lot harder to
construct.}. PETR does not allow this: for starters, it only matches true verbs
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
develops parser that can produce TreeBank output. \fn{I had originally expected
that this would simplify the code but it does not really seem to have done so,
since the quirks of a full parse are, if anything, more complex than those of a
pattern-based shallow parse. And the parse doesn't take care of everything: for
example comma-delimited clause deletion and passive voice detection are
essentially done the same way as in TAB, but now with the added complexity of
requiring the tags in the tree to remain balanced. This is also essentially
just an extension of TAB, which already tagged a number of phrases and clauses:
the difference is that TreeBank tags all of them.}  One thing that may result
from this will be the ability to easily adapt PETR to other languages \fn{TAB
had been adapted to Spanish a couple of times, and KEDS to German and Spanish.}
since the TreeBank format is standard across many languages. It will still be
necessary to adjust for some of the phrase and word-ordering rules, but because
of the complete markup, and the fact that the system works *only* with this
markup, modification for other languages should be easier.

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


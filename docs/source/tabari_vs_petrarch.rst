===================
TABARI VS. PETRARCH
===================

PETRARCH is the third implementation of a series of automated coders which 
originated with the Kansas Event Data System (KEDS) project at the University of Kansas in the 1990s: for details see 
`http://eventdata.parusanalytics.com/papers.dir/KEDS.History.0611.pdf <http://eventdata.parusanalytics.com/papers.dir/KEDS.History.0611.pdf>`_. PETRARCH's immediate predecessor is the C++ TABARI program and while the codebase for PETRARCH is entirely new, at the present time [June 2014] the system still uses modified versions of a number of TABARI dictionaries, though we expect this will gradually change. Furthermore, TABARI is still in active use -- sometimes with, sometimes without attribution -- and consequently this section will briefly discuss the differences between the two programs.

The core difference -- which cascades through the entire system -- is that PETRARCH uses fully-parsed Penn TreeBank input: its coding is parser-based, whereas the coding of TABARI was largely pattern-based. This has a number of very substantial implications. 

First, because TABARI was a pattern-based shallow parser, it
could get the right answer for the wrong reason, and at least some of the
dictionary entries -- in particular those treating nouns as if they were verbs -- 
depended on this. This became very apparent in the adaptations of the TABARI unit
tests, many of which had to be discarded because they used only patterns, not
grammatically-correct constructions. 
PETRARCH, in contrast, only matches true verbs: ``(VP (VB`` in the parse tree. While means that a small number of existing patterns that were erroneously based on nouns no longer work, the parser virtually eliminates the problem of noun-verb disambiguation (or, rather, relegates it to whatever parser is producing the Treebank output), which is a vastly more important issue. 

Parsed input is, however, typically less robust than
pattern-based input, since the addition or deletion of words that seem trivial
to a native speaker (or at least this native speaker) will sometimes change the
parse (which is, of course, itself produced by a very complex program). This probably has
two implications. First, it means that PETRARCH will be more conservative than TABARI,
which again seems to be what people want. Second, while the TABARI dictionaries provide a starting point, they will eventually need to be adapted.  That said,
there have also been some pleasant surprises where features that had to be
dealt with as special cases in TABARI are taken care of automatically in PETRARCH, and
the full parts-of-speech markup should simplify the dictionaries: a large number of the TABARI verb patterns existed solely to handle noun-verb disambiguation and can be eliminated.

Third, switching to one or more open-source parsers -- we are currently using the Stanford CoreNLP parser -- means that we are relegating the
parsing to the linguists [#]_ and more generally to the very large community that
developing parsers that can produce TreeBank output. [#]_ This has somewhat simplified the code but not dramatically as the quirks of a full parse are, if anything, more complex than those of a
pattern-based shallow parse. And the parse doesn't take care of everything: for
example comma-delimited clause deletion and passive voice detection are
essentially done the same way as in TABARI. 

Nonetheless, the shift to Treebank input may allow PETRARCH to be easily adapted to other languages [#]_ since the TreeBank format is standard across many languages. It will still be
necessary to adjust for some of the phrase and word-ordering rules, and of course the dictionaries would need to be translated, but except for passive-voice detection. PETRARCH works only with the Treebank tags, not the content.

Finally, Treebank identifies any noun phrase that could potentially be a political actor, whereas TABARI was restricted to identifying actors that were in the dictionaries. By adjusting the ``new_actor_length`` parameter in the ``PETR_config.ini`` file, arbitrary noun phrases can be recorded in the source and target slots of the event data whenever these occur in the subject and object positions of the verb phrase; this allows post-processing of the data to extract the high-frequency named entities which are not in the dictionaries. 

So what's not to like? Speed. TABARI could code very rapidly, typically around 1,000 to 2,000 sentences per second depending on the dictionaries. PETRARCH currently codes at only about 150 sentences per second, and the CoreNLP system parses at about 2 to 5 sentences per second. Consequently the computational demands are much higher, and high-volume coding will require a cluster computer of some sort. Presumably most of the performance hit in PETRARCH is due to the use of Python rather than C++ [#]_

A few other major changes:

1. PETRARCH does not use word stemming. Like the later versions of TABARI, it  automatically produces regular form forms and noun plurals, and allows irregular forms to be specified: the current dictionary has all of these.

2. PETRARCH makes much greater use of synonym sets than TABARI, and these are objects in the dictionaries in general, not just specific patterns. [#]_ The PETRARCH verb dictionary has organized around both verb and noun synonym sets derived from `WordNet <http://wordnet.princeton.edu/>`_ and other sources

3. The functions of the TABARI `.project` and `.options` files are now incorporated into the ``PETR_config.ini`` file.

4. Earlier versions of TABARI incorporated a text-based user interface for machine-assisted coding and dictionary development. As the complexity of the TABARI dictionaries increased, this gradually broke down, and no comparable facility is planned for the PETRARCH program itself, though it would be possible to create one or more standalone programs that invoke the program to do doing. 

5. The text input format is considerably more complex and contains embedded
   XML.

6. The dictionary formats have changed substantially and will not be compatible
   with TABARI in either direction.
   
7. Discard phrases -- the TABARI ``[###]`` codes -- are incorporated into a separate dictionary file rather than being part of the `.actors` and `.verbs` dictionaries.
   
.. [#] Resist impulse to insert remark here about political scientists writing parsers being similar to [MIT] linguists pontificating on politics...

.. [#] But would someone please write a high-speed Treebank parser in Python rather than Java? And "high-speed" probably rules out ``nltk.``

.. [#]  TABARI had been adapted to Spanish a couple of times, and KEDS to German and Spanish.

.. [#]  The payoff here is that the Python code is substantially shorter and easier to modify, Python is much more robust across platforms than C++, and Python has a much larger, and younger, community of programmers.

.. [#] TABARI version 0.8 finally implemented synonym sets but dictionaries using these were never developed.
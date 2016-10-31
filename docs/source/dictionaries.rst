PETRARCH Dictionary Formats
===========================

There are five separate input dictionaries or lists that PETRACH makes use of:
the verb dictionary, the actor dictionary, the agent dictionary, the issues dictionary,
and the discard list. The following sections describe these files in
greater detail. In addition to this documentation, which is intended for individuals 
planning to work on dictionaries, the source code contains internal documentation on
how the dictionary information is stored by the program.

The PETRARCH dictionaries are generally derived from the earlier TABARI dictionaries, 
and information on those formats can be found in the TABARI manual: 

`http://eventdata.parusanalytics.com/tabari.dir/TABARI.0.8.4b2.manual.pdf <http://eventdata.parusanalytics.com/tabari.dir/TABARI.0.8.4b2.manual.pdf>`_


General Rules for dictionaries
------------------------------

All of the files are in "flat ASCII" format and should only be edited using a program that produces a a file without embedded control codes; for example Emacs or BBEdit.

**Comments in input files:**

Comments should be delineated with a hash sign #, as in Python or Unix
Everything after this symbol and before the next newline will be ignored by the parser.
::

	# this is a Python-like comment, inherited from Unix
	
	something I want # followed by a Python-like comment

The program is *not* set up to handle clever variations like nested comments,  multiple 
comments on a line, or non-comment information in multi-line comments: yes, we are
perfectly capable of writing code that could handle these contingencies, but it 
is not a priority at the moment. We trust you can cope within these limits.

Blank lines and lines with only whitespace are also skipped.

Storage in Memory
-----------------
When the dictionaries are read by the program, they are read into memories as prefix trees,
i.e. Tries. This makes searching the stored dictionaries very efficient during the parse, but
adds to the memory overhead and can be somewhat confusing if you don't know what you're working
with. This data structure stores each word at a node, and following a path in the tree will lead
to a pattern. Let's take a small part of the discard list as an example:

.. code-block:: none

    WORLD BOXING ASSOCIATION
    WORLD BOXING COUNCIL
    WORLD CUP


These three entries would be stored in the following Trie:

.. code-block:: none

                PETRglobals.DiscardList
                            |
                            |
                           WORLD
                            /\
                   ________/  \_________
                  |                     |
                BOXING                 CUP
                  /\                    |
             ____/  \______             #
            |              |
          COUNCIL     ASSOCIATION
            |              |
            #              #


Note that all patterns are terminated with a hash sign. This is to signify that there is
a pattern that ends here. If no hash sign is present during a matching, then that would be
an incomplete match. For the Issue and Actor/Agent dictionaries, the hash sign then links
to a storage container with the information associated with the entry.

The Trie is the general principle underlying all of the dictionary storage in Petrarch. The
Verb dictionary storage has its own quirks due to the increased complexity of patterns present,
but it is still fundamentally a Trie. That will be discussed in the verb section.



Verb Dictionary
---------------

The verb dictionary file consists of a set of synsets followed by a series of verb
synonyms and patterns.


**Synsets:**

Synonym sets (synsets) are labelled with a string beginning with & and defined using
the label followed by a series of lines beginning with ``+`` containing words or phrases.
The phrases are interpreted as requiring consecutive words; the words can be separated 
with underscores (they are converted to spaces). Synset phrases can
only contain words, not ``$``, ``+``, ``%`` or ``^`` tokens. Synsets can be used anywhere in a pattern that a word or phrase can be used. A synset must be defined before it is used: a pattern containing an undefined synset will be ignored.

Regular plurals are generated automatically  by adding 'S' to the root, adding 'IES' if the root ends in 'Y', and added 'ES' if the root ends in 'SS'.
The method for handling irregular plurals is currently different for the verbs
and agents dictionaries: these will be reconciled in the future, probably using
the agents syntax.
Plurals are not created when:

* The phrase ends with ``_``. 

* The label ends with ``_``, in which case plurals are not generated for any of
  the phrases; this is typically used for synonym sets that do not involve nouns
        
The ``_`` is dropped in both cases. Irregular plurals do not have a special syntax; 
just enter these as additional synonyms.


**Verb Synonym Blocks and Patterns:**

A verb synonym block is a set of verbs which are synonymous (or close enough) with 
respect to the patterns. The program automatically generates the regular forms of the 
verb if it is regular (and, implicitly, English); otherwise the irregular forms can be 
specified in ``{...}`` following the primary verb. An optional code for the isolated verb 
can	follow in ``[...]``.  

The verb block begins with a comment of the form 

::

--- <GENERAL DESCRIPTION> [<CODE>] ---

where the ``---`` signals the beginning of a new block. The code in ``[...]`` is the 
primary code -- typically a two-digit+0 cue-category code -- for the block, and this 
will be used for all other verbs unless these have their own code. If no code is 
present, this defaults to the null code ``---`` which indicates that the isolated verb 
does not generate an event. The null code also can be used as a secondary code.	


**Multiple-word verbs**

Multiple-word "verbs" such as "CONDON OFF", "WIRE TAP" and "BEEF UP" are entered by
connecting the words with an underscore and putting a '+'
in front of the word in the phrase that is going to be identified as a verb.
If there is no ``{...}``, regular 
forms are constructed for the word designated by '+'; otherwise all of the irregular 
forms are given in ``{...}``. If you can't figure out which part of the phrase is the 
verb, the phrase you are looking at is probably a noun, not a verb. Multi-word verbs 
are treated in patterns just as single-word verbs are treated.


Example:

::

    +BEEF_UP
    +CORDON_OFF {+CORDONED_OFF +CORDONS_OFF +CORDONING_OFF}
    +COME_UPON {+COMES_UPON +CAME_UPON +COMING_UPON}
    WIRE_+TAP {WIRE_+TAPS WIRE_+TAPPED  WIRE_+TAPPING }


A note on the current state of Petrarch's ability to handle compound verbs: The syntax
parser we use (Stanford CoreNLP) often has trouble dealing with pre-compounded verbs, i.e.
those where the extra stuff comes before the verb, and because Petrarch relies so heavily on
this parser, meanings are sometimes missed. Post-compound verbs don't share this problem, and
are more frequently parsed correctly.



**Patterns**

This is followed by a set of patterns -- these begin with ``-`` -- which are based roughly on
the syntax from TABARI patterns, but the patterns in Petrarch's dictionaries also contain
some syntactic annotation. Pattern lines begin with a
-, and are followed by a five-part pattern:

::

- [Pre-Verb Nouns] [Pre-Verb Prepositoins] * [Post-verb Nouns] [Post-verb prepositions]

Any of these can be left empty. Singular nouns are left bare, and should be the "head" of the phrase
they are a member of, e.g. the head of "Much-needed financial aid" would be "aid." If multiple nouns or
adjectives are needed, then that phrase is put in braces as in ``{FINANCIAL AID}``, where the last word is the
head. Prepositional phrases are put in parentheses where the first element is the preposition, and the second
element is a noun, or a braced noun phrase.

::

    * (FOR AID)
    * (FOR {FINANCIAL AID})

After these comes the CAMEO code in brackets. Make sure there is a space before the open brace.
Then, a comment with the intended word to be matched is often included.

Note that these patterns do not contain other verbs. This is different from TABARI, and even earlier
versions of Petrarch. This is to simplify the verbs dictionary, and make the pattern matching
faster and more effective.

**Combinations**

Petrarch handles many verb-verb interactions automatically through its reformatting of CAMEO's semantic
heirarchy (See utilities.convert_code for more). For instance, if it were parsing the phrase

" A will [help B]"
 
it would code "to help B" first, then the phrase would become "A will [_ B 0x0040]".
And then since ``help=0x0040`` is a subcategory of ``will=0x3000``, then it just adds them together,
ending with the code ``[A B 0x3040]``. This code is translated back into CAMEO for the final output,
yielding ``[A B 033]``. This process works for most instances where the idea of the phrase as a whole
is a combination of the ideas of its children.

**Transformations**

Sometimes these verb-vertb interactions aren't represented in the
ontology. It is possible to specify what happens when one verb finds that it is acting on another verb.
Say you wanted to convert phrases of the form "A said A will attack B" into " A threatens B."
You would say

::

~ a (a b WILL_ATTACK) SAY = a b 138

This is effectively a postfix notational system, and every line starts with a ~.
The first element is the topmost source actor, the last element is the topmost verb (the verbs in the patterns
are converted to codes, so synonyms also match). The inner parenthetical has the same format, with the
first element being the lower source, the second the lower target, and the third the lower verb. It
is possible to replace letter variables with a period '.' to represent "non-specified actor", or with
an underscore ``_`` to specify "non-present actor." Verbs can also be replaced with "Q" to mean "any verb."

These transformations are sometimes necessary, but most cases can be handled by the combination process.


**Storage in Memory**

The verb dictionary, when stored into memory, has three subdictionaries: words, patterns, and transformations.

The words portion contains the base verbs. They are stored as ``VERB--STUFF BEFORE--#--STUFF AFTER--#--INFO``. For
most verbs (i.e. those that are not compounds), The entry just goes ``VERB -- # -- # -- INFO``.

The transformation contains almost a literal transcription of the pattern, ordered
``VERB1--SOURCE1--VERB2--SOURCE2--TARGET2--INFO``.

The verb patterns in memory have extra annotative symbols after every word to indicate the type of
word that comes next. The very first word encountered is always a noun. Then it follows a series of rules
that specify what comes next:

  * Comma ',' = The next word is the same type as the previous one
  * Asterisk '*' = The first half of the pattern is over, move to the second half
  * Hash sign '#' = The pattern is over
  * Pipe '|' = The next word is a preposition
  * Dash '-' = The next word is a specifier is a noun or extension of noun phrase

This means that when searching, we only have to check 5 cases, rather than compare to all remaining patterns.
As an example, consider these three example entries under 'request':

::

    * HELP
    * {FINANCIAL HELP}
    * HELP (AGAINST REVOLT)

They would be stored as

::

                            PETRglobals.VerbDict['patterns']['REQUEST']
                                                |
                                                |
                                               '*'
                                                |
                                              HELP
                                              / | \
                                  _'|'_______/  |  \_______ '-' __
                                 |             '#'                |
                                 |                                |
                                 |                           FINANCIAL
                              AGAINST                             |
                                 |                                |
                                 |                               '#'
                                '-'
                                 |
                               REVOLT
                                 |
                                '#'



Note that "Financial Help" is stored as "Help Financial," because "Help" is the head of the phrase
and is thus much easier to find, and once we've found that we can then look for "Financial."


Actor Dictionary
----------------

Actor dictionaries are similar to those used in TABARI (see Chapter 5 of the manual) except that the date restrictions must be on separate lines (in TABARI, this was
optional) The general structure of the actors dictionary is a series of records of the form

::

    [primary phrase]
    [optional synonym phrases beginning with '+']
    [optional date restrictions beginning with '\t']

A "phrase string" is a set of character strings separated by either blanks or
underscores.

A "code" is a character string without blanks

A "date" has the form YYYYMMDD or YYMMDD. These can be mixed, e.g.

::

    JAMES_BYRNES_  ; CountryInfo.txt
        [USAELI 18970101-450703]
        [USAGOV 450703-470121]

**Primary phrase format:**

``phrase_string  { optional [code] }``

If the code is present, it becomes the default code if none of the date restrictions
are satisfied. If it is not present and none of the restrictions are satisfied,
this is equivalent to a null code

*Synonym phrase*

``+phrase_string``

*Date restriction*

``\t[code restriction]``

where ``\t`` is the tab character and the restriction [1]_ takes the form

::

    <date : applies to times before date
    >date : applies to times after date
    date-date: applies to times between dates

The limits of the date restrictions are interpreted as "or equal to." A date restriction of the form ``\t[code]`` is the same as a default restriction.


**Example:**

::

	# .actor file produced by translate.countryinfo.pl from CountryInfo.120106.txt
	# Generated at: Tue Jan 10 14:09:48 2012
	# Version: CountryInfo.120106.txt

	AFGHANISTAN_  [AFG]
	+AFGHAN_
	+AFGANISTAN_
	+AFGHANESTAN_
	+AFGHANYSTAN_
	+KABUL_
	+HERAT_

	MOHAMMAD_ZAHIR_SHAH_  ; CountryInfo.txt
		[AFGELI 320101-331108]
		[AFGGOV 331108-730717]
		[AFGELI 730717-070723]

	ABDUL_QADIR_  ; CountryInfo.txt
	+NUR_MOHAMMAD_TARAKI_  ; CountryInfo.txt
	+HAFIZULLAH_AMIN_  ; CountryInfo.txt
		[AFGELI 620101-780427]
		[AFGGOV 780427-780430]
		[AFGELI]

	HAMID_KARZAI_  [AFGMIL]; CountryInfo.txt
	+BABRAK_KARMAL_  ; CountryInfo.txt
	+SIBGHATULLAH_MOJADEDI_  ; CountryInfo.txt
		[AFGGOV 791227-861124]
		[AFGGOV 791227-810611]

**Detecting actors which are not in the dictionary**

Because PETRARCH uses parsed input, it has the option of detecting actors---noun phrases---which are not in the dictionary. This is set using the ``new_actor_length`` option in the ``PETR_config.ini`` file: see the description of that file for details.

Agent Dictionary
----------------

Basic structure of the agents dictionary is a series of records of the form

::

        phrase_string {optional plural}  [agent_code]


A "phrase string" is a set of character strings separated by either blanks or
underscores. As with the verb patterns, a blank between words means that additional words can occur between the previous word and the next word; a ``_`` (underscore) means that the words must be consecutive.


An "agent_code" is a character string without blanks that is either preceded (typically)
or followed by ``~``. If the ``~`` precedes the code, the code is added after the actor
code; if it follows the code, the code is added before the actor code (usually done
for organizations, e.g. ``NGO~``)

**Plurals:**

Regular plurals -- those formed by adding 'S' to the root, adding 'IES' if the
root ends in 'Y', and added 'ES' if the root ends in 'SS' -- are generated automatically

If the plural has some other form, it follows the root inside ``{...}``  [1]_

If a plural should not be formed -- that is, the root is only singular or only
plural, or the singular and plural have the same form (e.g. "police"), use a null
string inside ``{}``.

If there is more than one form of the plural -- "attorneys general" and "attorneys
generals" are both in use -- just make a second entry with one of the plural forms
nulled (though in this instance -- ain't living English wonderful? -- you could null
the singular and use an automatic plural on the plural form) Though in a couple
test sentences, this phrase confused the CoreNLP parser.

**Substitution Markers:**

These are used to handle complex equivalents, notably

::

        !PERSON! = MAN, MEN, WOMAN, WOMEN, PERSON
        !MINST! = MINISTER, MINISTERS, MINISTRY, MINISTRIES

and used in the form

::

        CONGRESS!PERSON! [~LEG}
        !MINIST!_OF_INTERNAL_AFFAIRS

The marker for the substitution set is of the form ``!...!`` and is followed by an =
and a comma-delimited list; spaces are stripped from the elements of the list so
these can be added for clarity. Every item in the list is substituted for the marker,
with no additional plural formation, so the first construction would generate

::

        CONGRESSMAN [~LEG}
        CONGRESSMEN [~LEG}
        CONGRESSWOMAN [~LEG}
        CONGRESSWOMEN [~LEG}
        CONGRESSPERSON [~LEG}


**Example:**

::

    <!-- PETRARCH VALIDATION SUITE AGENTS DICTIONARY -->
    <!-- VERSION: 0.1 -->
    <!-- Last Update: 27 November 2013 -->

    PARLIAMENTARY_OPPOSITION {} [~OPP] #jap 11 Oct 2002
    AMBASSADOR [~GOV] # LRP 02 Jun 2004
    COPTIC_CHRISTIAN [~CHRCPT] # BNL 10 Jan 2002
    FOREIGN_MINISTER [~GOVFRM] # jap 4/14/01
    PRESIDENT [~GOVPRS] # ns 6/26/01
    AIR_FORCE {} [~MIL] # ab 06 Jul 2005
    OFFICIAL_MEDIA {} [~GOVMED] # ab 16 Aug 2005
    ATTORNEY_GENERAL {ATTORNEYS_GENERAL} [~GOVATG] # mj 05 Jan 2006
    FOREIGN_MINISTRY [~GOV] # mj 17 Apr 2006
    HUMAN_RIGHTS_ACTIVISTS  [NGM~] # ns 6/14/01
    HUMAN_RIGHTS_BODY  [NGO~] # BNL 07 Dec 2001
    TROOP {} [~MIL] # ab 22 Aug 2005

Discard List
------------

The discard list is used to identify sentences that should not be coded, for example sports events and historical chronologies. [2]_
If the string, prefixed with ``' '``, is found in the ``<Text>...</Text>`` sentence, the
sentence is not coded. Prefixing the string with a ``+`` means the entire story is not
coded with the string is found. If the string ends with ``_``, the matched string must also end with
a blank or punctuation mark; otherwise it is treated as a stem. The matching is not
case sensitive.

.. [2] In TABARI, discards were intermixed in the ``.actors`` dictionary and ``.verbs`` patterns, using the ``[###]`` code. They are now a separate dictionary. 


**Example:**

::

    +5K RUN #  ELH 06 Oct 2009
    +ACADEMY AWARD   # LRP 08 Mar 2004
    AFL GRAND FINAL   # MleH 06 Aug 2009
    AFRICAN NATIONS CUP   # ab 13 Jun 2005
    AMATEUR BOXING TOURNAMENT   # CTA 30 Jul 2009
    AMELIA EARHART
    ANDRE AGASSI   # LRP 10 Mar 2004
    ASIAN CUP   # BNL 01 May 2003
    ASIAN FOOTBALL   # ATS 9/27/01
    ASIAN MASTERS CUP   # CTA 28 Jul 2009
    +ASIAN WINTER GAMES   # sls 14 Mar 2008
    ATP HARDCOURT TOURNAMENT   # mj 26 Apr 2006
    ATTACK ON PEARL HARBOR   # MleH 10 Aug 2009
    AUSTRALIAN OPEN
    AVATAR   # CTA 14 Jul 2009
    AZEROTH   # CTA 14 Jul 2009  (World of Warcraft)
    BADMINTON  # MleH 28 Jul 2009
    BALLCLUB   # MleH 10 Aug 2009
    BASEBALL
    BASKETBALL
    BATSMAN  # MleH 14 Jul 2009
    BATSMEN  # MleH 12 Jul 2009

Issues List
-----------

The optional ``Issues`` dictionary is used to do simple string matching and return a comma-delimited list of codes. The standard format is simply a set of lines of the form

        ``<string> [<code>]``

For purposes of matching, a ``' '`` is added to the beginning and end of the string: at
present there are no wild cards, though that is easily added.

The following expansions can be used (these apply to the string that follows up to
the next blank):

::

        n: Create the singular and plural of the noun
        v: Create the regular verb forms ('S','ED','ING')
        +: Create versions with ' ' and '-'

The file format allows ``#`` to be used as a in-line comment delimiter.

Issues are written to the event record as a comma-delimited list to a tab-delimited
field, e.g.

::

    20080801	ABC	EDF	0001	POSTSECONDARY_EDUCATION 2, LITERACY 1	AFP0808-01-M008-02
    20080801	ABC	EDF	0004        AFP0808-01-M007-01
    20080801	ABC	EDF	0001	NUCLEAR_WEAPONS 1	AFP0808-01-M008-01

where ``XXXX NN``, corresponds to the issue code and the number of matched phrases in the
sentence that generated the event.

This feature is optional and triggered by a file name in the
``PETR_config.ini`` file at ``issuefile_name = Phoenix.issues.140225.txt``.

In the current code, the occurrence of an ignore phrase of either type cancels all
coding of issues from the sentence.

**Example:**

::

    <ISSUE CATEGORY="ID_ATROCITY">
    n:atrocity [ID_ATROCITY]
    n:genocide [ID_ATROCITY]
    ethnic cleansing [ID_ATROCITY]
    ethnic v:purge [ID_ATROCITY]
    ethnic n:purge [ID_ATROCITY]
    war n:crime [ID_ATROCITY]
    n:crime against humanity [ID_ATROCITY]
    n:massacre [ID_ATROCITY]
    v:massacre [ID_ATROCITY]
    al+zarqawi network [NAMED_TERROR_GROUP]
    ~Saturday Night massacre
    ~St. Valentine's Day massacre
    ~~Armenian genocide  # not coding historical cases
    </ISSUE>



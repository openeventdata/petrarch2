PETRARCH Dictionary Formats
===========================

There are five separate input dictionaries or lists that PETRACH makes use of:
the verb dictionary, the actor dictionary, the agent dictionary, the discard
list, and the issues list. The following sections describe these files in
greater detail.

Verb Dictionary
---------------

**Verb Dictionary Organization:**

The verb dictionary consists of a set of synsets followed by a series of verb 
synonyms and patterns.

**Verb Synonym Blocks and Patterns:**

A verb synonym block is a set of verbs which are synonymous (or close enough) with 
respect to the patterns. The program automatically generates the regular forms of the 
verb if it is regular (and, implicitly, English); otherwise the irregular forms can be 
specified in {...} following the primary verb. An optional code for the isolated verb 
can	follow in [...].  

The verb block begins with a comment of the form 

::

--- <GENERAL DESCRIPTION> [<CODE>] ---

where the ``###`` signals the beginning of a new block. The code IN [...] is the 
primary code -- typically a two-digit cue-category code -- for the block, and this 
will be used for all other verbs unless these have their own code. Th null code ``---``
which indicates that the isolated verb does not generate an event can be used as 
either a primary or secondary code.

This is followed by a set of patterns -- these begin with ``-`` -- which generally 
follow the same syntax as TABARI patterns. The pattern set is terminated with a 
blank line.
    
**Synsets:**

Synonym sets (synsets) are labelled with a string beginning with & and defined using
the label followed by a series of lines beginning with ``+`` containing words or phrases.
The phrases are interpreted as requiring consecutive words; the words can be separated 
with either spaces or underscores (they are converted to spaces). Synset phrases can 
only contain words, not ``$``, ``+``, ``%`` or ``^`` tokens or synsets. At present, a synsets cannot  
contain another synset as an element. [see note below] Synsets be used anywhere in a  
pattern that a word or phrase can be used. A synset must be defined before it is used:  
a pattern containing an undefined synset will be ignored -- but those definitions can 
occur anywhere in the file.

Plurals are generated automatically using the rules in ``read_verb_dictionary``/ 
``make_plural(st)`` except when

* The phrase ends with ``_``. 

* The label ends with ``_``, in which case plurals are not generated for any of
  the phrases; this is typically used for synonyms that are not nouns
        
The ``_`` is dropped in both cases.

**Example:**

::

    &CURRENCY 
    +DOLLARS
    +EUROS
    +AUSTRIAN FLORIN
    +GOLDEN_GOBLIN_GALLEONS_
    +PESO
    +KRONER_
    +YUM YENNYEN 
    +JAVANESE YEN
    +SWISS FRANCS
    +YEN

    &ALTCURR
    +BITCOIN
    +PIRATE GOLD_   
    +LEPRECHAUN GOLD_

    &AUXVERB3_
    +HAVE
    +HAS
    +HAD


    ### GRANT ### 
    GRANT [070]
    GIVE {GAVE GIVEN }  # jw  11/14/91
    CONTRIBUTE # tony  3/12/91
    - ** &CURRENCY [903] # -PAS 12.01.12
    - ** &ALTCURR [904] # -PAS 14.05.08
    - ** RUPEES  [071]


    ### EXPLAIN_VERBAL ### 
    EXPLAIN [010]
    COMMENT 
    ASSERT 
    SAY  {SAID }
    CLARIFY {CLARIFIES CLARIFIED } [040]
    CLEAR_UP 
    - ** RESTORATION RELATIONS [050:050]  # ANNOUNCE <ab 02 Dec 2005> 
    - ** COMMIT &MILITARY TO + [0332]  # SAY <sls 13 Mar 2008> 
    - ** ATTACK ON + AS &CRIME [018]  # DESCRIBE <ab 31 Dec 2005> 
    - ** &CURRENCY DEBT_RELIEF [0331]  # ANNOUNCE <ab 02 Dec 2005>  , ANNOUNCE
    - ** WELCOMED OFFER FROM + [050]  # ANNOUNCE <ab 02 Dec 2005> 
    - ** + THAT $ WILL PULLOUT [0356]  # INFORM <sms 30 Nov 2007> 
    - ** POSSIBILITY OF &FIGHT [138]  # MENTION <OY 11 Mar 2006> 
    - ** AGREED JOIN COALITION [031]  # ANNOUNCE <OY 15 Mar 2006> 
    - ** TRACES RESPONSIBILITY [112]  # REPORT
    - CONFIRMED ** OF BOMBINGS [010]  # REPORT
    - ** INITIATIVE END &FIGHT [036]  # ANNOUNCE <ab 02 Dec 2005> 

    &TESTSYN3
        +TO THE END
    +TO THE DEATH
    +UNTIL HELL FREEZES OVER

    &TESTSYN4
    +TO THE END OF THE EARTH
    +TO THE DEATH

    VOW  [170] ;tony  3/9/91
    - ** RESIST &TESTSYN3 [113] ; pas 4/20/03
    - ** RESIST &TESTSYN4  [115] ; pas 4/20/03
    - ** RESISTANCE TO THE INVADING  [114] ; pas 4/20/03
    - ** RESIST  [112] ;tony  4/29/91
    - ** WAR  [173] ;tony  4/22/91

**Programming Notes:**

1. 	TABARI allowed recursive synsets -- that is, synsetS embedded in patterns and other synsets. It should be possible to do this fairly easily, at least with basic synsets as elements (not as patterns) but a simple call in syn_match(isupperseq) was not sufficient, so this needs more work.	    

2.	For TABARI legacy purposes, the construction "XXXX_ " is converted to "XXXX_ ", an open match. However, per the comments below, generally TABARI dictionaries should be converted before being used with PETRARCH.
    
3. The verb dictionary is stored as follows:

::

        [0] True: primary form
        [1] Code
        [2:] 3-tuples of lower pattern, upper pattern and code. Upper pattern is stored
                in reverse order
        [0] False
        [1]: optional verb-specific code (otherwise use the primary code)
        [2]: primary form (use as a pointer to the pattern list)	

    
**Verb Dictionary Differences from TABARI:**

On the **very** remote chance -- see Note 1 -- that you are trying to modify a TABARI  
.verbs dictionary to the PETRARCH format, the main thing you will need to eliminate 
any stemmed words:  PETRARCH only works with complete words. On the positive side, 
PETRARCH will only look at string as a "verb" if it has been identified as such by 
the parser, so the patterns required for noun/verb disambiguation are no longer 
needed. PATRARCH also does not allow disconjunctive sets in patterns: to accommodate 
legacy dictionaries, patterns containing these are skipped, but in order to work,
these should be replaced with synsets. Also see additional remarks at the beginning 
of the file.

The other big difference between PETRARCH and TABARI is verb-noun disambiguation: 
the pattern-based approach of TABARI needed a lot of information to insure that a 
word that **might** be a verb was, in fact, a verb (or was a noun that occurred in a 
context where it indicated an event anyway: TABARI's [in]famous tendency to code the 
right thing for the wrong reason. PETRARCH, in contrast, only looks as a verb when 
the parsing has identified it as, in fact, a verb. This dramatically reduces false 
positives and eliminates the need for any pattern which was required simply for 
disambiguation, but it also means that PETRARCH is a lot more discriminating about 
what actually constitutes an event. The big difference here is that verb-only 
codes are the norm in PETRARCH dictionaries but the exception in TABARI dictionaries.

The active PETRARCH verbs dictionary has been extensively reorganized into both 
verb and noun synonym sets, and you are probably better off adding vocabulary to 
this [see Note 1] than converting a dictionary, but it can be done. An unconverted 
TABARI dictionary, on the other hand, will generally not work at all well with 
PETRARCH.

Note 1. 

Yeah, right. Every project we've encountered -- including those funded by multiple 
millions of dollars and those allegedly producing multiple millions of events -- has 
regarded the NSF-funded CAMEO verbs dictionaries as a sacred artifact of the Data 
Fairy, lowered from Asgaard along the lines of this

`http://www.wikiart.org/en/jacob-jordaens/allegory-of-the-peace-of-westphalia-1654 <http://www.wikiart.org/en/jacob-jordaens/allegory-of-the-peace-of-westphalia-1654>`_

[not exactly sure where the .verbs file is in that painting, but I'm sure it is in  
there somewhere]

but then subsequently subject said dictionaries to bitter complaints that they aren't 
coding properly.

Look, dudes and dudettes, these dictionaries have been open source for about as long 
as the US has been at war in Afghanistan -- which is to say, a really long time -- and 
if you don't like how the coding is being done, add some new open-source vocabulary 
to the dictionaries instead of merely parasitizing the existing work. Dude.

The **real** problem, one suspects, is embodied in the following nugget of wisdom:

    Opportunity is missed by most people because it is dressed in overalls and looks 
    like work.
        -Thomas A. Edison

Dude.

Actor Dictionary
----------------

**Actor dictionary list elements:**

Actors are stored in a dictionary of a list of pattern lists keyed on the first
word of the phrase. The pattern lists are sorted by length.  The individual
pattern lists begin with an integer index to the tuple of possible codes (that
is, with the possibility of date restrictions) in PETRglobals.ActorCodes,
followed by the connector from the key, and then a series of 2-tuples
containing the remaining words and connectors. A 2-tuple of the form ('', ' ')
signals the end of the list.

<14.02.26>: Except at the moment these are just 2-item lists, not tuples, but
this could be easily changed and presumably would be more efficient: these are
not changed so they don't need to be lists.<>

**Connector:**

::

    blank: words can occur between the previous word and the next word
    _ (underscore): words must be consecutive: no intervening words

The codes with possible date restrictions are stored as lists in a [genuine] tuple in
``PETRglobals.ActorCodes`` in the following format where ``ordate`` is an ordinal date:

::

    [code] : unrestricted code
    [0,ordate,code] : < restriction
    [1,ordate,code] : > restriction
    [2,ordate,ordate, code] : - (interval) restriction

Synonyms simply use the integer code index to point to these tuples.

**Strict Formatting of the Actor Dictionary:**

[With some additional coding, this can be relaxed, but anything following these
rules should read correctly]

Basic structure is a series of records of the form

::

    [primary phrase]
    [optional synonym phrases beginning with '+']
    [optional date restrictions beginning with '\t']

Material that is ignored:

1. Anything following ';' (this is the old KEDS/TABARI format and should probably be replaced with '#' for consistency
2. Any line beginning with '#' or <!
3. Any null line (that is, line consisting of only \n

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

where restriction -- everything is interpret as 'or equal' -- takes the form

::

    <date : applies to times before date
    >date : applies to times after date
    date-date: applies to times between dates

A date restriction of the form ``\t[code]`` is the same as a default restriction.


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

Agent Dictionary
----------------

Agents are stored in a simpler version of the Actors dictionary: a list of
phrases keyed on the first word of the phrase.  The individual phrase lists
begin with the code, the connector from the key, and then a series of 2-tuples
containing the remaining words and connectors. A 2-tuple of the form ``('', ' ')``
signals the end of the list.

**Connector:**

::

    blank: words can occur between the previous word and the next word
    _ (underscore): words must be consecutive: no intervening words

**Formatting of the Agent Dictionary:**

[With some additional coding, this can be relaxed, but anything following these
rules should read correctly]
Basic structure is a series of records of the form

::

        phrase_string {optional plural}  [agent_code]

Material that is ignored:

1. Anything following '#'
2. Any line beginning with '#' or '<!'
3. Any null line (that is, line consisting of only \n

A "phrase string" is a set of character strings separated by either blanks or
underscores.

A "agent_code" is a character string without blanks that is either preceded (typically)
or followed by ``~``. If the ``~`` precedes the code, the code is added after the actor
code; if it follows the code, the code is added before the actor code (usually done
for organizations, e.g. ``NGO~``)

**Plurals:**

Regular plurals -- those formed by adding 'S' to the root, adding 'IES' if the
root ends in 'Y', and added 'ES' if the root ends in 'SS' -- are generated automatically

If the plural has some other form, it follows the root inside {...}

If a plural should not be formed -- that is, the root is only singular or only
plural, or the singular and plural have the same form (e.g. "police"), use a null
string inside {}.

If there is more than one form of the plural -- "attorneys general" and "attorneys
generals" are both in use -- just make a second entry with one of the plural forms
nulled (though in this instance -- ain't living English wonderful? -- you could null
the singular and use an automatic plural on the plural form) Though in a couple
test sentences, this phrase confused SCNLP.

**Substitution Markers:**

These are used to handle complex equivalents, notably

::

        !PERSON! = MAN, MEN, WOMAN, WOMEN, PERSON
        !MINST! = MINISTER, MINISTERS, MINISTRY, MINISTRIES

and used in the form

::

        CONGRESS!PERSON! [~LEG}
        !MINIST!_OF_INTERNAL_AFFAIRS

The marker for the substitution set is of the form !...! and is followed by an =
and a comma-delimited list; spaces are stripped from the elements of the list so
these can be added for clarity. Every time in the list is substituted for the marker,
with no additional plural formation, so the first construction would generate

::

        CONGRESSMAN [~LEG}
        CONGRESSMEN [~LEG}
        CONGRESSWOMAN [~LEG}
        CONGRESSWOMEN [~LEG}
        CONGRESSPERSON [~LEG}


**Agent code combination rules:**

By default, agent codes are assigned in the order they are found, and all
phrases that correspond to an agent are coded, followed by the removal of
duplicate codes.  This is in contrast to patterns, where only the longest
matching pattern is used. Someone is also welcome to implement this
alternative, but in the spirit of maximizing the information that the agent
system can extract, we're defaulting to "all matches". This can lead to
information that is either redundant (e.g. ``REBEL OPPOSITION GROUP [ROP]``
and ``OPPOSITION GROUP [OPP]`` would yield ROPOPP where ROP is sufficient) or
situations where the same information produces codes in a different order, e.g.
``OPPOSITION' [OPP]``, ``LEGISLATOR [LEG]``, ``PARIAMENTARY [LEG]`` produces ``LEGOPP``
for "pariamentary opposition" and ``OPPLEG`` for "opposition legislators."

Agent code combination rules provide a systematic way of deal with this. Rules
can have two forms:

::

    [original code] => [replacement code] : substitute the replacement when the exact original code occurs

    [original code] +> [replacement code] : substitute the replacement when the any permutation of the 3-character blocks in the original code occurs

Rules are applied until none occur, to 6- and 9-character codes can be transformed
using temporary substitutions.

Rules can be specified either in-line -- typically associated with a set of agents
relevant to the rules -- or in a block

Inline: ``<Combine rule = "...">``
Block: delimited by ``<CombineBlock>...</CombineBlock>`` with the rules on the intervening lines, one per line.

The command ``<Combine rule = "alphabetic">`` specifies that the agents will first
be alphabetized by 3-character blocks -- prefixed and suffixed sets are treated
separately -- and then the rules applied. Again, longer codes can be dealt with
using substitutions.

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
    <Combine rule = "LAWGOVATGMIL => GOV">  # remove match to ATTORNEY and GENERAL
    FOREIGN_MINISTRY [~GOV] # mj 17 Apr 2006
    HUMAN_RIGHTS_ACTIVISTS  [NGM~] # ns 6/14/01
    HUMAN_RIGHTS_BODY  [NGO~] # BNL 07 Dec 2001
    <Combine rule = "NGMNGO +> NGM">
    TROOP {} [~MIL] # ab 22 Aug 2005

Discard List
------------

If the string, prefixed with ' ', is found in the ``<Text>...</Text>`` sentence, the
sentence is not coded. Prefixing the string with a '+' means the entire story is not
coded with the string is found [see ``read_record()`` for details on story/sentence
identification]. If the string ends with '_', the matched string must also end with
a blank or punctuation mark; otherwise it is treated as a stem. The matching is not
case sensitive.

The file format allows ``#`` to be used as a in-line comment delimiter.

File is stored as a simple list and the interpretation of the strings is done in
``check_discards()``.

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

"Issues" do simple string matching and return a comma-delimited list of codes.
The standard format is simply

        ``<string> [<code>]``

For purposes of matching, a ' ' is added to the beginning and end of the string: at
present there are not wild cards, though that is easily added.

The following expansions can be used (these apply to the string that follows up to
the next blank):

::

        n: Create the singular and plural of the noun
        v: Create the regular verb forms ('S','ED','ING')
        +: Create versions with ' ' and '-'

The file format allows ``#`` to be used as a in-line comment delimiter.

File is stored in ``PETRglobals.IssueList`` as a list of tuples (string, index) where
index refers to the location of the code in ``PETRglobals.IssueCodes``. The coding is done
in ``check_issues()``.

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



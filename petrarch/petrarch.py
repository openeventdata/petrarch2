import os
import sys
import glob
import time
import argparse
import xml.etree.ElementTree as ET

import PETRglobals  # global variables
import PETRreader  # input routines
import PETRwriter  # output routines
import utilities


# ================================  PARSER/CODER GLOBALS  ================== #

ParseList = []   # linearized version of parse tree
ParseStart = 0   # first element to check (skips (ROOT, initial (S

# text that can be matched prior to the verb; this is stored in reverse order
UpperSeq = []
LowerSeq = []  # text that can be matched following the verb

SourceLoc = 0  # location of the source within the Upper/LowerSeq
TargetLoc = 0  # location of the target within the Upper/LowerSeq

SentenceID = ''   # ID line
EventCode = ''   # event code from the current verb
SourceCode = ''   # source code from the current verb
TargetCode = ''   # target code from the current verb


# ================================  VALIDATION GLOBALS  ==================== #

DoValidation = False   # using a validation file
ValidOnly = False      # only evaluate cases where <Sentence valid="true">
# validation mode : code triples that were produced; set in make_event_strings
CodedEvents = []
ValidEvents = []  # validation mode : code triples that should be produced
ValidInclude = []  # validation mode : list of categories to include
ValidExclude = []  # validation mode : list of categories to exclude
# validation mode :pause conditions: 1: always; -1 never; 0 only on error
# [default]
ValidPause = 0


# ================================  UTILITY GLOBALS  ====================== #


# ================================  DEBUGGING GLOBALS  ==================== #
# (comment out the second line in the pair to activate. Like you couldn't
# figure that out.) prints ParseList in
# evaluate_validation_record()/code_record() following
# NE assignment
ShowParseList = True
ShowParseList = False

ShowRTTrees = True  # displays parse trees in read_TreeBank
ShowRTTrees = False

# prints upper and lower sequences ParseList in make_check_sequences()
ShowCodingSeq = True
ShowCodingSeq = False

ShowPattMatch = True  # prints pattern match info in check_verbs()
ShowPattMatch = False

# prints search and intermediate strings in the (NE conversion
ShowNEParsing = True
ShowNEParsing = False

ShowMarkCompd = True  # prints intermediate strings in the compound markup
ShowMarkCompd = False


# ================== EXCEPTIONS ================== #

class DupError(Exception):  # template
    pass


class MissingAttr(Exception):  # could not find expected attribute field
    pass


class StopCoding(Exception):  # exit the coding due to <Stop>
    pass


class HasParseError(Exception):  # exit the coding due to parsing error
    pass


class SkipRecord(Exception):  # skip a validation record
    pass


class UnbalancedTree(Exception):  # unbalanced () in the parse tree
    pass


# ================== ERROR MESSAGE STRINGS ================== #

ErrMsgExitValidation = "\nExiting: This information is required for running a validation file"
ErrMsgUnbalancedTree = "Unbalanced <Parse> tree; record was skipped"


def raise_parsing_error(call_location_string):
# <14.02.27: this is currently used as a generic escape from misbehaving
# functions, so it is not necessarily an actual unbalanced tree, just that
# we've hit something unexpected.
    global SentenceID, NParseErrors, DoValidation
    errorstring = 'Parsing error in ' + call_location_string
    PETRwriter.write_record_error(errorstring, SentenceID)
#	print errorstring
    if not DoValidation:
        NParseErrors += 1
    if PETRglobals.StoponError:
        raise HasParseError
    else:
        raise UnbalancedTree(errorstring)


# ========================== DEBUGGING FUNCTIONS ========================== #

def show_tree_string(sent):
    """
    Indexes the () or (~in a string tree and prints as an indented list.
    """
# show_tree_string() also prints the totals
# call with ' '.join(list) to handle the list versions of the string
    newlev = False
    level = -1
    prevlevel = -1
    ka = 0
    nopen = 0
    nclose = 0
    sout = ''
    while ka < len(sent):
        if sent[ka] == '(':
            level += 1
            nopen += 1
            newlev = True
            if level != prevlevel or 'VP' == sent[ka + 1:ka + 3] or 'SB' == sent[ka + 1:ka + 3]:
                # new line only with change in level, also with (VP, (SB
                sout += '\n' + level * '  '
# sout += '\n' + level*'  '                         # new line for every (
            sout += '(-' + str(level) + ' '
        elif sent[ka] == ')' or sent[ka] == '~':
            nclose += 1
            prevlevel = level
            if not newlev:
                sout += '\n' + level * '  '
            if sent[ka] == ')':
                sout += str(level) + '-)'
            else:
                sout += str(level) + '~'
            level -= 1
            newlev = False
        else:
            sout += sent[ka]
        ka += 1
    print sout
    if nopen == nclose:
        print "Balanced:",
    else:
        print "Unbalanced:",
    print "Open", nopen, "Close", nclose, '\n'
    if nopen != nclose and PETRglobals.StoponError:
        raise HasParseError


def check_balance():
    """
    Check the (/~ count in a ParseList and raises UnbalancedTree if it is not
    balanced.
    """
    nopen = 0
    nclose = 0
    ka = 0
    while ka < len(ParseList):
        if ParseList[ka] == '(':
            nopen += 1
        elif ParseList[ka] == '~':
            nclose += 1
        ka += 1
    if nopen != nclose:
        raise UnbalancedTree

# ========================== VALIDATION FUNCTIONS ========================== #


def change_Config_Options(line):
    """Changes selected configuration options."""
    # need more robust error checking
    theoption = line['option']
    value = line['value']
    print "<Config>: changing", theoption, "to", value
    if theoption == 'new_actor_length':
        try:
            PETRglobals.NewActorLength = int(value)
        except ValueError:
            PETRwriter.write_FIN_error(
                "<Config>: new_actor_length value must be an integer; command ignored")
    elif theoption == 'require_dyad':
        PETRglobals.RequireDyad = not 'false' in value.lower()
    elif theoption == 'stop_on_error':
        PETRglobals.StoponError = not 'false' in value.lower()
    elif 'comma_' in theoption:
        try:
            cval = int(value)
        except ValueError:
            PETRwriter.write_FIN_error(
                "<Config>: comma_* value must be an integer; command ignored")
            return
        if '_min' in theoption:
            PETRglobals.CommaMin = cval
        elif '_max' in theoption:
            PETRglobals.CommaMax = cval
        elif '_bmin' in theoption:
            PETRglobals.CommaBMin = cval
        elif '_bmax' in theoption:
            PETRglobals.CommaBMax = cval
        elif '_emin' in theoption:
            PETRglobals.CommaEMin = cval
        elif '_emax' in theoption:
            PETRglobals.CommaEMax = cval
        else:
            PETRwriter.write_FIN_error(
                "<Config>: unrecognized option beginning with comma_; command ignored")
    # insert further options here in elif clauses as this develops; also
    # update the docs in open_validation_file():
    else:
        PETRwriter.write_FIN_error("<Config>: unrecognized option")


def extract_EventCoding_info(codings):
    """Extracts fields from <EventCoding record and appends to ValidEvents."""
# currently does not raise errors if the information is missing but instead
# sets the fields to null strings
    """
    Structure of ValidEvents
    noevents: empty list
    otherwise list of triples of [sourcecode, targetcode, eventcode]
    """
    global ValidEvents

    for coding in codings:
        event_attrs = coding.attrib
        if 'noevents' in event_attrs:
            ValidEvents = []
            return
        else:
            ValidEvents.append([event_attrs['sourcecode'],
                                event_attrs['targetcode'],
                                event_attrs['eventcode']])


def evaluate_validation_record(item):
    """
    def evaluate_validation_record(): Read validation record, setting EventID
    and a list of correct coded events, code using read_TreeBank(), then check
    the results. Returns True if the lists of coded and expected events match
    or the event is skipped; false otherwise; also prints the
    mismatches
    Raises EOFError exception if EOF hit.
    Raises StopCoding if <Stop> found or
    Raises SkipRecord if <Skip> found or record is skipped due to In/Exclude
    category lists
    """
    global SentenceDate, SentenceID, SentenceCat, SentenceText, SentenceValid
    global CodedEvents, ValidEvents
    global ValidInclude, ValidExclude, ValidPause, ValidOnly
    global ParseList
    #TODO: remove this and make read_TreeBank take it as an arg
    global treestr

    ValidEvents = []  # code triples that should be produced
    # code triples that were produced; set in make_event_strings
    CodedEvents = []
#		print line
    extract_Sentence_info(item.attrib)

    if ValidOnly and not SentenceValid:
        raise SkipRecord
        return True

    if len(ValidInclude) > 0 and SentenceCat not in ValidInclude:
        raise SkipRecord
        return True

    if len(ValidExclude) > 0 and SentenceCat in ValidExclude:
        raise SkipRecord
        return True

    extract_EventCoding_info(item.findall('EventCoding'))

    SentenceText = item.find('Text').text.replace('\n', '')

    if item.find('Skip'):  # handle skipping -- leave fin at end of tree
        raise SkipRecord
        return True

    if item.find('Stop'):
        raise StopCoding
        return True

    parsed = item.find('Parse').text
    treestr = utilities._format_parsed_str(parsed)

    try:
        read_TreeBank()
    except UnbalancedTree:
        PETRwriter.write_record_error(
            ErrMsgUnbalancedTree,
            SentenceID,
            SentenceCat)
    #TODO: maybe?
    #break

    print '\nSentence:', SentenceID, '[', SentenceCat, ']'
    print SentenceText
#	print '**',ParseList

    try:
        check_commas()
    except SkipRecord:
        return

    assign_NEcodes()
#	print '**+',ParseList
    if False:
        print 'EV-1:'
        show_tree_string(' '.join(ParseList))
    if ShowParseList:
        print 'EVR-Parselist::', ParseList

    check_verbs()

#	print 'EVR-2.1:',ValidEvents
#	print 'EVR-2.2:',CodedEvents

    if len(ValidEvents) > 0:
        print 'Expected Events:'
        for event in ValidEvents:
            print event
    else:
        print 'No events should be coded'

    if len(CodedEvents) > 0:
        print 'Coded Events:'
        for event in CodedEvents:
            print SentenceID + '\t' + event[0] + '\t' + event[1] + '\t' + event[2]
    else:
        print 'No events were coded'

    if (len(ValidEvents) == 0) and (len(CodedEvents) == 0):
        return True  # noevents option

    # compare the coded and expected events
    allokay = True
    ke = 0
    while ke < len(CodedEvents):  # check that all coded events have matches
        kv = 0
        while kv < len(ValidEvents):
            if (len(ValidEvents[kv]) > 3):
                kv += 1
                continue  # already matched
            else:
                if (CodedEvents[ke][0] == ValidEvents[kv][0]) and (CodedEvents[ke][1] == ValidEvents[kv][1]) and (CodedEvents[ke][2] == ValidEvents[kv][2]):
                    CodedEvents[ke].append('+')  # mark these as matched
                    ValidEvents[kv].append('+')
                    break
            kv += 1
        if (len(CodedEvents[ke]) == 3):
            print "No match for the coded event:", CodedEvents[ke]
            allokay = False
        ke += 1

    for vevent in ValidEvents:  # check that all expected events were matched
        if (len(vevent) == 3):
            print "No match for the expected event:", vevent
            allokay = False
    return allokay


def check_envirattr(line, stag, sattr):
# checks whether line contains sattr and exits with error if not found.
# this doesn't do anything with the attribute, just extracts the list and
# checks for it
    PETRreader.extract_attributes(line)
    try:
        PETRreader.get_attribute(sattr)
    except MissingAttr:
        print "Missing '" + sattr + "' field in " + stag + " line", ErrMsgExitValidation
        sys.exit()


def open_validation_file(xml_root):
    """
def open_validation_file():

1. Opens validation file TextFilename as FIN
2. After "</Environment>" found, closes FIN, opens ErrorFile, sets various
validation options, then reads the dictionaries (exits if these are not set)
3. Can raise MissingXML
4. Can exit on EOFError, MissingAttr

Validation File Format
    Validation files are used for debugging and unit testing, combining the
    contents of a project file and text file as well as providing information
    on the correct coding for each record. \footnote{This approach is used
    based on some decidedly aggravating experiences during the TABARI
    development where the validation records and the required .verbs and
    .actors files were not properly synchronized.}

    Required elements in the <Environment> block
            <Environment>
                    <Verbfile name="<filename>">
                    <Actorfile name="<filename>">  (there can only be one,
                                                    unlike in the config file,
                                                    which allows a list)
                    <Agentfile name="<filename>">
            </Environment>

    Options elements in the <Environment> block
            <Include categories="<space-delimited list of categories to include in test>">
                    if 'valid' is included as a category, only records
                    containing valid="true" in <SENTENCE> will be evaluated.
            <Exclude categories="<space-delimited list of categories to exclude in test>">
            [if a category is in both lists, the case is excluded. But please
            don't do this]
            <Pause value="<always, never>">
                    Pause conditions:
                            always  -- pause after every record
                            never   -- never pause (errors are still recorded
                                                    in file)
                            stop    -- exit program on the default condition
                                        [below]
                            default -- pause only when EventCodes record
                                        doesn't correspond to the generated
                                        events or if there is no EventCodes
                                        record

    General record fields : all of these tags should occur on their own lines
    <Sentence>...</Sentence>:
            Delimits the record. The <Sentence...> tag can have the following
            fields: date: date of the text in YYYYMMDD format. This is
            required; if it is not present the record will be skipped

              id : identification string in any format [optional] category:
                  category in any format; this is used by the <Include> and
                  <Exclude> options [optional]

              place: code to be used for anonymous actors [optional]

    </Text>...</Text>:
            delimits the source text. This is used only for the display. The
            tags should occur on their own lines
    <Parse>...</Parse>
            Delimits the TreeBank parse tree text: this used only for the
            actual coding.

    Required elements in each record: for validation, one or more of these
    should occur prior to the TreeBank. If none are present, the record is
    coded and the program pauses unless <Pause value = "never'> has been used.

    <EventCodes sourcecode="<code>" targetcode="<code>" eventcode="<code>">
    <EventCodes noevents = "True"> : indicates the record generates no events
              (presently, system just looks for the presence of a 'noevents'
              attribute) (This is also equivalent to no <EventCodes record, but
              better to state this explicitly.)

    Optional elements in record
            <Skip>: skip this record without coding
            <Stop>: stop coding and exit program
            <Config option ="<config.ini option from list below>" value ="<value>">:
                    Change values of PETR_config.ini globals.
                    Currently works for: new_actor_length, require_dyad,
                    stop_on_error, comma_*

    Additional notes:
    1. The validation file currently does not use a discard file.

    === EXAMPLE ===

    <Sentence date="19950101" id="DEMO-01" category="DEMO">
            <!-- [Simple coding] -->
            <EventCoding sourcecode="ARN" targetcode="GON" eventcode="064">
            <Text>
            Arnor is about to restore full diplomatic ties with Gondor almost
            five years after crowds trashed its embassy, a senior official
            said on Saturday.
            </Text>
            <Parse>
            (ROOT
              (S
                    (S
                      (NP (NNP Arnor))
                      (VP (VBZ is)
                            (VP (IN about)
                              (S
                                    (VP (TO to)
                                      (VP (VB restore)
                                            (NP (JJ full) (JJ diplomatic) (NNS ties))
                                            (PP (IN with)
                                              (NP (NNP Gondor)))
                                            (SBAR
                                              (NP (RB almost) (CD five) (NNS years))
                                              (IN after)
                                              (S
                                                    (NP (NNS crowds))
                                                    (VP (VBD trashed)
                                                      (NP (PRP$ its) (NN embassy)))))))))))
                    (, ,)
                    (NP (DT a) (JJ senior) (NN official))
                    (VP (VBD said)
                      (PP (IN on)
                            (NP (NNP Saturday))))
                    (. .)))
            </Parse>
            </Sentence>

    """
    global ValidInclude, ValidExclude, ValidPause, ValidOnly

    environment = xml_root.find('Environment')
    if environment is None:
        print 'Missing <Environment> block in validation file'
        print 'Exiting program.'
        sys.exit()

    ValidInclude, ValidExclude, ValidPause, gotErrorfile, ValidOnly = _check_envr(environment)

    check1 = [len(PETRglobals.VerbFileName) == 0,
              len(PETRglobals.ActorFileList) == 0,
              len(PETRglobals.AgentFileName) == 0]
    if any(check1):
        print "Missing <Verbfile>, <AgentFile> or <ActorFile> in validation file <Environment> block", ErrMsgExitValidation
        sys.exit()

    if not gotErrorfile:
        PETRwriter.open_ErrorFile()
    PETRwriter.write_ErrorFile('Validation file: ' +
                               PETRglobals.TextFileList[0] + '\nVerbs file: ' +
                               PETRglobals.VerbFileName + '\nActors file: ' +
                               PETRglobals.ActorFileList[0] + '\n' +
                               '\nAgents file: ' + PETRglobals.AgentFileName +
                               '\n')
    if len(ValidInclude):
        PETRwriter.write_ErrorFile(
            'Include list: ' + ', '.join(ValidInclude) + '\n')
    if len(ValidExclude):
        PETRwriter.write_ErrorFile(
            'Exclude list: ' + ', '.join(ValidExclude) + '\n')
    PETRwriter.write_ErrorFile('\n')
    PETRwriter.ErrorN += 0

    print 'Verb dictionary:', PETRglobals.VerbFileName
    verb_path = utilities._get_data('data/dictionaries',
                                    PETRglobals.VerbFileName)
    PETRreader.read_verb_dictionary(verb_path)

    print 'Actor dictionaries:', PETRglobals.ActorFileList[0]
    actor_path = utilities._get_data('data/dictionaries',
                                     PETRglobals.ActorFileList[0])
    PETRreader.read_actor_dictionary(actor_path)

    print 'Agent dictionary:', PETRglobals.AgentFileName
    agent_path = utilities._get_data('data/dictionaries',
                                     PETRglobals.AgentFileName)
    PETRreader.read_agent_dictionary(agent_path)


def _check_envr(environ):
    for elem in environ:
        if elem.tag == 'Verbfile':
            PETRglobals.VerbFileName = elem.text

        if elem.tag == 'Actorfile':
            PETRglobals.ActorFileList[0] = elem.text

        if elem.tag == 'Agentfile':
            PETRglobals.AgentFileName = elem.text

        if elem.tag == 'Errorfile':
            PETRwriter.open_ErrorFile(
                elem.text,
                PETRreader.check_attribute('unique'))
            gotErrorfile = True

        if elem.tag == 'Include':
            ValidInclude = elem.text.split()
            print '<Include> categories', ValidInclude
            if 'valid' in ValidInclude:
                ValidOnly = True
                ValidInclude.remove('valid')
        else:
            ValidInclude = ''

        if elem.tag == 'Exclude':
            ValidExclude = elem.tag.split()
            print '<Exclude> categories', ValidExclude
        else:
            ValidExclude = ''

        if elem.tag == 'Pause':
            theval = elem.text
            if 'lways' in theval:
                ValidPause = 1   # skip first char to allow upper/lower case
            elif 'ever' in theval:
                ValidPause = 2
            elif 'top' in theval:
                ValidPause = 3
            else:
                ValidPause = 0

    return ValidInclude, ValidExclude, ValidPause, gotErrorfile, ValidOnly

# ================== TEXTFILE INPUT ================== #


def get_NE(NPphrase):
    """
    def get_NE(NPphrase):
    Convert (NP...) ) to NE: copies any (NEC phrases with markup, remainder of
    the phrase without any markup
    Can raise UnbalancedTree, though that should have been trapped before this
    """
    nplist = ['(NE --- ']
    seg = NPphrase.split()
    if ShowNEParsing:
        print 'List:', seg
        print "gNE input tree",
        show_tree_string(NPphrase)
        print 'List:', seg
    ka = 1
    while ka < len(seg):
        if seg[ka] == '(NEC':  # copy the phrase
            nplist.append(seg[ka])
            ka += 1
            nparen = 1  # paren count
            while nparen > 0:
                if ka >= len(seg):
                    raise_parsing_error('get_NE()-1')
                if seg[ka][0] == '(':
                    nparen += 1
                elif seg[ka] == ')':
                    nparen -= 1
                nplist.append(seg[ka])
#				print 'gNE1',nplist
                ka += 1
        # copy the phrase without the markup
        elif seg[ka][0] != '(' and seg[ka] != ')':
            nplist.append(seg[ka])
#			print 'gNE2',nplist
            ka += 1
        else:
            ka += 1

    nplist.append(')')
#	print 'gNE3',nplist
    return nplist


def read_TreeBank():
    """
    def read_TreeBank():
    Reads parsed sentence in the Penn TreeBank II format and puts the
    linearized version in the list ParseList. Sets ParseStart. Leaves global
    input file fin at line following </parse>. Probably should do something
    with an EOF error.

    This routine is supposed to be agnostic towards the line-feed and tab
    formatting of the parse tree

    Can raise UnbalancedTree error, and this is supposed to be the first line
    of defense against that: ParseList should come out of this balanced. There
    is extensive commented-out debugging code to check for this """

    """ ParseList coding Because they are still based in a shallow parsing
    approach, the KEDS/TABARI/PETR dictionaries are based on linear string
    matching rather than a tree representation, which differs from the VRA and
    BBN approach, but is much faster. The information in the tree is used
    primarily for clause delineation and [via the Stanford system]
    co-referencing.

    The read_TreeBank() function is currently the "first line of defense" in
    modifying the fully parsed input to a form that will work with the
    dictionaries developed under the older shallow parser. As of <13.11.25>
    this is focused on converting noun phrases ('(NP') to a shallower 'NE'
    (named-entity) format. Additional modifications may follow.

    Clauses are generally delineated using (XXX for the beginning and ~XXX for
    the end, where XXX are the TreeBank tags. The current code will leave some
    excess ')' at the end.

    Additional markup:

    1. Simple noun phrases -- those which are delineated by '(NP ... '))' --
    have their tag converted to 'NE' and the intermediate POS TreeBank marking
    removed. These are the only phrases that can match actors and agents. A
    placeholder code '---' is added to this structure.

        Note that because CoreNLP separates the two components of a possessive
        marking (that is, noun + apostrophe-S), this cannot be used as part of
        an actor string,
        so for example
                CHINA'S BLUEWATER NAVY
        is going to look like
                CHINA 'S BLUEWATER NAVY
        In the rather unlikely case that the actor with and without the
        possessive would map to different code, do a global substitution, for
        example 'S -> QX and then match that, i.e.
                CHINAQX BLUEWATER NAVY
        Realistically, however, a noun and its possessive will be equivalent in
        actor coding.

    2. The possessive structure (NP (NP ... (POS )) ... ) is converted to an NE
    with the (POS 'S) eliminated, so this also cannot be in a dictionary

    3. The prepositional phrase structure (NP (NP ... )) (PP ) NP( ... )) is
    converted to an NE; the preposition (IN ...) is retained

    4. The text of an (SBAR inside an (NP is retained

    5. (VP and complex (NP are indexed so that the end of the phrase can be
    identified so these have the form (XXn and ~XXn

    Errors:

    ErrMsgUnbalancedTree: this is raised when the indices checking for clause
    boundaries go out of the bounds [0,len(treestr)-1]. In fact, a tree
    probably needs to be seriously off to get this far: it is much more likely
    that an unbalanced tree will just generate a nonsensical parse and probably
    just get skipped.  But the program will keep running.


    <13.11.27> Reflections of PETR vs TABARI parsing
    As is well known, the shallow parsing of TABARI, while getting things wrong
    for the wrong reasons, also frequently got things right for the wrong
    reasons, which is to say it was rather robust on variations, grammatical or
    otherwise, in the sentences.  With the use of CoreNLP, we no longer have
    this advantage, and it is likely to take some coder experimentation with an
    extensive set of real texts to determine the various contingencies that
    needs to be accommodated.

    At present, the special cases are handled though very specific code blocks.
    If enough of these accumulate, the code will be more maintainable if we can
    develop a general language for specifying these rules -- which should not
    be difficult given that the input from CoreNLP is well-structured -- but
    for the time being, we don't have enough rules to see what, if anything is
    needed. [Those rules might also leave the text with balanced parentheses,
    as this is generally considered "a good thing"]

    """

    global ParseList, ParseStart
    global treestr
    global fullline
    global ncindex

    def get_forward_bounds(ka):
    # returns the bounds of a phrase in treestr that begins at ka, including
    # final space can raise UnbalancedTree error
        global treestr  # <13.12.07> see note above
        kb = ka + 1
        nparen = 1  # paren count
        while nparen > 0:
            if kb >= len(treestr):
                raise_parsing_error('get_forward_bounds(ka)')
            if treestr[kb] == '(':
                nparen += 1
            elif treestr[kb] == ')':
                nparen -= 1
            kb += 1
#		print "gfb:",ka,kb,treestr[ka:kb+1]
        return [ka, kb]

    def get_enclosing_bounds(ka):
    # returns the bounds of a phrase in treestr that encloses the phrase
    # beginning at ka can raise UnbalancedTree error
        global treestr  # <13.12.07> see note above
        kstart = ka - 1
        nparen = 0  # paren count
        while nparen <= 0:  # back out to the phrase tag that encloses this
            if kstart < 0:
                raise_parsing_error('get_enclosing_bounds(ka)')
            if treestr[kstart] == '(':
                nparen += 1
            elif treestr[kstart] == ')':
                nparen -= 1
            kstart -= 1
        return [kstart + 1, get_forward_bounds(kstart + 1)[1]]

    def mark_compounds():
    # determine the inner-most phrase of each CC and mark:
    # NEC: compound noun phrase for (NP tags
    # CCP: compound phrase for (S and (VP tags [possibly add (SBAR to this?]
    # otherwise just leave as CC

        global treestr

        ka = -1
        while ka < len(treestr):
            ka = treestr.find('(CC', ka + 3)  #
            if ka < 0:
                break
            kc = treestr.find(')', ka + 3)
            bds = get_enclosing_bounds(ka)
            kb = bds[0]
            if ShowMarkCompd:
                print '\nMC1:', treestr[kb:]
            # these aren't straightforward compound noun phrases we are looking
            # for
            if '(VP' in treestr[bds[0]:bds[1]] or '(S' in treestr[bds[0]:bds[1]]:
                # convert CC to CCP, though <14.05.12> we don't actually do
                # anything with this yet: (NEC is the trigger for additional
                # processing of compounds
                treestr = treestr[:ka + 4] + 'P' + treestr[ka + 4:]
                if ShowMarkCompd:
                    print '\nMC2:', treestr[kb:]
            # nested compounds: don't go there...
            elif treestr[bds[0]:bds[1]].count('(CC') > 1:
                # convert CC to CCP, though <14.05.12> we don't actually do
                # anything with this yet: (NEC is the trigger for additional
                # processing of compounds
                treestr = treestr[:ka + 4] + 'P' + treestr[ka + 4:]
                if ShowMarkCompd:
                    print '\nMC3:', treestr[kb:]
            elif treestr[kb + 1:kb + 3] == 'NP':
                # make sure we actually have multiple nouns in the phrase
                if treestr.count('(N', bds[0], bds[1]) >= 3:
                    treestr = treestr[:kb + 2] + 'EC' + \
                        treestr[kb + 3:]  # convert NP to NEC
                    if ShowMarkCompd:
                        print '\nMC4:', treestr[kb:]

    def resolve_compounds(ka):
        """
        Assign indices, eliminates the internal commas and (CC, and duplicate
        any initial adjectives inside a compound.

        This leaves the (NEC with leaving just the (NE.
        Returns treestr loc (ka) past the end of the phrase.
        Index assignment may involve just a simple (NNP or (NNS.

            Parsing bug note: <14.01.13>
            In what appear to be rare circumstances, CoreNLP does not correctly
            delimit two consecutive nouns in a compound as (NP. Specifically,
            in the test sentence

                    Mordor and the Shire welcomed a resumption of formal
                    diplomatic ties between Minas Tirith and Osgiliath.

            the second compound phrase is marked as

                (NP (NNP Minas) (NNP Tirith) (CC and) (NNP Osgiliath))

            but if "Osgiliath" is changed to "Hong Kong" it gives the correct

                    (NP (NP (NNP Minas) (NNP Tirith)) (CC and) (NP (NNP Hong) (NNP Kong))

            A systematic check of one of the GigaWord files shows that this
            appears to occur only very rarely -- and in any case is a parsing
            error -- so this routine does not check for it.
        """
        global treestr, fullline

        necbds = get_forward_bounds(ka)  # get the bounds of the NEC phrase
        if ShowMarkCompd:
            print 'rc/RTB: NEC:', necbds, treestr[necbds[0]:necbds[1]]
        ka += 4

        adjlist = []  # get any adjectives prior to first noun
        while not treestr.startswith('(NP', ka) and not treestr.startswith('(NN', ka):
            if treestr.startswith('(JJ', ka):
                npbds = get_forward_bounds(ka)
                if ShowMarkCompd:
                    print 'rc/RTB-1: JJ:', npbds, treestr[npbds[0]:npbds[1]]
                adjlist.extend(treestr[npbds[0]:npbds[1]].split())
#				print '++:',adjlist
            ka += 1

        while ka < necbds[1]:  # convert all of the NP, NNS and NNP to NE
#				print treestr[ka:necbds[1]]
            if treestr.startswith('(NP', ka) or treestr.startswith('(NN', ka):
                npbds = get_forward_bounds(ka)
                if ShowMarkCompd:
                    print 'rc/RTB-1: NE:', npbds, treestr[npbds[0]:npbds[1]]
                # just a single element, so get it
                if treestr.startswith('(NN', ka):
                    seg = treestr[npbds[0]:npbds[1]].split()
                    nplist = ['(NE --- ']
                    if len(adjlist) > 0:
                        nplist.extend(adjlist)
                    print '++1:', nplist
                    nplist.extend([seg[1], ' ) '])
                    print '++2:', nplist
                else:
                    nplist = get_NE(treestr[npbds[0]:npbds[1]])
                if ShowMarkCompd:
                    print 'rc/RTB-2: NE:', nplist
                for kb in range(len(nplist)):
                    fullline += nplist[kb] + ' '
                ka = npbds[1]
            ka += 1
        fullline += ' ) '  # closes the nec
        if ShowMarkCompd:
            print 'rc/RTB3: NE:', fullline
        return necbds[1] + 1

    def reduce_SBAR(kstart):
    # collapse SBAR beginning at kstart to a string without any markup;
    # change clause marker to SBR, which is subsequently eliminated

        global treestr

        bds = get_enclosing_bounds(kstart + 5)
#		print 'RS1:',treestr[bds[0]:bds[1]]
        frag = ''
        segm = treestr[bds[0]:bds[1]]
        kc = 0
        while kc < len(segm):
            kc = segm.find(' ', kc)
            if kc < 0:
                break
            if segm[kc + 1] != '(':  # skip markup, just get words
                kd = segm.find(' )', kc)
                frag += segm[kc:kd]
                kc = kd + 3
            else:
                kc += 2
#		print 'RS2:',frag
        # bound with '(SBR ' and ' )'
        treestr = treestr[:bds[0]] + '(SBR ' + frag + treestr[bds[1] - 2:]
#		print 'RS3:',treestr

    def process_preposition(ka):
    # process (NP containing a (PP and return an nephrase: if this doesn't have
    # a simple structure of  (NP (NP ...) (PP...) (NP/NEC ...)) without any
    # further (PP -- i.e. multiple levels of prep phrases -- it returns a null
    # string.

        global treestr, ncindex

        bds = get_enclosing_bounds(ka)  # this should be a (NP (NP
#		print 'PPP0: ',ka,bds[0],bds[1],treestr[bds[0]:bds[1]]
        if treestr.startswith('(NP (NP', bds[0]):
            nepph = '(NP '  # placeholder: this will get converted
            npbds = get_forward_bounds(bds[0] + 4)  # get the initial (NP
            nepph += treestr[npbds[0] + 4:npbds[1] - 2]
        elif treestr.startswith('(NP (NEC', bds[0]):
            nepph = '(NP (NEC '  # placeholder:
            npbds = get_forward_bounds(bds[0] + 4)  # get the initial (NEC
            # save the closing ' ) '
            nepph += treestr[npbds[0] + 4:npbds[1] + 1]
        else:
#			print 'PPP0: no (NP (NP/(NEC'
            return ''  # not what we are expecting, so bail
#		print 'PPP1: ',nepph
        # get the preposition and transfer it
        ka = treestr.find('(IN ', npbds[1])
        nepph += treestr[ka:treestr.find(' ) ', ka + 3) + 3]
#		print 'PPP2: ',nepph, '\n     ',ka,bds[1],treestr[ka+4:bds[1]]
        # find first (NP or (NEC after prep
        kp = treestr.find('(NP ', ka + 4, bds[1])
        kec = treestr.find('(NEC ', ka + 4, bds[1])
#		print 'PPP1.5', kp, kec
        if kp < 0 and kec < 0:
#			print 'PPP2a: No NP or NEC'
            return ''  # not what we are expecting, so bail
        if kp < 0:
            kp = len(treestr)  # no (NP gives priority to (NEC and vice versa
        if kec < 0:
            kec = len(treestr)
        if kp < kec:
            kb = kp
#			print 'PPP2a: got NP', treestr[kb:bds[1]]
        else:
            kb = kec
#		 	print 'PPP2a: got NEC', treestr[kb:bds[1]]
        npbds = get_forward_bounds(kb)  #
        if '(PP' in treestr[npbds[0]:npbds[1]]:
#			print 'PPP2b: Embedded (PP'
            return (
                # there's another level of (PP here  <14.04.21: can't we just
                # reduce this per (SBR?
                ''
            )
        # leave the (NEC in place. <14.01.15> It should be possible to add an
        # index here, right?
        if treestr[kb + 2] == 'E':
            nepph += treestr[kb:npbds[1] + 1]  # pick up a ') '
        else:
            # skip the (NP and pick up the final ' ' (we're using this to close
            # the original (NP
            nepph += treestr[npbds[0] + 4:npbds[1] - 1]
        if '(SBR' in treestr[npbds[1]:]:  # transfer the phrase
#			print 'PPP2c: Embedded (SBR'
            kc = treestr.find('(SBR', npbds[1])
            nepph += treestr[kc:treestr.find(') ', kc) + 2]
        nepph += ')'  # close the phrase
# exst = '\"'+ nepph + '\"'  # add quotes to see exactly what we've got here
#		print 'PPP3: ',exst
        return nepph

    fullline = ''
    vpindex = 1
    npindex = 1
    ncindex = 1

    if ShowRTTrees:
#	if False:
        print 'RT1:', treestr  # debug
        show_tree_string(treestr)
    kopen = 0
    kclose = 0
    for item in ParseList:
        if item.startswith('('):
            kopen += 1
        if item == ')':
            kclose += 1
    if ShowRTTrees:
        print 'RT1 count:', treestr.count('('), treestr.count(')')

    mark_compounds()

    if ShowRTTrees:
        print 'RT1.5 count:', treestr.count('('), treestr.count(')')

    ka = 0
    while ka < len(treestr):
        if treestr.startswith('(NP ', ka):
            npbds = get_forward_bounds(ka)

            ksb = treestr.find(
                '(SBAR ',
                npbds[0],
                npbds[1])  # reduce (SBARs inside phrase
            while ksb >= 0:
                reduce_SBAR(ksb)
                # recompute the bounds because treestr has been modified
                npbds = get_forward_bounds(ka)
                ksb = treestr.find('(SBAR ', npbds[0], npbds[1])
            nephrase = ''
            if ShowNEParsing:
                print 'BBD: ', treestr[npbds[0]:npbds[1]]
            if '(POS' in treestr[ka + 3:npbds[1]]:  # get the (NP possessive
                kb = treestr.find('(POS', ka + 4)
                nephrase = treestr[ka + 4:kb - 1]  # get string prior to (POS
#				print '++:',treestr[kb:]
                if treestr[kb + 12] == 's':
                    incr = 14
                else:
                    incr = 13   # allow for (POS ')
#					print '**:',treestr[kb+13:]
                # skip over (POS 's) and get the remainder of the NP
                nephrase += ' ' + treestr[kb + incr:npbds[1]]
                if ShowNEParsing:
                    print 'RTPOS: NE:', nephrase

                try:
                    # this gets too complicated to handle in some very rare
                    # cases of a possessive on a compound, so skip it for now
                    check_balance()
                except:
                    raise SkipRecord

            elif '(PP' in treestr[ka + 3:npbds[1]]:  # prepositional phrase
                if False:
#				if True:
                    print 'PPP-1: ', treestr[ka:npbds[1]]
                    print 'PPP-1a: ', treestr.find('(PP', ka + 3, npbds[1]), ka, npbds[1]
                    print 'PPP-1b: ', get_enclosing_bounds(treestr.find('(PP', ka + 3, npbds[1]))
                nephrase = process_preposition(
                    treestr.find('(PP', ka + 3, npbds[1]))
                if ShowNEParsing:
                    print 'RTPREP: NE:', nephrase

            # no further (NPs, so convert to NE
            elif '(NP' not in treestr[ka + 3:npbds[1]] and '(NEC' not in treestr[ka + 3:npbds[1]]:
                nephrase = treestr[ka:npbds[1]]
                if ShowNEParsing:
                    print 'RTNP: NE:', nephrase

            if len(nephrase) > 0:
                nplist = get_NE(nephrase)
                if not nplist:
                    # <14.02.27> Seems like an odd place to hit this error, and it will probably go away...
                    raise_parsing_error('read_TreeBank()-1')
                for kb in range(len(nplist)):
                    fullline += nplist[kb] + ' '
                ka = npbds[1] + 1
            else:  # it's something else...
                fullline += '(NP' + str(npindex) + ' '  # add index
                npindex += 1
                ka += 4

        elif treestr.startswith('(NEC ', ka):
            fullline += '(NEC' + str(ncindex) + ' '
            ncindex += 1
            ka = resolve_compounds(ka)

        elif treestr.startswith('(VP ', ka):  # assign index to VP
            fullline += '(VP' + str(vpindex) + ' '
            vpindex += 1
            ka += 4
        else:
            fullline += treestr[ka]
            ka += 1

# if ShowRTTrees:   # <14.04.28> this is seems to have been solved...
# check for balance at intermediate points
# print 'Balance check:',ka,fullline.count('('), fullline.count(')')
# print '                  ',treestr[ka:].count('('),
# treestr[ka:].count(')'),' ::
# ',fullline.count('(')+treestr[ka:].count('('),
# fullline.count(')')+treestr[ka:].count(')')

    # convert the text to ParseList format; convert ')' to ~XX tags
    ParseList = fullline.split()
#	print '<<',ParseList
    kopen = 0
    kclose = 0
    for item in ParseList:
        if item.startswith('('):
            kopen += 1
        elif item == ')':
            kclose += 1
#		else: print item
    if ShowRTTrees:
        print 'RT2 count:', kopen, kclose
    ka = 0
    opstack = []
    while ka < len(ParseList):
        if ParseList[ka][0] == '(':
            opstack.append(ParseList[ka][1:])
        if ParseList[ka][0] == ')':
            if len(opstack) == 0:
                break
            op = opstack.pop()
#			print '<<',op
            ParseList[ka] = '~' + op
        ka += 1

    if ShowRTTrees:
        print 'RT2:', ParseList
        show_tree_string(' '.join(ParseList))

    ParseStart = 2  # skip (ROOT (S

    try:
        check_balance()
    except:
        try:
            # this can re-raise UnbalancedTree
            raise_parsing_error('end of read_TreeBank()')
        except UnbalancedTree:
            raise SkipRecord

# ================== CODING ROUTINES  ================== #


def get_loccodes(thisloc):
    """
    Returns the list of codes from a compound, or just a single code if not
    compound.

    get_loccodes(thisloc): Extracting noun phrases which are not in the
    dictionary: If no actor or agent generating a non-null code can be found
    using the source/target rules, PETRARCH can output the noun phrase in
    double-quotes. This is controled by the configuration file option
    new_actor_length, which is set to an integer which gives the maximum length
    for new actor phrases extracted. If this is set to zero [default], no
    extraction is done andthe behavior is the same as TABARI. Setting this to a
    large number will extract anything found in a (NP noun phrase, though
    usually true actors contain a small number of words. These phrases can then
    be processed with named-entity- resolution software to extend the
    dictionaries.
    """
    global UpperSeq, LowerSeq, codelist, StoryEventList

    StoryEventList = []

    def add_code(neloc, isupperseq):
    # appends the code or phrase from UpperSeq/LowerSeq starting at neloc
    # isupperseq determines the choice of sequence

        global UpperSeq, LowerSeq, codelist

        if isupperseq:
            # "add_code neitem"; nothing to do with acne...
            acneitem = UpperSeq[neloc]
        else:
            acneitem = LowerSeq[neloc]
        accode = acneitem[acneitem.find('>') + 1:]
#		print 'AC-1:',acneitem, accode
        if accode != '---' or PETRglobals.NewActorLength == 0:
            codelist.append(accode)
        else:  # get the phrase
            if isupperseq:
                acphr = "\"" + UpperSeq[neloc - 1]
                ka = neloc - 2  # UpperSeq is stored in reverse order
                # no bounds check here; hoping these are okay by now. Yeah,
                # right
                while UpperSeq[ka][0] != '~':
                    acphr += ' ' + UpperSeq[ka]
                    ka -= 1
            else:
                acphr = "\"" + LowerSeq[neloc + 1]
                ka = neloc + 2
                while LowerSeq[ka][0] != '~':
                    acphr += ' ' + LowerSeq[ka]
                    ka += 1
            acphr += "\""
            if acphr.count(' ') < PETRglobals.NewActorLength:
                codelist.append(acphr)
            else:
                codelist.append(accode)

    codelist = []
#	print 'GLC0',thisloc
#	print '   USeq:',UpperSeq
#	print '   LSeq:',LowerSeq
    if thisloc[1]:
        try:
            neitem = UpperSeq[thisloc[0]]
        except IndexError:
            # at this point some sort of markup we can't handle, not
            # necessarily unbalanced
            raise_parsing_error('get_loccodes()-1')

#		print 'GLC1',neitem
        # extract the compound codes from the (NEC ... ~NEC sequence
        if '(NEC' in neitem:
            ka = thisloc[0] - 1  # UpperSeq is stored in reverse order
            while '~NEC' not in UpperSeq[ka]:
#				print 'GLC2',ka, UpperSeq[ka]
                if '(NE' in UpperSeq[ka]:
                    add_code(ka, True)
#					codelist.append(UpperSeq[ka][UpperSeq[ka].find('>')+1:])
                ka -= 1
                if ka < 0:
                    # at this point some sort of markup we can't handle, not
                    # necessarily unbalanced
                    raise_parsing_error('get_loccodes()-2')

# else: codelist.append(neitem[neitem.find('>')+1:]) # simple code
        else:
            add_code(thisloc[0], True)  # simple code
    else:
        try:
            neitem = LowerSeq[thisloc[0]]
        except IndexError:
            # at this point some sort of markup we can't handle, not
            # necessarily unbalanced
            raise_parsing_error('get_loccodes()-3')
#		print 'GLC3',neitem
        StoryEventList.append([SentenceID])
        for event in CodedEvents:
            StoryEventList.append(event)
#			print SentenceID + '\t' + event[0] + '\t' + event[1] + '\t' + event[2]
        if '(NEC' in neitem:  # extract the compound codes
            ka = thisloc[0] + 1
            while '~NEC' not in LowerSeq[ka]:
#				print 'GLC4',ka, LowerSeq[ka]
                if '(NE' in LowerSeq[ka]:
                    add_code(ka, False)
#					codelist.append(LowerSeq[ka][LowerSeq[ka].find('>')+1:])
                ka += 1
                if ka >= len(LowerSeq):
                    # at this point some sort of markup we can't handle, not
                    # necessarily unbalanced
                    raise_parsing_error('get_loccodes()-4')

#		else: codelist.append(neitem[neitem.find('>')+1:])
        else:
            add_code(thisloc[0], False)  # simple code
#	print 'GLC5',codelist
    return codelist


def find_source():
    """
    def find_source():
    Assign SourceLoc to the first coded or compound (NE in the UpperSeq; if
    neither found then first (NE with --- code Note that we are going through
    the sentence in normal order, so we go through UpperSeq in reverse order.
    Also note that this matches either (NE and (NEC: these are processed
    differently in make_event_string()
    """
    global UpperSeq, SourceLoc
#	print "FS-1"
    kseq = len(UpperSeq) - 1
    while kseq >= 0:
        if ('(NEC' in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return
        if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return
        kseq -= 1
                                                        # failed, so check for
                                                        # uncoded source
    kseq = len(UpperSeq) - 1
    while kseq >= 0:
        if ('(NE' in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return
        kseq -= 1


def find_target():
# Assign TargetLoc
    """ Priorities for assigning target:
            1. first coded (NE in LowerSeq that does not have the same code as
            SourceLoc; codes are not checked with either SourceLoc or the
            candidate target are compounds (NEC
            2. first null-coded (NE in LowerSeq ;
            3. first coded (NE in UpperSeq -- that is, searching backwards from
            the verb -- that does not have the same code as SourceLoc;
            4. first null-coded (NE in UpperSeq
    """

    global UpperSeq, LowerSeq, SourceLoc, TargetLoc
    srccodelist = get_loccodes(SourceLoc)
    if len(srccodelist) == 1:
        srccode = '>' + srccodelist[0]
    else:
        srccode = '>>>>'  # placeholder for a compound; this will not occur
#	print 'FT-1: srccode',srccode
#	print UpperSeq, LowerSeq
    kseq = 0
    while kseq < len(LowerSeq):
        if ('(NE' in LowerSeq[kseq]) and ('>---' not in LowerSeq[kseq]):
            if (srccode not in LowerSeq[kseq]):
                TargetLoc = [kseq, False]
                return
        kseq += 1
                                                        # failed, so check for
                                                        # uncoded target in
                                                        # LowerSeq
    kseq = 0
    while kseq < len(LowerSeq):
        # source might also be uncoded now
        if ('(NE' in LowerSeq[kseq]) and ('>---' in LowerSeq[kseq]):
            TargetLoc = [kseq, False]
            return
        kseq += 1

    # still didn't work, so look in UpperSeq going away from the verb, so we
    # increment through UpperSeq
    kseq = 0
    while kseq < len(UpperSeq):
        if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]):
            if (srccode not in UpperSeq[kseq]):
                TargetLoc = [kseq, True]
                return
        kseq += 1
                                                        # that failed as well,
                                                        # so finally check for
                                                        # uncoded target
    kseq = 0
    while kseq < len(UpperSeq):
        if ('(NE' in UpperSeq[kseq]) and ('>---' in UpperSeq[kseq]):
            # needs to be a different (NE from source
            if (kseq != SourceLoc[0]):
                TargetLoc = [kseq, True]
                return
        kseq += 1


def make_check_sequences(verbloc, endtag):
# create the upper and lower sequences to be checked by the verb patterns based
# on the verb at ParseList[verbloc]. Lower sequence includes only words in the
# VP Upper sequence currently terminated by ParseStart, ~S or ~,

    """
    Note-1: Adding location and code information to (NE
    <13.11.15>
    The trade-off here is storing this as text, which involves the cost of
    str{kword) vs storing the information in a list, which means we need
    something more complex then "if ('(NE'..." to check for it...that is, *Seq
    now contains multiple data types. My logic here is that the *Seq lists are
    potentially evaluated a large number of times, whereas the text only needs
    to be decoded when a pattern in matched, but that could be wrong.

    Hmmm, do we really need the location, or just the code? Getting the code is
    cheap
    """
    global ParseList, ParseStart
    global UpperSeq, LowerSeq

#	print "MCS-0",verbloc, ParseList[verbloc], endtag
#	print "MCS-0.5",len(ParseList)

    # generate the upper sequence: note that this is in reverse word order
    UpperSeq = []
    kword = verbloc - 1
    while kword >= ParseStart:
#		if ('~S' in ParseList[kword]) or ('~,' in ParseList[kword]): break
        if ('~,' in ParseList[kword]):
            break
        if ('(NE' == ParseList[kword]):
            code = UpperSeq.pop()  # remove the code
            # <pas 13.07.26> See Note-1
            UpperSeq.append(ParseList[kword] + '<' + str(kword) + '>' + code)
        elif ('NEC' in ParseList[kword]):
            UpperSeq.append(ParseList[kword])
        elif ('~NE' in ParseList[kword]):
            UpperSeq.append(ParseList[kword])
        elif (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
            UpperSeq.append(ParseList[kword])
        kword -= 1

    if ShowCodingSeq:
        print "Upper sequence:", UpperSeq
# for alist in UpperSeq: print alist  # debug

    # generate the lower sequence
    LowerSeq = []
    kword = verbloc + 1
    # limit this to the verb phrase itself
    while (endtag not in ParseList[kword]):
#		print "MCS-2",kword, ParseList[kword]
        if ('(NE' == ParseList[kword]):
            # <pas 13.07.26> See Note-1
            LowerSeq.append(
                ParseList[kword] + '<' + str(kword) + '>' + ParseList[kword + 1])
            kword += 1  # skip code
        elif ('NEC' in ParseList[kword]):
            LowerSeq.append(ParseList[kword])
        elif ('~NE' in ParseList[kword]):
            LowerSeq.append(ParseList[kword])
        elif (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
            LowerSeq.append(ParseList[kword])
        kword += 1
        # <14.04.23>: need to just set this to len(ParseList)?
        if kword >= len(ParseList):
            # at this point some sort of markup we can't handle, not
            # necessarily unbalanced
            raise_parsing_error('make_check_sequences()')
            return

    if ShowCodingSeq:
        print "Lower sequence:", LowerSeq
# for alist in LowerSeq: print alist  # debug


def verb_pattern_match(patlist, aseq, isupperseq):
    """
    Attempts to match patlist against UpperSeq or LowerSeq; returns True on
    success.
    """
# Can set SourceLoc and TargetLoc for $, + and % tokens
# Still need to handle %

    global SourceLoc, TargetLoc
    global kpatword, kseq

    ShowVPM = True
    ShowVPM = False

    def find_ne(kseq):
    # return the location of the (NE element in aseq starting from kseq, which
    # is inside an NE
        ka = kseq
# print "fn-1/VPM:" , ka, aseq[ka]   # debug
# print "fn-2/VPM:" , aseq, isupperseq   # debug
        while '(NE' not in aseq[ka]:
            if isupperseq:
                ka += 1
            else:
                ka -= 1
            if ka < 0 or ka >= len(aseq):
                print "++:", ka
                # at this point some sort of markup we can't handle, not
                # necessarily unbalanced
                raise_parsing_error('find_ne(kseq) in verb_pattern_match()')

# print "VPM/FN-1: Found NE:" , ka, aseq[ka]   # debug
        return ka

    def syn_match(isupperseq):
        global kseq, kpatword
#		print "&targ:",patlist[kpatword]
        if patlist[kpatword] in PETRglobals.VerbDict:
            # first try the single word cases
            if aseq[kseq] not in PETRglobals.VerbDict[patlist[kpatword]]:
                for words in PETRglobals.VerbDict[patlist[kpatword]]:
#					print '&&:',words
                    """
                    #11,914 additions and 298 deletions
                        if words[0] == '&':
                            if syn_match(isupperseq):
                                    if last_patword(): return True
                                    if last_seqword(): return False
                            else: return False
                    elif ' ' in words: # try to match a phrase """
                    if ' ' in words:  # try to match a phrase
                        # <14.05.08> may want to pre-split this and store as a
                        # list
                        wordlist = words.split()
#						print '>>:',wordlist, aseq
                        # need to go through phrase in reverse in upperseq
                        if isupperseq:
                            ka = len(wordlist) - 1
                            offset = 0
                            while (ka >= 0) and ((kseq + offset) < len(aseq)) and (aseq[kseq + offset] == wordlist[ka]):
                                ka -= 1   # will this handle reverse matches?
                                offset += 1
                            if ka < 0:
                                ka = len(wordlist)  # triggers match below
                        else:
                            ka = 0
                            while (ka < len(wordlist)) and ((kseq + ka) < len(aseq)) and (aseq[kseq + ka] == wordlist[ka]):
                                ka += 1
                        if ka == len(wordlist):
                            # last_seq() will also increment
                            kseq += len(wordlist) - 1
#							print words,"matches", kseq
                            return True
                return False
            else:
#				print "&Match:",aseq[kseq]
                return True
        else:
            # throw an error here, but actually should trap these in
            # read_verb_dict so the check won't be needed
            print "&Error:", patlist[kpatword], "not in dictionary"

    def last_seqword():
        global kseq
        kseq += 1
        if kseq >= len(aseq):
            return True  # hit end of sequence before full pattern matched
        else:
            return False

    def last_patword():
        global kpatword
        kpatword += 2  # skip connector
        if kpatword >= len(patlist):
            return True
        else:
            return False

    def no_skip():
        global kpatword
        if patlist[kpatword - 1] == ' ':
            if last_seqword():
                return True
            else:
                return False
        else:
            return True

    if ShowVPM:
        print "VPM-0", patlist, aseq, str(isupperseq)   # debug
    if len(patlist) == 0:
        return True  # nothing to evaluate, so okay
    if len(aseq) == 0:
        return False    # nothing to match, so fails
    insideNE = False
    kpatword = 1  # first word, skipping connector
    kseq = 0
    while kpatword < len(patlist):  # iterate over the words in the pattern
        if ShowVPM:
            print "VPM-1: pattern", patlist[kpatword]  # debug

        # nothing to see here, move along, move along. Though in fact this
        # should not occur
        if len(patlist[kpatword]) == 0:
            if last_patword():
                return False
            continue

        if ('~NE' in aseq[kseq]) or ('(NE' in aseq[kseq]):
#			print "NE flip", kseq, aseq[kseq], insideNE,
            if last_seqword():
                return False  # hit end of sequence before full pattern matched
            insideNE = not insideNE
#			print "NE result", insideNE

        elif len(patlist[kpatword]) == 1:  # deal with token assignments here
            if insideNE:
                if patlist[kpatword] == '$':
                    SourceLoc = [find_ne(kseq), isupperseq]
                elif patlist[kpatword] == '+':
                    TargetLoc = [find_ne(kseq), isupperseq]

                elif patlist[kpatword] == '^': 	# skip to the end of the (NE
#					print "Skipping",kseq, aseq[kseq:kseq+8], insideNE
                    while '~NE' not in aseq[kseq]:
                        if isupperseq:
                            kseq -= 1
                        else:
                            kseq += 1
                        if kseq < 0 or kseq >= len(aseq):
# print "skip/VPM:", kseq, aseq,'\n', aseq[kseq-8:kseq-1]   # debug
                            # at this point some sort of markup we can't
                            # handle, not necessarily unbalanced
                            raise_parsing_error("""find_ne(kseq) in skip
                                                assessment,
                                                verb_pattern_match()""")
                    if ShowVPM:
                        print "VPM/FN-1: Found NE:", kseq, aseq[kseq]   # debug
                    insideNE = False
# print "VPM-2:" , kseq, aseq[kseq]   # debug
# print "VPM-3:" , aseq, isupperseq   # debug

                elif patlist[kpatword] == '%':
                    pass  # deal with compound

                if ShowVPM:
                    # debug
                    print "VPM-4: Token assignment ", patlist[kpatword], aseq[find_ne(kseq)]
                if last_patword():
                    return True
                if last_seqword():
                    return False
# print "VPM-4:" , kseq, aseq[kseq], insideNE   # debug
# print "VPM-5:" , aseq, isupperseq   # debug
            elif patlist[kpatword - 1] == ' ':
                if last_seqword():
                    return False
            else:
                return False

        elif patlist[kpatword][0] == '&':  # match a synset
            if syn_match(isupperseq):
                if ShowVPM:
                    # debug
                    print "VPM-3: synMatch ", kseq, patlist[kpatword], aseq[kseq]
#				sys.exit()
                if last_patword():
                    return True
                if last_seqword():
                    return False
            else:
                if ShowVPM:
                    # debug
                    print "VPM-2: Synset Fail ", patlist[kpatword], aseq[kseq]
                if no_skip():
                    return False

        elif patlist[kpatword] != aseq[kseq]:
            if ShowVPM:
                print "VPM-2: Fail ", patlist[kpatword], aseq[kseq]   # debug
            if no_skip():
                return False

        else:  # match successful to this point
            if ShowVPM:
                print "VPM-3: Match ", patlist[kpatword], aseq[kseq]   # debug
            if last_patword():
                return True
            if last_seqword():
                return False

    return (
        True  # complete pattern matched (I don't think we can ever hit this)
    )


def check_verbs():
# Primary coding loop which looks for verbs, checks whether any of their
# patterns match, then fills in the source and target if there has been a
# match. Stores events in EventList.
    """
    Note: the "upper" sequence is the part before the verb -- that is, higher
    on the screen -- and the "lower" sequence is the part after the verb.
    Assuming, of course, that I've used these consistently.

    SourceLoc, TargetLoc structure

    [0]: the location in *Seq where the NE begins
    [1]: True - located in UpperSeq, otherwise in LowerSeq
    """
    global EventCode, SourceLoc, TargetLoc
    global EventList
    global IsPassive
    global ParseStart, ParseList

    def check_passive(kitem):
        """
        Check whether the verb phrase beginning at kitem is passive; returns
        location of verb if true, zero otherwise.
        """
        try:
            cpendtag = ParseList.index('~' + ParseList[kitem][1:])
        except ValueError:
            # <14.05.02>: Really shouldn't be hitting this...problems should
            # have been caught earlier...
            raise_parsing_error("check_passive()")
#		print "CV/CP:",ParseList[kitem:cpendtag]
        # no point in looking before + 3 since we need an auxiliary verb
        if '(VBN' in ParseList[kitem + 3:cpendtag]:
            ppvloc = ParseList.index('~VBN', kitem + 3)
            if 'BY' not in ParseList[ppvloc + 3:cpendtag]:
                return 0
            else:  # check for the auxiliary verb
                ka = ppvloc - 3
                while ka > kitem:
                    if '~VB' in ParseList[ka]:
                        if ParseList[ka - 1] in ['WAS', 'IS', 'BEEN', 'WAS']:
                            return (
                                # <14.04.30> replace this with a synset? Or a
                                # tuple? Or has the compiler done that anyway?
                                ppvloc - 1
                            )
                    ka -= 1
                return 0
        else:
            return 0

    EventList = []
    kitem = ParseStart
    while kitem < len(ParseList):
        if ('(VP' in ParseList[kitem]) and ('(VB' in ParseList[kitem + 1]):
            vpstart = kitem   # check_passive could change this
            pv = check_passive(kitem)
            IsPassive = (pv > 0)
            if IsPassive:
#				print "Got passive"
                kitem = pv - 2  # kitem + 2 is now at the passive verb
            targ = ParseList[kitem + 2] + ' '
            if ShowPattMatch:
                print "CV-0", targ
            if targ in PETRglobals.VerbDict:
                SourceLoc = [-1, True]
                TargetLoc = [-1, True]
                if ShowPattMatch:
                    print "CV-1 Found", targ
                endtag = '~' + ParseList[vpstart][1:]
                hasmatch = False
                make_check_sequences(kitem + 2, endtag)
                if PETRglobals.VerbDict[targ][0]:
                    patternlist = PETRglobals.VerbDict[targ]
                else:
                    # redirect from a synonym
                    patternlist = PETRglobals.VerbDict[
                        PETRglobals.VerbDict[targ][1]]
                kpat = 2
                if ShowPattMatch:
                    print "CV-2 patlist", patternlist
                while kpat < len(patternlist):
                    SourceLoc = [-1, True]
                    TargetLoc = [-1, True]
                    if verb_pattern_match(patternlist[kpat][0], UpperSeq, True):
                        if ShowPattMatch:
                            print "Found upper pattern match"   # debug
                        if verb_pattern_match(patternlist[kpat][1], LowerSeq, False):
                            if ShowPattMatch:
                                print "Found lower pattern match"   # debug
                            EventCode = patternlist[kpat][2]
                            hasmatch = True
                            break
                    kpat += 1
                if not hasmatch and patternlist[1] != '---':
                    if ShowPattMatch:
                        print "Matched on the primary verb"   # debug
                    EventCode = patternlist[1]
                    hasmatch = True

                if hasmatch:
                    if SourceLoc[0] < 0:
                        find_source()
                    if ShowPattMatch:
                        print "CV-3 src", SourceLoc
                    if SourceLoc[0] >= 0:
                        if TargetLoc[0] < 0:
                            find_target()
                        if TargetLoc[0] >= 0:
                            if ShowPattMatch:
                                print "CV-3 tar", TargetLoc
                            make_event_strings()

                if hasmatch:
                    while (endtag not in ParseList[kitem]):
                        kitem += 1  # resume search past the end of VP
        kitem += 1


def get_actor_code(index):
    """ Get the actor code, resolving date restrictions. """
    global SentenceOrdDate

    codelist = PETRglobals.ActorCodes[index]
    if len(codelist) == 1 and len(codelist[0]) == 1:
        return codelist[0][0]  # no restrictions: the most common case
    for item in codelist:
# print "GAC-1",index, item  # debug
        if len(item) > 1:  # interval date restriction
            if item[0] == 0 and SentenceOrdDate <= item[1]:
                return item[2]
            if item[0] == 1 and SentenceOrdDate >= item[1]:
                return item[2]
            if item[0] == 2 and SentenceOrdDate >= item[1] and SentenceOrdDate <= item[2]:
                return item[3]
    # interval search failed, so look for an unrestricted code
    for item in codelist:
        if len(item) == 1:
            return item[0]
    return '---' 	# if no condition is satisfied, return a null code;


def actor_phrase_match(patphrase, phrasefrag):
    """Determines whether the actor pattern patphrase occurs in phrasefrag."""
# returns True if match is successful. Insha'Allah...

# APMprint = True   # yes, kept having to come back to debug this...
    APMprint = False
    connector = patphrase[1]
    kfrag = 1   # already know first word matched
    kpatword = 2  # skip code and connector
    if APMprint:
        # debug
        print "APM-1", len(patphrase), patphrase, "\nAPM-2", len(phrasefrag), phrasefrag
    if len(patphrase) == 2:
        if APMprint:
            print "APM-2.1: singleton match"   # debug
        return True  # root word is a sufficient match
    # <14.02.28>: these both do the same thing, except one handles a string of
    # the form XXX and the other XXX_. This is probably unnecessary. though it
    # might be...I suppose those are two distinct cases.
    if len(patphrase) == 3 and patphrase[2][0] == "":
        if APMprint:
            print "APM-2.2: singleton match"   # debug
        return True  # root word is a sufficient match
    if kfrag >= len(phrasefrag):
        return False     # end of phrase with more to match
    while kpatword < len(patphrase):  # iterate over the words in the pattern
        if APMprint:
            # debug
            print "APM-3", kfrag, kpatword, "\n  APM Check:", kpatword, phrasefrag[kfrag], patphrase[kpatword][0]
        if phrasefrag[kfrag] == patphrase[kpatword][0]:
            if APMprint:
                print "  APM match"  # debug
            connector = patphrase[kpatword][1]
            kfrag += 1
            kpatword += 1
            if kpatword >= len(patphrase):
                return True  # complete pattern matched
        else:
            if APMprint:
                print "  APM fail"  # debug
            if connector == '_':
                return False  # consecutive match required, so fail
            else:
                kfrag += 1  # intervening words are allowed
        if kfrag >= len(phrasefrag):
            return False     # end of phrase with more to match
    return (
        True  # complete pattern matched (I don't think we can ever hit this)
    )


def check_NEphrase(nephrase):
    """
    This function tries to find actor and agent patterns matching somewhere in
    the phrase.  The code for the first actor in the phrase is used as the
    base; there is no further search for actors

    All agents with distinct codes that are in the phrase are used -- including
    phrases which are subsets of other phrases (e.g. 'REBEL OPPOSITION GROUP
    [ROP]' and 'OPPOSITION GROUP' [OPP]) and they are appended in the order
    they are found. If an agent generates the same 3-character code (e.g.
    'PARLIAMENTARY OPPOSITION GROUP [OOP]' and 'OPPOSITION GROUP' [OPP]) the
    code is appended only the first time it is found.

    Note: In order to avoid accidental matches across codes, this checks in
    increments of 3 character blocks. That is, it assumes the CAMEO convention
    where actor and agent codes are usually 3 characters, occasionally 6 or 9,
    but always multiples of 3.
    """

    kword = 0
    actorcode = ""
    if ShowNEParsing:
        print "CNEPh initial phrase", nephrase  # debug
    # iterate through the phrase looking for actors
    while kword < len(nephrase):
        phrasefrag = nephrase[kword:]
        if ShowNEParsing:
            print "CNEPh Actor Check", phrasefrag[0]  # debug
        # check whether patterns starting with this word exist in the
        # dictionary
        if phrasefrag[0] in PETRglobals.ActorDict:
            if ShowNEParsing:
                print "                Found", phrasefrag[0]  # debug
            patlist = PETRglobals.ActorDict[nephrase[kword]]
            if ShowNEParsing:
                print "CNEPh Mk1:", patlist
            # iterate over the patterns beginning with this word
            for index in range(len(patlist)):
                if actor_phrase_match(patlist[index], phrasefrag):
                    # found a coded actor
                    actorcode = get_actor_code(patlist[index][0])
                    if ShowNEParsing:
                        print "CNEPh Mk2:", actorcode
                    break
        if len(actorcode) > 0:
            break   # stop after finding first actor
        else:
            kword += 1

    kword = 0
    agentlist = []
    while kword < len(nephrase):  # now look for agents
        phrasefrag = nephrase[kword:]
        if ShowNEParsing:
            print "CNEPh Agent Check", phrasefrag[0]  # debug
        # check whether patterns starting with this word exist in the
        # dictionary
        if phrasefrag[0] in PETRglobals.AgentDict:
            if ShowNEParsing:
                print "                Found", phrasefrag[0]  # debug
            patlist = PETRglobals.AgentDict[nephrase[kword]]
            # iterate over the patterns beginning with this word
            for index in range(len(patlist)):
                if actor_phrase_match(patlist[index], phrasefrag):
                    agentlist.append(patlist[index][0])   # found a coded actor
                    break
        kword += 1   # continue looking for more agents

    if len(agentlist) == 0:
        if len(actorcode) == 0:
            return [False]  # no actor or agent
        else:
            return [True, actorcode]  # actor only

    if len(actorcode) == 0:
        actorcode = '---'   # unassigned agent

    for agentcode in agentlist:  # assemble the composite code
        if agentcode[0] == '~':
            agc = agentcode[1:]  # extract the code
        else:
            agc = agentcode[:-1]
        aglen = len(agc)  # set increment to the length of the agent code
#		print aglen, actorcode, agentcode, agc
        ka = 0  # check if the agent code is already present
        while ka < len(actorcode) - aglen + 1:
            if agc == actorcode[ka:ka + aglen]:
                ka = -1  # signal duplicate
                break
            ka += 3
        if ka < 0:
            break
        if agentcode[0] == '~':
            actorcode += agc
        else:
            actorcode = agc + actorcode
    return [True, actorcode]


def check_commas():
    """
    Removes comma-delimited clauses from ParseList.

     check_commas() Note that the order here is to remove initial, remove
     terminal, then remove intermediate. Initial and terminal remove are done
     only once; the intermediate is iterated. In a sentence where the clauses
     can in fact be removed without affecting the structure, the result will
     still be balanced. If this is not the case, the routine raises a
     Skip_Record rather than continuing with whatever mess is left.

    Because this is working with ParseList, any commas inside (NP should
    already have had their tags removed as they were converted to (NE

    This was a whole lot simpler in TABARI, but TABARI also made some
    really weird matches following comma-clause deletion.
    """

    def count_word(loclow, lochigh):
        """
        Returns the number of words in ParseList between loclow and lochigh - 1
        """
        cwkt = 0
        ka = loclow
        while ka < lochigh:
            if ParseList[ka] == '(NE':
                ka += 2  # skip over codes
            else:
                if ParseList[ka][0] != '(' and ParseList[ka][0] != '~' and ParseList[ka][0].isalpha():
                    cwkt += 1
                ka += 1
# print "cw/cc-1:", loclow, lochigh, cwkt   # debug
        return cwkt

    def find_end():
        """
        Returns location of tag on punctuation at end of phrase, defined as
        last element without ~
        """
        ka = len(ParseList) - 1
        while ka >= 2 and ParseList[ka][0] == '~':
            ka -= 1
# print "cc/fe:",ParseList[ka-1:ka+2]   # debug
        return ka - 1

    def delete_phrases(loclow, lochigh):
        """
        Deletes the complete phrases in ParseList between loclow and lochigh -
        1, leaving other mark-up.

        This is the workhorse for this function only removes (xx...~xx
        delimited phrases when these are completely within the clause being
        removed. This will potentially leave the tree in something of a mess
        grammatically, but it will be balanced.
        """
        # since you are wondering, we go through this in reverse in order to
        # use index(), as there is no rindex() for lists.
        global ParseList  # 14.05.02: wtf is this needed??
#		print 'dph/CC:',ParseList[loclow:lochigh]
        stack = []  # of course we use a stack...this is a tree...
        ka = lochigh - 1
        while ka >= loclow:
            if ParseList[ka][0] == '~':
                stack.append(ParseList[ka][1:])
#				print 'push:',stack
            # remove this complete phrase
            elif len(stack) > 0 and ParseList[ka][0] == '(' and ParseList[ka][1:] == stack[-1]:
                targ = '~' + ParseList[ka][1:]
                ParseList = ParseList[:ka] + \
                    ParseList[ParseList.index(targ, ka + 1) + 1:]
#				print 'pop:',stack,'\n',ParseList[loclow]
                stack.pop()
            ka -= 1

    global ParseList

    # displays trees at various points as ParseList is mangled
    ShowCCtrees = True
    ShowCCtrees = False

    if '(,' not in ParseList:
        return

    if ShowCCtrees:
        print 'chkcomma-1-Parselist::', ParseList
        show_tree_string(' '.join(ParseList))

    if PETRglobals.CommaBMax != 0:  # check for initial phrase
        """
        Initial phrase elimination in check_commas(): delete_phrases() will
        tend to leave a lot of (xx opening tags in place, making the tree a
        grammatical mess, which is why initial clause deletion is turned off by
        default.
        """

        kount = count_word(2, ParseList.index('(,'))
#		print "cc-1:", kount
        if kount >= PETRglobals.CommaBMin and kount <= PETRglobals.CommaBMax:
            # leave the comma in place so an internal can catch it
            delete_phrases(2, ParseList.index('(,'))

        if ShowCCtrees:
            print 'chkcomma-1a-Parselist::', ParseList
            show_tree_string(' '.join(ParseList))

    if PETRglobals.CommaEMax != 0:  # check for terminal phrase
        kend = find_end()
#		print "cc-2", ParseList[kend - 1:]
        ka = kend - 1  # terminal: reverse search for '('
        while ka >= 2 and ParseList[ka] != '(,':
            ka -= 1
        if ParseList[ka] == '(,':
            kount = count_word(ka, len(ParseList))
#			print "cc-2a:", kount, ParseList[ka:]
            if kount >= PETRglobals.CommaEMin and kount <= PETRglobals.CommaEMax:
                # leave the comma in place so an internal can catch it
                delete_phrases(ka + 3, kend)
#				print "cc-2b", ParseList[ka+3:kend]
# ParseList = ParseList[:ka + 3] + ParseList[kend:]  # leave the comma in
# place so an internal can catch it

        if ShowCCtrees:
            print 'chkcomma-2a-Parselist::'
            show_tree_string(' '.join(ParseList))
            print "cc-2t:", kount

    if PETRglobals.CommaMax != 0:
#		print "cc-3"
        ka = ParseList.index('(,')
        while True:
            try:
                kb = ParseList.index('(,', ka + 1)
            except ValueError:
                break
            kount = count_word(ka + 2, kb)  # ka+2 skips over , ~,
# print "cc-3:", ParseList[ka:ka+3], ParseList[kb:kb+3], kount  # debug
            if kount >= PETRglobals.CommaMin and kount <= PETRglobals.CommaMax:
                delete_phrases(ka, kb)  # leave the second comma in place
            ka = kb

        if ShowCCtrees:
            print 'chkcomma-3a-Parselist::'
            show_tree_string(' '.join(ParseList))

    # check for dangling initial or terminal (, , ~,

    ka = ParseList.index('(,')   # initial
    if count_word(2, ka) == 0:
#		print "%%--",ParseList[ka:ka+3]
        ParseList = ParseList[:ka] + ParseList[ka + 3:]

    kend = find_end()
    ka = kend - 1  # terminal: reverse search for '(,'
    while ka >= 2 and ParseList[ka] != '(,':
        ka -= 1
    if ParseList[ka] == '(,':
        if count_word(ka + 1, kend) == 0:
# print "##--",ParseList[ka:ka+3]
            ParseList = ParseList[:ka] + ParseList[ka + 3:]

    if ShowCCtrees:
        print 'chkcomma-end-Parselist::'
        show_tree_string(' '.join(ParseList))

    try:
        check_balance()
    except:
        try:
            # this can re-raise UnbalancedTree
            raise_parsing_error('end of check_comma()')
        except UnbalancedTree:
            raise SkipRecord


def assign_NEcodes():
    """ Assigns non-null codes to NE phrases where appropriate """

    def expand_compound_element(kstart):
        """
        An almost but not quite a recursive call on
        expand_compound_NEPhrase().
        """
        # this difference is that the (NEC has already been established so we
        # are just adding elements inside the list and there is no further
        # check: we're not allowing any further nesting of compounds. That
        # could doubtlessly be done fairly easily with some possibly too-clever
        # additional code but such constructions are virtually unknown in
        # actual news stories.
        global ParseList

        try:
            kend = ParseList.index('~NE', kstart)
            print 'exCel1:', ParseList[kstart:kend]
            ncstart = ParseList.index('(NEC', kstart, kend)
            ncend = ParseList.index('~NEC', ncstart, kend)
        except ValueError:
            # at this point some sort of markup we can't handle, not
            # necessarily unbalanced
            raise_parsing_error('expand_compound_element()')
            return

        # first element is always '(NE'
        prelist = ParseList[kstart + 1:ncstart]
        postlist = ParseList[ncend + 1:kend]
    # print 'exCel2:\n **',prelist,'\n **',ParseList[ncstart:ncend+1],'\n
    # **',postlist
        newlist = []
        ka = ncstart + 1
        while ka < ncend - 1:  # convert all of the NP, NNS and NNP to NE
    #				print treestr[ka:necbds[1]]
            # any TreeBank (N* tag is legitimate here
            if '(N' in ParseList[ka]:
                endtag = '~' + ParseList[ka][1:]
                itemlist = ['(NE', '---']
                itemlist.extend(prelist)
                ka += 1
                while ParseList[ka] != endtag:
                    itemlist.append(ParseList[ka])
                    ka += 1
                itemlist.extend(postlist)
                itemlist.append('~NE')
                newlist.extend(itemlist)
    #			print 'exCel3:',newlist
            ka += 1  # okay to increment since next item is (, or (CC
        ParseList = ParseList[:kstart] + newlist + ParseList[kend + 1:]
    #	print 'exCel4:',ParseList
        return kstart + len(newlist)

    def expand_compound_NEPhrase(kstart, kend):
        # Expand the compound phrases inside an (NE: this replaces these with a
        # list of NEs with the remaining text simply duplicated. Code and agent
        # resolution will then be done on these phrases as usual. This will
        # handle two separate (NECs, which is as deep as one generally
        # encounters.
        global ParseList
    #	print 'exNEp0:', ParseList[kstart:kend]
        ncstart = ParseList.index('(NEC', kstart, kend)
        ncend = ParseList.index('~NEC', ncstart, kend)
        # first element is always '---'
        prelist = ParseList[kstart + 1:ncstart - 1]
        postlist = ParseList[ncend + 1:kend]
    # print 'exNEp1:\n --',prelist,'\n --',ParseList[ncstart:ncend+1],'\n
    # --',postlist
        newlist = ['(NEC']
        ka = ncstart + 1
        while ka < ncend - 1:  # convert all of the NP, NNS and NNP to NE
    #				print treestr[ka:necbds[1]]
            if '(N' in ParseList[ka]:
                endtag = '~' + ParseList[ka][1:]
                itemlist = ['(NE']
                itemlist.extend(prelist)
                ka += 1
                while ParseList[ka] != endtag:
                    itemlist.append(ParseList[ka])
                    ka += 1
                itemlist.extend(postlist)
                itemlist.append('~NE')
                newlist.extend(itemlist)
    #			print 'exNEp2:',newlist
            ka += 1  # okay to increment since next item is (, or (CC
        newlist.append('~NEC')
        # insert a tell-tale here in case we need to further expand this
        newlist.append('~TLTL')
        ParseList = ParseList[:kstart] + newlist + ParseList[kend + 1:]
    #	print 'exNEp3:',ParseList
        if '(NEC' in newlist[1:-1]:  # expand next set of (NEC if it exists
            ka = kstart + 1
    #		print 'exNEp4:', ParseList[ka: ParseList.index('~TLTL',kstart)]
            while '(NE' in ParseList[ka:ParseList.index('~TLTL', ka)]:
                ka = expand_compound_element(ka)
    #			print 'exNEp5:', ParseList[ka: ParseList.index('~TLTL',ka)]

        ParseList.remove('~TLTL')  # tell-tale is no longer needed

    global ParseStart, ParseList
    global nephrase

    kitem = ParseStart
    while kitem < len(ParseList):
        if '(NE' == ParseList[kitem]:
            if ShowNEParsing:
                print "NE-0:", kitem, ParseList[kitem - 1:]
            nephrase = []
            kstart = kitem
            kcode = kitem + 1
            kitem += 2  # skip NP, code,
            if kitem >= len(ParseList):
                # at this point some sort of markup we can't handle, not
                # necessarily unbalanced
                raise_parsing_error('assign_NEcodes()-1')
                return
            while '~NE' != ParseList[kitem]:
                # <14.01.15> At present, read_TreeBank can leave (NNx in place
                # in situations involving (PP and (NEC: so COMPOUND-07. This is
                # a mildly kludgy workaround that insures a check_NEphrase gets
                # clean input
                if ParseList[kitem][1:3] != 'NN':
                    nephrase.append(ParseList[kitem])
                kitem += 1
                if kitem >= len(ParseList):
                    # at this point some sort of markup we can't handle, not
                    # necessarily unbalanced
                    raise_parsing_error('assign_NEcodes()-2')
                    return
            if ShowNEParsing:
                print "aNEc", kcode, ":", nephrase   # debug
            if '(NEC' in nephrase:
                expand_compound_NEPhrase(kstart, kitem)
                kitem = kstart - 1  # process the (NEs following the expansion
            else:
                result = check_NEphrase(nephrase)
                if result[0]:
                    ParseList[kcode] = result[1]
                    if ShowNEParsing:
                        print "Assigned", result[1]   # debug
        kitem += 1

# raise_parsing_error('assign_NEcodes()-3') # this will be hit only if
# missing a closing tag


def make_event_strings():
# creates the set of event strings, handing compound actors and symmetric
# events
    global SentenceLoc, SentenceID
    global EventCode, SourceLoc, TargetLoc
    global CodedEvents
    global IsPassive

    def make_events(codessrc, codestar, codeevt):
    # create events from each combination in the actor lists except
    # self-references
        global CodedEvents
        global SentenceLoc
        global IsPassive

        for thissrc in codessrc:
            cursrccode = thissrc
            if thissrc[0:3] == '---' and len(SentenceLoc) > 0:
                cursrccode = SentenceLoc + thissrc[3:]  # add location if known
            for thistar in codestar:
                if thissrc != thistar:  # skip self-references
                    curtarcode = thistar
                    if thistar[0:3] == '---' and len(SentenceLoc) > 0:
                        # add location if known
                        curtarcode = SentenceLoc + thistar[3:]
                    if IsPassive:
                        CodedEvents.append([curtarcode, cursrccode, codeevt])
                    else:
                        CodedEvents.append([cursrccode, curtarcode, codeevt])

    def expand_compound_codes(codelist):
    # expand coded compounds, that is, codes of the format XXX/YYY
        for ka in range(len(codelist)):
            if '/' in codelist[ka]:
                parts = codelist[ka].split('/')
    # print 'MES2:', parts  # debug
                # this will insert in order, which isn't necessary but might be
                # helpful
                kb = len(parts) - 2
                codelist[ka] = parts[kb + 1]
                while kb >= 0:
                    codelist.insert(ka, parts[kb])
                    kb -= 1

#	print 'MES1: ',SourceLoc, TargetLoc
    srccodes = get_loccodes(SourceLoc)
    expand_compound_codes(srccodes)
    tarcodes = get_loccodes(TargetLoc)
    expand_compound_codes(tarcodes)

#TODO: This needs to be fixed
    SentenceLoc = ''

#	print 'MES2: ',srccodes, tarcodes, EventCode
    if len(srccodes) == 0 or len(tarcodes) == 0:
        # <14.02.27> This is here temporarily (ha!) to just get this thing to
        # handle timing tests (and in the presence of some known bugs): this
        # should not be a persistent issue. Really
        PETRwriter.write_record_error(
            'Empty codes in make_event_strings()',
            SentenceID)
        return

    if ':' in EventCode:  # symmetric event
        if srccodes[0] == '---' or tarcodes[0] == '---':
            if tarcodes[0] == '---':
                # <13.12.08> Is this behavior defined explicitly in the
                # manual???
                tarcodes = srccodes
            else:
                srccodes = tarcodes
        ecodes = EventCode.partition(':')
#		print 'MES3: ',ecodes
        make_events(srccodes, tarcodes, ecodes[0])
        make_events(tarcodes, srccodes, ecodes[2])
    else:
        make_events(srccodes, tarcodes, EventCode)

    # remove null coded cases
    if PETRglobals.RequireDyad:
        ka = 0
        # need to evaluate the bound every time through the loop
        while ka < len(CodedEvents):
            if CodedEvents[ka][0] == '---' or CodedEvents[ka][1] == '---':
                del CodedEvents[ka]
            ka += 1
    if len(CodedEvents) == 0:
        return

    # remove duplicates
    ka = 0
    # need to evaluate the bound every time through the loop
    while ka < len(CodedEvents) - 1:
        kb = ka + 1
        while kb < len(CodedEvents):
            if CodedEvents[ka] == CodedEvents[kb]:
                del CodedEvents[kb]
            kb += 1
        ka += 1

#	print "MES exit:",CodedEvents
    return

# ========================== PRIMARY CODING FUNCTIONS ====================== #


def reset_event_list(firstentry=False):
# set the event list and story globals for the current story or just intialize
# if firstentry probably should replace the magic numbers -6:-3 here and in
# do_coding
    global SentenceDate, StoryDate, SentenceSource, StorySource
    global SentenceID, CurStoryID, SkipStory
    global StoryEventList, StoryIssues
    global NStory

    StoryEventList = []
    if PETRglobals.IssueFileName != "":
        StoryIssues = {}

    SkipStory = False
    if firstentry:
        CurStoryID = ''
    else:
        CurStoryID = SentenceID[-6:-3]
        StoryDate = SentenceDate
        StorySource = SentenceSource
        NStory += 1
#	print 'CurStoryID',CurStoryID


def extract_Sentence_info(item):
    """ Extracts  various global fields from the <Sentence record
    item is a dictionary of attributes generated from the XML input
    """
# can raise SkipRecord if date is missing

    global SentenceDate, SentenceID, SentenceCat, SentenceLoc, SentenceValid
    global SentenceOrdDate
    SentenceID = item['id']
    SentenceCat = item['category']
    if 'place' in item:
        SentenceLoc = item['place']
    else:
        SentenceLoc = ''
    if item['valid'].lower() == 'true':
        SentenceValid = True
    else:
        SentenceValid = False
    if 'date' in item:
        SentenceDate = item['date']
        SentenceOrdDate = PETRreader.dstr_to_ordate(SentenceDate)
    else:
        PETRwriter.write_FIN_error(ErrMsgMissingDate)
        raise SkipRecord


def read_record():
    """
    Primary input routine: reads an input record, and directly sets
    SentenceText and SentenceSource.

    read_record() also sets various other sentence globals (e.g. SentenceDate,
    SentenceID, ParseList ) via routines called from here.

    Raises StopCoding if <Stop> found PETRreader.read_FIN_line() can raise
    EOFError; this is passed through

    PETR organizes records into 'stories' and 'sentences' using the final six
    characters of the id field. These are assumed to be of the form NNN-SS
    where NNN are the final three digits of the story ID and SS is the sentence
    order. At present, the system just uses NNN -- that is, the ID[-6:-3] slice
    -- to determine when a new story has been encountered, but the SS is useful
    for determining lede and HLEAD sentences.

    At present, the 'story' identification is used in two features
     -- Tuple filtering is used within the story
     -- A +<string> in the Discards file skips the entire story when the string
         is found
    """
    global SentenceDate, SentenceText, SentenceID, SentenceSource
    global NSent

    SentenceSource = ''
    line = PETRreader.read_FIN_line()
    while line:
#		print line
        if ('<Sentence ' in line):
            try:
                extract_Sentence_info(line)
            except MissingAttr:
                print 'Skipping sentence: Missing date field in', line,
                return  # let SkipRecord be caught by calling routine
            NSent += 1
            # debug
            # add zero to match the new format
            SentenceID = SentenceID[:-1] + '0' + SentenceID[-1]
#			print SentenceID
            # debug

        # need to substitute something more robust here
        if ('<Source ' in line):
            extract_attributes(line)
            SentenceSource = check_attribute('id')

        if ('<Text>' in line):
            SentenceText = ''
            line = PETRreader.read_FIN_line()
            while '</Text>' not in line:
                SentenceText += line[:-1]
                if ' ' not in SentenceText[-1]:
                    SentenceText += ' '
                line = PETRreader.read_FIN_line()

        if ('<Stop>' in line):
            raise StopCoding
            return  # let StopCoding be caught by calling routine

        if '<Parse>' in line:
            try:
                read_TreeBank()
                break
            # without the 'break', this will just skip processing the record
            # and go to the next one
            except UnbalancedTree:
                PETRwriter.write_record_error(
                    ErrMsgUnbalancedTree,
                    SentenceID,
                    SentenceCat)
            except EOFError:
                raise

        line = PETRreader.read_FIN_line()

    if not line:
        raise EOFError
    print '\nSentence:', SentenceDate, SentenceID
    print SentenceText
#	print '**',ParseList


def check_discards():
    """
    Checks whether any of the discard phrases are in SentenceText, giving
    priority to the + matches. Returns [indic, match] where indic
       0 : no matches
       1 : simple match
       2 : story match [+ prefix]
    """
    global SentenceText

    sent = SentenceText.upper()  # case insensitive matching

    for target in PETRglobals.DiscardList:  # check all of the '+' cases first
        if target[0] == '+':
            mtarg = target[1:]
            if target[-1] == '_':
                mtarg = mtarg[:-1]
            loc = sent.find(mtarg)
            if loc >= 0:
                if target[-1] == '_':
                    if sent[loc + len(mtarg)] in ' .!?':
                        return [2, target]
                else:
                    return [2, target]

    for target in PETRglobals.DiscardList:
        if target[0] != '+':
            mtarg = target
            if target[-1] == '_':
                mtarg = mtarg[:-1]
#				print '--',target, mtarg
            loc = sent.find(mtarg)
            if loc >= 0:
                if target[-1] == '_':
#					print '-'+sent[loc+len(mtarg)]+'-'
                    if sent[loc + len(mtarg)] in ' .!?':
                        return [1, target]
                else:
                    return [1, target]
    return [0, '']


def get_issues():
    """
    Finds the issues in SentenceText, returns as a list of [code,count]
    Current version  <14.02.28> stops coding and sets the issues to zero if it
    finds *any* ignore phrase
    """
    global SentenceText

    sent = SentenceText.upper()  # case insensitive matching
    issues = []

    for target in PETRglobals.IssueList:
        if target[0] in sent:  # found the issue phrase
            code = PETRglobals.IssueCodes[target[1]]
            if code[0] == '~':  # ignore code, so bail
                return []
            ka = 0
            gotcode = False
            while ka < len(issues):
                if code == issues[ka][0]:
                    issues[ka][1] += 1
                    break
                ka += 1
            if ka == len(issues):  # didn't find the code, so add it
                issues.append([code, 1])

    return issues


def code_record():
# code using ParseList read_TreeBank, then return results in StoryEventList
# first element of StoryEventList for each sentence -- this signals the start
# of a list events for a sentence -- followed by  lists containing
# source/target/event triples
    global CodedEvents
    global ParseList
    global SentenceID
    global NEmpty

    # code triples that were produced; this is set in make_event_strings
    CodedEvents = []

    try:
        check_commas()
    except SkipRecord:
        return

    try:
        assign_NEcodes()
    except NameError:
        print SentenceOrdDate
    if ShowParseList:
        print 'code_rec-Parselist::', ParseList

    check_verbs()

    if len(CodedEvents) > 0:
        return CodedEvents
    else:
        NEmpty += 1
        print "No events coded"

#	if len(raw_input("Press Enter to continue...")) > 0: sys.exit()


def write_events():
    """
    Check for duplicates in the article_list, then write the records in PETR
    format
    <14.02.28>: Duplicate checking currently not implemented
    <14.02.28>: Currently set to code only events with identified national
    actors
    """
    global StoryDate, StorySource, SentenceID, StoryEventList, fevt
    global NEvents
    global StoryIssues

    if len(StoryEventList) == 0:
        return
#	print "we: Mk0", StoryEventList
    for eventlist in StoryEventList:
#		print "we: Mk1", eventlist
        if len(eventlist) == 1:  # signals new sentence id
            sent_id = eventlist[0]
        else:  # write the event
            # do not print unresolved agents
            if eventlist[0][0] != '-' and eventlist[1][0] != '-':
                print 'Event:', StoryDate + '\t' + eventlist[0] + '\t' + eventlist[1] + '\t' + eventlist[2] + '\t' + sent_id + '\t' + StorySource
                if PETRglobals.IssueFileName != "" and len(StoryIssues[sent_id[-2:]]) > 0:
                    print '       Issues:', StoryIssues[sent_id[-2:]]
                fevt.write(
                    SentenceDate + '\t' + eventlist[0] + '\t' + eventlist[1] + '\t' + eventlist[2])

                if PETRglobals.IssueFileName != "":
                    fevt.write('\t')
                    ka = 0
                    while ka < len(StoryIssues[sent_id[-2:]]):
                        # output code and count
                        fevt.write(
                            StoryIssues[sent_id[-2:]][ka][0] + ' ' + str(StoryIssues[sent_id[-2:]][ka][1]))
                        if ka < len(StoryIssues[sent_id[-2:]]) - 1:
                            fevt.write(', ')
                        ka += 1

                fevt.write('\t' + sent_id + '\t' + StorySource + '\n')
                NEvents += 1


def make_fake_events():
# just for debugging, but you probably always guessed that
    global SentenceID, StoryEventList
    StoryEventList.append([SentenceID])
    ka = 1
    while ka < 5:
        StoryEventList.append(['ABC', 'EDF', str(ka).zfill(4)])
        ka += 1


def do_validation(filepath):
    """ Coding using a validation file. """
    global NParseErrors

    start_time = time.time()
    nvalid = 0

    tree = ET.parse(filepath)
    root = tree.getroot()

    open_validation_file(root)
    sents = root.find('Sentences')

    NParseErrors = 0
    for item in sents:
        if item.tag == 'Config':
            change_Config_Options(item.attrib)
        if item.tag == 'Sentence':
            try:
                vresult = evaluate_validation_record(item)
                if vresult:
                    print "Events correctly coded in", SentenceID, '\n'
                    nvalid += 1
                else:
                    print "Error: Mismatched events in", SentenceID, '\n'
                    if ValidPause == 3:
                        sys.exit()  # debug

                if ValidPause == 2:
                    continue  # evaluate pause conditions
                elif ValidPause == 1 or not vresult:
                    inkey = raw_input("Press <Return> to continue; 'q' to quit-->")
                    if 'q' in inkey or 'Q' in inkey:
                        break

            except EOFError:
                print "Exiting: end of file"
                PETRreader.close_FIN()
                print "Records coded correctly:", nvalid
                sys.exit()
            except StopCoding:
                print "Exiting: <Stop> record "
                PETRreader.close_FIN()
                print "Records coded correctly:", nvalid
                sys.exit()
            except SkipRecord:
                print "Skipping this record."
            except HasParseError:
                print "Exiting: parsing error "
                PETRreader.close_FIN()
                sys.exit()


def do_coding(event_dict, out_file):
    """
    Main coding loop Note that entering any character other than 'Enter' at the
    prompt will stop the program: this is deliberate.
    <14.02.28>: Bug: PETRglobals.PauseByStory actually pauses after the first
                sentence of the *next* story
    """
    global StoryDate, StorySource, SentenceID, SentenceCat, SentenceText
    global CurStoryID, SkipStory
    global NStory, NSent, NEvents, NDiscardSent, NDiscardStory, NEmpty
    global NParseErrors
    global fevt
    global StoryIssues
    global CodedEvents

    #These are pulled from read_record()
    global SentenceDate, SentenceSource, SentenceOrdDate
    #Things to make local and global namespaces not conflict
    #TODO: Change this
    global treestr, ParseList

    NStory = 0
    NSent = 0
    NEvents = 0
    NEmpty = 0
    NDiscardSent = 0
    NDiscardStory = 0
    NParseErrors = 0

    for key in event_dict:
        print 'Processing {}'.format(key)
        StoryDate = event_dict[key]['meta']['date']
        StorySource = 'TEMP'
        for sent in event_dict[key]['sents']:
            SentenceID = '{}_{}'.format(key, sent)
            #TODO: This is why Python 3 might be nice.
            SentenceText = event_dict[key]['sents'][sent]['content'].encode('utf-8')
            SentenceDate = StoryDate
            SentenceOrdDate = PETRreader.dstr_to_ordate(SentenceDate)
            SentenceSource = 'TEMP'

            parsed = event_dict[key]['sents'][sent]['parsed']
            treestr = parsed
            #TODO: Make read_TreeBank take treestr as an arg and return
            #something
            read_TreeBank()
            reset_event_list(True)

#TODO
#Can implement this easily. The sentences are organized by story in the dicts
#so it's easy to rework this. Just when we're done with a key then write out
#the events for the included sentences. Gonna skip it for now
#            if not PETRglobals.CodeBySentence:
#                # write events when we hit a new story
#                if SentenceID[-6:-3] != CurStoryID:
#                    if not SkipStory:
#                        write_events()
#                    reset_event_list()
#                    if PETRglobals.PauseByStory:
#                        if len(raw_input("Press Enter to continue...")) > 0:
#                            sys.exit()
#            else:
#                reset_event_list()

            if SkipStory:
                print "Skipped"
                continue

            disc = check_discards()
            if disc[0] > 0:
                if disc[0] == 1:
                    print "Discard sentence:", disc[1]
                    NDiscardSent += 1
                else:
                    print "Discard story:", disc[1]
                    SkipStory = True
                    NDiscardStory += 1

                coded_events = None

            else:
                try:
                    coded_events = code_record()
                except UnbalancedTree as why:
                    print "Unable to interpret parse tree:", why
                    coded_events = None

            if coded_events:
                event_dict[key]['sents'][sent]['events'] = coded_events


            if coded_events and PETRglobals.IssueFileName != "":
                event_issues = get_issues()
                if event_issues:
                    event_dict[key]['sents'][sent]['issues'] = event_issues

            if PETRglobals.PauseBySentence:
                if len(raw_input("Press Enter to continue...")) > 0:
                    sys.exit()

    return event_dict

    print "Summary:"
    print "Stories read:", NStory, "   Sentences coded:", NSent, "  Events generated:", NEvents
    print "Discards:  Sentence", NDiscardSent, "  Story", NDiscardStory, "  Sentences without events:", NEmpty
    print "Parsing errors:", NParseErrors


def parse_cli_args():
    """Function to parse the command-line arguments for PETRARCH."""
    __description__ = """
PETRARCH
(https://openeventdata.github.io/) (v. 0.01)
    """
    aparse = argparse.ArgumentParser(prog='petrarch',
                                     description=__description__)

    sub_parse = aparse.add_subparsers(dest='command_name')
    parse_command = sub_parse.add_parser('parse', help="""Command to run the
                                         PETRARCH parser.""",
                                         description="""Command to run the
                                         PETRARCH parser.""")
    parse_command.add_argument('-i', '--inputs',
                               help='File, or directory of files, to parse.',
                               required=True)
    parse_command.add_argument('-P', '--parsed', action='store_true',
                               default=False, help="""Whether the input
                               document contains StanfordNLP-parsed text.""")
    parse_command.add_argument('-o', '--output',
                               help='File to write parsed events.',
                               required=True)
    parse_command.add_argument('-c', '--config',
                               help="""Filepath for the PETRARCH configuration
                               file. Defaults to PETR_config.ini""",
                               required=False)

    batch_command = sub_parse.add_parser('validate', help="""Command to run
                                         the PETRARCH validation suite.""",
                                         description="""Command to run the
                                         PETRARCH validation suite.""")
    batch_command.add_argument('-i', '--inputs',
                               help="""Optional file that contains the
                               validation records. If not specified, defaults
                               to the built-in PETR.UnitTest.records.txt""",
                               required=False)

    args = aparse.parse_args()
    return args


def main():
    cli_args = parse_cli_args()

    PETRglobals.RunTimeString = time.asctime()

    if cli_args.command_name == 'validate':
        PETRreader.parse_Config(utilities._get_config('PETR_config.ini'))
        if not cli_args.inputs:
            validation_file = utilities._get_data('data/text',
                                                  'PETR.UnitTest.records.xml')
            do_validation(validation_file)
        else:
            do_validation(cli_args.inputs)

    if cli_args.command_name == 'parse':
        start_time = time.time()

        if cli_args.config:
            PETRreader.parse_Config(cli_args.config)
        else:
            PETRreader.parse_Config(utilities._get_config('PETR_config.ini'))

        read_dictionaries()

        if os.path.isdir(cli_args.inputs):
            if cli_args.inputs[-1] != '/':
                paths = glob.glob(cli_args.inputs + '/*.xml')
            else:
                paths = glob.glob(cli_args.inputs + '*.xml')
        elif os.path.isfile(cli_args.inputs):
            paths = [cli_args.inputs]
        else:
            print 'Please enter a valid directory or file of source texts.'
            sys.exit()

        print '\n\n'

        run(paths, cli_args.output, cli_args.parsed)

        print "Coding time:", time.time() - start_time
        # note that this will be removed if there are no errors
        PETRwriter.close_ErrorFile()

    print "Finished"


def read_dictionaries():
        # need to allow this to be set in the config file or command line
        PETRwriter.open_ErrorFile()
        print 'Verb dictionary:', PETRglobals.VerbFileName
        verb_path = utilities._get_data('data/dictionaries',
                                        PETRglobals.VerbFileName)
        PETRreader.read_verb_dictionary(verb_path)

        print 'Actor dictionaries:', PETRglobals.ActorFileList
        for actdict in PETRglobals.ActorFileList:
            actor_path = utilities._get_data('data/dictionaries', actdict)
            PETRreader.read_actor_dictionary(actor_path)

        print 'Agent dictionary:', PETRglobals.AgentFileName
        agent_path = utilities._get_data('data/dictionaries',
                                         PETRglobals.AgentFileName)
        PETRreader.read_agent_dictionary(agent_path)

        print 'Discard dictionary:', PETRglobals.DiscardFileName
        discard_path = utilities._get_data('data/dictionaries',
                                           PETRglobals.DiscardFileName)
        PETRreader.read_discard_list(discard_path)

        if PETRglobals.IssueFileName != "":
            print 'Issues dictionary:', PETRglobals.IssueFileName
            issue_path = utilities._get_data('data/dictionaries',
                                             PETRglobals.IssueFileName)
            PETRreader.read_issue_list(issue_path)


def run(filepaths, out_file, s_parsed):
    events = PETRreader.read_xml_input(filepaths, s_parsed)
    if not s_parsed:
        events = utilities.stanford_parse(events)
    updated_events = do_coding(events, 'TEMP')
    utilities.write_events(updated_events, out_file)


def run_pipeline(data, out_file=None, write_output=True):
    PETRreader.parse_Config(utilities._get_config('PETR_config.ini'))
    read_dictionaries()

    events = PETRreader.read_pipeline_input(data)
    events = utilities.stanford_parse(events)
    updated_events = do_coding(events, 'TEMP')
    if not write_output:
        output_events = utilities.pipe_output(updated_events)
        return output_events
    elif write_output and not out_file:
        print 'Please specify an output file...'
        sys.exit()
    elif write_output and out_file:
        utilities.write_events(updated_events, out_file)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import glob
import time
import types
import logging
import argparse
import xml.etree.ElementTree as ET

# petrarch.py
##
# Automated event data coder
##
# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.10; it is standard Python 2.7
# so it should also run in Unix or Windows.
#
# INITIAL PROVENANCE:
# Programmers:
#             Philip A. Schrodt
#			  Parus Analytics
#			  Charlottesville, VA, 22901 U.S.A.
#			  http://eventdata.parusanalytics.com
#
#             John Beieler
#			  Caerus Associates/Penn State University
#			  Washington, DC / State College, PA, 16801 U.S.A.
#			  http://caerusassociates.com
#             http://bdss.psu.edu
#
# GitHub repository: https://github.com/openeventdata/petrarch
#
# Copyright (c) 2014	Philip A. Schrodt.	All rights reserved.
#
# This project is part of the Open Event Data Alliance tool set; earlier developments
# were funded in part by National Science Foundation grant SES-1259190
#
# This code is covered under the MIT license
#
# Report bugs to: schrodt735@gmail.com
#
# REVISION HISTORY:
# 22-Nov-13:	Initial version
# Summer-14:	Numerous modifications to handle synonyms in actor and verb dictionaries
# 20-Nov-14:	write_actor_root/text added to parse_Config
# ------------------------------------------------------------------------

import PETRglobals  # global variables
import PETRreader  # input routines
import PETRwriter
import utilities
import PETRtree

# ================================  PARSER/CODER GLOBALS  ================== #

# ParseList = []   # linearized version of parse tree
# ParseStart = 0   # first element to check (skips (ROOT, initial (S

# text that can be matched prior to the verb; this is stored in reverse order
#UpperSeq = []
# LowerSeq = []  # text that can be matched following the verb

# SourceLoc = 0  # location of the source within the Upper/LowerSeq
# TargetLoc = 0  # location of the target within the Upper/LowerSeq

SentenceID = ''   # ID line
# EventCode = ''   # event code from the current verb
# SourceCode = ''   # source code from the current verb
# TargetCode = ''   # target code from the current verb


# ================================  VALIDATION GLOBALS  ==================== #

DoValidation = False   # using a validation file
ValidOnly = False      # only evaluate cases where <Sentence valid="true">
# validation mode : code triples that were produced; set in make_event_strings
#CodedEvents = []
ValidEvents = []  # validation mode : code triples that should be produced
ValidInclude = []  # validation mode : list of categories to include
ValidExclude = []  # validation mode : list of categories to exclude
# validation mode :pause conditions: 1: always; -1 never; 0 only on error
# [default]
ValidPause = 0
ValidError = ''      # actual error code
ValidErrorType = ''  # expected error code

# ================================  DEBUGGING GLOBALS  ==================== #
# (comment out the second line in the pair to activate. Like you couldn't
# figure that out.)

# prints ParseList in evaluate_validation_record()/code_record() following
# NE assignment
ShowParseList = True
ShowParseList = False

# displays parse trees in read_TreeBank
ShowRTTrees = True
ShowRTTrees = False

ShowCodingSeq = True
ShowCodingSeq = False

ShowPattMatch = True
ShowPattMatch = False

ShowNEParsing = True
ShowNEParsing = False

ShowMarkCompd = True
ShowMarkCompd = False

# ================== EXCEPTIONS ================== #


class DupError(Exception):  # template
    pass


class HasParseError(Exception):  # exit the coding due to parsing error
    pass


class SkipRecord(Exception):  # skip a validation record
    pass


class UnbalancedTree(Exception):  # unbalanced () in the parse tree
    pass


# problems were found at some point in read_TreeBank
class IrregularPattern(Exception):
    pass


# problems were found in a specific pattern in check_verbs [make this
# local to that function?]
class CheckVerbsError(Exception):
    pass

# ================== ERROR FUNCTIONS ================== #

"""
<14.09.014> This function has now been replaced by more specific error messages and
it should be possible to eliminate it
def raise_parsing_error(call_location_string):
# <14.02.27: this is currently used as a generic escape from misbehaving
# functions, so it is not necessarily an actual unbalanced tree, just that
# we've hit something unexpected.
    global SentenceID
    logger = logging.getLogger('petr_log')
    errorstring = 'Parsing error in ' + call_location_string
    logger.warning('{}{}'.format(errorstring, SentenceID))
    if PETRglobals.StoponError:
        raise HasParseError
    else:
        raise UnbalancedTree(errorstring)
"""


def raise_ParseList_error(call_location_string):
    """
    Handle problems found at some point during the coding/evaluation of ParseList, and is
    called when the problem seems sufficiently important that the record should not be coded.
    Logs the error and raises HasParseError.
    """

    #global SentenceID, ValidError
    warningstr = call_location_string + \
        '; record skipped: {}'.format(SentenceID)
    logger = logging.getLogger('petr_log')
    logger.warning(warningstr)
    raise HasParseError


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
            if level != prevlevel or 'VP' == sent[
                    ka + 1:ka + 3] or 'SB' == sent[ka + 1:ka + 3]:
                # new line only with change in level, also with (VP, (SB
                sout += '\n' + level * '  '
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
    if nopen == nclose:
        print("Balanced:", end=' ')
    else:
        print("Unbalanced:", end=' ')
    print("Open", nopen, "Close", nclose, '\n')
    if nopen != nclose and PETRglobals.StoponError:
        raise HasParseError


def check_balance(ParseList):
    """
    Check the (/~ count in a ParseList and raises UnbalancedTree if it is not
    balanced.
    """
    nopen = 0
    ka = 0
    stop = len(ParseList)
    while ka < stop:
        if ParseList[ka][0] == '(':
            nopen += 1
        elif ParseList[ka][0] == '~':
            nopen -= 1
        ka += 1
    if nopen != 0:
        raise UnbalancedTree


# ========================== VALIDATION FUNCTIONS ========================== #


def change_Config_Options(line):
    """Changes selected configuration options."""
    # need more robust error checking
    theoption = line['option']
    value = line['value']
    #print("<Config>: changing", theoption, "to", value)
    if theoption == 'new_actor_length':
        try:
            PETRglobals.NewActorLength = int(value)
        except ValueError:
            logger.warning(
                "<Config>: new_actor_length must be an integer; command ignored")
    elif theoption == 'require_dyad':
        PETRglobals.RequireDyad = not 'false' in value.lower()
    elif theoption == 'stop_on_error':
        PETRglobals.StoponError = not 'false' in value.lower()
    elif 'comma_' in theoption:
        try:
            cval = int(value)
        except ValueError:
            logger.warning(
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
            logger.warning(
                "<Config>: unrecognized option beginning with comma_; command ignored")
    # insert further options here in elif clauses as this develops; also
    # update the docs in open_validation_file():
    else:
        logger.warning("<Config>: unrecognized option")


def _check_envr(environ):
    for elem in environ:
        if elem.tag == 'Verbfile':
            PETRglobals.VerbFileName = elem.text

        if elem.tag == 'Actorfile':
            PETRglobals.ActorFileList[0] = elem.text

        if elem.tag == 'Agentfile':
            PETRglobals.AgentFileName = elem.text

        if elem.tag == 'Discardfile':
            PETRglobals.DiscardFileName = elem.text

        if elem.tag == 'Errorfile':
            print('This is deprecated. Using a different errorfile. ¯\_(ツ)_/¯')

        if elem.tag == 'Include':
            ValidInclude = elem.text.split()
            print('<Include> categories', ValidInclude)
            if 'valid' in ValidInclude:
                ValidOnly = True
                ValidInclude.remove('valid')
        else:
            ValidInclude = ''

        if elem.tag == 'Exclude':
            ValidExclude = elem.tag.split()
            print('<Exclude> categories', ValidExclude)
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

    return ValidInclude, ValidExclude, ValidPause, ValidOnly

# ================== TEXTFILE INPUT ================== #


def read_TreeBank(tree_string):
    """
    Reads parsed sentence in the Penn TreeBank II format and puts the linearized version
    in the list ParseList. Sets ParseStart. Leaves global input file fin at line
    following </parse>. The routine is appears to be agnostic towards the line-feed and tab
    formatting of the parse tree

    TO DO <14.09.03>: Does this handle an unexpected EOF error?

    TO DO <14.09.03>: This really belongs as a separate module and the code seems
    sufficiently stable now that this could be done

    read_TreeBank() can raise quite a few different named errors which are handled by
    check_irregulars(); these can be checked as ValidErrorType. ParseList should come out
    of this balanced. In addition to the error trapping there is extensive commented-out
    debugging code.

    ======= ParseList coding =========

    Because they are still based in a shallow parsing approach, the KEDS/TABARI/PETR
    dictionaries are based on linear string matching rather than a tree representation,
    which differs from the VRA-Reader and BBN-Serif approach, but is much faster, or
    perhaps more accurately, let the Treebank parser do the work once, rather than
    re-evaluating a tree every time events are coded. The information in the tree is used
    primarily for clause delineation.

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

    The routine check_irregulars() handles a variety of conditions where the input
    or the parsing is not going well; check the various error messages for details


    <13.11.27> Reflections of PETR vs TABARI parsing
    As is well known, the shallow parsing of TABARI, while getting things wrong
    for the wrong reasons, also frequently got things right for the wrong
    reasons, which is to say it was rather robust on variations, grammatical or
    otherwise, in the sentences.  With the use of CoreNLP, we no longer have
    this advantage, and it is likely to take some coder experimentation with an
    extensive set of real texts to determine the various contingencies that
    needs to be accommodated.

    """

    ParseList = ""
    ParseStart = 0

    treestr = tree_string

    def check_irregulars(knownerror=''):
        """
        Checks for some known idiosyncratic ParseList patterns that indicate problems in the
        the input text or, if knownrecord != '', just raises an already detected error. In
        either case, logs the specific issue, sets the global ValidError (for unit tests)
        and raises IrregularPattern.
        Currently tracking:
           -- bad_input_parse
           -- empty_nplist
           -- bad_final_parse
           -- get_forward_bounds
           -- get_enclosing_bounds
           -- resolve_compounds
           -- get_NE_error
           -- dateline [pattern]
       """
        #global ValidError
        if knownerror:
            if knownerror == 'bad_input_parse':
                warningstr = '<Parse>...</Parse> input was not balanced; record skipped: {}'
            elif knownerror == 'empty_nplist':
                warningstr = 'Empty np_list in read_Tree; record skipped: {}'
            elif knownerror == 'bad_final_parse':
                warningstr = 'ParseList unbalanced at end of read_Tree; record skipped: {}'
            elif knownerror == 'get_forward_bounds':
                warningstr = 'Upper bound error in get_forward_bounds in read_Tree; record skipped: {}'
            elif knownerror == 'get_enclosing_bounds':
                warningstr = 'Lower bound error in get_enclosing_bounds in read_Tree; record skipped: {}'
            elif knownerror == 'resolve_compounds':
                warningstr = 'get_NE() error in resolve_compounds() in read_Tree; record skipped: {}'
            elif knownerror == 'get_NE_error':
                warningstr = 'get_NE() error in main loop of read_Tree; record skipped: {}'
            else:
                warningstr = """Unknown error type encountered in check_irregulars()
         --------- this is a programming bug but nonetheless the record was skipped: {}"""
            logger = logging.getLogger('petr_log')
            logger.warning(warningstr.format(SentenceID))
            ValidError = knownerror
            raise IrregularPattern

        ntag = 0
        taglist = []
        ka = 0
        while ka < len(ParseList):
            if ParseList[ka][0] == '(':
                taglist.append(ParseList[ka])
                ntag += 1
                if ntag > 2:
                    break  # this is all we need for dateline
            ka += 1
        if taglist[:3] == ['(ROOT', '(NE', '(NEC']:
            logger = logging.getLogger('petr_log')
            logger.warning(
                'Dateline pattern found in ParseList; record skipped: {}'.format(SentenceID))
            ValidError = 'dateline'
            raise IrregularPattern

    def get_NE(NPphrase):
        """
        Convert (NP...) ) to NE: copies any (NEC phrases with markup, remainder of
        the phrase without any markup
        Can raise IrregularPattern, which is caught and re-raised at the calling point
        """
        nplist = ['(NE --- ']
        seg = NPphrase.split()
        if ShowNEParsing:
            print('List:', seg)
            print("gNE input tree", end=' ')
            show_tree_string(NPphrase)
            print('List:', seg)
        ka = 1
        while ka < len(seg):
            if seg[ka] == '(NEC':  # copy the phrase
                nplist.append(seg[ka])
                ka += 1
                nparen = 1  # paren count
                while nparen > 0:
                    if ka >= len(seg):
                        raise IrregularPattern
                    if seg[ka][0] == '(':
                        nparen += 1
                    elif seg[ka] == ')':
                        nparen -= 1
                    nplist.append(seg[ka])
                    ka += 1
            # copy the phrase without the markup
            elif seg[ka][0] != '(' and seg[ka] != ')':
                nplist.append(seg[ka])
                ka += 1
            else:
                ka += 1

        nplist.append(')')
        return nplist

    def get_forward_bounds(ka):
        """
        Returns the bounds of a phrase in treestr that begins at ka, including the final space.
        """  # <13.12.07> see note above
        kb = ka + 1
        nparen = 1  # paren count
        while nparen > 0:
            if kb >= len(treestr):
                check_irregulars('get_forward_bounds')
            if treestr[kb] == '(':
                nparen += 1
            elif treestr[kb] == ')':
                nparen -= 1
            kb += 1
        return [ka, kb]

    def get_enclosing_bounds(ka):
        """
        Returns the bounds of a phrase in treestr that encloses the phrase beginning at ka
        """
        kstart = ka - 1
        nparen = 0  # paren count
        while nparen <= 0:  # back out to the phrase tag that encloses this
            if kstart < 0:
                check_irregulars('get_enclosing_bounds')
            if treestr[kstart] == '(':
                nparen += 1
            elif treestr[kstart] == ')':
                nparen -= 1
            kstart -= 1
        return [kstart + 1, get_forward_bounds(kstart + 1)[1]]

    def resolve_compounds(ka, fline):
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
        fullline = fline

        necbds = get_forward_bounds(ka)  # get the bounds of the NEC phrase
        if ShowMarkCompd:
            print('rc/RTB: NEC:', necbds, treestr[necbds[0]:necbds[1]])
        ka += 4

        adjlist = []  # get any adjectives prior to first noun
        while not treestr.startswith(
                '(NP', ka) and not treestr.startswith('(NN', ka):
            if treestr.startswith('(JJ', ka):
                npbds = get_forward_bounds(ka)
                if ShowMarkCompd:
                    print('rc/RTB-1: JJ:', npbds, treestr[npbds[0]:npbds[1]])
                adjlist.extend(treestr[npbds[0]:npbds[1]].split())
            ka += 1

        while ka < necbds[1]:  # convert all of the NP, NNS and NNP to NE
            if treestr.startswith('(NP', ka) or treestr.startswith('(NN', ka):
                npbds = get_forward_bounds(ka)
                if ShowMarkCompd:
                    print('rc/RTB-1: NE:', npbds, treestr[npbds[0]:npbds[1]])
                # just a single element, so get it
                if treestr.startswith('(NN', ka):
                    seg = treestr[npbds[0]:npbds[1]].split()
                    nplist = ['(NE --- ']
                    if len(adjlist) > 0:
                        nplist.extend(adjlist)
                    nplist.extend([seg[1], ' ) '])
                else:
                    try:
                        nplist = get_NE(treestr[npbds[0]:npbds[1]])
                    except IrregularPattern:
                        check_irregulars('resolve_compounds')

                if ShowMarkCompd:
                    print('rc/RTB-2: NE:', nplist)
                for kb in range(len(nplist)):
                    fullline += nplist[kb] + ' '
                ka = npbds[1]
            ka += 1
        fullline += ' ) '  # closes the nec
        if ShowMarkCompd:
            print('rc/RTB3: NE:', fullline)
        return necbds[1] + 1, fullline

    def process_preposition(ka):
        """
        Process (NP containing a (PP and return an nephrase: if this doesn't have a
        simple structure of  (NP (NP ...) (PP...) (NP/NEC ...)) without any further
        (PP -- i.e. multiple levels of prep phrases -- it returns a null string.
        """

        # this should be a (NP (NP
        bds = get_enclosing_bounds(ka)
        if treestr.startswith('(NP (NP', bds[0]):
            # placeholder: this will get converted
            nepph = '(NP '
            npbds = get_forward_bounds(bds[0] + 4)      # get the initial (NP
            nepph += treestr[npbds[0] + 4:npbds[1] - 2]
        elif treestr.startswith('(NP (NEC', bds[0]):
            nepph = '(NP (NEC '                         # placeholder:
            npbds = get_forward_bounds(bds[0] + 4)      # get the initial (NEC
            # save the closing ' ) '
            nepph += treestr[npbds[0] + 4:npbds[1] + 1]
        else:
            # not what we are expecting, so bail
            return ''
            # get the preposition and transfer it
        ka = treestr.find('(IN ', npbds[1])
        nepph += treestr[ka:treestr.find(' ) ', ka + 3) + 3]
        # find first (NP or (NEC after prep
        kp = treestr.find('(NP ', ka + 4, bds[1])
        kec = treestr.find('(NEC ', ka + 4, bds[1])
        if kp < 0 and kec < 0:
            # not what we are expecting, so bail
            return ''
        if kp < 0:
            # no (NP gives priority to (NEC and vice versa
            kp = len(treestr)
        if kec < 0:
            kec = len(treestr)
        if kp < kec:
            kb = kp
        else:
            kb = kec
        npbds = get_forward_bounds(kb)
        if '(PP' in treestr[npbds[0]:npbds[1]]:
            # there's another level of (PP here  <14.04.21: can't we just
            return ('')
            # reduce this per (SBR?
            # leave the (NEC in place. <14.01.15> It should be possible to add an
            # index here, right?
        if treestr[kb + 2] == 'E':
            nepph += treestr[kb:npbds[1] + 1]           # pick up a ') '
        else:
                                                        # skip the (NP and pick up the final ' ' (we're using this to close
                                                        # the original (NP
            nepph += treestr[npbds[0] + 4:npbds[1] - 1]
        if '(SBR' in treestr[npbds[1]:]:                # transfer the phrase
            kc = treestr.find('(SBR', npbds[1])
            nepph += treestr[kc:treestr.find(') ', kc) + 2]
        nepph += ')'                                    # close the phrase
        return nepph

    logger = logging.getLogger('petr_log')
    fullline = ''
    vpindex = 1
    npindex = 1
    ncindex = 1

    if ShowRTTrees:
        print('RT1 treestr:', treestr)  # debug
        print('RT1 count:', treestr.count('('), treestr.count(')'))
        show_tree_string(treestr)
    if treestr.count('(') != treestr.count(')'):
        check_irregulars('bad_input_parse')

    if '~' in treestr:
        treestr = treestr.replace('~', '-TILDA-')

    ##############################
    # Mark Compounds#
    ##############################
    ka = -1
    while ka < len(treestr):
        ka = treestr.find('(CC', ka + 3)  #
        if ka < 0:
            break
        kc = treestr.find(')', ka + 3)
        bds = get_enclosing_bounds(ka)
        kb = bds[0]
        if ShowMarkCompd:
            print('\nMC1:', treestr[kb:])
        # these aren't straightforward compound noun phrases we are looking for
        if '(VP' in treestr[bds[0]:bds[1]] or '(S' in treestr[bds[0]:bds[1]]:
            # convert CC to CCP, though <14.05.12> we don't actually do anything with
            # this: (NEC is a sufficient trigger for additional processing of
            # compounds
            treestr = treestr[:ka + 3] + 'P' + treestr[ka + 3:]
            if ShowMarkCompd:
                print('\nMC2:', treestr[kb:])
        # nested compounds: don't go there...
        elif treestr[bds[0]:bds[1]].count('(CC') > 1:
            # convert CC to CCP: see note above
            treestr = treestr[:ka + 4] + 'P' + treestr[ka + 4:]
            if ShowMarkCompd:
                print('\nMC3:', treestr[kb:])
        elif treestr[kb + 1:kb + 3] == 'NP':
            # make sure we actually have multiple nouns in the phrase
            if treestr.count('(N', bds[0], bds[1]) >= 3:
                treestr = treestr[:kb + 2] + 'EC' + \
                    treestr[kb + 3:]  # convert NP to NEC
                if ShowMarkCompd:
                    print('\nMC4:', treestr[kb:])
    #############################

    if ShowRTTrees:
        print('RT1.5 count:', treestr.count('('), treestr.count(')'))

    ka = 0
    while ka < len(treestr):
        if treestr.startswith('(NP ', ka):
            npbds = get_forward_bounds(ka)

            ksb = treestr.find(
                '(SBAR ',
                npbds[0],
                npbds[1])
            while ksb >= 0:

                ########################
                # REDUCE SBAR
                #######################
                bds = get_enclosing_bounds(ksb + 5)
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
                # bound with '(SBR ' and ' )'
                treestr = treestr[:bds[0]] + \
                    '(SBR ' + frag + treestr[bds[1] - 2:]
                #########################

                # recompute the bounds because treestr has been modified
                npbds = get_forward_bounds(ka)
                ksb = treestr.find('(SBAR ', npbds[0], npbds[1])
            nephrase = ''
            if ShowNEParsing:
                print('BBD: ', treestr[npbds[0]:npbds[1]])
            if '(POS' in treestr[ka + 3:npbds[1]]:  # get the (NP possessive
                kb = treestr.find('(POS', ka + 4)
                nephrase = treestr[ka + 4:kb - 1]  # get string prior to (POS
                if treestr[kb + 12] == 's':
                    incr = 14
                else:
                    incr = 13   # allow for (POS ')
                # skip over (POS 's) and get the remainder of the NP
                nephrase += ' ' + treestr[kb + incr:npbds[1]]
                if ShowNEParsing:
                    print('RTPOS: NE:', nephrase)

            elif '(PP' in treestr[ka + 3:npbds[1]]:  # prepositional phrase
                if False:
                    print('PPP-1: ', treestr[ka:npbds[1]])
                    print(
                        'PPP-1a: ',
                        treestr.find(
                            '(PP',
                            ka + 3,
                            npbds[1]),
                        ka,
                        npbds[1])
                    print(
                        'PPP-1b: ',
                        get_enclosing_bounds(
                            treestr.find(
                                '(PP',
                                ka + 3,
                                npbds[1])))
                nephrase = process_preposition(
                    treestr.find('(PP', ka + 3, npbds[1]))
                if ShowNEParsing:
                    print('RTPREP: NE:', nephrase)

            # no further (NPs, so convert to NE
            elif '(NP' not in treestr[ka + 3:npbds[1]] and '(NEC' not in treestr[ka + 3:npbds[1]]:
                nephrase = treestr[ka:npbds[1]]
                if ShowNEParsing:
                    print('RTNP: NE:', nephrase)

            if len(nephrase) > 0:
                try:
                    nplist = get_NE(nephrase)
                except IrregularPattern:
                    check_irregulars('get_NE_error')

                if not nplist:
                    # <14.02.27> Seems like an odd place to hit this error, and it will probably go away...
                    check_irregulars('empty_nplist')
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
            ka, fullline = resolve_compounds(ka, fullline)

        elif treestr.startswith('(VP ', ka):  # assign index to VP
            fullline += '(VP' + str(vpindex) + ' '
            vpindex += 1
            ka += 4
        else:
            fullline += treestr[ka]
            ka += 1

    # convert the text to ParseList format; convert ')' to ~XX tags
    ParseList = fullline.split()
    kopen = 0
    kclose = 0
    for item in ParseList:
        if item.startswith('('):
            kopen += 1
        elif item == ')':
            kclose += 1
    if ShowRTTrees:
        print('RT2 count:', kopen, kclose)
    ka = 0
    opstack = []
    while ka < len(ParseList):
        if ParseList[ka][0] == '(':
            opstack.append(ParseList[ka][1:])
        if ParseList[ka][0] == ')':
            if len(opstack) == 0:
                break
            op = opstack.pop()
            ParseList[ka] = '~' + op
        ka += 1

    if ShowRTTrees:
        print('RT2:', ParseList)
        show_tree_string(' '.join(ParseList))

    ParseStart = 2  # skip (ROOT (S

    check_irregulars()

    try:
        check_balance(ParseList)
    except UnbalancedTree:
        check_irregulars('bad_final_parse')

    return ParseList, ParseStart

# ================== CODING ROUTINES  ================== #


def get_loccodes(thisloc, CodedEvents, UpperSeq, LowerSeq):
    """
    Returns the list of codes from a compound, or just a single code if not compound

    Extracting noun phrases which are not in the dictionary: If no actor or agent
    generating a non-null code can be found using the source/target rules, PETRARCH can
    output the noun phrase in double-quotes. This is controlled by the configuration file
    option new_actor_length, which is set to an integer which gives the maximum length
    for new actor phrases extracted. If this is set to zero [default], no extraction is
    done and the behavior is the same as TABARI. Setting this to a large number will
    extract anything found in a (NP noun phrase, though usually true actors contain a
    small number of words. These phrases can then be processed with named-entity-resolution
    software to extend the dictionaries.
    """

    def get_ne_text(neloc, isupperseq):
        """ Returns the text of the phrase from UpperSeq/LowerSeq starting at neloc. """
        if isupperseq:
            acphr = UpperSeq[neloc - 1]
            ka = neloc - 2  # UpperSeq is stored in reverse order
            # we can get an unbalanced sequence when multi-word verbs cut into
            # the noun phrase: see DEMO-30 in unit-tests
            while ka >= 0 and UpperSeq[ka][0] != '~':
                acphr += ' ' + UpperSeq[ka]
                ka -= 1
        else:
            acphr = LowerSeq[neloc + 1]
            ka = neloc + 2
            while LowerSeq[ka][0] != '~':
                acphr += ' ' + LowerSeq[ka]
                ka += 1

        return acphr

    def add_code(neloc, isupperseq, cl):
        """
        Appends the code or phrase from UpperSeq/LowerSeq starting at neloc.
        isupperseq determines the choice of sequence

        If PETRglobals.WriteActorText is True, root phrase is added to the code following the
        string PETRglobals.TextPrimer
        """
        codelist = cl

        if isupperseq:
            # "add_code neitem"; nothing to do with acne...
            acneitem = UpperSeq[neloc]
        else:
            acneitem = LowerSeq[neloc]
        accode = acneitem[acneitem.find('>') + 1:]
        if accode != '---':
            codelist.append(accode)
        elif PETRglobals.NewActorLength > 0:  # get the phrase
            acphr = '"' + get_ne_text(neloc, isupperseq) + '"'
            if acphr.count(' ') < PETRglobals.NewActorLength:
                codelist.append(acphr)
            else:
                codelist.append(accode)
            if PETRglobals.WriteActorRoot:
                codelist[-1] += PETRglobals.RootPrimer + '---'

        if PETRglobals.WriteActorText and len(codelist) > 0:
            codelist[-1] += PETRglobals.TextPrimer + \
                get_ne_text(neloc, isupperseq)

        return codelist

    codelist = []
    if thisloc[1]:

        try:
            neitem = UpperSeq[thisloc[0]]
        except IndexError:

            raise_ParseList_error(
                'Initial index error on UpperSeq in get_loccodes()')

        # extract the compound codes from the (NEC ... ~NEC sequence
        if '(NEC' in neitem:
            ka = thisloc[0] - 1  # UpperSeq is stored in reverse order
            while '~NEC' not in UpperSeq[ka]:
                if '(NE' in UpperSeq[ka]:
                    codelist = add_code(ka, True, codelist)
                ka -= 1
                if ka < 0:
                    raise_ParseList_error(
                        'Bounds underflow on UpperSeq in get_loccodes()')
        else:
            codelist = add_code(thisloc[0], True, codelist)  # simple code
    else:

        try:
            neitem = LowerSeq[thisloc[0]]
        except IndexError:
            raise_ParseList_error(
                'Initial index error on LowerSeq in get_loccodes()')
        # for event in CodedEvents:
            #print(SentenceID + '\t' + event[0] + '\t' + event[1] + '\t' + event[2])
        if '(NEC' in neitem:  # extract the compound codes
            ka = thisloc[0] + 1
            while '~NEC' not in LowerSeq[ka]:
                if '(NE' in LowerSeq[ka]:
                    add_code(ka, False, codelist)

                ka += 1
                if ka >= len(LowerSeq):
                    raise_ParseList_error(
                        'Bounds overflow on LowerSeq in get_loccodes()')
        else:
            codelist = add_code(thisloc[0], False, codelist)  # simple code
    if len(codelist) == 0:  # this can occur if all codes in an (NEC are null
        codelist = ['---']

    return codelist


def find_source(UpperSeq, Src):
    """
    Assign SourceLoc to the first coded or compound (NE in the UpperSeq; if
    neither found then first (NE with --- code Note that we are going through
    the sentence in normal order, so we go through UpperSeq in reverse order.
    Also note that this matches either (NE and (NEC: these are processed
    differently in make_event_string()
    """
    SourceLoc = Src
    kseq = len(UpperSeq) - 1
    while kseq >= 0:
        if ('(NEC' in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return SourceLoc
        if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return SourceLoc
        kseq -= 1
        # failed, so check for
        # uncoded source
    kseq = len(UpperSeq) - 1
    while kseq >= 0:
        if ('(NE' in UpperSeq[kseq]):
            SourceLoc = [kseq, True]
            return SourceLoc
        kseq -= 1
    return SourceLoc


def find_target(UpperSeq, LowerSeq, CodedEvents, SourceLoc, trgloc):
    """
    Assigns TargetLoc

    Priorities for assigning target:
        1. first coded (NE in LowerSeq that does not have the same code as
        SourceLoc; codes are not checked with either SourceLoc or the
        candidate target are compounds (NEC
        2. first null-coded (NE in LowerSeq ;
        3. first coded (NE in UpperSeq -- that is, searching backwards from
        the verb -- that does not have the same code as SourceLoc;
        4. first null-coded (NE in UpperSeq
    """
    TargetLoc = trgloc
    try:
        srccodelist = get_loccodes(SourceLoc, CodedEvents, UpperSeq, LowerSeq)

    except:

        raise_ParseList_error(
            'tuple error in get_loccodes(SourceLoc) called from find_target()')
    if len(srccodelist) == 1:
        srccode = '>' + srccodelist[0]
    else:
        srccode = '>>>>'  # placeholder for a compound; this will not occur
    kseq = 0
    while kseq < len(LowerSeq):
        if ('(NE' in LowerSeq[kseq]) and ('>---' not in LowerSeq[kseq]):
            if (srccode not in LowerSeq[kseq]):
                TargetLoc = [kseq, False]
                return TargetLoc
        kseq += 1

    kseq = 0
    while kseq < len(LowerSeq):
        # source might also be uncoded now
        if ('(NE' in LowerSeq[kseq]) and ('>---' in LowerSeq[kseq]):
            TargetLoc = [kseq, False]
            return TargetLoc
        kseq += 1

    # still didn't work, so look in UpperSeq going away from the verb, so we
    # increment through UpperSeq
    kseq = 0
    while kseq < len(UpperSeq):
        if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]):
            if (srccode not in UpperSeq[kseq]):
                TargetLoc = [kseq, True]
                return TargetLoc
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
                return TargetLoc
        kseq += 1

    return TargetLoc


def get_upper_seq(kword, ParseList, ParseStart):
    """
    Generate the upper sequence starting from kword; Upper sequence currently
    terminated by ParseStart, ~S or ~,
    """

    UpperSeq = []
    while kword >= ParseStart:
        # print(kword,UpperSeq)
        if ('~,' in ParseList[kword]):
            break
        if ('(NE' == ParseList[kword]):
            code = UpperSeq.pop()  # remove the code
            UpperSeq.append(
                ParseList[kword] +
                '<' +
                str(kword) +
                '>' +
                code)  # <pas 13.07.26> See Note-1
        elif ('NEC' in ParseList[kword]):
            UpperSeq.append(ParseList[kword])
        elif ('~NE' in ParseList[kword]):
            UpperSeq.append(ParseList[kword])
        elif (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
            UpperSeq.append(ParseList[kword])
        kword -= 1
        if kword < 0:
            # error is handled in check_verbs
            raise_ParseList_error('Bounds underflow in get_upper_seq()')
            return  # not needed, right?

    if ShowCodingSeq:
        print("Upper sequence:", UpperSeq)

    return UpperSeq


def get_lower_seq(kword, endtag, ParseList):
    """
    Generate the lower sequence starting from kword; lower sequence includes only
    words in the VP
    """

    LowerSeq = []
    # limit this to the verb phrase itself
    while (endtag not in ParseList[kword]):
        if ('(NE' == ParseList[kword]):
            LowerSeq.append(
                ParseList[kword] +
                '<' +
                str(kword) +
                '>' +
                ParseList[
                    kword +
                    1])  # <pas 13.07.26> See Note-1
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
            # error is handled in check_verbs
            raise_ParseList_error('Bounds overflow in get_lower_seq()')
            return LowerSeq  # not needed, right?

    if ShowCodingSeq:
        print("Lower sequence:", LowerSeq)
    return LowerSeq


def make_multi_sequences(multilist, verbloc, endtag, ParseList, ParseStart):
    """
    Check if the multi-word list in multilist is valid for the verb at ParseList[verbloc],
    then create the upper and lower sequences to be checked by the verb patterns. Lower
    sequence includes only words in the VP; upper sequence currently terminated by ParseStart,
    ~S or ~, Returns False if the multilist is not valid, True otherwise.
    """

    logger = logging.getLogger('petr_log')
    ka = 1
    if multilist[0]:  # words follow the verb
        kword = verbloc + 1
        while ka < len(multilist):
            if (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
                if ParseList[kword] == multilist[ka]:
                    ka += 1
                else:
                    return False, "", ""
            kword += 1
        upper = get_upper_seq(verbloc - 1, ParseList, ParseStart)
        lower = get_lower_seq(kword, endtag, ParseList)
        return True, upper, lower
    else:
        kword = verbloc - 1
        while ka < len(multilist):
            if (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
                if ParseList[kword] == multilist[ka]:
                    ka += 1
                else:
                    return False, "", ""
            kword -= 1

        upper = get_upper_seq(kword, ParseList, ParseStart)
        lower = get_lower_seq(verbloc + 1, endtag, ParseList)
        return True, upper, lower


def skip_item(item):
    """ Determines whether a particular item in the parse needs to be skipped """
    if item[0] in "~(":
        return 1
    if item in ["THE", "A", "AN", "IT", "HE", "THEY",
                "HER", "HAS", "HAD", "HAVE", "SOME", "FEW", "THAT"]:
        return 2
    if item in ["HUNDRED", "THOUSAND", "MILLION", "BILLION", "TRILLION", "DOZEN",
                "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]:
        return 3
    if item in ["DOLLAR", "DUCAT"]:
        return 5
    try:
        int(item)
        return 4
    except:
        return 0


def check_verbs(ParseList, ParseStart, CodedEv):
    """
    Primary coding loop which looks for verbs, checks whether any of their
    patterns match, then fills in the source and target if there has been a
    match. Stores events using make_event_strings().

    Note: the "upper" sequence is the part before the verb -- that is, higher
    on the screen -- and the "lower" sequence is the part after the verb.
    Assuming, of course, that I've used these consistently.

    SourceLoc, TargetLoc structure

    [0]: the location in *Seq where the NE begins
    [1]: True - located in UpperSeq, otherwise in LowerSeq
    """
    CodedEvents = CodedEv

    SourceLoc = ""

    def raise_CheckVerbs_error(kloc, call_location_string):
        """
        Handle problems found at some point internal to check_verbs: skip the verb that
        caused the problem but do [not?] skip the sentence. Logs the error and information on the
        verb phrase and raises CheckVerbsError.
        This is currently only used for check_passive()
        15.04.29: pas -- is that supposed to be "not"?
        """
        global SentenceID
        warningstr = call_location_string + \
            'in check_verbs; verb sequence {} skipped: {}'.format(
                ' '.join(
                    ParseList[
                        kloc:kloc +
                        5]),
                SentenceID)
        logger = logging.getLogger('petr_log')
        logger.warning(warningstr)
        raise CheckVerbsError

    def check_passive(kitem):
        """
        Check whether the verb phrase beginning at kitem is passive; returns
        location of verb if true, zero otherwise.
        """
        try:
            cpendtag = ParseList.index('~' + ParseList[kitem][1:])
        except ValueError:
            raise_CheckVerbs_error(kitem, "check_passive()")
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

    kitem = ParseStart

    while kitem < len(ParseList):

        upper = []
        lower = []
        # print(kitem,ParseList[kitem],ParseList[kitem+1])
        if ('(VP' in ParseList[kitem]) and ('(VB' in ParseList[kitem + 1]):
            vpstart = kitem   # check_passive could change this
            try:
                pv = check_passive(kitem)
            except CheckVerbsError:
                kitem += 1
                continue
            IsPassive = (pv > 0)
            if IsPassive:
                kitem = pv - 2  # kitem + 2 is now at the passive verb
            targ = ParseList[kitem + 2]
            if ShowPattMatch:
                print(
                    "CV-0",
                    "'" +
                    targ +
                    "'",
                    targ in PETRglobals.VerbDict['verbs'])
            if targ in PETRglobals.VerbDict['verbs']:
                SourceLoc = ""
                TargetLoc = ""
                if ShowPattMatch:
                    print("CV-1 Found", targ)

                endtag = '~' + ParseList[vpstart][1:]
                hasmatch = False

                patternlist = PETRglobals.VerbDict['verbs'][targ]
                verbcode = '---'

                #################################
                # Find verb boundaries, verb code
                #
                #   notes: Post-compound verbs should
                #          work fine, e.g. "put off".
                #          still unclear how pre-compounds work
                #
                #################################

                verb_start = kitem + 2
                verb_end = kitem + 2

                # Prioritize compound verb matches
                # I'm sure theres some information theoretical reason this is a
                # good idea

                meaning = ''
                # print(targ)
                verbdata = {}
                hasmatch = False
                if not patternlist.keys() == ['#']:
                    # compound verb, look ahead
                    #print("LOOKING AHEAD",patternlist,ParseList,targ)

                    i = kitem + 3
                    found_flag = True
                    # accounts for long compounds, dunno if these actually
                    # exist
                    while found_flag:
                        skipcheck = skip_item(ParseList[i])
                        if skipcheck:
                            i += 1
                            continue
                        if ParseList[i] in patternlist:
                            if '#' in patternlist[ParseList[i]]:
                                found_flag = False
                                verb_end = i
                                upper_compound = patternlist[ParseList[i]]['#']
                                hasmatch = True
                                if not '#' in upper_compound:
                                    # this verb is compounded in both directions, again don't know how SNLP will parse this
                                    #print("DOUBLE COMPOUND VERB")
                                    # print(targ,upper_compound,patternlist,"\n\n",ParseList)
                                    raise_CheckVerbs_error()
                                verbdata = upper_compound['#']
                            else:
                                i += 1  # Does this actually work?
                                # if ParseList[i] == "REALLY":
                                # print(ParseList,patternlist,i)
                                #    exit()
                        else:
                            # print(verb_start,verb_end,patternlist,ParseList[i])

                            if '#' in patternlist:
                                verbdata = patternlist['#']['#']
                            #print("Incomplete match on compound verb")
                            break

                if not hasmatch:
                    if not patternlist['#'].keys() == ['#']:
                        # Compound verb, look behind
                        i = kitem - 1
                        found_flag = True
                        while found_flag and i >= 0:
                            # print(ParseList[i])
                            skipcheck = skip_item(ParseList[i])
                            if skipcheck:
                                i -= 1
                                continue
                            if ParseList[i] in patternlist['#']:
                                if '#' in patternlist['#'][ParseList[i]]:
                                    found_flag = False
                                    verb_start = i
                                    verbdata = patternlist['#'][
                                        ParseList[i]]['#']
                                    hasmatch = True
                                else:
                                    i -= 1
                            else:

                                # print(verb_start,verb_end,patternlist,ParseList[i])
                                #print("Incomplete match on compound verb")
                                if '#' in patternlist:
                                    verbdata = patternlist['#']['#']
                                break
                    if not hasmatch:
                        # Simple verb
                        if '#' in patternlist['#']:
                            verbdata = patternlist['#']['#']
                            hasmatch = True

                if not verbdata == {}:
                    meaning = verbdata['meaning']
                    code = verbdata['code']
                    line = verbdata['line']

                upper = get_upper_seq(verb_start - 1, ParseList, ParseStart)
                lower = get_lower_seq(verb_end + 1, endtag, ParseList)
                if not meaning == '':
                    patternlist = PETRglobals.VerbDict['phrases'][meaning]
                if ShowPattMatch:
                    print("CV-2 patlist")

                vpm, lowsrc, lowtar = verb_pattern_match(
                    patternlist, upper, lower)
                hasmatch = False
                if not vpm == {}:
                    hasmatch = True
                    EventCode = vpm[0]['code']
                    line = vpm[0]['line']
                    SourceLoc = lowsrc if not lowsrc == "" else vpm[2]
                    TargetLoc = lowtar if not lowtar == "" else vpm[1]

                if hasmatch and EventCode == '---':
                    hasmatch = False
                if not hasmatch and verbcode != '---':
                    if ShowPattMatch:
                        print(
                            "Matched on the primary verb",
                            targ,
                            meaning,
                            line)
                    EventCode = verbcode
                    hasmatch = True
                if hasmatch:
                    # print("##########",SourceLoc)
                    if SourceLoc == "":
                        SourceLoc = find_source(upper, SourceLoc)
                    if ShowPattMatch:
                        print("CV-3 src", SourceLoc)
                    if not SourceLoc == "":
                        if TargetLoc == "":
                            TargetLoc = find_target(
                                upper,
                                lower,
                                CodedEvents,
                                SourceLoc,
                                TargetLoc)
                        if not TargetLoc == "":
                            if ShowPattMatch:
                                print("CV-3 tar", TargetLoc)
                            CodedEvents = make_event_strings(
                                CodedEvents,
                                upper,
                                lower,
                                SourceLoc,
                                TargetLoc,
                                IsPassive,
                                EventCode)
                            # print(CodedEvents)
                if hasmatch:

                    while (endtag not in ParseList[kitem]):
                        kitem += 1  # resume search past the end of VP
        kitem += 1
    return CodedEvents, SourceLoc


def verb_pattern_match(patlist, upper, lower):
    """
    ##########################################
    ##
    ##      Symbols:
    ##          $ = Source
    ##          + = Target
    ##          ^ ="Skip to end of the (NE
    ##          % = Compound
    ##
    ##########################################
    """

    VPMPrint = False

    def find_actor(phrase, i):
        for j in range(i, len(phrase)):
            if phrase[j][0] == "(":
                return j

    def upper_match(pathdict):

        ########################
        # Match upper phrase
        ########################
        in_NE = False
        in_NEC = False
        phrase_actor = ""
        phrase = upper
        matchlist = []
        option = 0
        path = pathdict
        pathleft = [(pathdict, 0, 0)]
        source = ""
        target = ""
        if VPMPrint:
            print("\nChecking upper", upper)
        i = 0
        while i < len(phrase):
            #print("checking","'"+upper[i]+"'",option,in_NEC,in_NE,'%' in path)

            skipcheck = skip_item(upper[i])

            # check direct word match
            if phrase[i] in path and not option > 0:
                if VPMPrint:
                    print("upper matched a word", phrase[i])
                matchlist.append(phrase[i])
                pathleft.append((path, i, 1))
                path = path[phrase[i]]

            # maybe a synset match
            elif 'synsets' in path and not option > 1:
                if VPMPrint:
                    print("could be a synset")
                matchflag = False
                for set in path['synsets'].keys():
                 #   print("SUP", set,PETRglobals.VerbDict['verbs'][set])
                    if upper[i] in PETRglobals.VerbDict['verbs'][set]:
                        if VPMPrint:
                            print("We found a synset match")
                        pathleft.append((path, i, 2))
                        path = path['synsets'][set]
                        matchlist.append(set)
                        i += 1
                        matchflag = True
                        break
                option = 0 if matchflag else 2
                continue
            # check for target match
            elif in_NE and (not option > 2) and '+' in path:
                pathleft.append((path, i, 3, target))
                i = find_actor(upper, i)
                target = [i, True]
                path = path['+']
                matchlist += ['+']
                if VPMPrint:
                    print("Matching phrase target", target)
                continue

            elif in_NE and (not option > 3) and '$' in path:
                pathleft.append((path, i, 4, source))
                i = find_actor(upper, i)
                source = [i, True]
                path = path['$']
                matchlist.append(source)
                if VPMPrint:
                    # check for source match
                    print("Matching phrase source")
                continue

            elif in_NE and (not option > 4) and '^' in path:
                j = i
                if VPMPrint:
                    print("Matching phrase skip")
                matchlist.append('^')
                while j >= 0:
                    if "~NE" == upper[j]:
                        pathleft.append((path, i, 5))
                        path = path['^']
                        i = j - 1
                        break
                    j -= 1
                if j >= 0:
                    continue

            elif (not in_NE) and in_NEC and (not option > 5) and '%' in path:
                if VPMPrint:
                    print("Matching compound", upper, i)
                ka = i
                while '(NEC' not in upper[ka]:
                    # print(upper[ka])
                    ka += 1
                    if ka >= len(upper):
                        option = 6
                        break
                if option == 6:
                    continue
                source = [ka, True]
                target = source
                pathleft.append((path, i, 6))
                path = path['%']
                matchlist.append('%')
                i = ka
                continue

            elif skipcheck > 0:
                # if VPMPrint:
                #    print("skipping")
                if "~NEC" in upper[i]:
                    in_NEC = not in_NEC
                elif "~NE" in upper[i]:
                    in_NE = not in_NE
                i += 1
                continue

            elif (not i >= len(upper)) and not option > 6:
                i += 1
                pathleft.append((path, i, 7))
                if VPMPrint:
                    print("skipping")
                option = 0
                matchlist.append("*")
                continue

            elif "#" in path:
                if VPMPrint:
                    print("Upper pattern matched", matchlist)
                return True, (path['#'], target, source)

            # return to last point of departure
            elif not pathleft[-1][2] == 0:
                if VPMPrint:
                    print("retracing", upper[i], path, upper[i] in path)
                p = pathleft.pop()
                path = p[0]
                i = p[1] + 1
                option = p[2]
                if option == 3:
                    target = p[3]
                elif option == 4:
                    source = p[3]
                matchlist.pop()
                continue

            else:
                if VPMPrint:
                    print("no match in upper", pathleft[-1][0].keys())
                return False, {}

            i += 1
            option = 0
            # print("MATCHED",matchlist)

        if "#" in path:
            return True, (path['#'], target, source)
        return False, {}

    #################################################
    # Match lower phrase via Depth-First-ish Search
    #################################################

    # Stack is of 3-tuples (path,index,option)
    path = patlist
    phrase_return = True

    option = 0
    i = 0
    matchlist = []
    pathleft = [(path, 0, 0)]
    target = ""
    source = ""
    in_NEC = False
    in_NE = False
    if VPMPrint:
        print("\nChecking phrase", lower)
    # print("\t\t\t\tpatlist:",patlist)
    phrase_actor = ""
    while i < len(lower):
        if pathleft == []:
            pathleft = [(path, i, 0)]
        if VPMPrint:
            print(
                "checking",
                "'" +
                lower[i] +
                "'",
                option,
                phrase_actor,
                in_NE)
        skipcheck = skip_item(lower[i])

        # return to last point of departure
        if i == len(lower) - 1 and not pathleft[-1][2] == 0:
            if VPMPrint:
                print("retracing", len(pathleft))
            p = pathleft.pop()
            path = p[0]
            i = p[1] + 1
            option = p[2]
            matchlist.pop()
            continue

        if skipcheck > 0:
            if "NEC" in lower[i]:
                in_NEC = not in_NEC
            elif "NE" in lower[i]:
                in_NE = not in_NE
                if len(lower[i]) > 3:
                    phrase_actor = i
            i += 1
            continue

        # check direct word match
        if lower[i] in path and not option > 0:
            if VPMPrint:
                print("matched a word", lower[i])
            matchlist.append(lower[i])
            pathleft.append((path, i, 1))
            path = path[lower[i]]

        # maybe a synset match
        elif 'synsets' in path and not option > 1:
            #print("could be a synset")
            matchflag = False
            for set in path['synsets'].keys():
                # if VPMPrint:
                    #print("SUP", set,PETRglobals.VerbDict['verbs'][set])
                if lower[i] in PETRglobals.VerbDict['verbs'][set]:
                    if VPMPrint:
                        print("We found a synset match")
                    pathleft.append((path, i, 2))
                    path = path['synsets'][set]
                    matchlist.append(set)
                    i += 1
                    matchflag = True
                    break
            option = 0 if matchflag else 2
            continue

        # check for target match
        elif in_NE and (not option > 2) and '+' in path:

            pathleft.append((path, i, 3, target))
            target = [phrase_actor, False]
            path = path['+']
            matchlist += [target]
            if VPMPrint:
                print("Matching phrase target")
            continue

        elif in_NE and (not option > 3) and '$' in path:

            pathleft.append((path, i, 4, source))
            source = [phrase_actor, False]
            path = path['$']
            matchlist.append(source)
            if VPMPrint:
                # check for source match
                print("Matching phrase source")
            continue

        elif in_NE and (not option > 4) and '^' in path:
            j = i
            if VPMPrint:
                print("Matching phrase skip")
            matchlist.append('^')
            while j < len(lower):
                if "~NE" == lower[j]:
                    pathleft.append((path, i, 5))
                    path = path['^']
                    i = j + 1

                    in_NE = False
                    break
                j += 1
            if not j < len(lower):
                i += 1
            continue

        elif not in_NE and in_NEC and (not option > 5) and '%' in path:
            if VPMPrint:
                print("Matching compound", upper, i)
            ka = i
            # print(ka)
            while '(NEC' not in upper[ka]:
                # print(upper[ka])
                ka += 1
                if ka >= len(upper):
                    option = 6
                    break
            if option == 6:
                continue
            source = lower[ka][-3:]
            target = source
            pathleft.append((path, i, 6))
            path = path['%']
            matchlist.append('%')
            continue

        elif i + 1 < len(lower) and not option > 6:
            option = 0
            pathleft.append((path, i, 7))
            i += 1
            matchlist.append("*")
            continue

        elif "#" in path:
            if VPMPrint:
                print(
                    "Lower pattern matched",
                    matchlist)           # now check upper
            result, data = upper_match(path['#'])
            if result:
                return data, source, target
            if VPMPrint:
                print("retracing", len(pathleft))
            p = pathleft.pop()
            path = p[0]
            i = p[1] + 1
            option = p[2]
            if option == 3:
                target = p[3]
            elif option == 4:
                source = p[3]
            if not matchlist == []:
                m = matchlist.pop()
                if m == '$':
                    source = ""
            continue

        # return to last point of departure
        elif not pathleft[-1][2] == 0:
            if VPMPrint:
                print("retracing", len(pathleft))
            p = pathleft.pop()
            path = p[0]
            i = p[1] + 1
            option = p[2]
            if option == 3:
                target = p[3]
            elif option == 4:
                source = p[3]
            matchlist.pop()
            continue

        else:
            if VPMPrint:
                print("no match in lower", pathleft.keys())
            phrase_return = False
            break

        i += 1
        option = 0

    return {}, "", ""


"""def get_actor_code(index):
#    Get the actor code, resolving date restrictions.
    global SentenceOrdDate

    codelist = PETRglobals.ActorCodes[index]
    if len(codelist) == 1 and len(codelist[0]) == 1:
        return codelist[0][0]  # no restrictions: the most common case
    for item in codelist:
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
    return '---' 	# if no condition is satisfied, return a null code;"""


def get_actor_code(index, SentenceOrdDate):
    """ Get the actor code, resolving date restrictions. """
    logger = logging.getLogger('petr_log')

    thecode = None
    try:
        codelist = PETRglobals.ActorCodes[index]
    except IndexError:

        logger.warning(
            '\tError processing actor in get_actor_code. Index: {}'.format(index))
        thecode = '---'
    if len(codelist) == 1 and len(codelist[0]) == 1:

        thecode = codelist[0][0]  # no restrictions: the most common case
    for item in codelist:
        if len(item) > 1:  # interval date restriction
            if item[0] == 0 and SentenceOrdDate <= item[1]:
                thecode = item[2]
                break
            if item[0] == 1 and SentenceOrdDate >= item[1]:
                thecode = item[2]
                break
            if item[0] == 2 and SentenceOrdDate >= item[
                    1] and SentenceOrdDate <= item[2]:
                thecode = item[3]
                break
    # if interval search failed, look for an unrestricted code
    if not thecode:
        # assumes even if PETRglobals.WriteActorRoot, the actor name at the end
        # of the list will have length >1 if
        for item in codelist:
            if len(item) == 1:
                thecode = item[0]

    if not thecode:
        thecode = '---'
    elif PETRglobals.WriteActorRoot:
        thecode += PETRglobals.RootPrimer + codelist[-1]

    return thecode


def actor_phrase_match(patphrase, phrasefrag):
    """
    Determines whether the actor pattern patphrase occurs in phrasefrag. Returns True if
    match is successful. Insha'Allah...
    """
    ret = False
    APMprint = False
    connector = patphrase[1]
    kfrag = 1   # already know first word matched
    kpatword = 2  # skip code and connector
    if APMprint:
        # debug
        print(
            "APM-1",
            len(patphrase),
            patphrase,
            "\nAPM-2",
            len(phrasefrag),
            phrasefrag)
    if len(patphrase) == 2:
        if APMprint:
            print("APM-2.1: singleton match")   # debug
        return True, 1  # root word is a sufficient match
    # <14.02.28>: these both do the same thing, except one handles a string of
    # the form XXX and the other XXX_. This is probably unnecessary. though it
    # might be...I suppose those are two distinct cases.
    if len(patphrase) == 3 and patphrase[2][0] == "":
        if APMprint:
            print("APM-2.2: singleton match")   # debug
        return True, 1  # root word is a sufficient match
    if kfrag >= len(phrasefrag):
        return False, 0     # end of phrase with more to match
    while kpatword < len(patphrase):  # iterate over the words in the pattern
        if APMprint:
            # debug
            print(
                "APM-3",
                kfrag,
                kpatword,
                "\n  APM Check:",
                kpatword,
                phrasefrag[kfrag],
                patphrase[kpatword][0])
        if phrasefrag[kfrag] == patphrase[kpatword][0]:
            if APMprint:
                print("  APM match")  # debug
            connector = patphrase[kpatword][1]
            kfrag += 1
            kpatword += 1
            # final element is just the terminator
            if kpatword >= len(patphrase) - 1:
                return True, kfrag  # complete pattern matched
        else:
            if APMprint:
                print("  APM fail")  # debug
            if connector == '_':
                return False, 0  # consecutive match required, so fail
            else:
                kfrag += 1  # intervening words are allowed
        if kfrag >= len(phrasefrag):
            return False, 0     # end of phrase with more to match

    return (

        # complete pattern matched (I don't think we can ever hit this)
        True, len(phrasefrag)
    )


def check_NEphrase(nephrase, date):
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

    If PETRglobals.WriteActorRoot is True, root phrase is added to the code following the
    string PETRglobals.RootPrimer
    """

    kword = 0
    actorcode = ""
    actor_index = [-1, -1]
    if ShowNEParsing:
        print("CNEPh initial phrase", nephrase)  # debug
    # iterate through the phrase looking for actors
    while kword < len(nephrase):
        phrasefrag = nephrase[kword:]
        if ShowNEParsing:
            print("CNEPh Actor Check", phrasefrag[0])  # debug
        # check whether patterns starting with this word exist in the
        # dictionary
        if phrasefrag[0] in PETRglobals.ActorDict:
            if ShowNEParsing:
                print("                Found", phrasefrag[0])  # debug
            patlist = PETRglobals.ActorDict[nephrase[kword]]
            # print(patlist)
            # if ShowNEParsing:
            # print("CNEPh Mk1:", patlist)
            # iterate over the patterns beginning with this word
            actor_index = (kword, kword)
            for index in range(len(patlist)):

                val, phraselen = actor_phrase_match(patlist[index], phrasefrag)
                if val:
                    # found a coded actor
                    actor_index = (kword, kword + phraselen)
                    actorcode = get_actor_code(patlist[index][0], date)
                    if ShowNEParsing:
                        print("CNEPh Mk2:", actorcode)
                    break
        if len(actorcode) > 0:
            break   # stop after finding first actor
        else:
            kword += 1

    kword = 0
    agentlist = []
    while kword < len(nephrase):  # now look for agents
        if kword >= actor_index[0] and kword < actor_index[1]:

            kword += 1  # Don't look for agents in the actor phrase
            continue
        phrasefrag = nephrase[kword:]
        if ShowNEParsing:
            print("CNEPh Agent Check", phrasefrag[0])  # debug
        # check whether patterns starting with this word exist in the
        # dictionary

        if phrasefrag[0] in PETRglobals.AgentDict:
            if ShowNEParsing:
                print("                Found", phrasefrag[0])  # debug
            patlist = PETRglobals.AgentDict[nephrase[kword]]
            # iterate over the patterns beginning with this word
            for index in range(len(patlist)):

                val = actor_phrase_match(patlist[index], phrasefrag)

                if val[0]:
                    agentlist.append(patlist[index][0])   # found a coded actor
                    kword += val[1] - 1
                    break
        kword += 1   # continue looking for more agents

    if len(agentlist) == 0:
        if len(actorcode) == 0:
            return [False]  # no actor or agent
        else:
            return [True, actorcode]  # actor only

    if len(actorcode) == 0:
        actorcode = '---'   # unassigned agent

    if PETRglobals.WriteActorRoot:
        part = actorcode.partition(PETRglobals.RootPrimer)
        actorcode = part[0]
        actorroot = part[2]

    for agentcode in agentlist:  # assemble the composite code
        if agentcode[0] == '~':
            agc = agentcode[1:]  # extract the code
        else:
            agc = agentcode[:-1]
        aglen = len(agc)  # set increment to the length of the agent code
        ka = 0  # check if the agent code is already present
        while ka <= len(actorcode) - aglen:
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
    if PETRglobals.WriteActorRoot:
        actorcode += PETRglobals.RootPrimer + actorroot

    return [True, actorcode]


def check_commas(plist):
    """
    Removes comma-delimited clauses from ParseList.

    Note that the order here is to remove initial, remove terminal, then remove
    intermediate. Initial and terminal remove are done only once; the
    intermediate is iterated. In a sentence where the clauses can in fact be
    removed without affecting the structure, the result will still be balanced.
    If this is not the case, the routine raises a Skip_Record rather than
    continuing with whatever mess is left.

    Because this is working with ParseList, any commas inside (NP should
    already have had their tags removed as they were converted to (NE

    This was a whole lot simpler in TABARI, but TABARI also made some really
    weird matches following comma-clause deletion.
    """
    ParseList = plist

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
                if ParseList[ka][0] != '(' and ParseList[ka][
                        0] != '~' and ParseList[ka][0].isalpha():
                    cwkt += 1
                ka += 1
        return cwkt

    def find_end():
        """
        Returns location of tag on punctuation at end of phrase, defined as
        last element without ~
        """
        ka = len(ParseList) - 1
        while ka >= 2 and ParseList[ka][0] == '~':
            ka -= 1
        return ka - 1

    def delete_phrases(loclow, lochigh, list):
        """
        Deletes the complete phrases in ParseList between loclow and lochigh - 1, leaving
        other mark-up.

        This is the workhorse for this function only removes (xx...~xx delimited phrases
        when these are completely within the clause being removed. This will potentially
        leave the tree in something of a mess grammatically, but it will be balanced.

        [Since you are wondering, we go through this in reverse in order to use index(),
        as there is no rindex() for lists.]
        """
        ParseList = list
        stack = []  # of course we use a stack...this is a tree...
        ka = lochigh - 1
        while ka >= loclow:
            if ParseList[ka][0] == '~':
                stack.append(ParseList[ka][1:])
            # remove this complete phrase
            elif len(stack) > 0 and ParseList[ka][0] == '(' and ParseList[ka][1:] == stack[-1]:
                targ = '~' + ParseList[ka][1:]
                ParseList = ParseList[:ka] + \
                    ParseList[ParseList.index(targ, ka + 1) + 1:]
                stack.pop()
            ka -= 1

        return ParseList

    logger = logging.getLogger('petr_log')
    # displays trees at various points as ParseList is mangled
    ShowCCtrees = True
    ShowCCtrees = False

    if '(,' not in ParseList:
        return ParseList

    if ShowCCtrees:
        print('chkcomma-1-Parselist::', ParseList)
        show_tree_string(' '.join(ParseList))

    if PETRglobals.CommaBMax != 0:  # check for initial phrase
        """
        Initial phrase elimination in check_commas(): delete_phrases() will tend to leave
        a lot of (xx opening tags in place, making the tree a grammatical mess, which is
        why initial clause deletion is turned off by default.
        """

        kount = count_word(2, ParseList.index('(,'))
        if kount >= PETRglobals.CommaBMin and kount <= PETRglobals.CommaBMax:
            # leave the comma in place so an internal can catch it
            loclow = 2
            lochigh = ParseList.index('(,')
            ##################
            # DELETE PHRASES
            ##################
            stack = []  # of course we use a stack...this is a tree...
            ka = lochigh - 1
            while ka >= loclow:
                if ParseList[ka][0] == '~':
                    stack.append(ParseList[ka][1:])
                # remove this complete phrase
                elif len(stack) > 0 and ParseList[ka][0] == '(' and ParseList[ka][1:] == stack[-1]:
                    targ = '~' + ParseList[ka][1:]
                    ParseList = ParseList[:ka] + \
                        ParseList[ParseList.index(targ, ka + 1) + 1:]
                    stack.pop()
                ka -= 1
            #################

        if ShowCCtrees:
            print('chkcomma-1a-Parselist::', ParseList)
            show_tree_string(' '.join(ParseList))
    if PETRglobals.CommaEMax != 0:  # check for terminal phrase
        kend = find_end()
        ka = kend - 1  # terminal: reverse search for '('
        while ka >= 2 and ParseList[ka] != '(,':
            ka -= 1
        if ParseList[ka] == '(,':
            kount = count_word(ka, len(ParseList))
            if kount >= PETRglobals.CommaEMin and kount <= PETRglobals.CommaEMax:
                # leave the comma in place so an internal can catch it

                #################
                # DELETE PHRASES
                ###################
                loclow = ka + 3
                lochigh = kend
                stack = []  # of course we use a stack...this is a tree...
                ka = lochigh - 1
                while ka >= loclow:
                    if ParseList[ka][0] == '~':
                        stack.append(ParseList[ka][1:])
                    # remove this complete phrase
                    elif len(stack) > 0 and ParseList[ka][0] == '(' and ParseList[ka][1:] == stack[-1]:
                        targ = '~' + ParseList[ka][1:]
                        ParseList = ParseList[:ka] + \
                            ParseList[ParseList.index(targ, ka + 1) + 1:]
                        stack.pop()
                    ka -= 1
                ####################


# ParseList = ParseList[:ka + 3] + ParseList[kend:]  # leave the comma in
# place so an internal can catch it

        if ShowCCtrees:
            print('chkcomma-2a-Parselist::')
            show_tree_string(' '.join(ParseList))
            print("cc-2t:", kount)
    if PETRglobals.CommaMax != 0:
        ka = ParseList.index('(,')
        while True:
            try:
                kb = ParseList.index('(,', ka + 1)
            except ValueError:
                break
            kount = count_word(ka + 2, kb)  # ka+2 skips over , ~,
            if kount >= PETRglobals.CommaMin and kount <= PETRglobals.CommaMax:

                #################
                # DELETE PHRASES
                #################
                loclow = ka
                lochigh = kb
                stack = []  # of course we use a stack...this is a tree...
                ka = lochigh - 1
                while ka >= loclow:
                    if ParseList[ka][0] == '~':
                        stack.append(ParseList[ka][1:])
                        # remove this complete phrase
                    elif len(stack) > 0 and ParseList[ka][0] == '(' and ParseList[ka][1:] == stack[-1]:
                        targ = '~' + ParseList[ka][1:]
                        ParseList = ParseList[:ka] + \
                            ParseList[ParseList.index(targ, ka + 1) + 1:]
                        stack.pop()
                    ka -= 1
            ###############

            ka = kb

        if ShowCCtrees:
            print('chkcomma-3a-Parselist::')
            show_tree_string(' '.join(ParseList))

    # check for dangling initial or terminal (, , ~,

    ka = ParseList.index('(,')   # initial
    if count_word(2, ka) == 0:
        ParseList = ParseList[:ka] + ParseList[ka + 3:]

    kend = find_end()
    ka = kend - 1  # terminal: reverse search for '(,'
    while ka >= 2 and ParseList[ka] != '(,':
        ka -= 1
    if ParseList[ka] == '(,':
        if count_word(ka + 1, kend) == 0:
            ParseList = ParseList[:ka] + ParseList[ka + 3:]

    if ShowCCtrees:
        print('chkcomma-end-Parselist::')
        show_tree_string(' '.join(ParseList))

    try:
        check_balance(ParseList)
    except UnbalancedTree:
        raise_ParseList_error('check_balance at end of check_comma()')
    return ParseList


def assign_NEcodes(plist, ParseStart, date):
    """
    Assigns non-null codes to NE phrases where appropriate.
    """

    def expand_compound_element(kstart, plist2):
        """
        An almost but not quite a recursive call on expand_compound_NEPhrase().
        This difference is that the (NEC has already been established so we are just
        adding elements inside the list and there is no further check: we're not allowing
        any further nesting of compounds. That could doubtlessly be done fairly easily
        with some possibly too-clever additional code but such constructions are virtually
        unknown in actual news stories.
        """
        ParseList = plist2

        try:
            kend = ParseList.index('~NE', kstart)
            ncstart = ParseList.index('(NEC', kstart, kend)
            ncend = ParseList.index('~NEC', ncstart, kend)
        except ValueError:
            raise_ParseList_error(
                'expand_compound_element() in assign_NEcodes')

        # first element is always '(NE'
        prelist = ParseList[kstart + 1:ncstart]
        postlist = ParseList[ncend + 1:kend]
    # **',postlist
        newlist = []
        ka = ncstart + 1
        while ka < ncend - 1:  # convert all of the NP, NNS and NNP to NE
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
            ka += 1  # okay to increment since next item is (, or (CC
        ParseList = ParseList[:kstart] + newlist + ParseList[kend + 1:]
        return kstart + len(newlist), ParseList

    def expand_compound_NEPhrase(kstart, kend, plist1):
        """
        Expand the compound phrases inside an (NE: this replaces these with a
        list of NEs with the remaining text simply duplicated. Code and agent
        resolution will then be done on these phrases as usual. This will
        handle two separate (NECs, which is as deep as one generally
        encounters.
        """
        ParseList = plist1

        ncstart = ParseList.index('(NEC', kstart, kend)
        ncend = ParseList.index('~NEC', ncstart, kend)
        # first element is always '---'
        prelist = ParseList[kstart + 1:ncstart - 1]
        postlist = ParseList[ncend + 1:kend]
    # --',postlist
        newlist = ['(NEC']
        ka = ncstart + 1

        while ka < ncend - 1:  # convert all of the NP, NNS and NNP to NE
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
            ka += 1  # okay to increment since next item is (, or (CC

        newlist.append('~NEC')
        # insert a tell-tale here in case we need to further expand this
        newlist.append('~TLTL')
        ParseList = ParseList[:kstart] + newlist + ParseList[kend + 1:]

        if '(NEC' in newlist[1:-1]:  # expand next set of (NEC if it exists
            ka = kstart + 1
            while '(NE' in ParseList[ka:ParseList.index('~TLTL', ka)]:
                ka, ParseList = expand_compound_element(ka, ParseList)
        ParseList.remove('~TLTL')  # tell-tale is no longer needed

        return ParseList

    ParseList = plist
    kitem = ParseStart
    while kitem < len(ParseList):
        if '(NE' == ParseList[kitem]:
            if ShowNEParsing:
                print("NE-0:", kitem, ParseList[kitem - 1:])
            nephrase = []
            kstart = kitem
            kcode = kitem + 1
            kitem += 2  # skip NP, code
            if kitem >= len(ParseList):
                raise_ParseList_error(
                    'Bounds overflow in (NE search in assign_NEcodes')

            while '~NE' != ParseList[kitem]:
                # <14.01.15> At present, read_TreeBank can leave (NNx in place
                # in situations involving (PP and (NEC: so COMPOUND-07. This is
                # a mildly kludgy workaround that insures a check_NEphrase gets
                # clean input
                if ParseList[kitem][1:3] != 'NN':
                    nephrase.append(ParseList[kitem])
                kitem += 1
                if kitem >= len(ParseList):
                    raise_ParseList_error(
                        'Bounds overflow in ~NE search in assign_NEcodes')

            if ShowNEParsing:
                print("aNEc", kcode, ":", nephrase)   # debug

            if '(NEC' in nephrase:

                ParseList = expand_compound_NEPhrase(kstart, kitem, ParseList)
                kitem = kstart - 1  # process the (NEs following the expansion
            else:
                result = check_NEphrase(nephrase, date)
                if result[0]:
                    ParseList[kcode] = result[1]
                    if ShowNEParsing:
                        print("Assigned", result[1])   # debug

        kitem += 1
    return ParseList


def make_event_strings(
        CodedEv, UpperSeq, LowerSeq, SourceLoc, TargetLoc, IsPassive, EventCode):
    """
    Creates the set of event strings, handing compound actors and symmetric
    events.
    """

    CodedEvents = CodedEv
    global SentenceLoc, SentenceID

    def extract_code_fields(fullcode):
        """ Returns list containing actor code and optional root and text strings """
        if PETRglobals.CodePrimer in fullcode:
            maincode = fullcode[:fullcode.index(PETRglobals.CodePrimer)]
            rootstrg = None
            textstrg = None
            if PETRglobals.WriteActorRoot:
                part = fullcode.partition(PETRglobals.RootPrimer)
                if PETRglobals.WriteActorText:
                    rootstrg = part[2].partition(PETRglobals.TextPrimer)[0]
                else:
                    rootstrg = part[2]
            if PETRglobals.WriteActorText:
                textstrg = fullcode.partition(PETRglobals.TextPrimer)[2]
            return [maincode, rootstrg, textstrg]

        else:
            return [fullcode, None, None]

    def make_events(codessrc, codestar, codeevt, CodedEvents_):
        """
        Create events from each combination in the actor lists except self-references
        """
        CodedEvents = CodedEvents_
        global SentenceLoc
        for thissrc in codessrc:
            if '(NEC' in thissrc:
                logger.warning(
                    '(NEC source code found in make_event_strings(): {}'.format(SentenceID))
                CodedEvents = []
                return
            srclist = extract_code_fields(thissrc)

            if srclist[0][0:3] == '---' and len(SentenceLoc) > 0:
                # add location if known <14.09.24: this still hasn't been
                # implemented <>
                srclist[0] = SentenceLoc + srclist[0][3:]
            for thistar in codestar:
                if '(NEC' in thistar:
                    logger.warning(
                        '(NEC target code found in make_event_strings(): {}'.format(SentenceID))
                    CodedEvents = []
                    return
                tarlist = extract_code_fields(thistar)
                # skip self-references based on code
                if srclist[0] != tarlist[0]:
                    if tarlist[0][0:3] == '---' and len(SentenceLoc) > 0:
                        # add location if known -- see note above
                        tarlist[0] = SentenceLoc + tarlist[0][3:]
                    if IsPassive:
                        templist = srclist
                        srclist = tarlist
                        tarlist = templist
                    CodedEvents.append([srclist[0], tarlist[0], codeevt])
                    if PETRglobals.WriteActorRoot:
                        CodedEvents[-1].extend([srclist[1], tarlist[1]])
                    if PETRglobals.WriteActorText:
                        CodedEvents[-1].extend([srclist[2], tarlist[2]])

        return CodedEvents

    def expand_compound_codes(codelist):
        """
        Expand coded compounds, that is, codes of the format XXX/YYY
        """
        for ka in range(len(codelist)):
            if '/' in codelist[ka]:
                parts = codelist[ka].split('/')
                # this will insert in order, which isn't necessary but might be
                # helpful
                kb = len(parts) - 2
                codelist[ka] = parts[kb + 1]
                while kb >= 0:
                    codelist.insert(ka, parts[kb])
                    kb -= 1

    logger = logging.getLogger('petr_log')
# p.a.s. 15.05.25: get_loccodes was generating the error "need string or buffer, tuple found" on some records that had been
# converted from the Levant Reuters series; which also occurred around line 1315 on a different record. For the time being,
# just trap and log it.
    try:
        srccodes = get_loccodes(SourceLoc, CodedEvents, UpperSeq, LowerSeq)
        expand_compound_codes(srccodes)
        tarcodes = get_loccodes(TargetLoc, CodedEvents, UpperSeq, LowerSeq)
        expand_compound_codes(tarcodes)
    except:

        logger.warning(
            'tuple error when attempting to extract src and tar codes in make_event_strings(): {}'.format(SentenceID))
        return CodedEvents

    # print(srccodes,tarcodes)
# TODO: This needs to be fixed: this is the placeholder code for having a general country-
#      level location for the sentence or story
    SentenceLoc = ''

    if len(srccodes) == 0 or len(tarcodes) == 0:
        logger.warning(
            'Empty codes in make_event_strings(): {}'.format(SentenceID))
        return CodedEvents
    if ':' in EventCode:  # symmetric event
        if srccodes[0] == '---' or tarcodes[0] == '---':
            if tarcodes[0] == '---':
                # <13.12.08> Is this behavior defined explicitly in the manual???
                tarcodes = srccodes
            else:
                srccodes = tarcodes
        ecodes = EventCode.partition(':')
        CodedEvents = make_events(srccodes, tarcodes, ecodes[0], CodedEvents)
        CodedEvents = make_events(tarcodes, srccodes, ecodes[2], CodedEvents)
    else:
        CodedEvents = make_events(srccodes, tarcodes, EventCode, CodedEvents)
    # remove null coded cases
    if PETRglobals.RequireDyad:
        ka = 0
        # need to evaluate the bound every time through the loop
        while ka < len(CodedEvents):
            if CodedEvents[ka][0] == '---' or CodedEvents[ka][1] == '---':
                del CodedEvents[ka]
            else:
                ka += 1

    if len(CodedEvents) == 0:
        return CodedEvents

    # remove duplicates
    ka = 0
    # need to evaluate the bound every time through the loop
    while ka < len(CodedEvents) - 1:
        kb = ka + 1
        while kb < len(CodedEvents):
            if CodedEvents[ka] == CodedEvents[kb]:
                del CodedEvents[kb]
            else:
                kb += 1
        ka += 1

    return CodedEvents

# ========================== PRIMARY CODING FUNCTIONS ====================== #


def extract_Sentence_info(item):
    """
    Extracts various global fields from the <Sentence record
    item is a dictionary of attributes generated from the XML input.

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
    return(SentenceDate, SentenceID, SentenceCat, SentenceLoc, SentenceValid,SentenceOrdDate)
    """


def check_discards(SentenceText):
    """
    Checks whether any of the discard phrases are in SentenceText, giving
    priority to the + matches. Returns [indic, match] where indic
       0 : no matches
       1 : simple match
       2 : story match [+ prefix]


    """
    sent = SentenceText.upper().split()  # case insensitive matching
    size = len(sent)
    level = PETRglobals.DiscardList
    depart_index = [0]
    discardPhrase = ""

    for i in range(len(sent)):

        if '+' in level:
            return [2, '+ ' + discardPhrase]
        elif '$' in level:
            return [1, ' ' + discardPhrase]
        elif sent[i] in level:
            # print(sent[i],SentenceText.upper(),level[sent[i]])
            depart_index.append(i)
            level = level[sent[i]]
            discardPhrase += " " + sent[i]
        else:
            if len(depart_index) == 0:
                continue
            i = depart_index[0]
            level = PETRglobals.DiscardList
    return [0, '']


def get_issues(SentenceText):
    """
    Finds the issues in SentenceText, returns as a list of [code,count]

    <14.02.28> stops coding and sets the issues to zero if it finds *any*
    ignore phrase
    """

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


def code_record(plist1, pstart, date):
    """
    Code using ParseList read_TreeBank, then return results in StoryEventList
    first element of StoryEventList for each sentence -- this signals the start
    of a list events for a sentence -- followed by lists containing
    source/target/event triples.
    """
    plist = plist1
    #global CodedEvents
    global SentenceID
    global NEmpty

    # code triples that were produced; this is set in make_event_strings
    CodedEvents = []

    logger = logging.getLogger('petr_log')

    try:
        plist = check_commas(plist)
    except IndexError:
        raise_ParseList_error('Index error in check_commas()')

    try:
        plist = assign_NEcodes(plist, pstart, date)
    except NameError:
        print(date)
    if ShowParseList:
        print('code_rec-Parselist::', plist)
    # try:
    # this can throw HasParseError which is caught in do_coding
    CodedEvents, SourceLoc = check_verbs(plist, pstart, CodedEvents)
    # except IndexError:  # <14.09.04: HasParseError should get all of these now
    #    print("VERBS ERROR")
    #    logger.warning('\tIndexError in parsing, but HasParseError should have caught this. Probably a bad sentence.')
    #    print('\tIndexError in parsing. Probably a bad sentence.')

    NEmpty = 0
    if len(CodedEvents) == 0:
        NEmpty += 1

    return CodedEvents, plist, NEmpty

#	if len(raw_input("Press Enter to continue...")) > 0: sys.exit()


def do_validation(filepath):
    """ Unit tests using a validation file. """
    nvalid = 0

    print("Using Validation File: ", filepath)
    answers = {}
    holding = {}

    tree = ET.iterparse(filepath)
    config = {}
    for event, elem in tree:
        if elem.tag == "Config":
            config[elem.attrib['option']] = elem.attrib

        if event == "end" and elem.tag == "Sentence":
            story = elem

            # Check to make sure all the proper XML attributes are included
            attribute_check = [key in story.attrib for key in
                               ['date', 'id', 'sentence', 'source']]
            if not attribute_check:
                print('Need to properly format your XML...')
                break

            parsed_content = story.find('Parse').text
            parsed_content = utilities._format_parsed_str(
                parsed_content)

            # Get the sentence information

            if story.attrib['sentence'] == 'true':

                entry_id, sent_id = story.attrib['id'].split('-')
                parsed = story.findall('EventCoding')
                entry_id = entry_id + "" + sent_id

                #if not entry_id == "AGENTS19": # Debugging validation files
                #    continue

                if not parsed is None:
                    for item in parsed:
                        answers[(entry_id, sent_id)] = answers.setdefault(
                            (entry_id, sent_id), []) + [item.attrib]
                else:
                    print("\n", entry_id, sent_id, ":INPUT MISSING\n")
                text = story.find('Text').text
                text = text.replace('\n', '').replace('  ', '')
                sent_dict = {
                    'content': text,
                    'parsed': parsed_content,
                    'config': config.copy(),
                    'date': story.attrib['date']}
                meta_content = {'date': story.attrib['date'],
                                'source': entry_id}
                content_dict = {'sents': {sent_id: sent_dict},
                                'meta': meta_content}
                if entry_id not in holding:
                    holding[entry_id] = content_dict
                else:
                    holding[entry_id]['sents'][sent_id] = sent_dict

    updated = do_coding(holding, 'VALIDATE')

    correct = 0
    count = 0
    
    for id, entry in sorted(updated.items()):
        count += 1
        if entry['sents'] is None:
            print("Correct:", id, "discarded\n")
            correct += 1
            continue
        for sid, sent in sorted(entry['sents'].items()):

            calc = []
            given = []
            if not 'events' in sent:
                calc += ["empty"]
            else:
                for event in sorted(sent['events']):
                    calc += [(event[0], event[1], event[2])]
            if not (id, sid) in answers:
                correct += 1
                continue
            for event in sorted(answers[(id, sid)]):
                if 'noevents' in event:
                    given += ["empty"]
                    continue
                elif 'error' in event:
                    given += ["empty"]

                    continue
                given += [(event["sourcecode"],
                           event["targetcode"],
                           event["eventcode"])]
            if sorted(given) == sorted(calc):
                correct += 1
            else:
                print(
                    "MISMATCH",
                    id,
                    sid,
                    "\nExpected:",
                    given,
                    "\nActual",
                    calc,
                    "\n")

    print("Correctly identified: ", correct, "out of", count)
    sys.exit()


def do_coding(event_dict, out_file):
    """
    Main coding loop Note that entering any character other than 'Enter' at the
    prompt will stop the program: this is deliberate.
    <14.02.28>: Bug: PETRglobals.PauseByStory actually pauses after the first
                sentence of the *next* story
    """

    treestr = ""

    NStory = 0
    NSent = 0
    NEvents = 0
    NEmpty = 0
    NDiscardSent = 0
    NDiscardStory = 0

    file = open("output.tex",'w')
    
    print("""
\\documentclass[11pt]{article}
\\usepackage{tikz-qtree}
\\usepackage{ifpdf}
\\usepackage{fullpage}
\\usepackage[landscape]{geometry}
\\ifpdf
    \\pdfcompresslevel=9
    \\usepackage[pdftex,     % sets up hyperref to use pdftex driver
            plainpages=false,   % allows page i and 1 to exist in the same document
            breaklinks=true,    % link texts can be broken at the end of line
            colorlinks=true,
            pdftitle=My Document
            pdfauthor=My Good Self
           ]{hyperref} 
    \\usepackage{thumbpdf}
\\else
    \\usepackage{graphicx}       % to include graphics
    \\usepackage{hyperref}       % to simplify the use of \href
\\fi

\\title{Petrarch Output}
\\date{}

\\begin{document}
""", file = file)


    logger = logging.getLogger('petr_log')
    times = 0
    sents = 0
    for key, val in event_dict.items():

        prev_code = []

        SkipStory = False
        print('\n\nProcessing {}'.format(key))
        StoryDate = event_dict[key]['meta']['date']
        StorySource = 'TEMP'

        for sent in val['sents']:
            if 'parsed' in event_dict[key]['sents'][sent]:
                if 'config' in val['sents'][sent]:
                    for id, config in event_dict[key][
                            'sents'][sent]['config'].items():
                        change_Config_Options(config)

                SentenceID = '{}_{}'.format(key, sent)

                print('\tProcessing {}'.format(SentenceID))
                SentenceText = event_dict[key]['sents'][sent]['content']
                # print(SentenceText)
                SentenceDate = event_dict[key]['sents'][sent][
                    'date'] if 'date' in event_dict[key]['sents'][sent] else StoryDate
                Date = PETRreader.dstr_to_ordate(SentenceDate)
                SentenceSource = 'TEMP'

                parsed = event_dict[key]['sents'][sent]['parsed']
                treestr = parsed
                
                #if not "IDIOM" in SentenceID:
                #    continue
                """
                disc = check_discards(SentenceText)
                
                if disc[0] > 0:
                    if disc[0] == 1:
                        print("Discard sentence:", disc[1])
                        logger.info('\tSentence discard. {}'.format(disc[1]))
                        NDiscardSent += 1
                        continue
                    else:
                        print("Discard story:", disc[1])
                        logger.info('\tStory discard. {}'.format(disc[1]))
                        SkipStory = True
                        NDiscardStory += 1
                        break
                
                """
                
                t1 = time.time()
                test_obj = PETRtree.Sentence(treestr,SentenceText,Date)
                
                coded_events = test_obj.get_events()
                #test_obj.do_verb_analysis()
                #print(test_obj.verb_analysis)
                
                
                test_obj.print_to_file(test_obj.tree,file = file)
                del(test_obj)
                code_time = time.time()-t1
                
                times+=code_time
                sents += 1
                print(code_time)

                """

                disc = check_discards(SentenceText)

                if disc[0] > 0:
                    if disc[0] == 1:
                        print("Discard sentence:", disc[1])
                        logger.info('\tSentence discard. {}'.format(disc[1]))
                        NDiscardSent += 1
                        continue
                    else:
                        print("Discard story:", disc[1])
                        logger.info('\tStory discard. {}'.format(disc[1]))
                        SkipStory = True
                        NDiscardStory += 1
                        break

    # TODO
    # Can implement this easily. The sentences are organized by story in the dicts
    # so it's easy to rework this. Just when we're done with a key then write out
    # the events for the included sentences. Gonna skip it for now
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

                else:
                    try:
                        ParseList, ParseStart = read_TreeBank(treestr)
                    except IrregularPattern:
                        continue
                    try:
                        coded_events, ParseList, emptyCount = code_record(
                            ParseList, ParseStart, Date)
                        NEmpty += emptyCount
                    except HasParseError:
                        coded_events = None
                """
                if coded_events:
                    event_dict[key]['sents'][sent]['events'] = coded_events
                if coded_events and PETRglobals.IssueFileName != "":
                    event_issues = get_issues(SentenceText)
                    if event_issues:
                        event_dict[key]['sents'][sent]['issues'] = event_issues

                if PETRglobals.PauseBySentence:
                    if len(input("Press Enter to continue...")) > 0:
                        sys.exit()

                prev_code = coded_events

            else:
                logger.info(
                    '{} has no parse information. Passing.'.format(SentenceID))
                pass

        if SkipStory:
            event_dict[key]['sents'] = None


    print("Summary:")
    print(
        "Stories read:",
        NStory,
        "   Sentences coded:",
        NSent,
        "  Events generated:",
        NEvents)
    print(
        "Discards:  Sentence",
        NDiscardSent,
        "  Story",
        NDiscardStory,
        "  Sentences without events:",
        NEmpty)
    print("Average Coding time = ", times/sents)
    print("\n\\end{document})",file=file)

    return event_dict


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

    unittest_command = sub_parse.add_parser('validate', help="""Command to run
                                         the PETRARCH validation suite.""",
                                            description="""Command to run the
                                         PETRARCH validation suite.""")
    unittest_command.add_argument('-i', '--inputs',
                                  help="""Optional file that contains the
                               validation records. If not specified, defaults
                               to the built-in PETR.UnitTest.records.txt""",
                                  required=False)

    batch_command = sub_parse.add_parser('batch', help="""Command to run a batch
                                         process from parsed files specified by
                                         an optional config file.""",
                                         description="""Command to run a batch
                                         process from parsed files specified by
                                         an optional config file.""")
    batch_command.add_argument('-c', '--config',
                               help="""Filepath for the PETRARCH configuration
                               file. Defaults to PETR_config.ini""",
                               required=False)
    args = aparse.parse_args()
    return args


def main():

    cli_args = parse_cli_args()
    utilities.init_logger('PETRARCH.log')
    logger = logging.getLogger('petr_log')

    PETRglobals.RunTimeString = time.asctime()

    if cli_args.command_name == 'validate':
        PETRreader.parse_Config(utilities._get_data('data/config/',
                                                    'PETR_config.ini'))
        read_dictionaries()
        if not cli_args.inputs:
            validation_file = utilities._get_data('data/text',
                                                  'PETR.UnitTest.records.xml')
            do_validation(validation_file)
        else:
            do_validation(cli_args.inputs)

    if cli_args.command_name == 'parse' or cli_args.command_name == 'batch':

        if cli_args.config:
            print('Using user-specified config: {}'.format(cli_args.config))
            logger.info(
                'Using user-specified config: {}'.format(cli_args.config))
            PETRreader.parse_Config(cli_args.config)
        else:
            logger.info('Using default config file.')
            PETRreader.parse_Config(utilities._get_data('data/config/',
                                                        'PETR_config.ini'))

        read_dictionaries()
        start_time = time.time()
        print('\n\n')

        if cli_args.command_name == 'parse':
            if os.path.isdir(cli_args.inputs):
                if cli_args.inputs[-1] != '/':
                    paths = glob.glob(cli_args.inputs + '/*.xml')
                else:
                    paths = glob.glob(cli_args.inputs + '*.xml')
            elif os.path.isfile(cli_args.inputs):
                paths = [cli_args.inputs]
            else:
                print(
                    '\nFatal runtime error:\n"' +
                    cli_args.inputs +
                    '" could not be located\nPlease enter a valid directory or file of source texts.')
                sys.exit()

            run(paths, cli_args.output, cli_args.parsed)

        else:
            run(PETRglobals.TextFileList, PETRglobals.EventFileName, True)

        print("Coding time:", time.time() - start_time)

    print("Finished")


def read_dictionaries(validation=False):

    if validation:
        verb_path = utilities._get_data(
            'data/dictionaries/',
            'PETR.Validate.verbs.txt')
        actor_path = utilities._get_data(
            'data/dictionaries',
            'PETR.Validate.actors.txt')
        agent_path = utilities._get_data(
            'data/dictionaries/',
            'PETR.Validate.agents.txt')
        discard_path = utilities._get_data(
            'data/dictionaries/',
            'PETR.Validate.discards.txt')
        return

    print('Verb dictionary:', PETRglobals.VerbFileName)
    verb_path = utilities._get_data(
        'data/dictionaries',
        PETRglobals.VerbFileName)

    PETRreader.read_verb_dictionary(verb_path)
    # PETRreader.show_verb_dictionary('Verbs_output.txt')

    print('Actor dictionaries:', PETRglobals.ActorFileList)
    for actdict in PETRglobals.ActorFileList:
        actor_path = utilities._get_data('data/dictionaries', actdict)
        PETRreader.read_actor_dictionary(actor_path)

    print('Agent dictionary:', PETRglobals.AgentFileName)
    agent_path = utilities._get_data('data/dictionaries',
                                     PETRglobals.AgentFileName)
    PETRreader.read_agent_dictionary(agent_path)

    print('Discard dictionary:', PETRglobals.DiscardFileName)
    discard_path = utilities._get_data('data/dictionaries',
                                       PETRglobals.DiscardFileName)
    PETRreader.read_discard_list(discard_path)

    if PETRglobals.IssueFileName != "":
        print('Issues dictionary:', PETRglobals.IssueFileName)
        issue_path = utilities._get_data('data/dictionaries',
                                         PETRglobals.IssueFileName)
        PETRreader.read_issue_list(issue_path)


def run(filepaths, out_file, s_parsed):
    events = PETRreader.read_xml_input(filepaths, s_parsed)
    if not s_parsed:
        events = utilities.stanford_parse(events)
    updated_events = do_coding(events, 'TEMP')
    PETRwriter.write_events(updated_events, out_file)


def run_pipeline(data, out_file=None, config=None, write_output=True,
                 parsed=False):
    utilities.init_logger('PETRARCH.log')
    logger = logging.getLogger('petr_log')
    if config:
        print('Using user-specified config: {}'.format(config))
        logger.info('Using user-specified config: {}'.format(config))
        PETRreader.parse_Config(config)
    else:
        logger.info('Using default config file.')
        logger.info('Config path: {}'.format(utilities._get_data('data/config/',
                                                                 'PETR_config.ini')))
        PETRreader.parse_Config(utilities._get_data('data/config/',
                                                    'PETR_config.ini'))

    read_dictionaries()

    logger.info('Hitting read events...')
    events = PETRreader.read_pipeline_input(data)
    if parsed:
        logger.info('Hitting do_coding')
        updated_events = do_coding(events, 'TEMP')
    else:
        events = utilities.stanford_parse(events)
        updated_events = do_coding(events, 'TEMP')
    if not write_output:
        output_events = PETRwriter.pipe_output(updated_events)
        return output_events
    elif write_output and not out_file:
        print('Please specify an output file...')
        logger.warning('Need an output file. ¯\_(ツ)_/¯')
        sys.exit()
    elif write_output and out_file:
        PETRwriter.write_events(updated_events, out_file)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import glob
import time
import logging
import argparse

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


# ========================== VALIDATION FUNCTIONS ========================== #

def get_version():
    return "1.2.0"


# ========================== OUTPUT/ANALYSIS FUNCTIONS ========================== #

def open_tex(filename):
    fname = open(filename, 'w')
    '''fname.write('Run time: ',
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
""", file = fname)'''

    return fname


def close_tex(fname):

    return
    print("\n\\end{document})", file=fname)


# ========================== PRIMARY CODING FUNCTIONS ====================== #


def check_discards(SentenceText):
    """
    Checks whether any of the discard phrases are in SentenceText, giving
    priority to the + matches. Returns [indic, match] where indic
       0 : no matches
       1 : simple match
       2 : story match [+ prefix]
    """
    sent = SentenceText.upper().split()  # case insensitive matching
    #size = len(sent)
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
    def recurse(words, path, length):
        if '#' in path:  # <16.06.06 pas> Swapped the ordering if these checks since otherwise it crashes when '#' is a "word" in the text
            return path['#'], length
        elif words and words[0] in path:
            return recurse(words[1:], path[words[0]], length + 1)
        return False

    sent = SentenceText.upper().split()  # case insensitive matching
    issues = []

    index = 0
    while index < len(sent):
        match = recurse(sent[index:], PETRglobals.IssueList, 0)
        if match:
            index += match[1]
            code = PETRglobals.IssueCodes[match[0]]
            if code[0] == '~':  # ignore code, so bail
                return []
            ka = 0
            #gotcode = False
            while ka < len(issues):
                if code == issues[ka][0]:
                    issues[ka][1] += 1
                    break
                ka += 1
            if ka == len(issues):  # didn't find the code, so add it
                issues.append([code, 1])
        else:
            index += 1
    return issues


def do_coding(event_dict):
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

    logger = logging.getLogger('petr_log')
    times = 0
    sents = 0
    for key, val in sorted(event_dict.items()):
        NStory += 1
        prev_code = []

        SkipStory = False
        print('\n\nProcessing story {}'.format(key))
        StoryDate = event_dict[key]['meta']['date']
        for sent in val['sents']:
            NSent += 1
            if 'parsed' in event_dict[key]['sents'][sent]:
                if 'config' in val['sents'][sent]:
                    for _, config in event_dict[key]['sents'][sent]['config'].items():
                        change_Config_Options(config)

                SentenceID = '{}_{}'.format(key, sent)
                SentenceText = event_dict[key]['sents'][sent]['content']
                SentenceDate = event_dict[key]['sents'][sent][
                    'date'] if 'date' in event_dict[key]['sents'][sent] else StoryDate
                Date = PETRreader.dstr_to_ordate(SentenceDate)

                print("\n", SentenceID)
                parsed = event_dict[key]['sents'][sent]['parsed']
                treestr = parsed
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

                t1 = time.time()
                sentence = PETRtree.Sentence(treestr, SentenceText, Date)
                print(sentence.txt)
                # this is the entry point into the processing in PETRtree
                coded_events, meta = sentence.get_events()
                code_time = time.time() - t1
                if PETRglobals.NullVerbs or PETRglobals.NullActors:
                    event_dict[key]['meta'] = meta
                    event_dict[key]['text'] = sentence.txt
                elif PETRglobals.NullActors:
                    event_dict[key]['events'] = coded_events
                    coded_events = None   # skips additional processing
                    event_dict[key]['text'] = sentence.txt
                else:
                    # 16.04.30 pas: we're using the key value 'meta' at two
                    # very different
                    event_dict[key]['meta']['verbs'] = meta
                    # levels of event_dict -- see the code about ten lines below -- and
                    # this is potentially confusing, so it probably would be useful to
                    # change one of those

                del(sentence)
                times += code_time
                sents += 1
                # print('\t\t',code_time)

                if coded_events:
                    event_dict[key]['sents'][sent]['events'] = coded_events
                    event_dict[key]['sents'][sent]['meta'] = meta
                    #print('DC-events:', coded_events) # --
                    #print('DC-meta:', meta) # --
                    #print('+++',event_dict[key]['sents'][sent])  # --
                    if PETRglobals.WriteActorText or PETRglobals.WriteEventText or PETRglobals.WriteActorRoot:
                        text_dict = utilities.extract_phrases(event_dict[key]['sents'][sent], SentenceID)
# --                        print('DC-td1:',text_dict) # --
                        if text_dict:
                            event_dict[key]['sents'][sent][
                                'meta']['actortext'] = {}
                            event_dict[key]['sents'][sent][
                                'meta']['eventtext'] = {}
                            event_dict[key]['sents'][sent][
                                'meta']['actorroot'] = {}
# --                            print('DC1:',text_dict) # --
                            for evt in coded_events:
                                if evt in text_dict:  # 16.04.30 pas bypasses problems with expansion of compounds
                                    event_dict[key]['sents'][sent]['meta'][
                                        'actortext'][evt] = text_dict[evt][:2]
                                    event_dict[key]['sents'][sent]['meta'][
                                        'eventtext'][evt] = text_dict[evt][2]
                                    event_dict[key]['sents'][sent]['meta'][
                                        'actorroot'][evt] = text_dict[evt][3:5]

                if coded_events and PETRglobals.IssueFileName != "":
                    event_issues = get_issues(SentenceText)
                    if event_issues:
                        event_dict[key]['sents'][sent]['issues'] = event_issues

                if PETRglobals.PauseBySentence:
                    if len(input("Press Enter to continue...")) > 0:
                        sys.exit()

                prev_code = coded_events
                NEvents += len(coded_events)
                if len(coded_events) == 0:
                    NEmpty += 1
            else:
                logger.info('{} has no parse information. Passing.'.format(SentenceID))
                pass

        if SkipStory:
            event_dict[key]['sents'] = None

    print("\nSummary:")
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
    print("Average Coding time = ", times / sents if sents else 0)
# --    print('DC-exit:',event_dict)
    return event_dict


def parse_cli_args():
    """Function to parse the command-line arguments for PETRARCH2."""
    __description__ = """
PETRARCH2
(https://openeventdata.github.io/) (v. 1.0.0)
    """
    aparse = argparse.ArgumentParser(prog='petrarch2',
                                     description=__description__)

    sub_parse = aparse.add_subparsers(dest='command_name')

    parse_command = sub_parse.add_parser('parse', help=""" DEPRECATED Command to run the
                                         PETRARCH parser. Do not use unless you've used it before. If you need to
                                         process unparsed text, see the README""",
                                         description="""DEPRECATED Command to run the
                                         PETRARCH parser. Do not use unless you've used it before.If you need to
                                         process unparsed text, see the README""")
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

    batch_command.add_argument('-i', '--inputs',
                               help="""Filepath for the input XML file. Defaults to
                               data/text/Gigaword.sample.PETR.xml""",
                               required=False)

    batch_command.add_argument('-o', '--outputs',
                               help="""Filepath for the input XML file. Defaults to
                               data/text/Gigaword.sample.PETR.xml""",
                               required=False)

    nulloptions = aparse.add_mutually_exclusive_group()

    nulloptions.add_argument(
        '-na',
        '--nullactors', action='store_true', default=False,
        help="""Find noun phrases which are associated with a verb generating  an event but are
                                not in the dictionary; an integer giving the maximum number of words follows the command.
                                Does not generate events. """,
        required=False)

    nulloptions.add_argument('-nv', '--nullverbs',
                             help="""Find verb phrases which have source and
                               targets but are not in the dictionary. Does not generate events. """,
                             required=False, action="store_true", default=False)

    args = aparse.parse_args()
    return args


def main():
    cli_args = parse_cli_args()
    utilities.init_logger('PETRARCH.log')
    logger = logging.getLogger('petr_log')

    PETRglobals.RunTimeString = time.asctime()

    print(cli_args)
    if cli_args.config:
        print('Using user-specified config: {}'.format(cli_args.config))
        logger.info(
            'Using user-specified config: {}'.format(cli_args.config))
        PETRreader.parse_Config(cli_args.config)
    else:
        logger.info('Using default config file.')
        PETRreader.parse_Config(utilities._get_data('data/config/',
                                                    'PETR_config.ini'))

    if cli_args.nullverbs:
        print('Coding in null verbs mode; no events will be generated')
        logger.info(
            'Coding in null verbs mode; no events will be generated')
        # Only get verb phrases that are not in the dictionary but are
        # associated with coded noun phrases
        PETRglobals.NullVerbs = True
    elif cli_args.nullactors:
        print('Coding in null actors mode; no events will be generated')
        logger.info(
            'Coding in null verbs mode; no events will be generated')
        # Only get actor phrases that are not in the dictionary but
        # associated with coded verb phrases
        PETRglobals.NullActors = True
        PETRglobals.NewActorLength = int(cli_args.nullactors)

    read_dictionaries()
    start_time = time.time()
    print('\n\n')

    paths = PETRglobals.TextFileList
    if cli_args.inputs:
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

    out = ""  # PETRglobals.EventFileName
    if cli_args.outputs:
        out = cli_args.outputs

    if cli_args.command_name == 'parse':
        run(paths, out, cli_args.parsed)

    else:
        run(paths, out, True)  # <===

    print("Coding time:", time.time() - start_time)

    print("Finished")


def read_dictionaries(validation=False):

    print('Verb dictionary:', PETRglobals.VerbFileName)
    verb_path = utilities._get_data(
        'data/dictionaries',
        PETRglobals.VerbFileName)
    PETRreader.read_verb_dictionary(verb_path)

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
    # this is the routine called from main()
    events = PETRreader.read_xml_input(filepaths, s_parsed)
    if not s_parsed:
        events = utilities.stanford_parse(events)
    updated_events = do_coding(events)
    if PETRglobals.NullVerbs:
        PETRwriter.write_nullverbs(updated_events, 'nullverbs.' + out_file)
    elif PETRglobals.NullActors:
        PETRwriter.write_nullactors(updated_events, 'nullactors.' + out_file)
    else:
        PETRwriter.write_events(updated_events, 'evts.' + out_file)


def run_pipeline(data, out_file=None, config=None, write_output=True,
                 parsed=False):
    # this is called externally
    utilities.init_logger('PETRARCH.log')
    logger = logging.getLogger('petr_log')
    if config:
        print('Using user-specified config: {}'.format(config))
        logger.info('Using user-specified config: {}'.format(config))
        PETRreader.parse_Config(config)
    else:
        logger.info('Using default config file.')
        logger.info(
            'Config path: {}'.format(
                utilities._get_data(
                    'data/config/',
                    'PETR_config.ini')))
        PETRreader.parse_Config(utilities._get_data('data/config/',
                                                    'PETR_config.ini'))

    read_dictionaries()

    logger.info('Hitting read events...')
    events = PETRreader.read_pipeline_input(data)
    if parsed:
        logger.info('Hitting do_coding')
        updated_events = do_coding(events)
    else:
        events = utilities.stanford_parse(events)
        updated_events = do_coding(events)
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

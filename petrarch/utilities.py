# -*- coding: utf-8 -*-

##	utilities.py [module]
##
# Utilities for the PETRARCH event data coder
##
# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.10; it is standard Python 2.7
# so it should also run in Unix or Windows.
#
# INITIAL PROVENANCE:
# Programmer:
#             John Beieler
#			  Caerus Associates/Penn State University
#			  Washington, DC / State College, PA, 16801 U.S.A.
#			  http://caerusassociates.com
#             http://bdss.psu.edu
#
# GitHub repository: https://github.com/openeventdata/petrarch
#
# Copyright (c) 2014	John Beieler.	All rights reserved.
#
# This project is part of the Open Event Data Alliance tool set
#
# This code is covered under the MIT license
#
# Report bugs to: john.b30@gmail.com
#
# REVISION HISTORY:
# Summer-14:	Initial version
# ------------------------------------------------------------------------


from __future__ import print_function
from __future__ import unicode_literals

import os
import logging
import corenlp
import dateutil.parser
import PETRglobals
from collections import defaultdict, Counter





def stanford_parse(event_dict):
    logger = logging.getLogger('petr_log')
    # What is dead can never die...
    print("\nSetting up StanfordNLP. The program isn't dead. Promise.")
    logger.info('Setting up StanfordNLP')
    core = corenlp.StanfordCoreNLP(PETRglobals.stanfordnlp,
                                   properties=_get_data('data/config/',
                                                        'petrarch.properties'),
                                   memory='2g')
    total = len(list(event_dict.keys()))
    print(
        "Stanford setup complete. Starting parse of {} stories...".format(total))
    logger.info(
        'Stanford setup complete. Starting parse of {} stories.'.format(total))
    for i, key in enumerate(event_dict.keys()):
        if (i / float(total)) * 100 in [10.0, 25.0, 50, 75.0]:
            print('Parse is {}% complete...'.format((i / float(total)) * 100))
        for sent in event_dict[key]['sents']:
            logger.info('StanfordNLP parsing {}_{}...'.format(key, sent))
            sent_dict = event_dict[key]['sents'][sent]

            if len(sent_dict['content']) > 512 or len(
                    sent_dict['content']) < 64:
                logger.warning(
                    '\tText length wrong. Either too long or too short.')
                pass
            else:
                try:
                    stanford_result = core.raw_parse(sent_dict['content'])
                    s_parsetree = stanford_result['sentences'][0]['parsetree']
                    if 'coref' in stanford_result:
                        sent_dict['coref'] = stanford_result['coref']

                    # TODO: To go backwards you'd do str.replace(' ) ', ')')
                    sent_dict['parsed'] = _format_parsed_str(s_parsetree)
                except Exception as e:
                    print('Something went wrong. ¯\_(ツ)_/¯. See log file.')
                    logger.warning(
                        'Error on {}_{}. ¯\_(ツ)_/¯. {}'.format(key, sent, e))
    print('Done with StanfordNLP parse...\n\n')
    logger.info('Done with StanfordNLP parse.')

    return event_dict


def story_filter(story_dict, story_id):
    """
    One-a-story filter for the events. There can only be only one unique
    (DATE, SRC, TGT, EVENT) tuple per story.

    Parameters
    ----------

    story_dict: Dictionary.
                Story-level dictionary as stored in the main event-holding
                dictionary within PETRARCH.

    story_id: String.
                Unique StoryID in standard PETRARCH format.

    Returns
    -------

    filtered: Dictionary.
                Holder for filtered events with the format
                {(EVENT TUPLE): {'issues': [], 'ids': []}} where the 'issues'
                list is optional.
    """
    filtered = defaultdict(dict)
    story_date = story_dict['meta']['date']
    for sent in story_dict['sents']:
        sent_dict = story_dict['sents'][sent]
        sent_id = '{}_{}'.format(story_id, sent)
        if 'events' in sent_dict:
            events = story_dict['sents'][sent]['events']
            for event in events:
                # do not print unresolved agents
                try:
                    if event[0][0] != '-' and event[1][0] != '-':
                        alist = [story_date]
                        alist.extend(event)
                        event_tuple = tuple(alist)
                        filtered[event_tuple]
                        if 'issues' in sent_dict:
                            filtered[event_tuple]['issues'] = Counter()
                            issues = sent_dict['issues']
                            for issue in issues:
                                filtered[event_tuple]['issues'][
                                    issue[0]] += issue[1]

                        # Will keep track of this info, but not necessarily write it
                        # out
                        filtered[event_tuple]['ids'] = []
                        filtered[event_tuple]['ids'].append(sent_id)
                except IndexError:
                    pass
        else:
            pass

    return filtered


def _format_parsed_str(parsed_str):
    parsed = parsed_str.split('\n')
    parsed = [line.strip() + ' ' for line in [line1.strip() for line1 in
                                              parsed if line1] if line]
    parsed = [line.replace(')', ' ) ').upper() for line in parsed]
    treestr = ''.join(parsed)

    return treestr


def _format_datestr(date):
    datetime = dateutil.parser.parse(date)
    date = '{}{:02}{:02}'.format(datetime.year, datetime.month, datetime.day)
    return date


def _get_data(dir_path, path):
    """Private function to get the absolute path to the installed files."""
    cwd = os.path.abspath(os.path.dirname(__file__))
    joined = os.path.join(dir_path, path)
    out_dir = os.path.join(cwd, joined)
    return out_dir


def _get_config(config_name):
    cwd = os.path.abspath(os.path.dirname(__file__))
    out_dir = os.path.join(cwd, config_name)
    return out_dir


def init_logger(logger_filename):

    logger = logging.getLogger('petr_log')
    logger.setLevel(logging.INFO)

    cwd = os.getcwd()
    logger_filepath = os.path.join(cwd, logger_filename)

    fh = logging.FileHandler(logger_filepath, 'w')
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('Running')

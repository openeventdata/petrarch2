# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.10; it is standard Python 2.7
# so it should also run in Unix or Windows.
#
# INITIAL PROVENANCE:
# Programmer: Philip A. Schrodt
#			  Parus Analytics
#			  Charlottesville, VA, 22901 U.S.A.
#			  http://eventdata.parusanalytics.com
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
# ------------------------------------------------------------------------

from __future__ import print_function
from __future__ import unicode_literals

import PETRglobals  # global variables
import utilities
import codecs

def get_actor_text(meta_strg):
    """ Extracts the source and target strings from the meta string. """
    pass
    

def write_events(event_dict, output_file):
    """
    Formats and writes the coded event data to a file in a standard
    event-data format.

    Parameters
    ----------

    event_dict: Dictionary.
                The main event-holding dictionary within PETRARCH.


    output_file: String.
                    Filepath to which events should be written.
    """
    global StorySource
    global NEvents
    global StoryIssues

    event_output = []
    for key in event_dict:
        story_dict = event_dict[key]
        if not story_dict['sents']:
            continue    # skip cases eliminated by story-level discard
#        print('WE1',story_dict)
        story_output = []
        filtered_events = utilities.story_filter(story_dict, key)
#        print('WE2',filtered_events)
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        else:
            StorySource = 'NULL'
        if 'url' in story_dict['meta']:
            url = story_dict['meta']['url']
        else:
            url = ''
        for event in filtered_events:
            story_date = event[0]
            source = event[1]
            target = event[2]
            code = filter(lambda a: not a == '\n', event[3])

            ids = ';'.join(filtered_events[event]['ids'])

            if 'issues' in filtered_events[event]:
                iss = filtered_events[event]['issues']
                issues = ['{},{}'.format(k, v) for k, v in iss.items()]
                joined_issues = ';'.join(issues)
            else:
                joined_issues = []

            print('Event: {}\t{}\t{}\t{}\t{}\t{}'.format(story_date, source,
                                                         target, code, ids,
                                                         StorySource))
#            event_str = '{}\t{}\t{}\t{}'.format(story_date,source,target,code)
            # 15.04.30: a very crude hack around an error involving multi-word
            # verbs
            if not isinstance(event[3], basestring):
                event_str = '\t'.join(
                    event[:3]) + '\t010\t' + '\t'.join(event[4:])
            else:
                event_str = '\t'.join(event)
            #print(event_str)
            if joined_issues:
                event_str += '\t{}'.format(joined_issues)
            else:
                event_str += '\t'

            if url:
                event_str += '\t{}\t{}\t{}'.format(ids, url, StorySource)
            else:
                event_str += '\t{}\t{}'.format(ids, StorySource)
                
            if PETRglobals.WriteActorText :
                if 'actortext' in filtered_events[event]:
                    event_str += '\t{}\t{}'.format(filtered_events[event]['actortext'][0],filtered_events[event]['actortext'][1])
                else:
                    event_str += '\t---\t---'
            if PETRglobals.WriteEventText :
                if 'eventtext' in filtered_events[event]:
                    event_str += '\t{}'.format(filtered_events[event]['eventtext'])
                else:
                    event_str += '\t---'
            if PETRglobals.WriteActorRoot :
                if 'actorroot' in filtered_events[event]:
                    event_str += '\t{}\t{}'.format(filtered_events[event]['actorroot'][0],filtered_events[event]['actorroot'][1])
                else:
                    event_str += '\t---\t---'
                
            story_output.append(event_str)

        story_events = '\n'.join(story_output)
        event_output.append(story_events)

    # Filter out blank lines
    event_output = [event for event in event_output if event]
    if output_file:
        f = codecs.open(output_file, encoding='utf-8', mode = 'w')
        for str in event_output:
#             field = str.split('\t')  # debugging
#            f.write(field[5] + '\n')
            f.write(str + '\n')
        f.close()


def pipe_output(event_dict):
    """
    Format the coded event data for use in the processing pipeline.

    Parameters
    ----------

    event_dict: Dictionary.
                The main event-holding dictionary within PETRARCH.


    Returns
    -------

    final_out: Dictionary.
                StoryIDs as the keys and a list of coded event tuples as the
                values, i.e., {StoryID: [(full_record), (full_record)]}. The
                ``full_record`` portion is structured as
                (story_date, source, target, code, joined_issues, ids,
                StorySource) with the ``joined_issues`` field being optional.
                The issues are joined in the format of ISSUE,COUNT;ISSUE,COUNT.
                The IDs are joined as ID;ID;ID.

    """
    final_out = {}
    for key in event_dict:
        story_dict = event_dict[key]
        if not story_dict['sents']:
            continue    # skip cases eliminated by story-level discard
        filtered_events = utilities.story_filter(story_dict, key)
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        else:
            StorySource = 'NULL'
        if 'url' in story_dict['meta']:
            url = story_dict['meta']['url']
        else:
            url = ''

        if filtered_events:
            story_output = []
            for event in filtered_events:
                story_date = event[0]
                source = event[1]
                target = event[2]
                code = event[3]

                ids = ';'.join(filtered_events[event]['ids'])

                if 'issues' in filtered_events[event]:
                    iss = filtered_events[event]['issues']
                    issues = ['{},{}'.format(k, v) for k, v in iss.items()]
                    joined_issues = ';'.join(issues)
                    event_str = (story_date, source, target, code,
                                 joined_issues, ids, url, StorySource)
                else:
                    event_str = (story_date, source, target, code, ids,
                                 url, StorySource)

                story_output.append(event_str)

            final_out[key] = story_output
        else:
            pass

    return final_out

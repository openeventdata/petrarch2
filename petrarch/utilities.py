import os
import corenlp
import utilities
import PETRglobals
import dateutil.parser


def stanford_parse(event_dict):
    #What is dead can never die...
    print "\nSetting up StanfordNLP. The program isn't dead. Promise."
    core = corenlp.StanfordCoreNLP(PETRglobals.stanfordnlp)
    for key in event_dict:
        for sent in event_dict[key]['sents']:
            print 'StanfordNLP parsing {}_{}...'.format(key, sent)
            sent_dict = event_dict[key]['sents'][sent]

            stanford_result = core.raw_parse(sent_dict['content'])
            s_parsetree = stanford_result['sentences'][0]['parsetree']
            if 'coref' in stanford_result:
                sent_dict['coref'] = stanford_result['coref']

            #TODO: To go backwards you'd do str.replace(' ) ', ')')
            sent_dict['parsed'] = utilities._format_parsed_str(s_parsetree)

    print 'Done with StanfordNLP parse...\n\n'

    return event_dict


def write_events(event_dict, output_file):
    """
    Check for duplicates in the article_list, then write the records in PETR
    format
    <14.02.28>: Duplicate checking currently not implemented
    <14.02.28>: Currently set to code only events with identified national
    actors
    """
    global StorySource
    global NEvents
    global StoryIssues

    #TODO: Make this a real thing
    StorySource = 'TEMP'

    event_output = []
    for key in event_dict:
        story_dict = event_dict[key]
        story_output = []
        story_date = story_dict['meta']['date']
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        for sent in story_dict['sents']:
            sent_dict = event_dict[key]['sents'][sent]
            if 'events' in sent_dict:
                event_list = sent_dict['events']
            else:
                print 'No events...'
                event_list = []

            sent_id = '{}_{}'.format(key, sent)
            if event_list:
                for event in event_list:
                    # do not print unresolved agents
                    if event[0][0] != '-' and event[1][0] != '-':
                        print 'Event:', story_date + '\t' + event[0] + '\t' + event[1] + '\t' + event[2] + '\t' + sent_id + '\t' + StorySource
                        event_str = '{}\t{}\t{}\t{}'.format(story_date,
                                                            event[0],
                                                            event[1],
                                                            event[2])
                        if 'issues' in sent_dict:
                            issues = sent_dict['issues']
                            joined_issues = '\t'.join(['{}\t{}'.format(iss[0],
                                                                    iss[1])
                                                    for iss in issues])
                            print 'Issues: {}'.format(joined_issues)

                            event_str += '\t{}'.format(joined_issues)

                        event_str += '\t{}\t{}'.format(sent_id, StorySource)
                        story_output.append(event_str)
        story_events = '\n'.join(story_output)
        event_output.append(story_events)

    #Filter out blank lines
    event_output = [event for event in event_output if event]
    final_event_str = '\n'.join(event_output)
    with open(output_file, 'w') as f:
        f.write(final_event_str)


def pipe_output(event_dict):
    final_out = {}
    for key in event_dict:
        story_dict = event_dict[key]
        story_output = []
        story_date = story_dict['meta']['date']
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        for sent in story_dict['sents']:
            sent_dict = event_dict[key]['sents'][sent]
            if 'events' in sent_dict:
                event_list = sent_dict['events']
            else:
                event_list = []

            sent_id = '{}_{}'.format(key, sent)
            if event_list:
                for event in event_list:
                    # do not print unresolved agents
                    if event[0][0] != '-' and event[1][0] != '-':
                        print 'Event:', story_date + '\t' + event[0] + '\t' + event[1] + '\t' + event[2] + '\t' + sent_id + '\t' + StorySource
                        if 'issues' in sent_dict:
                            issues = sent_dict['issues']
                            joined_issues = ';'.join(['{},{}'.format(iss[0],
                                                                     iss[1])
                                                      for iss in issues])

                            event_str = (story_date, event[0], event[1],
                                         event[2], joined_issues, sent_id,
                                         StorySource)
                        else:
                            event_str = (story_date, event[0], event[1],
                                         event[2], sent_id, StorySource)
                        story_output.append(event_str)
        if story_output:
            final_out[key] = story_output

    return final_out


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

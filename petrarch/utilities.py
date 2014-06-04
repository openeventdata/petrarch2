import corenlp
import PETRglobals


def stanford_parse(event_dict):
    core = corenlp.StanfordCoreNLP(PETRglobals.stanfordnlp)
    for key in event_dict:
        for sent in event_dict[key]['sents']:
            print 'StanfordNLP parsing {}_{}...'.format(key, sent)
            sent_dict = event_dict[key]['sents'][sent]

            stanford_result = core.raw_parse(sent_dict['text'])
            s_parsetree = stanford_result['sentences'][0]['parsetree']
            s_coref = stanford_result['coref']
            sent_dict['parsed'] = s_parsetree
            sent_dict['coref'] = s_coref

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

#TODO
#Shouldn't need this since only coded events are put into the dict
#    if len(StoryEventList) == 0:
#        return
#	print "we: Mk0", StoryEventList
    event_output = []
    for key in event_dict:
        story_dict = event_dict[key]
        story_output = []
        story_date = story_dict['meta']['date']
        for sent in story_dict['sents']:
            sent_dict = event_dict[key]['sents'][sent]
            if 'events' in sent_dict:
                event_list = sent_dict['events']
            else:
                print 'No events...'
                pass

            sent_id = '{}_{}'.format(key, sent)
            for event in event_list:
        #		print "we: Mk1", eventlist
#TODO
#Don't think I need this since I'm only including the coded events
#                if len(eventlist) == 1:  # signals new sentence id
#                    sent_id = eventlist[0]
                #else:  # write the event
                # do not print unresolved agents
                if event[0][0] != '-' and event[1][0] != '-':
                    print 'Event:', story_date + '\t' + event[0] + '\t' + event[1] + '\t' + event[2] + '\t' + sent_id + '\t' + StorySource
#TODO: Skip issues for now
#                    if PETRglobals.IssueFileName != "" and len(StoryIssues[sent_id[-2:]]) > 0:
#                        print '       Issues:', StoryIssues[sent_id[-2:]]
                    event_str = '{}\t{}\t{}\t{}'.format(story_date,
                                                        event[0],
                                                        event[1],
                                                        event[2])

#TODO: Skip issues for now
#                    if PETRglobals.IssueFileName != "":
#                        fevt.write('\t')
#                        ka = 0
#                        while ka < len(StoryIssues[sent_id[-2:]]):
#                            # output code and count
#                            fevt.write(
#                                StoryIssues[sent_id[-2:]][ka][0] + ' ' + str(StoryIssues[sent_id[-2:]][ka][1]))
#                            if ka < len(StoryIssues[sent_id[-2:]]) - 1:
#                                fevt.write(', ')
#                            ka += 1
                    event_str += '\t{}\t{}'.format(sent_id, 'TEMP')
                    story_output.append(event_str)
        story_events = '\n'.join(story_output)
        event_output.append(story_events)

    #Filter out blank lines
    event_output = [event for event in event_output if event]
    final_event_str = '\n'.join(event_output)
    with open(output_file, 'w') as f:
        f.write(final_event_str)

                    #fevt.write('\t' + sent_id + '\t' + StorySource + '\n')
#TODO: Keep track of number, type, etc. of things coded.
                    #NEvents += 1


def output_pipeline(event_dict):
    event_output = []
    for key in event_dict:
        story_dict = event_dict[key]
        for sent in story_dict['sents']:
            sent_dict = event_dict[key]['sents'][sent]
            if 'events' in sent_dict:
                event_list = sent_dict['events']
            else:
                print 'No events...'
                pass

            sent_id = '{}_{}'.format(key, sent)
            for event in event_list:
                # do not print unresolved agents
                if event[0][0] != '-' and event[1][0] != '-':
                    print 'Event:', story_dict['meta']['date'] + '\t' + event[0] + '\t' + event[1] + '\t' + event[2] + '\t' + sent_id + '\t' + StorySource
#TODO: Skip issues for now
#                    if PETRglobals.IssueFileName != "" and len(StoryIssues[sent_id[-2:]]) > 0:
#                        print '       Issues:', StoryIssues[sent_id[-2:]]
                    event_list = [(story_dict['meta']['date'], event[0],
                                   event[1], event[2], sent_id, 'SOURCE')]

#TODO: Skip issues for now. It will look like event_str += ['Issue', 'Issue']
#                    if PETRglobals.IssueFileName != "":
#                        fevt.write('\t')
#                        ka = 0
#                        while ka < len(StoryIssues[sent_id[-2:]]):
#                            # output code and count
#                            fevt.write(
#                                StoryIssues[sent_id[-2:]][ka][0] + ' ' + str(StoryIssues[sent_id[-2:]][ka][1]))
#                            if ka < len(StoryIssues[sent_id[-2:]]) - 1:
#                                fevt.write(', ')
#                            ka += 1
                    event_output.append(event_list)

    #Filter out blank lines
    event_output = [event for event in event_output if event]

    return event_output

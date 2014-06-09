import utilities


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

    event_output = []
    print 'hitting write_events...'
    for key in event_dict:
        story_dict = event_dict[key]
        story_output = []
        filtered_events = utilities.story_filter(story_dict, key)
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        else:
            StorySource = 'NULL'
        for event in filtered_events:
            story_date = event[0]
            source = event[1]
            target = event[2]
            code = event[3]

            ids = ';'.join(filtered_events[event]['ids'])

            if 'issues' in filtered_events[event]:
                iss = filtered_events[event]['issues']
                issues = ['{},{}'.format(k, v) for k, v in iss.iteritems()]
                joined_issues = ';'.join(issues)
            else:
                joined_issues = []

            print 'Event: {}\t{}\t{}\t{}\t{}\t{}'.format(story_date, source,
                                                         target, code, ids,
                                                         StorySource)
            event_str = '{}\t{}\t{}\t{}'.format(story_date,
                                                source,
                                                target,
                                                code)
            if joined_issues:
                event_str += '\t{}'.format(joined_issues)

            event_str += '\t{}\t{}'.format(ids, StorySource)
            story_output.append(event_str)

        story_events = '\n'.join(story_output)
        event_output.append(story_events)

    #Filter out blank lines
    event_output = [event for event in event_output if event]
    final_event_str = '\n'.join(event_output)
    with open(output_file, 'w') as f:
        f.write(final_event_str)


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
                values, i.e.,

    """
    final_out = {}
    for key in event_dict:
        story_dict = event_dict[key]
        filtered_events = utilities.story_filter(story_dict, key)
        if 'source' in story_dict['meta']:
            StorySource = story_dict['meta']['source']
        else:
            StorySource = 'NULL'

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
                    issues = ['{},{}'.format(k, v) for k, v in iss.iteritems()]
                    joined_issues = ';'.join(issues)
                    event_str = (story_date, source, target, code,
                                 joined_issues, ids, StorySource)
                else:
                    event_str = (story_date, source, target, code, ids,
                                 StorySource)

                story_output.append(event_str)

            final_out[key] = story_output
        else:
            pass

    return final_out

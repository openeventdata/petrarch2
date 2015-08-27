

from __future__ import print_function
from __future__ import unicode_literals


import PETRglobals
import PETRreader
import time
import utilities
import numpy as np


#   PETRtree.py
#   Author: Clayton Norris
#           Caerus Associates/ University of Chicago
#
#
#   Purpose:
#           Called from petrarch.py, this contains the main logic
#           of the Petrarch software. Sentences are stored into
#           Sentence class objects, which contain a tree of Phrase
#           class objects. The phrases then do analyses of their role
#           in the sentence and the event information of the overall sentence
#           is calculated and returned within the get_events() method
#
#
#   Revision history:
#       July 2015 - Created
#       August 2015 - First release



class Phrase:
    """
    This is a general class for all Phrase instances, which make up the nodes in the syntactic tree.
    The three subtypes are below.
    
    """
    
    def __init__(self, label, date):
        """
        Initialization for Phrase classes. 
        
        
        Parameters
        -----------
    
        label: list
                Label for the phrase type, date
        
        Returns
        -------
        An instantiated Phrase object

        """
        self.label = label if not label == "MD" else "VB"
        self.children = []
        self.phrasetype = label[0]
        self.annotation = ""
        self.text = ""
        self.parent = None
        self.meaning = ""
        self.verbclass = ""
        self.date = date
        self.index = -1
        self.head = None
        self.head_phrase = None
        self.color = False
    
    
    
    def get_meaning(self):
        """
        Method for returning the meaning of the subtree rooted by this phrase,
        is overwritten by all subclasses, so this works primarily for
        S and S-Bar phrases.
        
        
        
        Parameters
        -----------
        self: Phrase object that called the method
        
        
        Returns
        -------
        
        events: list
                Combined meanings of the phrases children
        """
        
        if self.label in "SBAR":
            lower = map(lambda b: b.get_meaning(), filter(lambda a: a.label in "SBARVP",self.children))
            events = []
            for item in lower:
                events += item
            if events:
                self.meaning = events
                return events
    
        return self.meaning



    def resolve_codes(self,codes):
        """
        Method that divides a list of mixed codes into actor and agent codes
        
        Parameters
        -----------
        codes: list
               Mixed list of codes
        
        Returns
        -------
        actorcodes: list
                    List of actor codes
                    
        agentcodes: list
                    List of actor codes
        
        """
        if not codes:
            return [],[]
        
        actorcodes = []
        agentcodes = []
        for code in codes:
            if code.startswith("~"):
                agentcodes.append(code)
            else:
                actorcodes.append(code)
        
        return actorcodes,agentcodes



    def mix_codes(self,agents,actors):
        """
        Combine the actor codes and agent codes addressing duplicates
        and removing the general "~PPL" if there's a better option.
        
        Parameters
        -----------
        agents, actors : Lists of their respective codes
        
        
        Returns
        -------
        codes: list
               [Agent codes] x [Actor codes]
        
        """
        codes = set()
        for act in (actors if actors else ['~']):
            for ag in (agents if agents else ['~']) :
                if ag == "~PPL" and len(agents) > 1:
                    continue
                code = act
                if not ag[1:] in act:
                    code += ag[1:]
                if not code in ['~','~~',""]:
                    codes.add(code)
        return list(codes)



    def return_head(self):
        return self.head,self.head_phrase



    def get_head(self):
        """
        Method for finding the head of a phrase. The head of a phrase is the rightmost
        word-level constituent such that the path from root to head consists only of similarly-labeled
        phrases.
        
        Parameters
        -----------
        self: Phrase object that called the method
        
        Returns
        -------
        possibilities[-1]: tuple (string,NounPhrase)
                (The text of the head of the phrase, the NounPhrase object whose rightmost child is the
                head).
                
        
        """
        self.get_head = self.return_head
        try:
            if self.label == 'S':
                self.head, self.head_phrase = map(lambda b: b.get_head(),filter(lambda a : a.label == 'VP', self.children))[0]
                return (self.head,self.head_phrase)
            elif self.label == 'ADVP':
                return self.children[0].text,self
            if (not self.label[1] == 'P'):
                return (self.text,self.parent)
        
            head_children = filter(lambda child : child.label.startswith(self.label[0]) and not child.label[1] == 'P', self.children)
            if head_children:
                possibilities = filter(None, map(lambda a: a.get_head(),head_children))
            else:
                other_children= filter(lambda child : child.label.startswith(self.label[0]), self.children)
                possibilities = filter(None, map(lambda a: a.get_head(),other_children))
            
            self.head_phrase = possibilities[-1][1]
            self.head = possibilities[-1][0]   # return the last, English usually compounds words to the front
            return possibilities[-1]
            
        except:
            return (None,None)


    def print_to_stdout(self,indent):
        print(indent, self.label,self.text,self.get_meaning(),self)
        for child in self.children:
            child.print_to_stdout(indent + "\t")



class NounPhrase(Phrase):
    """
    Class specific to noun phrases. 
    
    Methods: get_meaning()  -   specific version of the super's method
             check_date()   -   find the date-specific version of an actor
             
    """
    def __init__(self, label, date):
        Phrase.__init__(self, label, date)
    
    
    def return_meaning(self):
        return self.meaning

    def check_date(self, match):
        """
        Method for resolving date restrictions on actor codes. 
        
        Parameters
        -----------
        match: list
               Dates and codes from the dictionary
        
        Returns
        -------
        code: string
              The code corresponding to how the actor should be coded given the date
        """
        
        code = None
        try:
       
            for j in match:
                dates = j[1]
                date = []
                code = ""
                for d in dates:
                    if d[0] in '<>':
                        date.append(d[0]+str(PETRreader.dstr_to_ordate(d[1:])))
                    else:
                        date.append(str(PETRreader.dstr_to_ordate(d)))
                curdate= self.date
                if not date:
                    code = j[0]
                elif len(date) == 1:
                    if date[0][0] == '<':
                        if curdate < int(date[0][1:]):
                            code = j[0]
                    else:
                        if curdate >= int(date[0][1:]):
                            code = j[0]
                else:
                    if curdate < int(date[1]):
                        if curdate >= int(date[0]):
                            code = j[0]
            
                if code:
                    return code
        except Exception as e:
            print(e)
            return code
        

        return code



    def get_meaning(self):
        """
        Combine the meanings of the children of this node to find the actor code.
        Priority is given to word-level children, then to NP-level children,
        then Prepositional phrases, then Verb phrases.
        
        Word level children are matched against the Actor and Agent dictionaries.
        
        Parameters
        -----------
        self: NounPhrase object that called the method.
        
        Returns
        -------
        self.meaning: [string]
                      Actor coding of the subtree rooted by this noun phrase, also set as attribute
        
        """
        
        self.get_meaning = self.return_meaning
        dict_entry = ("",-1)
        dicts = (PETRglobals.ActorDict, PETRglobals.AgentDict)
        match_in_progress = {}
        codes = []
        NPcodes = []
        PPcodes = []
        VPcodes = []
        i = 0
        option = -1
        pathleft = [({},i,-1)]
        
        APMprint = True
        while i < len(self.children):
            child = self.children[i]
            if match_in_progress != {} :
                if child.text in match_in_progress and not option == 2:
                    pathleft.append((match_in_progress,i,2))
                    match_in_progress = match_in_progress[child.text]
                elif "#" in match_in_progress:
                    match = match_in_progress['#']
                    if isinstance(match,type([])): # We've matched from the actor dictionary
                        code = self.check_date(match)
                        if not code is None:
                            codes.append(code)
                    else:                           # We've matchd from the agent dictionary
                        codes.append(match_in_progress['#'])
                    match_in_progress = {}
                    option = -1
                    continue
                else:
                    p = pathleft.pop()
                    if option == 1:
                        i = p[1] + 1
                    else:
                        i = p[1]
                    match_in_progress = p[0]
                    option = p[2]
                    continue
                
            else:
                if child.label[:2] in ["NN","JJ","DT"] and not child.color:
                    text = child.text
                    if (not option >= 0) and text in PETRglobals.ActorDict:
                        dict_entry = (text,0)
                    elif text in PETRglobals.AgentDict and not option == 1:
                        dict_entry = (text,1)
                    try:
                        match_in_progress = dicts[dict_entry[1]][dict_entry[0]]
                        pathleft.append(({},i,dict_entry[1]))
                        dict_entry = None
                    except:
                        if False:
                            print("No match")
                elif child.label == "NP" and not child.color:
                    m = child.get_meaning()
                    if not m == "":
                        NPcodes+= m
                elif child.label == "PP":
                    m = child.get_meaning()
                    if not m == None:
                        PPcodes += m
                elif child.label == "PRP":
                    # Find antecedent
                    not_found = True
                    level = self.parent
                    reflexive = child.text.endswith("SELF") or child.text.endswith("SELVES")
                    local = True
                    while not_found and level.parent:
                        if level.label.startswith("NP") and reflexive: #Intensive, ignore
                            break
                        if local and level.label in ["S","SBAR"]:
                            local = False
                            level=level.parent
                            continue
                        
                        if (not local) or (reflexive and local):
                            for child in level.parent.children:
                                if isinstance(child,NounPhrase) and not child.get_meaning() == "~" :  # Do we just want to pick the first?
                                    not_found = False
                                    codes += child.get_meaning()
                                    break

                        level = level.parent
                elif child.label == "VP":
                    meaning = child.get_meaning()
                    if meaning and isinstance(meaning[0][1],basestring):
                        VPcodes += child.get_theme()
        
                elif child.label == "EX":
                    m =  self.convert_existential().get_meaning()
                    self.meaning = m
                    return m
            i += 1
            option = -1
            if(i >= len(self.children) and not match_in_progress == {}):
                if "#" in match_in_progress:
                    match = match_in_progress['#']
                    if isinstance(match,list):
                        code = self.check_date(match)
                        if not code is None:
                            codes.append(code)
                    else:
                        codes.append(match)
                
                else:
                    
                
                    p = pathleft.pop()
                    match_in_progress = p[0]
                    option = p[2]
                    if option == 1:
                        i = p[1] + 1
                    else:
                        i= p[1]
                    
            
        
        actorcodes,agentcodes = self.resolve_codes(codes)
        NPactor, NPagent = self.resolve_codes(NPcodes)
        PPactor, PPagent = self.resolve_codes(PPcodes)
        VPactor, VPagent = self.resolve_codes(VPcodes)
        if not actorcodes:
            actorcodes += NPactor
            if not actorcodes:
                actorcodes += PPactor
                if not actorcodes:
                    actorcodes += VPactor                # Do we want to pull meanings from verb phrases? Could be risky
        
        if not agentcodes:
            agentcodes += NPagent
            if not agentcodes:
                agentcodes += PPagent
                if not agentcodes:
                    agentcodes += VPagent
                    
        
        self.meaning = self.mix_codes(agentcodes,actorcodes)

        return self.meaning




    def convert_existential(self):
        # Reshuffle the tree to get existential "There are" phrases into a more basic form
        parent = self.parent
        sister = parent.children[1]
        neice = sister.children[1]
        subject = neice.children[0]
        predicate = neice.children[1]
    
    
        parent.children[0] = subject
        subject.parent = parent
       
        sister.children[1] = predicate
        predicate.parent = sister
    
        self.parent = None


        #parent.print_to_stdout("")
        return subject


class PrepPhrase(Phrase):

    def __init__(self, label, date):
        Phrase.__init__(self, label, date)
        self.meaning = ""
        self.prep = ""
        self.head = ""

    def get_meaning(self):
        """
        Return the meaning of the non-preposition constituent, and store the
        preposition.
        """
        self.prep = self.children[0].text
        if len(self.children) > 1 and not self.children[1].color:
            
            self.meaning = self.children[1].get_meaning() if isinstance(self.children[1],NounPhrase) else ""
            self.head = self.children[1].get_head()[0]
            
        return self.meaning

    def get_prep(self):
        
        return self.children[0].text


class VerbPhrase(Phrase):
    """
    Subclass specific to Verb Phrases
    
    Methods
    -------
    __init__: Initialization and Instatiation
    
    is_valid: Corrects a known stanford error regarding miscoded noun phrases
    
    get_theme: Returns the coded target of the VP
    
    get_meaning: Returns event coding described by the verb phrase
    
    get_lower: Finds meanings of children
    
    get_upper: Finds grammatical subject
    
    get_code: Finds base verb code and calls match_pattern
    
    match_pattern: Matches the tree to a pattern in the Verb Dictionary
    
    get_S: Finds the closest S-level phrase above the verb
    
    match_transform: Matches an event code against transformation patterns in the dictionary
    
    """

    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
        self.meaning = ""    # "meaning" for the verb, i.e. the events coded by the vp
        self.upper = ""      # contains the meaning of the noun phrase in the specifier position for the vp or its parents
        self.lower = ""      # contains the meaning of the subtree c-commanded by the verb
        self.passive = False
        self.code = 0
        self.valid = self.is_valid()
        self.S  = None
    
    def is_valid(self):
        """
        This method is largely to overcome frequently made Stanford errors, where phrases like "exiled dissidents" were
        marked as verb phrases, and treating them as such would yield weird parses.
        
        Once such a phrase is identified because of its weird distribution, it is converted to 
        a NounPhrase object
        
        """
        try:
            if self.children[0].label == "VBN":
                helping = ["HAVE","HAD","HAVING","HAS"]
                if ((not (self.parent.get_head()[0] in helping or self.parent.children[0].text in helping)) and
                         len(filter(lambda a: isinstance(a,VerbPhrase),self.parent.children)) <= 1  and
                         not self.check_passive()):
                    
                    self.valid = False
                    
                    np_replacement = NounPhrase("NP",self.date)
                    np_replacement.children = self.children
                    np_replacement.parent = self.parent
                    np_replacement.index = self.index
                    
                    self.parent.children.remove(self)
                    self.parent.children.insert(self.index,np_replacement)
                    del(self)
                    self = np_replacement
                    return False
            self.valid = True
        except IndexError as e:
            self.valid = True
        return True
    
    def get_theme(self):
        """
        This is used by the NounPhrase.get_meaning() method to determine relevant
        information in the VerbPhrase.
        """
        m = self.get_meaning()
        if m[0][1] == 'passive':
            return m[0][0]
        return [m[0][1]]
    
    def return_meaning(self):
        return self.meaning
    
    def get_meaning(self):
        """
        This determines the event coding of the subtree rooted in this verb phrase.
        
        Four methods are key in this process: get_upper(), get_lower(), get_code() 
        and match_transform().
        
        First, get_meaning() gets the verb code from get_code()
        
        Then, it checks passivity. If the verb is passive, then it looks within 
        verb phrases headed by [by, from, in] for the source, and for an explicit target
        in verb phrases headed by [at,against,into,towards]. If no target is found,
        this space is filled with 'passive', a flag used later to assign a target
        if it is in the grammatical subject position. 
        
        If the verb is not passive, then the process goes:
        
        1) call get_upper() and get_lower() to check for a grammatical subject 
        and find the coding of the subtree and children, respectively.
        
        2) If get_lower returned a list of events, combine those events with
        the upper and code, add to event list.
        
        3) Otherwise, combine upper, lower, and code  and add to event list
        
        4) Check to see if there are S-level children, if so, combine with
        upper and code, add to list. 
        
        5) call match_transform() on all events in the list
        
        
        Parameters
        ----------
        self: VerbPhrase object that called the method
       
        Returns
        -------
        events: list
                List of events coded by the subtree rooted in this phrase.
        
        """
        time1 = time.time()
        self.get_meaning = self.return_meaning
        
        c, passive = self.get_code()
        s_options = filter(lambda a: a.label in "SBAR",self.children)

        def resolve_events(event):
            """
            Helper method to combine events, accounting for 
            missing sources, and  targets, passives, multiple-
            target passives, and codeless verbs.
            
            Parameters
            ----------
            event: tuple
                   (source, target, code) of lower event
            
            Returns
            -------
            returns: [tuple]
                     list of resolved event tuples
            """
            first,second,third = [up,"",""]
            if not isinstance(event,tuple):
                second = event
                third = c
            if not (up or c) :
                return [event]
            elif event[1] == 'passive':
                first = event[0]
                third = utilities.combine_code(c,event[2])
                if up:
                    returns = []
                    for source in up:
                        returns += [(first,source,third)]
                    return returns
                second = 'passive'
            elif not event[0] in ['',[],[""],["~"],["~~"]]:
                second = event
                third = c
            else:
                second = event[1]
                third = utilities.combine_code(c,event[2])
            return [(first,second,third)]

        events = []
        if self.check_passive() or passive:
            # Check for source in preps
            source_options = []
            target_options = self.get_upper()
            for child in self.children:
                if isinstance(child,PrepPhrase):
                    if child.get_prep() in ["BY","FROM","IN"]:
                        source_options += child.get_meaning()
                    elif child.get_prep() in ["AT","AGAINST","INTO","TOWARDS"]:
                        target_options += child.get_meaning()
            if not target_options:
                target_options = ["passive"]
            if source_options or c:
                events = map(lambda a: (source_options, a, c if self.check_passive() else passive), target_options)
                if self.check_passive():
                    self.meaning = events
                    return events
    
        up = self.get_upper()
        up = "" if up in ['',[],[""],["~"],["~~"]] else up
        low,neg = self.get_lower()
        if not low:
            low = ""
        if neg:
            c = 0
        
        if isinstance(low,list):
            for event in low:
                events += resolve_events(event)
        elif not s_options:
            if up or c:
                events.append((up,low,c))
            elif low:
                events.append(low)

        lower = map(lambda a: a.get_meaning(),s_options)
        sents = []

        for item in lower:
            sents += item
        
        if sents:
            for event in sents:
                if event[1] or event[2]:
                    ev = resolve_events(event)[0]
                    if isinstance(ev[1],list):
                        for item in ev[1]:
                            events.append((ev[0],item,ev[2]))
                    else:
                        events += resolve_events(event)
        maps = map(self.match_transform, events)
        events = reduce(lambda a,b: a + b, maps,[])
        self.meaning = events
        try:
            return list(set(events))
        except:
            return events
    

    def return_upper(self):
        return self.upper
    
    def return_passive(self):
        return self.passive
    
    def check_passive(self):
        """
        Check if the verb is passive under these conditions:
            1) Verb is -ed form, which is notated by stanford as VBD or VBN
            2) Verb has a form of "be" as its next highest verb 
            
        Parameters
        ----------
        self: VerbPhrase object calling the method
        
        Returns
        -------
        self.passive: boolean
                      Whether or not it is passive
        """
        self.check_passive = self.return_passive
        if True:
            if self.children[0].label in ["VBD","VBN"]:
                level= self.parent
                if level.label == "NP":
                    self.passive = True
                    return True
                for i in range(2):
                    if level and isinstance(level,VerbPhrase):
                        if level.children[0].text in ["AM","IS","ARE","WAS","WERE","BE","BEEN","BEING"]:
                            self.passive = True
                            return True
                    level = level.parent
                    if not level:
                        break
    
        else:
            print("Error in passive check")
        self.passive = False
        return False


    def return_S(self):
        return self.S

    def get_S(self):
        """
        Navigate up the tree following a VP path to find the closest s-level phrase. 
        There is the extra condition that if the S-level phrase is a "TO"-phrase 
        without a second subject specified, just so that "A wants to help B" will
        navigate all the way up to "A wants" rather than stopping at "to"
        
        Parameters
        -----------
        self: VerbPhrase object that called the method
        
        Returns
        -------
        level: VerbPhrase object
               Lowest non-TO S-level phrase object above the verb
        """
        self.get_S = self.return_S
        not_found = True
        level = self
        while not_found and not level.parent is None:
            if isinstance(level.parent, VerbPhrase):
                level = level.parent
            elif level.parent.label == "S":
                if level.children[0].label == "TO" and level.index == 0:
                    level = level.parent
                    continue
                self.S = level.parent
                return level.parent
            else:
                return level
        return None
    


    def get_upper(self):
        """
        Finds the meaning of the specifier (NP sibling) of the VP. 
        
        Parameters
        -----------
        self: VerbPhrase object that called the method
        
        Returns
        -------
        self.upper: List 
                    Actor codes of spec-VP
        """
        self.get_upper = self.return_upper
        
        for child in self.parent.children:
            if isinstance(child, NounPhrase) and not child.get_meaning() == ["~"]:
                self.upper = child.get_meaning()
                return self.upper
        return []



    def return_lower(self):
        return self.lower

    def get_lower(self):
        """
        Find the meaning of the children of the VP, and whether or not there is a "not" in the VP.
        
        If the VP has VP children, look only at these.
        
        Otherwise, this function pretty much is identical to the NounPhrase.get_meaning() 
        method, except that it doesn't look at word-level children, because it shouldn't
        have any. 
        
        Parameters
        -----------
        self: VerbPhrase object that called the method
        
        Returns
        -------
        self.lower: list
                    Actor codes or Event codes, depending on situation
        
        negated: boolean
                 Whether a "not" is present
        
        """
    
        self.get_lower = self.return_lower
        
        lower = []
        v_options = filter(lambda a: (isinstance(a,VerbPhrase) and a.is_valid()),self.children)
        
        lower = map(lambda a: a.get_meaning(),v_options)

        events  = []
        
        negated = (lower and self.children[1].text) == "NOT"
        for item in lower:
            
            if negated:
                adjusted = []
                for event in item:
                    if isinstance(event,tuple):
                        adjusted.append((event[0],event[1],event[2] - 0xFFFF))
                    else:
                        adjusted.append(event)
                item = adjusted
            events += item
        
        if events:
            self.lower = events
            return events,negated
        
        NPcodes = []
        PPcodes = []
        VPcodes = []
        
        for child in self.children:
            if isinstance(child, NounPhrase):
                NPcodes += child.get_meaning()
            elif isinstance(child, PrepPhrase):
                PPcodes += (child.get_meaning())
            elif False and child.label in "SBAR":
                for ch in (child.children[-1].children if child.label == "SBAR" else child.children):
                    if isinstance(ch, NounPhrase):
                        Scodes += ch.get_meaning()
                    elif isinstance(ch, PrepPhrase):
                        Scodes += ch.get_meaning()
                    elif isinstance(ch, VerbPhrase):
                        Scodes += ch.get_meaning()[1]
        
        actorcodes,agentcodes = ([],[])
        NPactor, NPagent = self.resolve_codes(NPcodes)
        PPactor, PPagent = self.resolve_codes(PPcodes)
        VPactor, VPagent = self.resolve_codes(VPcodes)
        
        actorcodes += NPactor
        if not actorcodes:
            actorcodes += PPactor
            if not actorcodes:
                actorcodes += VPactor
    
        agentcodes += NPagent
        if not agentcodes:
            agentcodes += PPagent
            if not agentcodes:
                agentcodes += VPagent
        
        self.lower = self.mix_codes(agentcodes,actorcodes)
        return self.lower,negated

    def return_code(self):
        return self.code
    
    def get_code(self):
        """
        Match the codes from the Verb Dictionary.
        
        Step 1.  Check for compound verb matches
        
        Step 2.  Check for pattern matches via match_pattern() method
        
        
        Parameters
        -----------
        self: VerbPhrase object that called the method
        
        Returns
        -------
        code:   int
                Code described by this verb, best read in hex
        """
        
        self.get_code = self.return_code
        dict = PETRglobals.VerbDict['verbs']
        if 'AND' in map(lambda a: a.text, self.children):
            return 0,0
        patterns = PETRglobals.VerbDict['phrases']
        verb = "TO" if self.children[0].label == "TO" else self.get_head()[0]
        
        meaning = ""
        path = dict
        passive = False
        if verb in dict:
            code = 0
            path = dict[verb]
            if ['#'] == path.keys():
                path = path['#']
                if True or path.keys() == ['#']:
                    try:
                        code = path['#']['code']
                        meaning = path['#']['meaning']
                    
                        self.verbclass = meaning if not meaning == "" else verb
                        if not code == '':
                            active, passive  = utilities.convert_code(code)
                            self.code = active
                    except:
                        self.code = (0,0)
            else:
                # Post - compounds
                for child in self.children:
                    if child.label in ["PRT","ADVP"]:
                        if child.children[0].text in path:
                            path = path[child.children[0].text]
                if "#" in path:
                    try:
                        code = path['#']['#']['code']
                        meaning = path['#']['#']['meaning']
                        self.verbclass = meaning if not meaning == "" else verb
                        if not code == '':
                            active, passive  = utilities.convert_code(code)
                            self.code = active
                    except:
                        pass
        
        match = self.match_pattern()
        if match:
            print("\t\t",match)
            active, passive  = utilities.convert_code(match['code'])
            self.code = active
        if passive and not active:
            self.check_passive = lambda : True
            self.code = passive
        return self.code, passive



    def match_transform(self,e):
        """
        Check to see if the event e follows one of the verb transformation patterns
        specified at the bottom of the Verb Dictionary file.
        
        If the transformation is present, adjust the event accordingly. 
        If no transformation is present, check if the event is of the form:
        
                    a ( b . Q ) P , where Q is not a top-level verb. 
           
            and then convert this to ( a b P+Q )
        
        Otherwise, return the event as-is.
        
        Parameters
        -----------
        e: tuple
           Event to be transformed
        
        Returns
        -------
        t: list of tuples
           List of modified events, since multiple events can come from one single event
        """
    
    
        def recurse(pdict,event,a2v = {}, v2a = {}):
            path = pdict
            if isinstance(pdict,list):
                verb = utilities.convert_code(path[2])[0] if not path[2] == "Q" else v2a["Q"]
                if isinstance(v2a[path[1]],tuple):
                    results = []
                    for item in v2a[path[1]]:
                        results.append((list(v2a[path[0]]),item,verb))
                    return results
                return [(list(v2a[path[0]]),v2a[path[1]],verb)]
            if isinstance(event,tuple):
                actor = None if not event[0] else tuple(event[0])
                masks = filter(lambda a :a in pdict, [event[2],event[2] - event[2] % 0x10,
                        event[2] - event[2] % 0x100,event[2] - event[2] % 0x1000])
                if masks:
                    path = pdict[masks[0]]
                elif -1 in pdict:
                    v2a["Q"] = event[2]
                    path = pdict[-1]
                else:
                    return False
            else:
                actor = event
            if actor in a2v:
                actor = a2v[actor]
            if not actor:
                actor = "_"
            if actor in path:
                return recurse(path[actor],event[1],a2v,v2a)
            elif not actor == '_':
                for var in sorted(path.keys())[::-1]:
                    if var in v2a:
                        continue
                    if not var == '.':
                        v2a[var] = actor
                        a2v[actor] = var
                    return recurse(path[var],event[1],a2v,v2a)
            return False
        
        
        try:
            t = recurse(PETRglobals.VerbDict['transformations'],e)
            if t:
                return t
            else:
                
                if e[0] and e[2] and isinstance(e[1],tuple) and  e[1][0] and not e[1][2] / (16 ** 3):
                    if isinstance(e[1][0],list):
                        results = []
                        for item in e[1][0]:
                    
                            results.append((e[0],item,utilities.combine_code(e[1][2],e[2])))
                        return results
                    return [(e[0],e[1][0],utilities.combine_code(e[2],e[1][2]))]


        except Exception as ex:
            pass #print(ex)
        return [e]
    

    def match_pattern(self):
        """ 
        Match the tree against patterns specified in the dictionary. For a more illustrated explanation
        of how this process works, see the Petrarch2.pdf file in the documentation. 
        
        
        Parameters
        -----------
        self: VerbPhrase object that called the method
        
        Returns
        -------
        False if no match, dict of match if present.
        
        """
        meaning = self.verbclass
        code = self.code

        def match_phrase(path,phrase):
            # Having matched the head of the phrase, this matches the full noun phrase, if specified
            for item in filter(lambda b: b.text in path,phrase.children):
            
                subpath = path[item.text]
                match = reroute(subpath,lambda a: match_phrase(a,item.head_phrase))
                if match:
                    item.color = True
                    return match
        
            
            return reroute(path,lambda a: match_phrase(a,phrase.head_phrase))
        
        def match_noun(path,phrase = self if not self.check_passive() else self.get_S(),preplimit = 0):
            # Matches a noun or head of noun phrase
            noun_phrases = []
            if preplimit:
                for sib in phrase.children:
                    if isinstance(sib,PrepPhrase) and sib.get_prep() in ["BY","FROM"]:
                        noun_phrases.append(sib.children[1])
            else:
                for child in phrase.children:
                    if child.label in ("NP","ADVP"):
                        noun_phrases.append(child)
                if isinstance(phrase,NounPhrase):
                    noun_phrases.append(phrase)
        
            for item in noun_phrases:
                head,headphrase  = item.get_head()
                
                if head and head in path:
                    subpath = path[head]
                    
                    # First check within the NP for PP's
                    skip = lambda a: False
                    match = reroute(subpath, skip , skip , lambda a: match_prep(a,item), skip )
                    if match:
                        headphrase.children[-1].color = True
                        return match

                    # Then check the other siblings
                    match = reroute(subpath,(lambda a : match_phrase(a,item.head_phrase))
                            if isinstance(item,NounPhrase) else None )
                    if match:
                        headphrase.children[-1].color = True
                        return match
            if '^' in path:
                phrase.color = True
                return reroute(path['^'], lambda a: match_phrase(a,phrase.head_phrase))
            return reroute(path,lambda a: match_phrase(a,phrase.head_phrase))

        def match_prep(path,phrase=self):
            # Matches preposition
            for item in filter(lambda b: isinstance(b,PrepPhrase),phrase.children):
                prep = item.children[0].text
                if prep in path:
                    subpath = path[prep]
                    match = reroute(subpath,lambda a : match_noun(a,item.children[1]), match_prep)
                    if match:
                        return match
            return reroute(path, o2 = match_prep)

        def reroute(subpath, o1 = match_noun, o2 = match_noun, o3 = match_prep, o4 = match_noun):
            
                if '-' in subpath:
                    match = o1(subpath['-'])
                    if match:
                        return match
                        
                if ',' in subpath:
                    match = o2(subpath[','])
                    if match:
                        return match
    
                if '|' in subpath:
                    match = o3(subpath['|'])
                    if match:
                        return match
                
                if '*' in subpath:
                    match = o4(subpath['*'])
                    if match:
                        return match
                
                if '#' in subpath:
                    return subpath['#']
                return False
        
        # Match pattern
        if meaning in PETRglobals.VerbDict['phrases']:
            path = PETRglobals.VerbDict['phrases'][meaning]
            if self.check_passive():
                return match_noun(path,self,1)
            else:
                return match_noun(path,self.get_S())
        return False



class Sentence:
    """
    Holds the information of a sentence and its tree.
    
    Methods
    -------
    
    __init__ : Initialization and instantiation
    
    str_to_tree: Reads CoreNLP parse into memory
    
    get_events: Extracts events from sentence tree
    
    print_tree: Prints tree to a LaTeX file
    """
    def __init__(self, parse, text, date):
        self.treestr = parse.replace(')', ' )')
        self.parse = parse
        self.agent = ""
        self.ID = -1
        self.actor = ""
        self.date = date
        self.longlat = (-1,-1)
        self.verbs = []
        self.tree = self.str_to_tree(parse.strip())
        self.txt = text
        self.verb_analysis = {}
        self.events = []
    
    def str_to_tree(self,str):
        """
        Take the Stanford CoreNLP parse and convert it to an object/pointer tree.
        
        Parameters
        -----------
        str: string 
             Pre-processed CoreNLP parse, needs to be formated by utilities.format_parsed_str
             before being passed.
        
        Returns
        -------
        root: Phrase object
              Top level of the tree that represents the sentence
        """
        segs = str.split()
        root = Phrase(segs[0][1:],self.date)
        level_stack = [root]
        existentials = []
        
        for element in segs[1:]:
            if element.startswith("("):
                lab = element[1:]
                if lab == "NP":
                    new = NounPhrase(lab, self.date)
                elif lab == "VP":
                    new = VerbPhrase(lab,self.date)
                    self.verbs.append(new)
                elif lab == "PP":
                    new = PrepPhrase(lab, self.date)
                else:
                    new = Phrase(lab, self.date)
                    if lab == "EX":
                        existentials.append(new)
                new.parent = level_stack[-1]
                new.index = len(level_stack[-1].children)
                level_stack[-1].children.append(new)
                level_stack.append(new)
            elif element.endswith(")"):
                try:
                    level_stack.pop()
                except:
                    break
            else:
                level_stack[-1].text = element
    
        for element in existentials:
            element.parent.convert_existential()
        return root



    def get_events(self,require_dyad = 1):
        """
        Take the coding of the highest verb phrase and return that, given:
                1) Target and source are both present
                2) Code is non-zero
                3) Target isn't another event
                
        Parameters
        -----------
        self: Sentence object calling the method
        
        Returns
        -------
        valid: list
               List of coded events that satisfy the above conditions, of form
               (source, target, code) where the code has been converted from an int
               back into CAMEO
        
        """
        events = map(lambda a : a.get_meaning(), filter(lambda b: b.label in "SVP" , self.tree.children))
        valid = []
        for sent in events:
            for event in sent:
                if isinstance(event,tuple) and isinstance(event[1],basestring) :
                    code = utilities.convert_code(event[2],0)
                    if event[0] and event[1] and code :
                        for source in event[0]:
                            valid.append([source,event[1],code])
                    elif (not require_dyad) and event[0] and code and not event[1]:
                        for source in event[0]:
                            print("##############",source,code)
                            valid.append([source,"---",code])
                    elif (not require_dyad) and event[1] and code and not event[0]:
                        print("%%%%%%%%%%%%%%%%%%",event[1],code)
                        valid.append(["---",event[1],code])
                    
                    
                    # If there are multiple actors in a cooperation scenario, code their cooperation as well
                    if len(event[0]) > 1 and (not event[1]) and code and code[:2] in ["03","04","05","06"]:
                        for source in event[0]:
                            for target in event[0]:
                                if not source == target:
                                    valid.append([source,target,code])
    
        return valid


    def print_to_file(self,root,file = ""):
        """
        Prints a LaTeX representation of the tree to a file, calls the recursive method
        print_tree() on the tree to print all of it
        """
        print("""   
                    \\resizebox{\\textwidth}{250}{%
                    \\begin{tikzpicture}
                    \\Tree""", file=file, end=" ")

        self.print_tree(root, "", file)
        print("\\end{tikzpicture}}\n\n", file=file)
        print("EVENTS: ",self.get_events(), file = file)
        print("\\\\\nTEXT: ", self.txt, file=file)
        print("\\newpage",file=file)
    
    
    def print_tree(self, root, indent="", f=""):
        """
        This prints a LaTeX formatted document of the tree. Calls on each of the children as well.
        """
        print("[."+root.label.replace("$",""),("{\\bf "+root.text+"}" if not root.text == "" else "") ,file = f,end = " ")
        if root.label in ["NP"]:
            m = root.get_meaning()
            k = ""
            for i in m:
                k += "+" + i
            print("[.{" + k + "}", file=f, end=" ")
        elif root.label in ["VP"]:
            m = root.get_meaning()
            print("[.{\it "+utilities.code_to_string(m)+"}",file = f,end = " ")
        
        for child in  root.children:
                self.print_tree(child,indent+"\t",f)
        if root.label in ["NP","VP"]:
            print(" ] ]",file = f,end=" \n")
        else:
            print(" ]", file=f, end=" ")

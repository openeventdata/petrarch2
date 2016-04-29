

from __future__ import print_function
from __future__ import unicode_literals


import PETRglobals
import PETRreader
import time
import utilities
import types

# -- from inspect import getouterframes, currentframe  # -- # used to track the levels of recursion



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
#       April 2016 - Bugs causing crashes in very low frequency cases corrected 

# pas 16.04.22: print() statements commented-out with '# --' were used in the debugging and can probably be removed

class Phrase:
    """
    This is a general class for all Phrase instances, which make up the nodes in the syntactic tree.
    The three subtypes are below.
    
    """
    
    def __init__(self, label, date,sentence):
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
        self.sentence = sentence
    
    
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

    def get_text(self):
        if self.color:
            return ""
        text = self.text
        for child in self.children:
            if isinstance(child,NounPhrase):
                text += " " + child.get_text()[0]
            else:
                text += " " + child.get_text()
        
        return text
    
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
# --        print('Prc-entry',len(getouterframes(currentframe(1))),codes) # --
        if not codes:
            return [],[]
        
        actorcodes = []
        agentcodes = []
        for code in codes:
            if not code:
                continue
            """if isinstance(code,tuple):
                actorcodes.append(code)
            else:
                agentcodes.append(code)"""
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
        
        
# --        print('mc-entry',actors,agents)
        codes = set()
        mix = lambda a, b : a + b if not b in a else a
        actors = actors if actors else ['~']
        for ag in agents:
            if ag == '~PPL' and len(agents) > 1:
                continue
#            actors = map( lambda a : mix( a[0], ag[1:]), actors)
            actors = map( lambda a : mix( a, ag[1:]), actors)
        
# --        print('mc-1',actors)
        return filter(lambda a : a not in ['','~','~~',None],actors)
        
        
        
        # 16.04.25 hmmm, this is either a construct of utterly phenomenal subtlety or else we never hit this code...
        codes = set()
        print('WTF-1')
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
        print(indent, self.label,self.text,self.get_meaning())
        for child in self.children:
            child.print_to_stdout(indent + "\t")



class NounPhrase(Phrase):
    """
    Class specific to noun phrases. 
    
    Methods: get_meaning()  -   specific version of the super's method
             check_date()   -   find the date-specific version of an actor
             
    """
    def __init__(self, label, date, sentence):
        Phrase.__init__(self, label, date, sentence )
    
    
    def return_meaning(self):
        return self.meaning


    def get_text(self):
        """
        Noun-specific get text method
        """
        PPcodes = []
        text = ""
        for child in self.children:
            if isinstance(child,PrepPhrase):
                m = self.resolve_codes(child.get_meaning())
                if m[0]:
                    PPcodes += child.get_meaning()
                else:
                    text += " " + child.get_text()
            if isinstance(child,NounPhrase):
                value = child.get_text()
                text += value[0]
                PPcodes += value[1]
            if child.label[:2] in ["JJ","NN","DT"]:
                text += " "+child.text
        return text,PPcodes

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
            #print(e)
            return code        

        return code


    def get_meaning(self):

        def recurse(path, words, length,so_far= ""):
            
# --            print('NPgm-rec-lev:',len(getouterframes(currentframe(1))))  # --
            
            if words and words[0] in path:
                match = recurse(path[words[0]],words[1:],length + 1 , so_far + " " + words[0])
                if match:
                    return match
            if '#' in path:
                if isinstance(path["#"],list):
                    code = self.check_date(path['#'])
                    if not code is None:
                        """print('NPgm-rec-1:',code)  # --
                        print('NPgm-rec-1.1:',path['#'][-1])"""
                        return [code] , so_far, length, [path['#'][-1]]   # 16.04.25 this branch always resolves to an actor; path['#'][-1] is the root string
                else:
# --                    print('NPgm-rec-2:',path['#'])
                    return [path['#']], so_far, length   # 16.04.25 this branch always resolves to an agent
            return False

        text_children = []
        PPcodes = []
        VPcodes = []
        NPcodes = []
        codes = []
        roots = []
 # --         print('NPgm-0:',self.get_text())  # --
      
        matched_txt = []
        
        for child in self.children:
            if isinstance(child,NounPhrase):
                value = child.get_text()
                text_children += value[0].split()
                NPcodes += value[1]
            elif child.label[:2] in ["JJ","DT","NN"]:
                text_children += child.get_text().split()
            
            elif child.label == "PP":
                m = self.resolve_codes(child.get_meaning())
# --                  print('gm-1:',m)  # --
                if m[0]:
                    PPcodes += child.get_meaning()
                else:
                    text_children += child.get_text().split()
    
            elif child.label == "VP":
                m = child.get_meaning()
                if m and isinstance(m[0][1],basestring):
                    m = self.resolve_codes(m[0][1])
                    if m[0]:
                        VPcodes += child.get_theme()
                    else:
                        pass
                        # We could add the subtree here, but there shouldn't be any codes with VP components
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
                            if isinstance(child,NounPhrase): 
                                if not child.get_meaning() == "~" :  # Do we just want to pick the first?
                                    not_found = False
                                    codes += child.get_meaning()
                                    break

                    level = level.parent
                    
                
        # check whether there are codes in the noun Phrase
        index = 0
        while index < len(text_children):
            match = recurse(PETRglobals.ActorDict,text_children[index:],0)  # checking for actors
            if match:
# --                print('NPgm-m-1:',match)
                codes += match[0]
                roots += match[3]
                index += match[2]
                matched_txt += [match[1]]
# --                print('NPgm-1:',matched_txt)
                continue

            match = recurse(PETRglobals.AgentDict,text_children[index:],0)  # checking for agents
            if match:
# --                print('NPgm-2.0:',roots)
                codes += match[0]
                roots += [['~']]
                index += match[2]
                matched_txt += [match[1]]
                """print('NPgm-2:',matched_txt) # --
                print('NPgm-2.1:',roots)"""
                continue
            index += 1
                        
        """print('NPgm-m-lev:',len(getouterframes(currentframe(1))))   # --            
        print('NPgm-m-codes:',codes)
        print('NPgm-m-roots:',roots)"""
        # combine the actor/agent codes
        actorcodes,agentcodes = self.resolve_codes(codes)
        PPactor, PPagent = self.resolve_codes(PPcodes)
        NPactor, NPagent = self.resolve_codes(NPcodes)
        VPactor, VPagent = self.resolve_codes(VPcodes)
        if not actorcodes:
            actorcodes += NPactor  # don't really need += here, right? pas 16.04.26
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

        """if len(actorcodes) > 0:
            print('NPgm-m-actorcodes:',actorcodes)
            print('NPgm-m-roots     :',roots)"""
        
        self.meaning = self.mix_codes(agentcodes,actorcodes)
        self.get_meaning = self.return_meaning
        """print('NPgm-3:',self.meaning)
        print('NPgm-4:',matched_txt)"""
        if matched_txt:
            self.sentence.metadata['nouns'] += [(matched_txt,self.meaning, roots[:len(matched_txt)])] 
#        self.sentence.print_nouns('NPgm-5:') # --
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

    def __init__(self, label, date, sentence):
        Phrase.__init__(self, label, date, sentence)
        self.meaning = ""
        self.prep = ""
        self.head = ""

    def get_meaning(self):
        """
        Return the meaning of the non-preposition constituent, and store the
        preposition.
        
        Note: pas 16.04.22
        Add this len() > 0 check to get around a very rare (about 0.001% of LN sentences) cases where a (PP (PRP structure
        caused an infinite recursion between NounPhrase.get_meaning() and PrepPhrase.get_meaning() in circumstances where
        self.children[1].get_text() gave an empty string. This solves the problem but I'm not completely confident this is 
        the right place to trap it: in the process of debugging I noticed that there were cases where this recursion 
        seemed to go a lot deeper than necessary, continuing with the same string, on some non-empty strings, though it 
        did not crash.  
        """
# --        print('PPgm-entry')  # --
        self.prep = self.children[0].text
        if len(self.children) > 1 and not self.children[1].color:            
            if isinstance(self.children[1],NounPhrase) and len(self.children[1].get_text()[0]) > 0: # see note above
# --                print('PPgm-503',self.children[1].get_text())  # --
                self.meaning = self.children[1].get_meaning() 
            else:
                self.meaning =  ""
#            self.meaning = self.children[1].get_meaning() if isinstance(self.children[1],NounPhrase) else ""  # code prior to the correction
# --            print('PPgm-2',self.meaning)  # --
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

    def __init__(self,label,date,sentence):
        Phrase.__init__(self,label,date,sentence)
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
                    
                    np_replacement = NounPhrase("NP",self.date,self.sentence)
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
        if isinstance(m[0],basestring):
            return [m[0]]
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
        
        c, passive,meta = self.get_code()
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
            returns = []
            first,second,third = [up,"",""]
            if not (up or c) :
                return [event]
            if not isinstance(event,tuple):
                second = event
                third = c
                if passive:
                    for item in first:
                        e2 = ([second],item,passive)
                        self.sentence.metadata[id(e2)] = [event,meta,7]
                        returns.append(e2)
            elif event[1] == 'passive':
                first = event[0]
                third = utilities.combine_code(c,event[2])
                if up:
                    returns = []
                    for source in up:
                        e = (first,source,third)
                        self.sentence.metadata[id(e)] = [event,up,1]
                        returns.append(e)
                    return returns
                second = 'passive'
            elif not event[0] in ['',[],[""],["~"],["~~"]]:
                second = event
                third = c
            else:
                second = event[1]
                third = utilities.combine_code(c,event[2])
            e = (first,second,third)
            self.sentence.metadata[id(e)] = [event,c,meta ,2]
            return returns + [e]

        events = []
        up = self.get_upper()
        if self.check_passive() or (passive and not c):
            # Check for source in preps
            source_options = []
            target_options = up
            for child in self.children:
                if isinstance(child,PrepPhrase):
                    if child.get_prep() in ["BY","FROM","IN"]:
                        source_options += child.get_meaning()
                        meta.append((child.prep, child.get_meaning()))
                    elif child.get_prep() in ["AT","AGAINST","INTO","TOWARDS"]:
                        target_options += child.get_meaning()
                        meta.append((child.prep, child.get_meaning()))
            if not target_options:
                target_options = ["passive"]
            if source_options or c:
                
                for i in target_options:
                    e = (source_options, i ,c if self.check_passive() else passive)
                    events.append(e)
                    self.sentence.metadata[id(e)] = [None,e,meta,3]
                    self.meaning = events
                    return events
    
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
                e = (up,low,c)
                self.sentence.metadata[id(e)] = [None,e,4]
                events.append(e)
            elif low:
                events.append(low)

        lower = map(lambda a: a.get_meaning(),s_options)
        sents = []

        for item in lower:
            sents += item
        
        if sents and not events:  # Only if nothing else has been found do we look at lower NP's?
                                  # This decreases our coding frequency, but removes many false positives
            for event in sents:
                if isinstance(event,tuple) and (event[1] or event[2]):
                    for ev in resolve_events(event):
                        if isinstance(ev[1],list):
                            for item in ev[1]:
                                local = (ev[0],item,ev[2])
                                self.sentence.metadata[id(local)] = [ev,item,5]
                                events.append(local)
                        else:
                            events += resolve_events(event)
        maps = []
        for i in events:
            evs = self.match_transform(i)
            if isinstance(evs,tuple):
                for j in evs[0]:
                    maps.append(j)
                    self.sentence.metadata[id(j)] = [i,evs[1],6]
            else:
                maps += evs
        self.meaning = maps
        return maps
    

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
# --          print('cp-entry')
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
# --          print('rS-entry')
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
# --          print('gS-entry')
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
        
        if len(self.children) > 1:
            negated = (lower and self.children[1].text) == "NOT" 
        else:
            negated = False
            
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
        meta = []
        dict = PETRglobals.VerbDict['verbs']
        if 'AND' in map(lambda a: a.text, self.children):
            return 0,0,['and']
        patterns = PETRglobals.VerbDict['phrases']
        verb = "TO" if self.children[0].label == "TO" else self.get_head()[0]
        meta.append(verb)
        meaning = ""
        path = dict
        passive = False
        if verb in dict:
            code = 0
            path = dict[verb]
            if ['#'] == path.keys():
                path = path['#']
                if True or path.keys() == ['#']: # Pre-compounds are weird
                    try:
                        code = path['#']['code']
                        meaning = path['#']['meaning']
                        
                        self.verbclass = meaning if not meaning == "" else verb
                        if not code == '':
                            active, passive  = utilities.convert_code(code)
                            self.code = active
                    except:
                        self.code = (0,0,[])
            else:
                # Post - compounds
                for child in self.children:
                    if child.label in ["PRT","ADVP"]:
                        if child.children[0].text in path:
                            meta.append(child.children[0].text)
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
        
# --          print('++1')
        match = self.match_pattern()
# --          print('++2')
        if match:
# --              print('++4',match)
# --              print('++3',match['line'])
            meta.append(match['line'])
# --              print(match)
            active, passive  = utilities.convert_code(match['code'])
            self.code = active
        if passive and not active:
            self.check_passive = lambda : True
            self.code = passive
        return self.code, passive,meta



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
                line = pdict[1]
                path = pdict[0]
                verb = utilities.convert_code(path[2])[0] if not path[2] == "Q" else v2a["Q"]
                if isinstance(v2a[path[1]],tuple):
                    results = []
                    for item in v2a[path[1]]:
                        results.append((list(v2a[path[0]]),item,verb))
                    return results, line
                return [(list(v2a[path[0]]),v2a[path[1]],verb)], line
            
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
        
        
        try :
            t = recurse(PETRglobals.VerbDict['transformations'],e)
            if t:
                return t
            else:
                
                if e[0] and e[2] and isinstance(e[1],tuple) and  e[1][0] and not e[1][2] / (16 ** 3):
                    if isinstance(e[1][0],list):
                        results = []
                        for item in e[1][0]:
                            event =(e[0],item,utilities.combine_code(e[1][2],e[2]))
                            results.append(event)
                        return results
                    event =(e[0],e[1][0],utilities.combine_code(e[2],e[1][2]))
                    return [event]


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
# --              print('mph-entry')
            if not phrase:
# --                  print('mph-False')
                return False
            for item in filter(lambda b: b.text in path,phrase.children):
                subpath = path[item.text]
# --                  print('mph-rr-1')
                match = reroute(subpath,lambda a: match_phrase(a,item.head_phrase))
                if match:
                    item.color = True
                    return match
# --              print('mph-reroute')                    
            return reroute(path,lambda a: match_phrase(a,phrase.head_phrase))
        
        def match_noun(path,phrase = self if not self.check_passive() else self.get_S(),preplimit = 0):
            # Matches a noun or head of noun phrase
# --              print('mn-entry')
            noun_phrases = []
            if not phrase:
                return False
            if preplimit:
                for sib in phrase.children:
                    if isinstance(sib,PrepPhrase) and len(sib.children) > 1 and sib.get_prep() in ["BY","FROM"] :
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
                    match = reroute(subpath, skip , skip , lambda a: match_prep(a,item), skip ,0)
                    if match:
                        headphrase.children[-1].color = True
                        return match

                    # Then check the other siblings
                    match = reroute(subpath,(lambda a : match_phrase(a,item.head_phrase))
                            if isinstance(item,NounPhrase) else None ) # pas 16.04.21: Trapped None by having reroute return False
                    if match:
                        headphrase.children[-1].color = True
                        return match
            if '^' in path:
                phrase.color = True
# --                  print('mn-reroute1')
                return reroute(path['^'], lambda a: match_phrase(a,phrase.head_phrase))
# --              print('mn-reroute2')
            return reroute(path,lambda a: match_phrase(a,phrase.head_phrase))

        def match_prep(path,phrase=self):
            # Matches preposition
# --              print('mp-entry')
            for item in filter(lambda b: isinstance(b,PrepPhrase),phrase.children):
                prep = item.children[0].text
                if prep in path:
                    subpath = path[prep]
# --                      print('mp-reroute1')                    
                    match = reroute(subpath,
                                    lambda a : match_noun(a,item.children[1])if len(item.children) > 1 else False,
                                    match_prep)
                    if match:
# --                        print('mp-False')
                        return match
# --              print('mp-reroute2')                    
            return reroute(path, o2 = match_prep)

        def reroute(subpath, o1 = match_noun, o2 = match_noun, o3 = match_prep, o4 = match_noun, exit = 1):
# --                  print('rr-entry:') # ,subpath
                if not o1:  # match_noun() can call reroute() with o1 == None; guessing returning False is the appropriate response pas 16.04.21
                    return False
                if '-' in subpath:
                    match = o1(subpath['-'])
                    if match:
# --                          print('rr-- match')
                        return match
                        
                if ',' in subpath:
# --                      print('rr-,')
                    match = o2(subpath[','])
                    if match:
                        return match
    
                if '|' in subpath:
# --                      print('rr-|')
                    match = o3(subpath['|'])
                    if match:
                        return match
                
                if '*' in subpath:
# --                      print('rr-*')
                    match = o4(subpath['*'])
                    if match:
                        return match
                
                if '#' in subpath and exit:
# --                      print('rr-#')
                    return subpath['#']
                    
# --                  print('rr-False')
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
    
    
    
    
    Metadata
    --------
    
    The sentence will return with a "metadata" dict. This has two parts.
    
        - sent.metadata['nouns'] will be a list of pairs of the form
                
                    ( [Words that were coded], [Codes produced])
                
                Each list in the tuple usually only has one element, but sometimes multiple can occur
                
        - The other elements of sent.metadata have the key as the event, and
                the value as a list of lists. Each element of the value list contains
                some information about verbs that combined to form that event. The first
                element usually contains the primary verb and pattern that was matched on, and the latter
                elements are helping verbs that were combined with it.
        
        
        For example, the metadata for the sentence 
            
                 BOKO HARAM HAS LAUNCHED MANY SIMILAR ATTACKS DURING ITS SIX-YEAR CAMPAIGN FOR A STRICT ISLAMIC STATE IN NORTHEASTERN NIGERIA .
                 
                 
        Looks like:
        
         {
            (u'NGAREB', u'NGAMUS', u'190'): [[u'LAUNCHED', '- * ATTACKS [190]'],
                                             [u'HAS']],
            
            u'nouns':                        [([u'BOKO HARAM'], [u'NGAREB']),
                                              ([u'NIGERIA'], [u'NGA']),
                                              ([u'ISLAMIC'], [u'NGAMUS'])]}
         }
    
    
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
        self.txt = ""
        self.tree = self.str_to_tree(parse.strip())
        self.verb_analysis = {}
        self.events = []
        self.metadata = {'nouns': [] }
    
    
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
        root = Phrase(segs[0][1:],self.date, self )
        level_stack = [root]
        existentials = []
        
        for element in segs[1:]:
            if element.startswith("("):
                lab = element[1:]
                if lab == "NP":
                    new = NounPhrase(lab, self.date, self)
                elif lab == "VP":
                    new = VerbPhrase(lab,self.date, self)
                    self.verbs.append(new)
                elif lab == "PP":
                    new = PrepPhrase(lab, self.date, self)
                else:
                    new = Phrase(lab, self.date, self)
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
                self.txt += " " +element
    
        for element in existentials:
            try:
                element.parent.convert_existential()
            except:
                pass
        return root


    def print_nouns(self,label):  # --    
        """ Debugging print """
        print(label)
        for la in self.metadata['nouns']:
            print('    ',la)


    def get_metadata(self, entry):
    
        metadict = self.metadata
        next = entry
        store = ""
        meta_total = []
        while id(next) in metadict:
            store = metadict[id(next)]
            meta_total.append(store)
            next = store[0]
        #if not meta_total:
        #    print(entry,self.txt)
        #    exit()
        return map(lambda a:  a[-2] if len(a) > 1 else a[0], meta_total[::-1])
    
    
    def return_events(self):
        return self.events
    

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
        meta = {'nouns' : self.metadata['nouns'] }
        """print('GF1',events) # --  
# --        print('GF2',meta) # --  
        self.print_nouns('GF2') # -- """ 
        valid = []
        try:
            for sent in events:
                for event in sent:
                    if event[1] == 'passive':
                        event = (event[0],None,event[2])
                    if isinstance(event,tuple) and isinstance(event[1],basestring) :
                        
                        code = utilities.convert_code(event[2],0)
                        print('checking event', event, hex(event[2]))
                        if event[0] and event[1] and code :
                            for source in event[0]:
                                valid.append((source.replace('~','---'),event[1].replace('~','---'),code))
                                meta[(source.replace('~','---'),event[1].replace('~','---'),code)] =  self.get_metadata(event)
    
                        elif (not require_dyad) and event[0] and code and not event[1]:
                            for source in event[0]:
                                valid.append((source.replace('~','---'),"---",code))
    
                        elif (not require_dyad) and event[1] and code and not event[0]:
                            valid.append(("---",event[1].replace('~','---'),code))
                        
                        
                        # If there are multiple actors in a cooperation scenario, code their cooperation as well
                        if len(event[0]) > 1 and (not event[1]) and code and code[:2] in ["03","04","05","06"]:
                            for source in event[0]:
                                for target in event[0]:
                                    if not source == target:
                                        valid.append((source.replace('~','---'),target.replace('~','---'),code))
        
            self.events = list(set(valid))
            self.get_events = self.return_events
# --            print('GF3',valid,'\nGF4',meta) # --  
            return valid , meta
        except Exception as e:
            print("Error in parsing:",e)
            return None, None


    '''def print_to_file(self,root,file = ""):

        """Prints a LaTeX representation of the tree to a file, calls the recursive method
        print_tree() on the tree to print all of it
        """
        print("""   
                    \\resizebox{\\textwidth}{250pt}{%
                    \\begin{tikzpicture}
                    \\Tree""", file=file, end=" ")

        self.print_tree(root, "", file)
        print("\\end{tikzpicture}}\n\n", file=file)
        print("EVENTS: ",self.get_events(), file = file)
        print("\\\\\nTEXT: ", self.txt, file=file)
        print("\\newpage",file=file)'''
    
    def print_to_file(self,root,file = ""):
        """
        Simplified version of the above for GF
        """
        print("EVENTS: ",self.get_events(), file = file)
        txtstrg = self.txt.encode('ascii', 'ignore').decode('ascii')  # <16.03.29> For now, just zap the unicode
        print("TEXT: ", txtstrg, file=file)
    
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

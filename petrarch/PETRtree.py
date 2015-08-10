

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
#           of the petrarch software. Sentences are stored into
#           Sentence class objects, which contain a tree of Phrase
#           class objects. The phrases then do analyses of their role
#           in the sentence and the event information of the overall sentence
#           is calculated and returned within the get_events() method
#
#
#   Revision history:
#       July 2015 - Created
#



class Phrase:

    def __init__(self, label, date):
        self.label = label if not label == "MD" else "VB"
        self.children = []
        self.phrasetype = label[0]
        self.annotation = ""
        self.text = ""
        self.parent = None
        self.meaning = ""
        self.date = date
        self.index = -1
        self.head = None
        self.head_phrase = None
    
    def get_meaning(self):
        if self.label in "SBAR":
            lower = map(lambda b: b.get_meaning(), filter(lambda a: a.label in "SBARVP",self.children))
            events = []
            for item in lower:
                events += item
            if events:
                self.lower = events
                return events
    
        return self.meaning

    def resolve_codes(self,codes):
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
        codes = set()
        for act in (actors if actors else ['~']):
            for ag in (agents if agents else ['~']) :
                code = act
                if not ag[1:] in act:
                    code += ag[1:]
                if not code in ['~','~~']:
                    codes.add(code)
        return list(codes)

    def return_head(self):
        return self.head,self.head_phrase

    def get_head(self):
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

    def get_code(self):
        if not self.label in "SBAR":
            return None

        child_codes = filter(None, map(lambda a: a.get_code(),self.children))
        if len(child_codes) == 0:
            child_codes = 0
        elif len(child_codes) == 1:
            child_codes = child_codes[0]
        else:
            child_codes = child_codes
        return child_codes


class NounPhrase(Phrase):

    def __init__(self, label, date):
        Phrase.__init__(self, label, date)
    
    
    def return_meaning(self):
        return self.meaning

    def check_date(self, match):
        code = None
        try:
            for j in match:
                dates = j[1]
                date = []
                for d in dates:
                    if d[0] in '<>':
                        date.append(d[0]+str(PETRreader.dstr_to_ordate(d[1:])))
                    else:
                        date.append(PETRreader.dstr_to_ordate(d))
                curdate= self.date
                if len(date) ==0:
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
        except:
            return code
        return code

    def get_meaning(self):
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
     
        ##
        #
        #   Check for the meanings of its children. This method will be called on the children nodes as well
        #          if meaning has not already been determined, which it shouldn't have because these should be
        #          1-regular in-degree graphs,but who knows.
        ##
        
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
                if child.label[:2] in ["NN","JJ","DT"]:
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
                elif child.label == "NP":
                    m = child.get_meaning()
                    if not m == "":
                        NPcodes+= m
                elif child.label == "PP":
                    m = child.get_meaning()
                    if not m == None:
                        PPcodes += m
                elif child.label == "PRP":
                    # Naively find antecedent ?
                    not_found = True
                    level = self.parent
                    reflexive = child.text.endswith("SELF") or child.text.endswith("SELVES")
                    local = True
                    while not_found and level.parent:
                        if level.label.startswith("NP") and reflexive: #Intensive
                            break
                        if local and level.label in ["S","SBAR"]:
                            local = False
                            level=level.parent
                            continue
                        
                        if (not local) or (reflexive and local):
                            for child in level.parent.children:
                                if isinstance(child,NounPhrase) and not child.get_meaning() == "" :  # Do we just want to pick the first?
                                    not_found = False
                                    codes += child.get_meaning()
                                    break

                        level = level.parent
                elif child.label == "VP":
                    meaning = child.get_meaning()
                    #print(meaning)
                    if meaning and isinstance(meaning[0][1],basestring):
                        VPcodes += child.get_theme()
        
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
        self.get_meaning = self.return_meaning # don't need to calculate every time

        return self.meaning


class PrepPhrase(Phrase):

    def __init__(self, label, date):
        Phrase.__init__(self, label, date)
        self.meaning = ""
        self.prep = ""
        self.noun_head = ""

    def get_meaning(self):
        self.prep = self.children[0].text
        if len(self.children) > 1:
            self.meaning = self.children[1].get_meaning() if isinstance(self.children[1],NounPhrase) else ""
            self.head = self.children[1].get_head()[0]
        
        return self.meaning

    def get_prep(self):
        
        return self.children[0].text


class VerbPhrase(Phrase):

    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
        self.meaning = "---" # "meaning" for the verb, i.e. the basic verb the synonym refers to
        self.upper = ""      # contains the meaning of the noun phrase in the specifier position for the vp or its parents
        self.lower = ""      # contains the meaning of the subtree c-commanded by the verb
        self.passive = False
        self.code = 0
        self.valid = self.is_valid()
        self.S  = None
    
    def is_valid(self):

        # This is largely to overcome frequently made Stanford errors, where phrases like "exiled dissidents" were
        # marked as verb phrases, and treating them as such would yield weird parses.
        
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
        m = self.get_meaning()
        if m[0][1] == 'passive':
            return m[0][0]
        return [m[0][1]]
    
    def return_meaning(self):
        #print("RETURNING")
        return self.meaning
    
    def get_meaning(self):
        self.get_meaning = self.return_meaning
        
        c = self.get_code()
        
        if self.check_passive():
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
                target_options = "passive"
            if source_options or c:
                self.meaning = [(source_options, target_options, c)]
                return self.meaning
    
        up = self.get_upper()
        up = "" if up in ['',[],[""],["~"],["~~"]] else up
        
        low,neg = self.get_lower()
        if not low:
            low = ""
        if neg:
            return []

        s_options = filter(lambda a: a.label in "SBAR",self.children)
        events = []
        def resolve_events(event):
            first,second,third = [up,"",""]
            if not isinstance(event,tuple):
                second = event
                third = c
            if not (up or c) :
                return event
            elif event[1] == 'passive':
                first = event[0]
                second = up[0] if up else 'passive'
                third = utilities.combine_code(c,event[2])
            elif not event[0] in ['',[],[""],["~"],["~~"]]:
                second = event
                third = c
            else:
                second = event[1]
                third = utilities.combine_code(c,event[2])
            
            return first,second,third
        
        if isinstance(low,list):
            for event in low:
                events.append(resolve_events(event))
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
                    events.append(resolve_events(event))

        events = map(self.match_transform, events)
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
        self.get_upper = self.return_upper
        not_found = True
        level = self
        while not_found and not level.parent is None:
            #if isinstance(level.parent,VerbPhrase) and level.label in ["S","SBAR","VP"]:
            #    self.upper = level.parent.upper
            #    return self.upper
            for child in level.parent.children:
                # Do we just want to pick the first?
                if isinstance(
                        child, NounPhrase) and not child.get_meaning() == ["~"]:
                    self.upper = child.get_meaning()
                    not_found = False
                    return self.upper
            #level = level.parent
            not_found = False
        return []

    def return_lower(self):
        return self.lower
    
    def get_lower(self):
        self.get_lower = self.return_lower
        
        lower = []
        v_options = filter(lambda a: (isinstance(a,VerbPhrase) and a.is_valid()),self.children)
        
        lower = map(lambda a: a.get_meaning(),v_options)

#        for child in filter(lambda a: (isinstance(a,VerbPhrase) and a.is_valid()) or a.label in "SBAR",self.children):
#            lower.append(child.get_meaning())

        events  = []
        negated = 0
        if lower:
            negated = self.children[1].text == "NOT"
        for item in lower:
            events += item
        if events:
            self.lower = events
            return events,negated
        
        NPcodes = []
        PPcodes = []
        VPcodes = []
        #Scodes = []
        
        for child in self.children:
            if isinstance(child, NounPhrase):
                NPcodes += child.get_meaning()
            elif isinstance(child, PrepPhrase):
                #print(child.get_meaning(),child.prep)
                PPcodes += (child.get_meaning())
            #elif isinstance(child, VerbPhrase):
                #meaning = child.get_meaning()
                #VPcodes += meaning[1] if isinstance(meaning[1],basestring)
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
                #if not actorcodes:
                #    actorcodes += Sactor
    
        agentcodes += NPagent
        if not agentcodes:
            agentcodes += PPagent
            if not agentcodes:
                agentcodes += VPagent
                #if not agentcodes:
                #    agentcodes += Sagent
        
        self.lower = self.mix_codes(agentcodes,actorcodes)
        return self.lower,negated

    def return_code(self):
        return self.code
    
    def get_code(self):
        self.get_code = self.return_code
        dict = PETRglobals.VerbDict['verbs']
        if 'AND' in map(lambda a: a.text, self.children):
            return 0
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
                        self.meaning = meaning if not meaning == "" else verb
                        if not code == '':
                            self.code, passive  = utilities.convert_code(code)
                    except:
                        self.code = 0
            else:
                # Post - compounds
                for child in self.children:
                    if child.label in ["PRT","ADVP"]:
                        if child.children[0].text in path:
                            #print(child.children[0].text)
                            path = path[child.children[0].text]
                if "#" in path:
                    try:
                        code = path['#']['#']['code']
                        meaning = path['#']['#']['meaning']
                        self.meaning = meaning if not meaning == "" else verb
                        if not code == '':
                            self.code, passive  = utilities.convert_code(code)
                    except:
                        pass
        
        match = self.match_pattern()
        if match:
            print(match)
            self.code, passive  = utilities.convert_code(match['code'])
        
        if passive:
            self.check_passive = lambda : True
        return self.code



    def match_transform(self,e):
        def recurse(pdict,event,a2v = {}, v2a = {}):
            path = pdict
            if isinstance(pdict,list):
                return v2a[path[0]],v2a[path[1]],utilities.convert_code(path[2])[0]
            if isinstance(event,tuple):
                actor = event[0] if not isinstance(event[0],list) else event[0][0]
                masks = filter(lambda a :a in pdict, [event[2],event[2] - event[2] % 0x10,
                        event[2] - event[2] % 0x100,event[2] - event[2] % 0x1000])
                if masks:
                    path = pdict[masks[0]]
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
            else:
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
        except Exception as ex:
            print(ex)
        return e
    

    def match_pattern(self):
        meaning = self.meaning
        code = self.code

        def match_phrase(path,phrase):
            # Having matched the head of the phrase, this matches the full noun phrase, if specified
            for item in filter(lambda b: b.text in path,phrase.children):
                
                subpath = path[item.text]
                match = reroute(subpath,lambda a: match_phrase(a,item.head_phrase))
                if match:
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
            
            for item in noun_phrases:
                head = item.get_head()[0]
                
                if head in path:
                    subpath = path[head]
                    match = reroute(subpath,(lambda a : match_phrase(a,item.head_phrase)) if isinstance(item,NounPhrase) else None)
                    if match:
                        return match
            return reroute(path,lambda a: match_phrase(a,phrase.head_phrase))

        def match_prep(path):
            # Matches preposition
            for item in filter(lambda b: isinstance(b,PrepPhrase),self.children):
                meaning = item.get_meaning()
                prep = item.prep
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
                #print('here',self.head)
                return match_noun(path,self,1)
            else:
                return match_noun(path,self.get_S())
        return False



class Sentence:

    def __init__(self, str, text, date):
        self.treestr = str.replace(')', ' )')
        self.parse = str
        self.agent = ""
        self.ID = -1
        self.actor = ""
        self.date = date
        self.longlat = (-1,-1)
        self.verbs = []
        self.tree = self.str_to_tree(str.strip())
        self.txt = text
        self.verb_analysis = {}
        self.events = []
    
    def str_to_tree(self,str):
        root = Phrase(str[1],self.date)
        level_stack = [root]
        for element in str[2:].split():
            if '(' in element:
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
                new.parent = level_stack[-1]
                new.index = len(level_stack[-1].children)
                level_stack[-1].children.append(new)
                level_stack.append(new)
            elif ')' in element:
                try:
                    level_stack.pop()
                except:
                    break
            else:
                level_stack[-1].text = element
        return root

    def get_events(self):
        events = map(lambda a : a.get_meaning(), filter(lambda b: b.label in "SVP" , self.tree.children))
        print(self.txt if self.txt else utilities.parse_to_text(self.parse).lower())
        print(events)
        print("\n\n")
        return events
        """
        for v in self.verbs:
            if not v.valid:
                continue
            scopes = v.get_meaning()
            code = v.get_code()
        
            if not False and not [] in scopes and not "" in scopes:
                #print("SRC: ",scopes[0],"TARG ",scopes[1],"CODE ",code)
                srcs = scopes[0]
                targs = scopes[1]
                for src in srcs:
                    if src == "~":
                        continue
                    for targ in targs:
                        if targ == "~":
                            continue
                        if not (src == targ and code == 0): # ... said he/she/it/they ...
                            if v.check_passive():
                                events.append([targ,src,str(code)] )
                            else:
                                if False and ':' in code:
                                    codes = code.split(':')
                                    events.append([src,targ,codes[0]])
                                    events.append([targ,src,codes[1]])
                                else:
                                    events.append([src,targ,str(code)] )
                
        """
    


    def do_verb_analysis(self):
        verbs = self.verbs
        records = self.verb_analysis
        preps = map(lambda a: a[:-1],open("data/dictionaries/Phoenix.prepositions.txt").readlines())
        for verb_obj in verbs:
            code= verb_obj.get_code()
            scopes = verb_obj.get_meaning()
            record = records.setdefault(verb_obj.meaning,{'count':0,'sources':0,'targets':0,'before':{},'after':{},'preps' : {}})
            record['count'] += 1
            record['sources'] += len(scopes[0])
            record['targets'] += len(scopes[1])
            try:
                segs = self.txt.upper().split(verb_obj.children[0].text)
                for i in range(0,5):
                    record['before'][segs[0][-i-1]] = record['before'].setdefault(segs[0][-i-1],0) + (6.0-i)/4
                    record['after'][segs[1][i]] = record['after'].setdefault(segs[1][i],0) + (6.0-i)/4
                    if segs[1][i] in preps:
                        record['preps'][segs[1][i]] = record['preps'].setdefault(segs[1][i],0) + 1
            except:
                print("oops")


    
    def print_to_file(self,root,file = ""):
    
        print("""
                    \\begin{tikzpicture}[scale= .25]
                    \\Tree""", file=file, end=" ")

        self.print_tree(root, "", file)
        print("""\\end{tikzpicture}
                      \\newpage
                    """, file=file)

    def print_tree(self, root, indent="", f=""):
        # This prints a LaTeX formatted document of the tree
        print("[."+root.label.replace("$",""),("{\\bf "+root.text+"}" if not root.text == "" else "") ,file = f,end = " ")
        if root.label in ["NP"]:
            m = root.get_meaning()
            k = ""
            for i in m:
                k += "+" + i
            print("[.{" + k + "}", file=f, end=" ")
        elif root.label in ["VP"]:
            m = root.get_meaning()
            #print(root.head,m)
            k = ""
            print("[.{\it "+utilities.code_to_string(m)+"}",file = f,end = " ")
            """
            if m[0] is None:
                k = ""
            else:
                for i in m[0]:
                    k += "+"+i
            j =""
            if m[1] == None:
                j == ""
            else:
                for g in m[1]:
                    j += "+"+str(g)
            if not isinstance(root.get_code(),np.ndarray):
                print("SOMETHING WENT WRONG")
                print(root.get_code())
                print(root.get_head())
            print("[.{\it Upper "+k+", Lower "+j+", Code: "+str(root.get_code())+(" Passive" if root.check_passive() else "")+"}",file = f,end = " ")"""
        for child in  root.children:
                self.print_tree(child,indent+"\t",f)
        if root.label in ["NP","VP"]:
            print(" ] ]",file = f,end=" \n")
        else:
            print(" ]", file=f, end=" ")

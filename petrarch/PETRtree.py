

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
        self.label = label
        self.children = []
        self.phrasetype = label[0]
        self.annotation = ""
        self.text = ""
        self.parent = None
        self.meaning = ""
        self.date = date
        self.index = -1
        self.head = None
    
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
        return self.head


    def get_head(self):
        self.get_head = self.return_head
        
        try:
            if self.label == 'S':
                self.head = map(lambda b: b.get_head(),filter(lambda a : a.label == 'VP', self.children))[0]
                return self.head
            
            if (not self.label[1] == 'P'):
                return self.text
        
            head_children = filter(lambda child : child.label.startswith(self.label[0]) and not child.label[1] == 'P', self.children)
            if head_children:
                possibilities = filter(lambda b: b, map(lambda a: a.text,head_children))
            else:
                other_children= filter(lambda child : child.label.startswith(self.label[0]), self.children)
                possibilities = filter(lambda b: b, map(lambda a: a.get_head(),other_children))
            
            self.head = possibilities[-1]   # return the last, English usually compounds words to the front
            return possibilities[-1]
            
        except:
            return None

    def get_code(self):
        if not self.label in "SBAR":
            return None

        child_codes = filter(lambda b: b is not None ,map(lambda a: a.get_code(),self.children))
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
                        if level.label in ["S","SBAR"]:
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
                    m = "" # child.get_meaning()[1]
                    if not m == "":
                        VPcodes+= m
        
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
        #VPactor, VPagent = self.resolve_codes(VPcodes)
        if not actorcodes:
            actorcodes += NPactor
            if not actorcodes:
                actorcodes += PPactor
        #        if not actorcodes:
        #            actorcodes += VPactor                # Do we want to pull meanings from verb phrases? Could be risky
        
        if not agentcodes:
            agentcodes += NPagent
            if not agentcodes:
                agentcodes += PPagent
         #       if not agentcodes:
         #           agentcodes += VPagent
                    
        
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
        self.meaning = self.children[1].get_meaning() if isinstance(self.children[1],NounPhrase) else ""
        self.prep = self.children[0].text
        self.head = self.children[1].get_head()
        return self.meaning


class VerbPhrase(Phrase):

    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
        self.meaning = "---" # "meaning" for the verb, i.e. the basic verb the synonym refers to
        self.upper = ""      # contains the meaning of the noun phrase in the specifier position for the vp or its parents
        self.lower = ""      # contains the meaning of the subtree c-commanded by the verb
        self.passive = False
        self.code = 0
        self.valid = self.is_valid()
    
    def is_valid(self):
        # This function is to weed out things like helping verbs and participles coded as verbs
        # Largely to overcome frequently made Stanford errors
        
        try:
            if self.children[0].label == "VBN":
                helping = ["HAVE","HAD","HAVING","HAS"]
                if ((not (self.parent.get_head() in helping or self.parent.children[0].text in helping)) and
                  len(filter(lambda a: isinstance(a,VerbPhrase),self.parent.children)) <= 1  and
                    not self.check_passive()):
                    self.valid = False
                    return False
            self.valid = True
        except:
            self.valid = True
        return True
    
    
    def return_meaning():
        return self.meaning
    
    def get_meaning(self):
        up = self.get_upper()
        low = self.get_lower() if self.get_lower() else ""
        c = self.get_code()
        #print("FINDING MEANING", self.children[0].text,c)
        
        
        s_options = filter(lambda a: a.label in "SBAR",self.children)
        events = []
        def resolve_events(event):
            first,second,third = [up,"",""]
            if not event[0] in ['',[],[""],["~"],["~~"]]:
                second = event
                third = c
            else:
                second = event[1]
                third = utilities.combine_code(c,event[2])
            return first,second,third
 
        if isinstance(low,list) :
            for event in low:
                events.append(resolve_events(event))
        elif not s_options:
            events.append((up,low,c))
        
        lower = map(lambda a: a.get_meaning(),s_options)
        sents = []
        for item in lower:
            sents += item
        
        if sents:
            for event in sents:
                events.append(resolve_events(event))
                
        #print("\t",events)
        
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
        return [""]

    def return_lower(self):
        return self.lower
    
    def get_lower(self):
        self.get_lower = self.return_lower
        
        lower = []
        v_options = filter(lambda a: (isinstance(a,VerbPhrase) and a.is_valid()),self.children)
        
        lower = map(lambda a: a.get_meaning(),v_options)

#        for child in filter(lambda a: (isinstance(a,VerbPhrase) and a.is_valid()) or a.label in "SBAR",self.children):
#            lower.append(child.get_meaning())
        events = []
        for item in lower:
            events += item
        if events:
            self.lower = events
            return events
        
        NPcodes = []
        PPcodes = []
        VPcodes = []
        #Scodes = []
        
        for child in self.children:
            if isinstance(child, NounPhrase):
                NPcodes += child.get_meaning()
            elif isinstance(child, PrepPhrase):
                PPcodes += (child.get_meaning())
            #elif isinstance(child, VerbPhrase):
            #    VPcodes += child.get_meaning()[1]
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
        #Sactor,Sagent = self.resolve_codes(Scodes)

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
        return self.lower

    def return_code(self):
        return self.code
    
    def get_code(self):
        self.get_code = self.return_code
        
        dict = PETRglobals.VerbDict['verbs']
        patterns = PETRglobals.VerbDict['phrases']
        verb = self.children[0].text
        if verb in dict:
            code = 0
            if '#' in dict[verb]:
                try:
                    code = dict[verb]['#']['#']['code']
                    meaning = dict[verb]['#']['#']['meaning']
                    self.meaning = meaning if not meaning == "" else verb
                    
                    if not code == '':
                        self.code = utilities.convert_code(code)
                    else:
                        self.code = utilities.convert_code(patterns[dict[verb]['#']['#']['meaning']]['#']['#']['code'])
                except:
                    self.code = 0
        
        
        # Combine with children codes
        child_codes = filter(lambda b: b is not None ,map(lambda a: a.get_code(),self.children))
        if len(child_codes) == 0:
            child_codes = 0
        elif len(child_codes) == 1:
            child_codes = child_codes[0]
        else:
            child_codes = child_codes
        #try:
        #    self.code = utilities.combine_code(self.code,child_codes )
        #except:
        #    print("weird additions")
        return self.code



class Sentence:

    def __init__(self, str, text, date):
        self.treestr = str.replace(')', ' )')
        self.parse = ""
        self.agent = ""
        self.ID = -1
        self.actor = ""
        self.date = date
        self.longlat = (-1,-1)
        self.verbs = []
        self.tree = self.str_to_tree(str[1:-1].strip())
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
        events = []
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
                

        return events


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
        if root.label in ["VP"]:
            m = root.get_meaning()
            k = ""
            print("[.{\it "+utilities.code_to_string(m)+(" Passive" if root.check_passive() else "")+"}",file = f,end = " ")
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

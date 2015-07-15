

from __future__ import print_function
from __future__ import unicode_literals


import PETRglobals
import PETRreader
import time

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
    
    def get_meaning(self):
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
                if not ag[1:] in act:
                    codes.add(act+ag[1:])
                else:
                    codes.add(act)

    
        return list(codes)

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
                            if isinstance(level,VerbPhrase):
                                codes += level.get_upper()
                                break
                            for child in level.parent.children:
                                if isinstance(child,NounPhrase) and not child.get_meaning() == "" :  # Do we just want to pick the first?
                                    not_found = False
                                    codes += child.get_meaning()
                                    break
                        
                        
                    
                        level = level.parent
                elif child.label == "VP":
                    m = child.get_meaning()[1]
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
        VPactor, VPagent = self.resolve_codes(VPcodes)
        if not actorcodes:
            actorcodes += NPactor
            if not actorcodes:
                actorcodes += PPactor
                if not actorcodes:
                    actorcodes += VPactor
        
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

    def get_meaning(self):
        self.meaning = self.children[1].get_meaning()
        self.prep = self.children[0].text
        return self.meaning


class VerbPhrase(Phrase):

    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
        self.meaning = "---" # "meaning" for the verb, i.e. the basic verb the synonym refers to
        self.upper = ""      # contains the meaning of the noun phrase in the specifier position for the vp or its parents
        self.lower = ""      # contains the meaning of the subtree c-commanded by the verb
        self.passive = False
        self.code = ""
        self.valid = self.is_valid()
    
    
    def get_head(self):
        for child in children:
            if "V" in child.label:
                return child
    
    def is_valid(self):
        # This function is to weed out things like helping verbs and participles coded as verbs
        helping = ["HAVE","HAD","HAVING"]
        if self.label == "VBN":
            if not self.parent.get_head().text in helping:
                self.valid = False
                return False
        self.valid = True
        return True
    
    
    
    def get_meaning(self):
        up = self.get_upper()
        low = self.get_lower()
        return up,low
        #return self.get_upper(), self.get_lower()

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
            if isinstance(level.parent,VerbPhrase) and level.label in ["S","SBAR","VP"]:
                self.upper = level.parent.upper
                return self.upper
            for child in level.parent.children:
                # Do we just want to pick the first?
                if isinstance(
                        child, NounPhrase) and not child.get_meaning() == "":
                    self.upper = child.get_meaning()
                    not_found = False
                    return self.upper
            level = level.parent



    def return_lower(self):
        return self.lower
    
    def get_lower(self):
        self.get_lower = self.return_lower
        # this is WAY harder than finding upper

        #### SUPER NAIVE ######
        #
        #   This probably only works with very basic sentences, will do some more tests and research
        #

        NPcodes = []
        PPcodes = []
        VPcodes = []
        Scodes = []
        
        for child in self.children:
            if isinstance(child, NounPhrase):
                NPcodes += child.get_meaning()
            elif isinstance(child, PrepPhrase):
                PPcodes += (child.get_meaning())
            elif isinstance(child, VerbPhrase):
                VPcodes += child.get_meaning()[1]
            elif child.label in "SBAR":
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
        Sactor,Sagent = self.resolve_codes(Scodes)

        actorcodes += NPactor
        if not actorcodes:
            actorcodes += PPactor
            if not actorcodes:
                actorcodes += VPactor
                if not actorcodes:
                    actorcodes += Sactor
    
        agentcodes += NPagent
        if not agentcodes:
            agentcodes += PPagent
            if not agentcodes:
                agentcodes += VPagent
                if not agentcodes:
                    agentcodes += Sagent
        
        self.lower = self.mix_codes(agentcodes,actorcodes)
        return self.lower

    def return_code(self):
        return str(self.code)
    
    def get_code(self):
        self.get_code = self.return_code
        
        dict = PETRglobals.VerbDict['verbs']
        patterns = PETRglobals.VerbDict['phrases']
        verb = self.children[0].text

        if verb in dict:
            code = '---'
            if '#' in dict[verb]:
                try:
                    code = dict[verb]['#']['#']['code']
                    meaning = dict[verb]['#']['#']['meaning']
                    self.meaning = meaning if not meaning == "" else verb
                    
                    if not code == '':
                        self.code = code
                        return code
                    self.code =patterns[dict[verb]['#']['#']['meaning']]['#']['#']['code']
                    
                    return self.code
                except:
                    return "---"
        return "---"


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
        
            if not code == "---" and not [] in scopes and not "" in scopes:
                #print("SRC: ",scopes[0],"TARG ",scopes[1],"CODE ",code)
                srcs = scopes[0]
                targs = scopes[1]
                for src in srcs:
                    if src == "~":
                        continue
                    for targ in targs:
                        if targ == "~":
                            continue
                        if not (src == targ and code == '010'): # ... said he/she/it/they ...
                            if v.check_passive():
                                events.append([targ,src,code] )
                            else:
                                if ':' in code:
                                    codes = code.split(':')
                                    events.append([src,targ,codes[0]])
                                    events.append([targ,src,codes[1]])
                                else:
                                    events.append([src,targ,code] )
                

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
                    j += "+"+g
            print("[.{\it Upper "+k+", Lower "+j+", Code: "+root.get_code()+(" Passive" if root.check_passive() else "")+"}",file = f,end = " ")
        for child in  root.children:
                self.print_tree(child,indent+"\t",f)
        if root.label in ["NP","VP"]:
            print(" ] ]",file = f,end=" \n")
        else:
            print(" ]", file=f, end=" ")

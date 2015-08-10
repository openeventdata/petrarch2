

from __future__ import print_function
from __future__ import unicode_literals


import PETRglobals
import PETRreader


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
<<<<<<< HEAD
        self.index = -1
    
    def get_meaning(self):
        return self.meaning

    def resolve_codes(self,codes):
        actorcodes = []
        agentcodes = []
        for code in codes:
            if code.startswith("~"):
                agentcodes.append(code[1:])
            else:
                actorcodes.append(code)
        return actorcodes,agentcodes
        
        
        

    def mix_codes(self,agents,actors):
        codes = set()
        for act in (actors if actors else ['~']):
            for ag in (agents if agents else ['']) :
                if not ag in act:
                    codes.add(act+ag)
                else:
                    codes.add(act)

    
        return list(codes)

=======

    def get_meaning(self):
        return self.meaning

>>>>>>> FETCH_HEAD


    def __init__(self, label, date):
        Phrase.__init__(self, label, date)

<<<<<<< HEAD


class NounPhrase(Phrase):

    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
    
=======
>>>>>>> FETCH_HEAD
    def return_meaning(self):
        return self.meaning

    def check_date(self, match):

        code = None
<<<<<<< HEAD
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
=======

        for j in match:
            dates = j[1]
            date = []
            for d in dates:
                if d[0] in '<>':
                    date.append(d[0] + str(PETRreader.dstr_to_ordate(d[1:])))
                else:
                    date.append(PETRreader.dstr_to_ordate(d))
            curdate = self.date
            print("Checking date:", curdate, date)
            if len(date) == 0:
                code = j[0]
            elif len(date) == 1:
                if date[0][0] == '<':
                    if curdate < int(date[0][1:]):
                        code = j[0]
>>>>>>> FETCH_HEAD
                else:
                    if curdate < int(date[1]):
                        if curdate >= int(date[0]):
                            code = j[0]
        except:
            return code
        return code

    def get_meaning(self):
        dict_entry = ("", -1)
        dicts = (PETRglobals.ActorDict, PETRglobals.AgentDict)
        match_in_progress = {}
        codes = []
        NPcodes = []
        PPcodes = []
        VPcodes = []
        i = 0
<<<<<<< HEAD
        option = -1
        pathleft = [({},i,-1)]
     
=======
        option = 0
        pathleft = [({}, i, 0)]

>>>>>>> FETCH_HEAD
        ##
        #
        #   Check for the meanings of its children. This method will be called on the children nodes as well
        #          if meaning has not already been determined, which it shouldn't have because these should be
        #          1-regular in-degree graphs,but who knows.
        ##
<<<<<<< HEAD
        
        APMprint = True
        while i < len(self.children):
            child = self.children[i]
            if match_in_progress != {} :
                if child.text in match_in_progress and not option == 2:
                    pathleft.append((match_in_progress,i,2))
                    match_in_progress = match_in_progress[child.text]
=======

        while i < len(self.children):
            child = self.children[i]
            if match_in_progress != {}:
                if child.text in match_in_progress:
                    match_in_progress = match_in_progress[child.text]
                    pathleft.append((match_in_progress, i, 0))
>>>>>>> FETCH_HEAD
                elif "#" in match_in_progress:
                    match = match_in_progress['#']
                    # We've matched from the actor dictionary
                    if isinstance(match, type([])):
                        code = self.check_date(match)
                        if not code is None:
                            codes.append(code)
                    # We've matchd from the agent dictionary
                    else:
                        codes.append(match_in_progress['#'])
                    match_in_progress = {}
                    option = -1
                    continue
                else:
                    p = pathleft.pop()
<<<<<<< HEAD
                    if option == 1:
                        i = p[1] + 1
                    else:
                        i = p[1]
                    match_in_progress = p[0]
                    option = p[2]
=======
                    i = p[1] + 1
                    match_in_progress = p[0]
                    option = p[2] - 1
>>>>>>> FETCH_HEAD
                    continue

            else:
                if child.label[:2] in ["NN", "JJ", "DT"]:
                    text = child.text
<<<<<<< HEAD
                    if (not option >= 0) and text in PETRglobals.ActorDict:
                        dict_entry = (text,0)
                    elif text in PETRglobals.AgentDict and not option == 1:
                        dict_entry = (text,1)
                    try:
                        match_in_progress = dicts[dict_entry[1]][dict_entry[0]]
                        pathleft.append(({},i,dict_entry[1]))
=======
                    if option == 0 and text in PETRglobals.ActorDict:
                        dict_entry = (text, 0)
                    elif text in PETRglobals.AgentDict:
                        dict_entry = (text, 1)
                    try:
                        match_in_progress = dicts[dict_entry[1]][dict_entry[0]]
                        pathleft.append(({}, i, dict_entry[1] + 1))
>>>>>>> FETCH_HEAD
                        dict_entry = None
                    except:
                        if False:
                            print("No match")
                elif child.label == "NP":
                    m = child.get_meaning()
                    if not m == "":
                        NPcodes += m
                elif child.label == "PP":
                    m = child.get_meaning()
                    if not m is None:
                        PPcodes += m
                elif child.label == "PRP":
                    # Naively find antecedent ?
                    not_found = True
                    level = self.parent
                    while not_found and not level.parent is None:
                        if level.label in ["NP", "S", "SBAR"]:
                            level = level.parent
                            continue
                        # if level.label == "VP":
                        #    codes += level.get_upper()
                        for child in level.parent.children:
<<<<<<< HEAD
                            if isinstance(child,NounPhrase) and not child.get_meaning() == "" :  # Do we just want to pick the first?
=======
                            print("COMPARING", child.text)
                            # Do we just want to pick the first?
                            if isinstance(
                                    child, NounPhrase) and not child.get_meaning() == "":
>>>>>>> FETCH_HEAD
                                not_found = False
                                codes += child.get_meaning()
                        level = level.parent
                elif child.label == "VP":
                    m = child.get_meaning()[1]
                    if not m == "":
<<<<<<< HEAD
                        VPcodes+= m
 
=======
                        VPcodes += m

>>>>>>> FETCH_HEAD
            i += 1
            option = -1
            if(i >= len(self.children) and not match_in_progress == {}):
                if "#" in match_in_progress:
                    match = match_in_progress['#']
<<<<<<< HEAD
                    if isinstance(match,list):
=======
                    print("MATCH", match)
                    if isinstance(match, list):
>>>>>>> FETCH_HEAD
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
<<<<<<< HEAD
                        i= p[1]
                    #print("retracing",i)
                    
                        
                    
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

        if self.meaning == "":
            self.meaning =['~']
=======
                        i = p[1]

        actorcodes = []
        codes += NPcodes
        agentcodes = ""
        for code in codes:
            try:
                if code[0] == '~' and not code[1:] in agentcodes:
                    agentcodes += code[1:]
                else:
                    actorcodes.append(code)
            except:
                print("Weird coding thing")
        if actorcodes == []:
            for code in PPcodes:
                try:
                    if code[0] == '~' and not code[1:] in agentcodes:
                        agentcodes += code[1:]
                    else:
                        actorcodes.append(code)
                except:
                    print("Weird coding thing in PP")

        if actorcodes == []:
            print("###########", VPcodes)
            actorcodes = VPcodes

        try:
            self.meaning = map(
                lambda x: x +
                agentcodes,
                actorcodes if len(actorcodes) > 0 else ['~'])
        except:
            self.meaning = ['~']
        # don't need to calculate every time
        self.get_meaning = self.return_meaning

>>>>>>> FETCH_HEAD
        if self.meaning == ['~']:
            self.meaning = NPcodes

        return self.meaning


<<<<<<< HEAD

=======
>>>>>>> FETCH_HEAD
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

<<<<<<< HEAD
    def __init__(self,label,date):
        Phrase.__init__(self,label,date)
        self.meaning = "---" # "meaning" for the verb, i.e. the basic verb the synonym refers to
        self.upper = ""      # contains the meaning of the noun phrase in the specifier position for the vp or its parents
        self.lower = ""      # contains the meaning of the subtree c-commanded by the verb
        self.passive = False
        self.code = ""
    
    
    def get_meaning(self):
        return self.get_upper(),self.get_lower()
    
    def return_upper(self):
        return self.upper
    
    def return_passive(self):
        return self.passive
    
    def check_passive(self):
        self.check_passive = self.return_passive
        
        try:
            if self.children[0].label in ["VBD","VBN"]:
                level= self.parent
                if level.label == "NP":
                    self.passive = True
                    return True
                for i in range(2):
                    if isinstance(level,VerbPhrase):
                        if level.children[0].text in ["AM","IS","ARE","WAS","WERE","BE","BEEN","BEING"]:
                            self.passive = True
                            return True
                    level = level.parent
        

        except:
            print("Error in passive check")
        self.passive = False
        return False
        

=======
    def __init__(self, label, date):
        Phrase.__init__(self, label, date)
        self.meaning = "---"  # code for this particular verb
        # contains the meaning of the noun phrase in the specifier position for
        # the vp or its parents
        self.upper = ""
        # contains the meaning of the subtree c-commanded by the verb
        self.lower = ""

    def get_meaning(self):

        return self.get_upper(), self.get_lower()

    def return_upper(self):
        return self.upper
>>>>>>> FETCH_HEAD

    def get_upper(self):
        self.get_upper = self.return_upper
        not_found = True
        level = self
        while not_found and not level.parent is None:
            if isinstance(level.parent,VerbPhrase):
                self.upper = level.parent.upper
                return self.upper
            for child in level.parent.children:
<<<<<<< HEAD
                if isinstance(child,NounPhrase) and not child.get_meaning() is None : # Do we just want to pick the first?
=======
                # Do we just want to pick the first?
                if isinstance(
                        child, NounPhrase) and not child.get_meaning() == "":
>>>>>>> FETCH_HEAD
                    self.upper = child.get_meaning()
                    not_found = False
                    return self.upper
            level = level.parent

<<<<<<< HEAD


    def return_lower(self):
        return self.lower
    
    def get_lower(self):
        self.get_lower = self.return_lower
=======
    def get_lower(self):

>>>>>>> FETCH_HEAD
        # this is WAY harder than finding upper

        #### SUPER NAIVE ######
        #
        #   This probably only works with very basic sentences, will do some more tests and research
        #
<<<<<<< HEAD
        
        #   edit: Maybe it actually works fine. Who knows
        
=======

>>>>>>> FETCH_HEAD
        NPcodes = []
        PPcodes = []
        VPcodes = []

        for child in self.children:
            if isinstance(child, NounPhrase):
                NPcodes += child.get_meaning()
            elif isinstance(child, PrepPhrase):
                PPcodes += (child.get_meaning())
            elif isinstance(child, VerbPhrase):
                VPcodes += child.get_meaning()[1]
            elif child.label in "SBAR":
                for ch in (
                        child.children[0].children if child.label == "SBAR" else child.children):
                    if isinstance(ch, NounPhrase):
                        NPcodes += ch.get_meaning()
                    elif isinstance(ch, PrepPhrase):
                        PPcodes += ch.get_meaning()
                    elif isinstance(ch, VerbPhrase):
                        VPcodes += ch.get_meaning()[1]

        if NPcodes == []:
            if PPcodes == []:
                try:
                    
                    return VPcodes
                except:
                    return ""
            self.lower = PPcodes
            return PPcodes
        self.lower = NPcodes
        return NPcodes

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

class Event:

    def __init__(self, str, text, date):
        self.treestr = str.replace(')', ' )')
        self.parse = ""
        self.agent = ""
        self.ID = -1
        self.actor = ""
        self.date = date
<<<<<<< HEAD
        self.longlat = (-1,-1)
        self.verbs = []
        self.tree = self.str_to_tree(str[1:-1].strip())
        self.txt = text
        self.verb_analysis = {}
    
    def str_to_tree(self,str):
        root = Phrase(str[1],self.date)
=======
        self.longlat = (-1, -1)
        self.tree = self.str_to_tree(str[1:-1].strip())
        self.txt = text

    def str_to_tree(self, str):
        root = Phrase(str[1], self.date)
>>>>>>> FETCH_HEAD
        level_stack = [root]
        for element in str[2:].split():
            if '(' in element:
                lab = element[1:]
                if lab == "NP":
                    new = NounPhrase(lab, self.date)
                elif lab == "VP":
<<<<<<< HEAD
                    new = VerbPhrase(lab,self.date)
                    self.verbs.append(new)
=======
                    new = VerbPhrase(lab, self.date)
>>>>>>> FETCH_HEAD
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

<<<<<<< HEAD

    def get_events(self):
        events = []
        for v in self.verbs:
            scopes = v.get_meaning()
            code = v.get_code()
        
            if not code == "---" and not [] in scopes and not "" in scopes:
                #print("SRC: ",scopes[0],"TARG ",scopes[1],"CODE ",code)
                srcs = scopes[0]
                targs = scopes[1]
                for src in srcs:
                    for targ in targs:
                        #if not (src == targ and code == '010'): # ... said it ...
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
    
=======
    def print_to_file(self, root, file=""):
>>>>>>> FETCH_HEAD
        print("""
                    \\begin{tikzpicture}[scale= .25]
                    \\Tree""", file=file, end=" ")

        self.print_tree(root, "", file)
        print("""\\end{tikzpicture}
                      \\newpage
                    """, file=file)

    def print_tree(self, root, indent="", f=""):
        # This prints a LaTeX formatted document of the tree
        print(
            "[." +
            root.label.replace(
                "$",
                ""),
            ("{\\bf " +
             root.text +
             "}" if not root.text == "" else ""),
            file=f,
            end=" ")
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
<<<<<<< HEAD
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
=======
                    k += "+" + i
            j = ""
            print(m)
            if m[1] is None:
                j == ""
            else:
                for g in m[1]:
                    j += "+" + g
            print("[.{\it Upper " + k + ", Lower " + j + "}", file=f, end=" ")
        for child in root.children:
            self.print_tree(child, indent + "\t", f)
        if root.label in ["NP", "VP"]:
            print(" ] ]", file=f, end=" \n")
>>>>>>> FETCH_HEAD
        else:
            print(" ]", file=f, end=" ")

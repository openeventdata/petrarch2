

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

    def get_meaning(self):
        return self.meaning


class NounPhrase(Phrase):

    def __init__(self, label, date):
        Phrase.__init__(self, label, date)

    def return_meaning(self):
        return self.meaning

    def check_date(self, match):

        code = None

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
                else:
                    if curdate >= int(date[0][1:]):
                        code = j[0]
            else:
                if curdate < int(date[1]):
                    if curdate >= int(date[0]):
                        code = j[0]
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
        option = 0
        pathleft = [({}, i, 0)]

        ##
        #
        #   Check for the meanings of its children. This method will be called on the children nodes as well
        #          if meaning has not already been determined, which it shouldn't have because these should be
        #          1-regular in-degree graphs,but who knows.
        ##

        while i < len(self.children):
            child = self.children[i]
            if match_in_progress != {}:
                if child.text in match_in_progress:
                    match_in_progress = match_in_progress[child.text]
                    pathleft.append((match_in_progress, i, 0))
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
                    continue
                else:
                    p = pathleft.pop()
                    i = p[1] + 1
                    match_in_progress = p[0]
                    option = p[2] - 1
                    continue

            else:
                if child.label[:2] in ["NN", "JJ", "DT"]:
                    text = child.text
                    if option == 0 and text in PETRglobals.ActorDict:
                        dict_entry = (text, 0)
                    elif text in PETRglobals.AgentDict:
                        dict_entry = (text, 1)
                    try:
                        match_in_progress = dicts[dict_entry[1]][dict_entry[0]]
                        pathleft.append(({}, i, dict_entry[1] + 1))
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
                    print("SEARCHING FOR ANTECEDENT")
                    not_found = True
                    level = self.parent
                    while not_found and not level.parent is None:
                        if level.label in ["NP", "S", "SBAR"]:
                            level = level.parent
                            continue
                        # if level.label == "VP":
                        #    codes += level.get_upper()
                        for child in level.parent.children:
                            print("COMPARING", child.text)
                            # Do we just want to pick the first?
                            if isinstance(
                                    child, NounPhrase) and not child.get_meaning() == "":
                                not_found = False
                                codes += child.get_meaning()
                        level = level.parent
                elif child.label == "VP":
                    m = child.get_meaning()[1]
                    if not m == "":
                        VPcodes += m

            i += 1
            if(i >= len(self.children) and not match_in_progress == {}):
                if "#" in match_in_progress:
                    print(text)
                    match = match_in_progress['#']
                    print("MATCH", match)
                    if isinstance(match, list):
                        code = self.check_date(match)
                        if not code is None:
                            codes.append(code)
                    else:
                        codes.append(match)
                else:
                    p = pathleft.pop()
                    match_in_progress = p[0]
                    option = p[2]
                    if option == 2:
                        i = p[1] + 1
                        option = 0
                    else:
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

        if self.meaning == ['~']:
            self.meaning = NPcodes

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

    def get_upper(self):
        not_found = True
        level = self
        while not_found and not level.parent is None:
            for child in level.parent.children:
                # Do we just want to pick the first?
                if isinstance(
                        child, NounPhrase) and not child.get_meaning() == "":
                    self.upper = child.get_meaning()
                    not_found = False
                    self.get_upper = self.return_upper
                    return self.upper
            level = level.parent

    def get_lower(self):

        # this is WAY harder than finding upper

        #### SUPER NAIVE ######
        #
        #   This probably only works with very basic sentences, will do some more tests and research
        #

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
            return PPcodes
        return NPcodes


class Event:

    def __init__(self, str, text, date):
        self.treestr = str.replace(')', ' )')
        self.parse = ""
        self.agent = ""
        self.ID = -1
        self.actor = ""
        self.date = date
        self.longlat = (-1, -1)
        self.tree = self.str_to_tree(str[1:-1].strip())
        self.txt = text

    def str_to_tree(self, str):
        root = Phrase(str[1], self.date)
        level_stack = [root]
        for element in str[2:].split():
            if '(' in element:
                lab = element[1:]
                if lab == "NP":
                    new = NounPhrase(lab, self.date)
                elif lab == "VP":
                    new = VerbPhrase(lab, self.date)
                elif lab == "PP":
                    new = PrepPhrase(lab, self.date)
                else:
                    new = Phrase(lab, self.date)
                new.parent = level_stack[-1]
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

    def print_to_file(self, root, file=""):
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
        else:
            print(" ]", file=f, end=" ")

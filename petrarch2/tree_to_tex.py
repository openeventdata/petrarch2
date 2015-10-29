#!/usr/bin/python


import sys

file = """(ROOT (S (NP (DT A) (JJ Pakistani) (NN woman)) (VP (VBD believed) (VP (VBN linked) (PP (TO to) (NP (NP (NNP Al-Qaeda)) (SBAR (WHNP (WP who)) (S (VP (VBD shot) (PP (IN at) (NP (NNP US) (JJ military) (NNS officers))) (SBAR (IN while) (S (SBAR (IN in) (S (NP (NP (NN detention)) (PP (IN in) (NP (NNP Afghanistan)))) (VP (VBD was) (VP (VBN extradited) (NP-TMP (NNP Monday)) (PP (TO to) (NP (DT the) (NNP United) (NNPS States))) (SBAR (WHADVP (WRB where)) (S (NP (PRP she)) (VP (VBZ faces) (NP (NP (NN trial)) (PP (IN for) (NP (PRP$ her) (NNS actions)))))))))))  (NP (DT a) (NNP US) (NN attorney)) (VP (VBD said))))))))))) ))
"""

file = file.replace("(",'[.')
file = file.replace(")",' ]')
print file

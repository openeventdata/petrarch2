PETRARCH2 v. PETRARCH
======================================

PETRARCH has been totally redone. The logic now more strongly follows the tree structure
provided to us by the TreeBank parse.

The verb dictionary has been completely reworked. Because of the tree-like nature of the
new logic, the old linear patterns were insufficient. Patterns have now been formatted
to follow the following rules:

    1) All patterns match exactly one verb
    2) Patterns are minimal in complexity
    3) Nouns, noun phrases, and prepositional phrases are annotated
            (For more on this see the dictionary documentation)

Internally, Petrarch does not store verb codes as their CAMEO versions, rather as a
hex code that has been translated from CAMEO into a new scheme that better represents
the relationship between verb codes.

CoreNLP parsing abilities have been depracated in Petrarch, due to the difficulty of
maintaining these across different OSs and systems. Instead we recommend other options
in the README file.

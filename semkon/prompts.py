CORRECTNESS = """
The file {rel_path} contains one or more propositions
about the codebase. The proposition we are interested in is on line
{line_num}, and is followed by a proof.

State whether the proof is correct.

By "correct", we mean very high confidence that

A. each step of the proof is valid,
B. the proof does in fact prove the proposition, and 
C. the proof is supported by what the code does.

Mark the proof as "incorrect" if you understand it and the code but the proof
is wrong. Use "unknown" if e.g. you don't 100% know how an external library
works, or the proof is missing logical steps that you can't fill in.
Skeptically and rigorously check every claim with references to the code.

There's no requirement on the level of explicit detail that the proof uses. On
one extreme, it could simply be something like "see code". In this case, the
proof is valid (A) and proves the proposition (B), so your output depends on
whether it's "supported by what the code does" (C), i.e. your job is to inspect
the codebase to see if the proposition is true ("correct" proof) or false
("incorrect" proof), and you would report "unknown" if you can't tell.

If the proof references an explicitly-stated axiom (or "assumption", etc) found
in the codebase, you can assume that the axiom is true. If the proof references
another proposition from the codebase, you can assume that the other
proposition is true if the codebase provides a proof for it (you don't have to
check that proof) or if it's well-known or if a reference to the literature is
provided. However, if the proof we're checking is part of a cycle of
dependencies where the proof of one proposition relies on the truth of the
next, report this proof as "incorrect".
"""

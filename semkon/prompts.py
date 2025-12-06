# https://www.anthropic.com/engineering/claude-code-best-practices#:~:text=trigger%20extended%20thinking%20mode

CORRECTNESS = """
The file {rel_path} contains one or more propositions
about the codebase. The proposition we are interested in is on line
{line_num}, and is followed by a proof.

State whether the proof is correct.

By "correct", we mean very high confidence that each step of the proof is valid,
the proof does in fact prove the proposition, and that the proof is supported by
what the code does. Mark the proof as "incorrect" if you understand it and the
code but the proof is wrong. Use "unknown" if e.g. you don't 100% know how an
external library works, or the proof needs more detail. Think hard: Skeptically
and rigorously check every claim with references to the code. If the proof
references an explicitly-stated axiom (or "assumption", etc) found in the
codebase, you can assume that the axiom is true. If the proof references another
proposition from the codebase, you can assume that the other proposition is true
if the codebase provides a proof for it (you don't have to check that proof) or
if it's well-known or if a reference to the literature is provided. However, if
the proof we're checking is part of a cycle of dependencies where the proof of
one proposition relies on the truth of the next, report this proof as
"incorrect"."""

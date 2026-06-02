Semkon: _semantika kontrolilo_ (semantic checker)

Semkon uses LLMs to check the correctness of proofs written as developer
documentation in your codebase.

Pros: uses natural language, cons: relatively high cost

Requires either `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`)
or `ANTHROPIC_API_KEY`. If both
are set, Semkon uses Claude Code OAuth.
<!-- noted that Anthropic ToS oesn't allow CLAUDE_CODE_OAUTH_TOKEN
to be used for CI on multi-developer projects -->
Proof checks use the default opus model
and property extraction uses the default haiku model.

Basic usage: `semkon path/to/your/codebase`.
Results are printed to standard output as YAML. Exit code is 0 if all proofs
correct, 1 otherwise.

For information on options, run: `semkon --help`

Install for development: `pip install -e ".[dev]"`

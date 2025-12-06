Semkon: _semantika kontrolilo_ (semantic checker)

Semkon uses LLMs to check the correctness of proofs written as comments in your
codebase.

Requires Anthropic API key.

Basic usage: `semkon path/to/your/codebase`.
Results are printed to standard output as YAML. Exit code is 0 if all proofs
correct, 1 otherwise.

For information on options, run: `semkon --help`

Install for development: `pip install -e ".[dev]"`

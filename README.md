Semkon: _semantika kontrolilo_ (semantic checker)

Semkon uses LLMs to check the correctness of proofs written as developer
documentation in your codebase.

Pros: uses natural language, cons: relatively high cost

Requires `OPENROUTER_API_KEY` environment variable. You may have to explicitly
allow the model provider in your OpenRouter settings.
<!-- https://openrouter.ai/workspaces/default/guardrails/default/edit -->

Basic usage: `semkon path/to/your/codebase`.
Results are printed to standard output as YAML. Exit code is 0 if all proofs
correct, 1 otherwise.

For information on options, run: `semkon --help`

Install for development: `pip install -e ".[dev]"`

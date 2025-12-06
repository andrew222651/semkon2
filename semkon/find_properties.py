import math
import re
import sys
from pathlib import Path
from typing import cast

import gitignore_parser
from pydantic import BaseModel
from pydantic_ai import Agent
from tqdm import tqdm

from .data_models import PropertyLocation


MAX_FILE_SIZE_BYTES = 100 * 1024  # 100 KB


def _is_text_file(abs_path: Path) -> bool:
    try:
        abs_path.read_text()
    except UnicodeDecodeError:
        return False
    return True


def _is_small_file(abs_path: Path) -> bool:
    return abs_path.stat().st_size < MAX_FILE_SIZE_BYTES


FILTER_ALWAYS = [
    "**/.git/",
]


class _FileFilters:
    def __init__(self, directory: Path, filter_paths: list[str]):
        self._directory = directory
        raw_rules = [
            gitignore_parser.rule_from_pattern(filter_path, base_path=directory)
            for filter_path in filter_paths + FILTER_ALWAYS
        ]
        self._filter_rules = [r for r in raw_rules if r is not None]

    def get_abs_paths(
        self,
        directory: Path | None = None,
        gitignore_rules: list[gitignore_parser.IgnoreRule] | None = None,
    ) -> list[Path]:
        if directory is None:
            directory = self._directory
        if gitignore_rules is None:
            gitignore_rules = []

        ret = []

        my_gitignore_rules = list(gitignore_rules)

        gitignore_file = directory / ".gitignore"
        if (
            gitignore_file.exists()
            and gitignore_file.is_file()
            and _is_text_file(gitignore_file)
        ):
            raw_rules = [
                gitignore_parser.rule_from_pattern(line, base_path=directory)
                for line in gitignore_file.read_text().splitlines()
            ]
            my_gitignore_rules.extend(r for r in raw_rules if r is not None)

        for f in directory.iterdir():
            if (
                f.is_file()
                and _is_small_file(f)
                and _is_text_file(f)
                and not any(
                rule.match(f)
                for rule in my_gitignore_rules + self._filter_rules
            )
            ):
                ret.append(f)

        for dir in directory.iterdir():
            if dir.is_dir() and not any(
                rule.match(dir)
                for rule in my_gitignore_rules + self._filter_rules
            ):
                ret.extend(
                    self.get_abs_paths(dir, gitignore_rules=my_gitignore_rules)
                )

        return ret


def _get_rel_paths(directory: Path, filter_paths: list[str]) -> list[Path]:
    ff = _FileFilters(directory, filter_paths=filter_paths)
    abs_paths = ff.get_abs_paths()
    return sorted(p.relative_to(directory) for p in abs_paths)


def _format_file(content: str, rel_path: Path | None = None) -> str:
    file_name = str(rel_path) if rel_path else "<file>"
    content_lines = content.splitlines()

    if not content_lines:
        return f"""================
{file_name} (empty)
================


"""

    lines_chars = math.floor(math.log10(len(content_lines))) + 1
    content_w_lines = "\n".join(
        f"{i + 1:>{lines_chars}} | {line}"
        for i, line in enumerate(content_lines)
    )

    return f"""================
{file_name} (line numbers added)
================

{content_w_lines}


"""


class _Proposition(BaseModel):
    line_num: int
    statement: str
    proof: str


class _PropositionsResponse(BaseModel):
    data: list[_Proposition]


async def _extract_propositions(
    content: str, filter_str: str | None = None, rel_path: Path | None = None
) -> list[_Proposition]:
    if not re.search(r"\bproof\b", content, re.IGNORECASE):
        return []

    if filter_str is not None and filter_str.strip():
        filter_text = f"* {filter_str}"
    else:
        filter_text = ""

    initial_message = f"""The following file is taken from a repository of source code.
It may (or may not) contain one or more formal propositions that have something to do with the codebase.
These would be written as developer documentation. They may be called "properties", "theorems", etc.
Extract all such propositions that satisfy the following criteria:
* They are written in natural language, not a programming language.
* They are in a mathematical style, like a computer scientist would write.
* They are explicitly labeled as a "property" or "theorem" or similar,
  and have an associated explicitly-labeled proof.
{filter_text}

For example, there may be propositions about running times,
correctness, or auxiliary facts.

{_format_file(content, rel_path=rel_path)}"""
    # https://ai.pydantic.dev/models/anthropic/#install
    # https://platform.claude.com/docs/en/about-claude/models/overview#latest-models-comparison
    llm = Agent('anthropic:claude-haiku-4-5', output_type=_PropositionsResponse)

    result = await llm.run(initial_message)
    return cast(_PropositionsResponse, result.output).data


async def get_all_properties(
    directory: Path,
    filter_paths: list[str],
    filter_str: str | None,
) -> list[PropertyLocation]:
    ret = []
    
    rel_paths = _get_rel_paths(directory, filter_paths=filter_paths)
    print("Searching for properties in files...", file=sys.stderr)
    for rel_path in tqdm(rel_paths):
        properties = await _extract_propositions(
            content=(directory / rel_path).read_text(),
            filter_str=filter_str,
            rel_path=rel_path,
        )
        for prop in properties:
            ret.append(PropertyLocation(
                rel_path=rel_path,
                line_num=prop.line_num,
            ))
    
    return ret

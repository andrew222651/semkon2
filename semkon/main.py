import logging
import sys
from pathlib import Path
from typing import Annotated

import cyclopts
import yaml
from tqdm import tqdm

from .claude_code import check_proof
from .data_models import PropertyResult
from .find_properties import get_all_properties


app = cyclopts.App()


@app.default
async def main(
    directory: Annotated[
        Path,
        cyclopts.Parameter(help="Repo to analyze"),
    ] = Path("."),
    filter_path: Annotated[
        list[str] | None,
        cyclopts.Parameter(
            help="Path to exclude from search, in .gitignore format. Repeat as needed.",
        ),
    ] = None,
    property_filter: Annotated[
        str | None,
        cyclopts.Parameter(
            help="Natural language instructions on which properties to check."
        ),
    ] = None,
):
    directory = directory.resolve()
    properties = await get_all_properties(
        directory=directory,
        filter_paths=filter_path or [],
        filter_str=property_filter,
    )

    data = []

    print("Checking proofs...", file=sys.stderr)
    for p in tqdm(properties):
        r = await check_proof(directory, p)
        v = PropertyResult(property_location=p, correctness_explanation=r)
        data.append(v.model_dump(mode="json"))

    print(yaml.dump(data, sort_keys=False))

    if any(
        v["correctness_explanation"]["correctness"] != "correct"
        for v in data
    ):
        exit(1)


if __name__ == "__main__":
    app()

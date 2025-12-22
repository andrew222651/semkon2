import asyncio
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Annotated

import cyclopts
import yaml

from .claude_code import check_proof
from .data_models import PropertyResult
from .find_properties import get_all_properties


app = cyclopts.App()

def run_in_process(directory, p):
    print("Checking", p, file=sys.stderr)
    return asyncio.run(check_proof(directory, p))

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
    concurrency: Annotated[
        int,
        cyclopts.Parameter(
            help="Number of concurrent proof checks to run.",
        ),
    ] = 2,
    
):
    directory = directory.resolve()
    properties = await get_all_properties(
        directory=directory,
        filter_paths=filter_path or [],
        filter_str=property_filter,
    )

    print("Checking proofs...", file=sys.stderr)

    with ProcessPoolExecutor(max_workers=concurrency) as executor:
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(executor, run_in_process, directory, p)
            for p in properties
        ]

        results = await asyncio.gather(*tasks)

    data = [
        PropertyResult(
            property_location=p, correctness_explanation=r
        ).model_dump(mode="json")
        for p, r in zip(properties, results)
    ]

    print(yaml.dump(data, sort_keys=False))

    if any(
        v["correctness_explanation"]["correctness"] != "correct"
        for v in data
    ):
        exit(1)


if __name__ == "__main__":
    app()

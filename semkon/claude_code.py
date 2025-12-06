from pathlib import Path
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query, SandboxSettings

from .data_models import CorrectnessExplanation, PropertyLocation
from .prompts import CORRECTNESS


def _run_query_sync(prompt: str, options: ClaudeAgentOptions):
    async def _inner():
        ret = None
        # have to let the async generator run to completion to avoid errors
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "structured_output") and ret is None:
                ret = message.structured_output
        if ret is None:
            raise RuntimeError("No structured output received")
        else:
            return ret

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_inner())
    finally:
        loop.close()


async def check_proof(
    directory: Path,
    property_location: PropertyLocation,
) -> CorrectnessExplanation:
    prompt = CORRECTNESS.format(
        rel_path=property_location.rel_path,
        line_num=property_location.line_num,
    )

    options = ClaudeAgentOptions(
        model="claude-opus-4-5",
        output_format={
            "type": "json_schema",
            "schema": CorrectnessExplanation.model_json_schema()
        },
        cwd=directory,
        allowed_tools=["ReadFile", "Bash", "WebFetch", "WebSearch"],
        sandbox=SandboxSettings(
            enabled=True,
        )
    )

    # have to use to_thread or there are errors
    structured = await asyncio.to_thread(_run_query_sync, prompt, options)
    return CorrectnessExplanation.model_validate(structured)

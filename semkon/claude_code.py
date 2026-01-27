import asyncio
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .data_models import CorrectnessExplanation, PropertyLocation
from .prompts import CORRECTNESS


def _run_query_sync(prompt: str, options: ClaudeAgentOptions):
    async def _inner():
        ret = None
        # have to let the async generator run to completion to avoid errors
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
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
    model: str,
) -> CorrectnessExplanation:
    """
    good models: opus 4.5, kimi k2.5
    bad models: haiku 4.5, gemini 3
    """

    # https://openrouter.ai/docs/guides/community/anthropic-agent-sdk
    os.environ["ANTHROPIC_BASE_URL"] = "https://openrouter.ai/api"
    os.environ["ANTHROPIC_AUTH_TOKEN"] = os.environ["OPENROUTER_API_KEY"]
    os.environ["ANTHROPIC_API_KEY"] = ""
    os.environ["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model

    prompt = CORRECTNESS.format(
        rel_path=property_location.rel_path,
        line_num=property_location.line_num,
    )

    options = ClaudeAgentOptions(
        model="opus",
        output_format={
            "type": "json_schema",
            "schema": CorrectnessExplanation.model_json_schema()
        },
        cwd=directory,
        allowed_tools=["ReadFile", "Bash", "WebFetch", "WebSearch"],
    )

    # have to use to_thread or there are errors
    structured = await asyncio.to_thread(_run_query_sync, prompt, options)
    return CorrectnessExplanation.model_validate(structured)

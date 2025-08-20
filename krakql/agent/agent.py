from venv import logger
from typing import AsyncGenerator

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.agents import BaseAgent
from litellm import override

from .sub_agents.field_advisor import FieldAdvisorAgent
from .sub_agents.argument_advisor import ArgumentAdvisorAgent


class KrakQLAgent(BaseAgent):
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for KrakQL.
        The state will contains the agent to call under the key "role".
        """
        
        # Get the content
        if ctx.session.state["role"] is None:
            yield Event(error_message="Role not defined. Please select one of FieldAdvisor or ArgumentAdvisor.")
        if ctx.session.state["role"] == "FieldAdvisor":
            async for event in self.sub_agents[0].run_async(ctx):
                #logger.info(f"[{self.name}] Event from FieldAdvisor: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event
        if ctx.session.state["role"] == "ArgumentAdvisor":
            async for event in self.sub_agents[1].run_async(ctx):
                #logger.info(f"[{self.name}] Event from ArgumentAdvisor: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event
        # Default
        yield Event(error_message="Role not supported. Please select one of FieldAdvisor or ArgumentAdvisor.")

krakQLAgent = KrakQLAgent(
    name="KrakQLAgent",
    description=("You are KrakQL, an LLM-powered agent designed to perform blind GraphQL introspection and retrieve the schema of a GraphQL API."),
    #instruction=prompts.KrakQLAgentInstruction,
    sub_agents=[FieldAdvisorAgent, ArgumentAdvisorAgent],
)

root_agent = krakQLAgent
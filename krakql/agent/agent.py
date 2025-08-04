from google.adk.agents import SequentialAgent

from .sub_agents.field_advisor import FieldAdvisorAgent


KrakQLAgent = SequentialAgent(
    name="KrakQLAgent",
    description=("You are KrakQL, an LLM-powered agent designed to perform blind GraphQL introspection and retrieve the schema of a GraphQL API."),
    #instruction=prompts.KrakQLAgentInstruction,
    sub_agents=[ FieldAdvisorAgent],
)

root_agent = KrakQLAgent
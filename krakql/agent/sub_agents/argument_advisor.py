from google.adk.agents import LlmAgent
from krakql.agent.prompts import ArgumentAdvisorSystemPrompt 
from krakql.agent.config import MODEL

ArgumentAdvisorAgent = LlmAgent(
    model=MODEL,
    name="ArgumentAdvisorAgent",
    instruction=ArgumentAdvisorSystemPrompt,
    output_key="argument_advisor_output",
    include_contents="none",
)

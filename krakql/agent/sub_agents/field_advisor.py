from google.adk.agents import LlmAgent
from krakql.agent.prompts import FieldAdvisorSystemPrompt 
from krakql.agent.config import MODEL

FieldAdvisorAgent = LlmAgent(
    model=MODEL,
    name="FieldAdvisorAgent",
    instruction=FieldAdvisorSystemPrompt,
    output_key="field_advisor_output",
    include_contents="none",
)

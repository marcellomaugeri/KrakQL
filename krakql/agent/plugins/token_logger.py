from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from krakql.entities.context import file_log

class TokenCounterLoggerPlugin(BasePlugin):
    """A custom plugin that counts token usage."""

    def __init__(self) -> None:
        """Initialize the plugin with counters."""
        super().__init__(name="token_counter_logger")
        
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> None:
        """Log the fields of the LLM response."""
        prompt_token_count = llm_response.usage_metadata.prompt_token_count # Input tokens
        candidates_token_count = llm_response.usage_metadata.candidates_token_count # Output tokens

        file_log().info(f"(# I/O Tokens): {prompt_token_count},{candidates_token_count}")
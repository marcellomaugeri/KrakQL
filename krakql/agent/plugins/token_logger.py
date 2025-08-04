from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
import logging

class TokenCounterLoggerPlugin(BasePlugin):
    """A custom plugin that counts token usage."""

    def __init__(self) -> None:
        """Initialize the plugin with counters."""
        super().__init__(name="token_counter_logger")
        self.input_tokens = 0
        self.output_tokens = 0
        
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> None:
        """Log the fields of the LLM response."""
        logging.info(f"LLM Response: {llm_response}")
        prompt_token_count = llm_response.usage_metadata.prompt_token_count # Input tokens
        candidates_token_count = llm_response.usage_metadata.candidates_token_count # Output tokens

        self.input_tokens += prompt_token_count
        self.output_tokens += candidates_token_count

        logging.info(f"Input tokens: {prompt_token_count}, Output tokens: {candidates_token_count}, Total input tokens: {self.input_tokens}, Total output tokens: {self.output_tokens}")
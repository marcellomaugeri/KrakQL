import asyncio
from collections import Counter
from typing import List, Optional, Dict, Tuple
from threading import Lock

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from krakql.agent.agent import root_agent as KrakQLAgent
from krakql.agent.prompts import FieldAdvisorPromptTemplate, ArgumentAdvisorPromptTemplate
from krakql.entities.context import log


class KrakQLAgentSingleton:
    """Simple singleton for KrakQL agent with synchronous initialization"""
    
    _instance: Optional['KrakQLAgentSingleton'] = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs) -> 'KrakQLAgentSingleton':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model: str = 'openai/gpt-5-nano'):
        if hasattr(self, '_initialized'):
            log().warning(f"KrakQLAgentSingleton is already initialized with model: {self.model}")
            return
            
        self._initialized = True
        # per-context counters keyed by (input_document, source)
        # source is e.g. 'fields' or 'args'
        self.tried_counters: Dict[Tuple[str, str], Counter] = {}
        
        # Initialize session and runner
        self.app_name = "krakql_app"
        self.user_id = "krakql_user"
        self.session_id = "krakql_session"
        self.session = None # Session must be initialised asynchronously
    
        # assign model
        self.model = model
        self._async_lock = asyncio.Lock()  # Add this line
        
        # Setup session service and runner
        self.session_service = InMemorySessionService()
        self.agent = KrakQLAgent
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

    def format_field_advisor_prompt(self, current_schema: str, input_document: str) -> str:
        """Format the prompt with the current schema and to avoid fields"""
        key = (input_document, "field")
        counter = self.tried_counters.get(key, Counter())
        if counter:
            top_tried = [field for field, _ in counter.most_common(10)]
            avoid_list = ", ".join(top_tried)
        else:
            avoid_list = "NONE"
        
        return FieldAdvisorPromptTemplate.format(
            current_schema=current_schema,
            document_path=input_document,
            fields_to_avoid=avoid_list
        )
        
    def format_argument_advisor_prompt(self, current_schema: str, input_document: str) -> str:
        """Format the prompt with the current schema and to avoid arguments"""
        key = (input_document, "argument")
        counter = self.tried_counters.get(key, Counter())
        if counter:
            top_tried = [arg for arg, _ in counter.most_common(10)]
            avoid_list = ", ".join(top_tried)
        else:
            avoid_list = "NONE"

        return ArgumentAdvisorPromptTemplate.format(
            current_schema=current_schema,
            document_path=input_document,
            arguments_to_avoid=avoid_list
        )

    async def init_session(self):
        if not self.session:
            self.session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )

    async def suggest_new_fields(self, current_schema: str, input_document: str) -> List[str]:
        """Get field advice from the KrakQL agent"""
        async with self._async_lock:
            prompt = self.format_field_advisor_prompt(current_schema, input_document)
            log().error(f"Prompt for FieldAdvisor: {prompt}")
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
                            
            final_response = ""
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=user_content,
                state_delta={"role": "FieldAdvisor"}
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break
            
            # Get the candidate, comma-separated fields
            candidate_fields = [field.strip() for field in final_response.split(",")]
            # Update tried fields counter
            self.update_tried_names(candidate_fields, input_document, "field")
            return candidate_fields
        
    async def suggest_new_arguments(self, current_schema: str, input_document: str) -> List[str]:
        """Get argument advice from the KrakQL agent"""
        async with self._async_lock:
            prompt = self.format_argument_advisor_prompt(current_schema, input_document)
            log().error(f"Prompt for ArgumentAdvisor: {prompt}")
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )

            final_response = ""
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=user_content,
                state_delta={"role": "ArgumentAdvisor"}
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break

            # Get the candidate, comma-separated arguments
            candidate_arguments = [arg.strip() for arg in final_response.split(",")]
            # Update tried arguments counter
            self.update_tried_names(candidate_arguments, input_document, "argument")
            return candidate_arguments

    def get_counters(self, input_document: Optional[str] = None, source: Optional[str] = None):
        """Get counters:
        - if both input_document and source provided, return that Counter (or empty Counter)
        - otherwise return the whole mapping
        """
        if input_document is not None and source is not None:
            return self.tried_counters.get((input_document, source), Counter())
        return self.tried_counters

    def update_tried_names(self, names: List[str], input_document: str, source: str):
        """Update the counter of tried items for a specific (document, source) context"""
        key = (input_document, source)
        if key not in self.tried_counters:
            self.tried_counters[key] = Counter()
        counter = self.tried_counters[key]
        for name in names:
            if name and name.strip():
                clean_name = name.strip().lower()
                counter[clean_name] += 1
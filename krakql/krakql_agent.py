import asyncio
from collections import Counter
from typing import List, Optional
from threading import Lock

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from krakql.agent.agent import root_agent as KrakQLAgent
from krakql.agent.prompts import FieldAdvisorPromptTemplate
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
        self.tried_fields_counter = Counter()
        
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

    def format_prompt(self, current_schema: str, input_document: str) -> str:
        """Format the prompt with the current schema and avoided fields"""
        if self.tried_fields_counter:
            # Get top 10 most frequently tried fields
            top_tried = [field for field, _ in self.tried_fields_counter.most_common(10)]
            avoid_list = ", ".join(top_tried)
        else:
            avoid_list = "none"
        
        return FieldAdvisorPromptTemplate.format(
            current_schema=current_schema,
            document_path=input_document.replace("FUZZ", "..."),
            fields_to_avoid=avoid_list
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
            prompt = self.format_prompt(current_schema, input_document)
            log().error(f"Prompt for FieldAdvisor: {prompt}")
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
                            
            final_response = ""
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=user_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break
            
            # Get the candidate, comma-separated fields
            candidate_fields = [field for field in final_response.split(",") if field.strip()]
            # Update tried fields counter
            self.update_tried_fields(candidate_fields)
            return candidate_fields

    def _get_counters(self):
        """Get the current counters for tried fields"""
        return self.tried_fields_counter

    def update_tried_fields(self, fields: List[str]):
        """Update the counter of tried fields"""
        for field in fields:
            if field and field.strip():
                clean_field = field.strip().lower()
                self.tried_fields_counter[clean_field] += 1